"""
诊断代理实现

实现自主诊断的AI Agent
"""

import json
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.agent.base import (
    BaseAgent,
    AgentState,
    AgentAction,
    AgentResult,
    AgentStatus,
    ActionType,
)
from src.agent.tools import AgentTools, ToolResult
from src.agent.memory import AgentMemory
from src.agent.prompts import PromptTemplates
from src.core.ai_analyzer import AIAnalyzer, AnalysisResult, SuggestedCommand
from src.core.log_parser import LogEntry, LogStatistics
from src.core.command_whitelist import CommandWhitelist
from src.core.ssh_executor import SSHConfig, CommandResult
from src.core.audit_logger import get_audit_logger, AuditLogger
from src.utils.exceptions import AgentMaxRoundsExceededError, AgentActionFailedError


@dataclass
class DiagnosticContext:
    """诊断上下文"""

    log_file: str
    entries: List[LogEntry]
    statistics: LogStatistics
    hosts: List[str]
    initial_analysis: Optional[AnalysisResult] = None


class DiagnosticAgent(BaseAgent):
    """
    诊断代理

    自主进行网络故障诊断的AI代理
    """

    def __init__(
        self,
        ai_analyzer: AIAnalyzer,
        whitelist: Optional[CommandWhitelist] = None,
        audit_logger: Optional[AuditLogger] = None,
        ssh_configs: Optional[Dict[str, SSHConfig]] = None,
        max_rounds: int = 5,
        mock_mode: bool = False,
    ):
        """
        初始化诊断代理

        Args:
            ai_analyzer: AI分析器
            whitelist: 命令白名单
            audit_logger: 审计日志记录器
            ssh_configs: SSH配置字典
            max_rounds: 最大执行轮数
            mock_mode: 是否使用模拟模式
        """
        super().__init__(max_rounds=max_rounds)

        self.ai_analyzer = ai_analyzer
        self.whitelist = whitelist or CommandWhitelist()
        self.audit_logger = audit_logger or get_audit_logger()
        self.mock_mode = mock_mode

        # 初始化工具和记忆
        self.tools = AgentTools(
            ai_analyzer=ai_analyzer,
            whitelist=self.whitelist,
            audit_logger=self.audit_logger,
            ssh_configs=ssh_configs,
            mock_mode=mock_mode,
        )
        self.memory = AgentMemory()

        # 诊断上下文
        self._context: Optional[DiagnosticContext] = None
        self._executed_commands: List[str] = []

    async def diagnose(
        self,
        log_file: str,
        entries: List[LogEntry],
        statistics: LogStatistics,
        hosts: Optional[List[str]] = None,
    ) -> AgentResult:
        """
        执行诊断

        Args:
            log_file: 日志文件路径
            entries: 日志条目
            statistics: 统计信息
            hosts: 目标主机列表

        Returns:
            诊断结果
        """
        start_time = time.time()

        # 初始化上下文
        self._context = DiagnosticContext(
            log_file=log_file,
            entries=entries,
            statistics=statistics,
            hosts=hosts or ["localhost"],
        )

        self.state.status = AgentStatus.IDLE
        self.state.started_at = datetime.now()

        # 记录审计日志
        self.audit_logger.log(
            action="agent_diagnose",
            result="started",
            details={
                "log_file": log_file,
                "hosts": self._context.hosts,
                "max_rounds": self.state.max_rounds,
            },
        )

        try:
            # 第一轮：初始分析
            await self._initial_analysis()

            # 后续轮次：执行命令和观察
            while self.state.current_round < self.state.max_rounds:
                action = await self.run_cycle()

                # 检查是否应该停止
                if action.type == ActionType.REPORT:
                    break

                if action.type == ActionType.DECIDE:
                    # 检查是否可以做出结论
                    if self._can_conclude():
                        break

            # 生成最终报告
            final_report = await self._generate_report()

            # 构建结果
            result = AgentResult(
                success=True,
                diagnosis=self._context.initial_analysis,
                actions_taken=self.actions,
                command_results=self._get_command_results(),
                final_report=final_report,
                rounds_completed=self.state.current_round,
                total_duration=time.time() - start_time,
            )

            self.state.status = AgentStatus.COMPLETED

            self.audit_logger.log(
                action="agent_diagnose",
                result="success",
                details={
                    "rounds": result.rounds_completed,
                    "duration": result.total_duration,
                },
            )

            return result

        except Exception as e:
            self.state.status = AgentStatus.FAILED

            self.audit_logger.log(
                action="agent_diagnose",
                result="failure",
                error_message=str(e),
            )

            return AgentResult(
                success=False,
                actions_taken=self.actions,
                final_report=f"诊断失败: {str(e)}",
                rounds_completed=self.state.current_round,
                total_duration=time.time() - start_time,
                errors=[str(e)],
            )

    async def _initial_analysis(self) -> None:
        """执行初始日志分析"""
        action = self._create_action(
            ActionType.ANALYZE,
            "分析日志文件",
            {"log_file": self._context.log_file},
        )

        self.state.status = AgentStatus.THINKING

        # 调用AI分析
        try:
            analysis = await self.ai_analyzer.analyze(
                self._context.entries,
                self._context.statistics,
            )
            self._context.initial_analysis = analysis
            action.success = True
            action.result = analysis.to_dict()

            # 记录事实
            self.memory.add_fact(
                f"问题类型: {analysis.problem_type}",
                source="AI分析",
                confidence=analysis.confidence,
            )

            for i, cause in enumerate(analysis.possible_causes[:3]):
                self.memory.add_hypothesis(
                    hypothesis=cause,
                    evidence=["AI分析识别的可能原因"],
                    confidence=analysis.confidence * (0.9 - i * 0.1),
                )

        except Exception as e:
            action.success = False
            action.error = str(e)
            raise AgentActionFailedError(f"初始分析失败: {e}", action="analyze")

        self.actions.append(action)
        self.state.current_round += 1

    async def think(self, context: Dict[str, Any]) -> AgentAction:
        """
        思考下一步操作

        Args:
            context: 当前上下文

        Returns:
            决定的操作
        """
        # 获取当前假设
        hypotheses = self.memory.get_active_hypotheses()

        # 获取建议命令
        suggested_commands = (
            self._context.initial_analysis.suggested_commands
            if self._context and self._context.initial_analysis
            else []
        )

        # 过滤已执行的命令
        pending_commands = [
            cmd
            for cmd in suggested_commands
            if cmd.command not in self._executed_commands
        ]

        if not pending_commands:
            # 没有更多命令，准备生成报告
            return self._create_action(
                ActionType.REPORT,
                "生成诊断报告",
            )

        # 选择下一个命令
        next_command = pending_commands[0]

        # 验证命令
        is_valid, cmd_info = self.whitelist.validate(next_command.command)

        if not is_valid:
            # 跳过无效命令
            self._executed_commands.append(next_command.command)
            return self._create_action(
                ActionType.EXECUTE,
                f"跳过无效命令: {next_command.command}",
                {"command": next_command.command, "valid": False},
            )

        return self._create_action(
            ActionType.EXECUTE,
            f"执行诊断命令: {next_command.description}",
            {
                "command": next_command.command,
                "category": next_command.category,
                "description": next_command.description,
                "valid": True,
            },
        )

    async def act(self, action: AgentAction) -> Any:
        """
        执行操作

        Args:
            action: 要执行的操作

        Returns:
            操作结果
        """
        self.state.status = AgentStatus.EXECUTING

        if action.type == ActionType.EXECUTE:
            params = action.parameters
            command = params.get("command")

            if not command or not params.get("valid", True):
                return None

            # 执行命令
            host = self._context.hosts[0] if self._context else "localhost"
            result = await self.tools.execute_command(command, host=host)
            self._executed_commands.append(command)

            # 记录审计日志
            self.audit_logger.log_agent_action(
                action_type="execute_command",
                result="success" if result.success else "failure",
                round_num=self.state.current_round,
                host=host,
                command=command,
            )

            return result

        elif action.type == ActionType.REPORT:
            return await self._generate_report()

        return None

    async def observe(self, action: AgentAction, result: Any) -> Dict[str, Any]:
        """
        观察结果

        Args:
            action: 执行的操作
            result: 操作结果

        Returns:
            观察结果
        """
        self.state.status = AgentStatus.OBSERVING

        observation: Dict[str, Any] = {
            "action_id": action.id,
            "action_type": action.type.value,
            "success": False,
            "findings": [],
        }

        if action.type == ActionType.EXECUTE and isinstance(result, ToolResult):
            observation["success"] = result.success

            if result.success and result.data:
                output = result.data.get("stdout", "")
                observation["output"] = output[:1000]  # 限制输出长度

                # 分析输出，提取关键信息
                findings = self._extract_findings(output)
                observation["findings"] = findings

                # 更新假设
                self._update_hypotheses(findings)

            elif result.error:
                observation["error"] = result.error
                self.memory.add_fact(
                    f"命令执行失败: {result.error}",
                    source=action.parameters.get("command", "unknown"),
                )

        # 记录到记忆
        self.memory.add_entry(
            round=self.state.current_round,
            action_type=action.type.value,
            action_description=action.description,
            observation=str(observation.get("output", observation.get("error", "")))[:500],
            result_summary=f"成功: {observation['success']}",
        )

        return observation

    def _extract_findings(self, output: str) -> List[str]:
        """从命令输出中提取关键发现"""
        findings = []

        # 检查常见问题模式
        patterns = {
            "timeout": ["timeout", "timed out", "超时"],
            "connection_refused": ["connection refused", "连接被拒绝"],
            "dns_failure": ["no such host", "dns", "解析失败", "NXDOMAIN"],
            "high_latency": ["time=", "latency", "延迟"],
            "packet_loss": ["packet loss", "丢失", "100% packet loss"],
        }

        output_lower = output.lower()

        for finding_type, keywords in patterns.items():
            for keyword in keywords:
                if keyword.lower() in output_lower:
                    findings.append(f"检测到{finding_type}: {keyword}")
                    break

        return findings

    def _update_hypotheses(self, findings: List[str]) -> None:
        """根据发现更新假设"""
        for finding in findings:
            # 简单的假设更新逻辑
            if "timeout" in finding.lower():
                self.memory.add_fact(
                    "存在超时问题",
                    source="命令输出",
                    confidence=0.8,
                )
            elif "connection_refused" in finding.lower():
                self.memory.add_fact(
                    "连接被拒绝",
                    source="命令输出",
                    confidence=0.9,
                )
            elif "dns" in finding.lower():
                self.memory.add_fact(
                    "存在DNS问题",
                    source="命令输出",
                    confidence=0.8,
                )

    def _can_conclude(self) -> bool:
        """检查是否可以得出结论"""
        # 如果有高置信度的确认假设，可以结束
        for h in self.memory.hypotheses:
            if h["status"] == "confirmed" and h["confidence"] > 0.8:
                return True

        # 如果已经执行了足够的命令
        if len(self._executed_commands) >= 3:
            return True

        return False

    async def _generate_report(self) -> str:
        """生成诊断报告"""
        sections = [
            "# 网络诊断报告",
            "",
            f"**诊断时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**执行轮次**: {self.state.current_round}",
            "",
        ]

        # 问题概述
        if self._context and self._context.initial_analysis:
            analysis = self._context.initial_analysis
            sections.extend(
                [
                    "## 问题概述",
                    "",
                    f"- **问题类型**: {analysis.problem_type}",
                    f"- **风险等级**: {analysis.risk_level}",
                    f"- **置信度**: {analysis.confidence:.0%}",
                    "",
                ]
            )

        # 发现的事实
        facts = self.memory.get_facts()
        if facts:
            sections.append("## 发现的事实")
            sections.append("")
            for fact, info in facts.items():
                sections.append(f"- {fact} (置信度: {info['confidence']:.0%})")
            sections.append("")

        # 假设验证
        if self.memory.hypotheses:
            sections.append("## 假设验证")
            sections.append("")
            for h in self.memory.hypotheses:
                status = {
                    "confirmed": "✓ 已确认",
                    "rejected": "✗ 已排除",
                    "active": "? 待验证",
                }.get(h["status"], h["status"])
                sections.append(f"- {status}: {h['hypothesis']} (置信度: {h['confidence']:.0%})")
            sections.append("")

        # 执行的命令
        if self._executed_commands:
            sections.append("## 执行的诊断命令")
            sections.append("")
            for cmd in self._executed_commands:
                sections.append(f"- `{cmd}`")
            sections.append("")

        # 建议
        if self._context and self._context.initial_analysis:
            sections.append("## 建议的排查步骤")
            sections.append("")
            for i, cause in enumerate(self._context.initial_analysis.possible_causes, 1):
                sections.append(f"{i}. {cause}")
            sections.append("")

        return "\n".join(sections)

    def _get_command_results(self) -> List[CommandResult]:
        """获取所有命令执行结果"""
        results = []
        for action in self.actions:
            if action.type == ActionType.EXECUTE and isinstance(action.result, ToolResult):
                if action.result.success and action.result.data:
                    results.append(
                        CommandResult(
                            command=action.parameters.get("command", ""),
                            exit_code=action.result.data.get("exit_code", 0),
                            stdout=action.result.data.get("stdout", ""),
                            stderr=action.result.data.get("stderr", ""),
                            duration=action.result.data.get("duration", 0),
                            host=self._context.hosts[0] if self._context else "localhost",
                            timestamp=action.timestamp,
                        )
                    )
        return results

    async def close(self) -> None:
        """关闭资源"""
        await self.tools.close_all()
