"""
工具执行器模块

管理和执行AI建议的诊断命令
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Callable, Dict, Any
from uuid import uuid4

from src.core.ai_analyzer import SuggestedCommand
from src.core.command_whitelist import CommandWhitelist, WhitelistedCommand
from src.core.ssh_executor import SSHExecutor, SSHConfig, CommandResult
from src.core.audit_logger import get_audit_logger, AuditLogger
from src.utils.exceptions import (
    CommandNotAllowedError,
    ExecutionPlanError,
    ApprovalRequiredError,
    ExecutionTimeoutError,
)


@dataclass
class PlannedCommand:
    """计划执行的命令"""

    command: SuggestedCommand  # 原始建议命令
    validated_command: str  # 验证后的命令字符串
    whitelist_info: Optional[WhitelistedCommand] = None  # 白名单信息
    targets: List[str] = field(default_factory=list)  # 目标主机列表
    requires_approval: bool = True  # 是否需要审批
    risk_level: str = "low"  # 风险等级


@dataclass
class ExecutionPlan:
    """执行计划"""

    id: str  # 计划ID
    commands: List[PlannedCommand]  # 计划执行的命令
    targets: List[str]  # 目标主机列表
    created_at: datetime  # 创建时间
    total_commands: int  # 总命令数
    high_risk_count: int  # 高风险命令数
    requires_approval: bool  # 是否需要审批

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "commands": [
                {
                    "command": cmd.command.command,
                    "description": cmd.command.description,
                    "category": cmd.command.category,
                    "validated_command": cmd.validated_command,
                    "risk_level": cmd.risk_level,
                    "targets": cmd.targets,
                }
                for cmd in self.commands
            ],
            "targets": self.targets,
            "created_at": self.created_at.isoformat(),
            "total_commands": self.total_commands,
            "high_risk_count": self.high_risk_count,
            "requires_approval": self.requires_approval,
        }


@dataclass
class ExecutionSession:
    """执行会话"""

    id: str  # 会话ID
    plan: ExecutionPlan  # 执行计划
    status: str  # pending, running, completed, failed, cancelled
    started_at: Optional[datetime] = None  # 开始时间
    completed_at: Optional[datetime] = None  # 完成时间
    results: List[Dict[str, Any]] = field(default_factory=list)  # 执行结果
    errors: List[str] = field(default_factory=list)  # 错误信息

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "plan_id": self.plan.id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "results": self.results,
            "errors": self.errors,
        }


# 审批回调类型
ApprovalCallback = Callable[[ExecutionPlan], bool]


class ToolExecutor:
    """
    工具执行器

    管理命令验证、审批和执行流程
    """

    def __init__(
        self,
        whitelist: Optional[CommandWhitelist] = None,
        audit_logger: Optional[AuditLogger] = None,
        auto_approve_low_risk: bool = False,
    ):
        """
        初始化工具执行器

        Args:
            whitelist: 命令白名单
            audit_logger: 审计日志记录器
            auto_approve_low_risk: 是否自动批准低风险命令
        """
        self.whitelist = whitelist or CommandWhitelist()
        self.audit_logger = audit_logger or get_audit_logger()
        self.auto_approve_low_risk = auto_approve_low_risk

        # SSH连接池
        self._ssh_connections: Dict[str, SSHExecutor] = {}

    def create_plan(
        self,
        commands: List[SuggestedCommand],
        hosts: Optional[List[str]] = None,
        validate: bool = True,
    ) -> ExecutionPlan:
        """
        创建执行计划

        Args:
            commands: 建议的命令列表
            hosts: 目标主机列表
            validate: 是否验证命令

        Returns:
            执行计划

        Raises:
            CommandNotAllowedError: 命令不在白名单中
        """
        hosts = hosts or ["localhost"]
        planned_commands: List[PlannedCommand] = []
        high_risk_count = 0
        requires_approval = False

        for cmd in commands:
            # 验证命令
            whitelist_info = None
            if validate:
                try:
                    whitelist_info = self.whitelist.validate_or_raise(cmd.command)
                except CommandNotAllowedError:
                    # 如果命令不在白名单，标记为需要审批
                    pass

            # 确定风险等级
            risk_level = "unknown"
            cmd_requires_approval = True

            if whitelist_info:
                risk_level = whitelist_info.risk_level
                cmd_requires_approval = risk_level in ("medium", "high")
                if risk_level == "high":
                    high_risk_count += 1

            if cmd_requires_approval and not self.auto_approve_low_risk:
                requires_approval = True

            planned_commands.append(
                PlannedCommand(
                    command=cmd,
                    validated_command=cmd.command,
                    whitelist_info=whitelist_info,
                    targets=hosts,
                    requires_approval=cmd_requires_approval,
                    risk_level=risk_level,
                )
            )

        plan = ExecutionPlan(
            id=str(uuid4()),
            commands=planned_commands,
            targets=hosts,
            created_at=datetime.now(),
            total_commands=len(planned_commands),
            high_risk_count=high_risk_count,
            requires_approval=requires_approval,
        )

        self.audit_logger.log(
            action="plan_create",
            result="success",
            details={
                "plan_id": plan.id,
                "total_commands": plan.total_commands,
                "high_risk_count": plan.high_risk_count,
            },
        )

        return plan

    def preview(self, plan: ExecutionPlan) -> str:
        """
        生成执行计划预览

        Args:
            plan: 执行计划

        Returns:
            预览文本
        """
        lines = [
            "=" * 60,
            "执行计划预览",
            "=" * 60,
            f"计划ID: {plan.id}",
            f"创建时间: {plan.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"目标主机: {', '.join(plan.targets)}",
            f"命令总数: {plan.total_commands}",
            f"高风险命令: {plan.high_risk_count}",
            f"需要审批: {'是' if plan.requires_approval else '否'}",
            "",
            "命令列表:",
            "-" * 60,
        ]

        for i, cmd in enumerate(plan.commands, 1):
            risk_icon = "⚠️" if cmd.risk_level == "high" else ("⚡" if cmd.risk_level == "medium" else "✓")
            lines.append(f"\n{i}. [{risk_icon}] {cmd.command.description}")
            lines.append(f"   分类: {cmd.command.category}")
            lines.append(f"   风险: {cmd.risk_level}")
            lines.append(f"   命令: {cmd.validated_command}")
            lines.append(f"   目标: {', '.join(cmd.targets)}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    async def execute_with_approval(
        self,
        plan: ExecutionPlan,
        approval_callback: ApprovalCallback,
        ssh_configs: Optional[Dict[str, SSHConfig]] = None,
        stop_on_error: bool = False,
    ) -> ExecutionSession:
        """
        带审批的执行

        Args:
            plan: 执行计划
            approval_callback: 审批回调函数
            ssh_configs: SSH配置字典 (host -> config)
            stop_on_error: 遇错是否停止

        Returns:
            执行会话
        """
        session = ExecutionSession(
            id=str(uuid4()),
            plan=plan,
            status="pending",
        )

        # 检查是否需要审批
        if plan.requires_approval:
            approved = approval_callback(plan)
            if not approved:
                session.status = "cancelled"
                session.errors.append("Execution cancelled by user")
                self.audit_logger.log(
                    action="plan_execute",
                    result="cancelled",
                    details={"plan_id": plan.id, "session_id": session.id},
                )
                return session

        # 执行
        return await self._execute_plan(session, ssh_configs, stop_on_error)

    async def execute_interactive(
        self,
        plan: ExecutionPlan,
        ssh_configs: Optional[Dict[str, SSHConfig]] = None,
        stop_on_error: bool = False,
    ) -> ExecutionSession:
        """
        交互式执行（每个命令确认）

        Args:
            plan: 执行计划
            ssh_configs: SSH配置字典
            stop_on_error: 遇错是否停止

        Returns:
            执行会话
        """
        session = ExecutionSession(
            id=str(uuid4()),
            plan=plan,
            status="pending",
        )

        session.started_at = datetime.now()
        session.status = "running"

        for planned_cmd in plan.commands:
            # 交互式确认
            if planned_cmd.requires_approval:
                print(f"\n执行命令: {planned_cmd.validated_command}")
                print(f"描述: {planned_cmd.command.description}")
                print(f"风险等级: {planned_cmd.risk_level}")
                response = input("是否执行? [y/N]: ")
                if response.lower() != "y":
                    session.errors.append(f"Skipped: {planned_cmd.validated_command}")
                    continue

            # 执行命令
            for host in planned_cmd.targets:
                try:
                    result = await self._execute_on_host(
                        planned_cmd.validated_command,
                        host,
                        ssh_configs,
                    )
                    session.results.append(
                        {
                            "command": planned_cmd.validated_command,
                            "host": host,
                            "success": result.success,
                            "exit_code": result.exit_code,
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "duration": result.duration,
                        }
                    )

                    if stop_on_error and not result.success:
                        session.status = "failed"
                        session.errors.append(f"Command failed on {host}: {result.stderr}")
                        break

                except Exception as e:
                    session.errors.append(f"Error on {host}: {str(e)}")
                    if stop_on_error:
                        session.status = "failed"
                        break

            if session.status == "failed":
                break

        if session.status == "running":
            session.status = "completed"

        session.completed_at = datetime.now()

        self.audit_logger.log(
            action="plan_execute",
            result="success" if session.status == "completed" else "failure",
            details={
                "plan_id": plan.id,
                "session_id": session.id,
                "results_count": len(session.results),
                "errors_count": len(session.errors),
            },
        )

        return session

    async def execute_dry_run(
        self,
        plan: ExecutionPlan,
    ) -> ExecutionSession:
        """
        干运行（只验证，不实际执行）

        Args:
            plan: 执行计划

        Returns:
            执行会话
        """
        session = ExecutionSession(
            id=str(uuid4()),
            plan=plan,
            status="completed",
            started_at=datetime.now(),
            completed_at=datetime.now(),
        )

        for cmd in plan.commands:
            for host in cmd.targets:
                session.results.append(
                    {
                        "command": cmd.validated_command,
                        "host": host,
                        "success": True,
                        "exit_code": 0,
                        "stdout": "[DRY RUN] Command would be executed",
                        "stderr": "",
                        "duration": 0,
                    }
                )

        return session

    async def _execute_plan(
        self,
        session: ExecutionSession,
        ssh_configs: Optional[Dict[str, SSHConfig]],
        stop_on_error: bool,
    ) -> ExecutionSession:
        """执行计划"""
        session.started_at = datetime.now()
        session.status = "running"

        for planned_cmd in session.plan.commands:
            for host in planned_cmd.targets:
                try:
                    result = await self._execute_on_host(
                        planned_cmd.validated_command,
                        host,
                        ssh_configs,
                    )

                    session.results.append(
                        {
                            "command": planned_cmd.validated_command,
                            "host": host,
                            "success": result.success,
                            "exit_code": result.exit_code,
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "duration": result.duration,
                        }
                    )

                    if stop_on_error and not result.success:
                        session.status = "failed"
                        session.errors.append(f"Command failed: {result.stderr}")
                        break

                except Exception as e:
                    session.errors.append(f"{host}: {str(e)}")
                    if stop_on_error:
                        session.status = "failed"
                        break

            if session.status == "failed":
                break

        if session.status == "running":
            session.status = "completed"

        session.completed_at = datetime.now()

        return session

    async def _execute_on_host(
        self,
        command: str,
        host: str,
        ssh_configs: Optional[Dict[str, SSHConfig]],
    ) -> CommandResult:
        """在指定主机上执行命令"""
        if host == "localhost":
            # 本地执行
            return await self._execute_local(command)

        # SSH远程执行
        if ssh_configs and host in ssh_configs:
            config = ssh_configs[host]
        else:
            config = SSHConfig(host=host)

        executor = self._ssh_connections.get(host)
        if executor is None or not executor.is_connected:
            executor = SSHExecutor(config, self.audit_logger)
            await executor.connect()
            self._ssh_connections[host] = executor

        return await executor.execute(command)

    async def _execute_local(self, command: str) -> CommandResult:
        """本地执行命令"""
        start_time = datetime.now()

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await proc.communicate()
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            return CommandResult(
                command=command,
                exit_code=proc.returncode or 0,
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                duration=duration,
                host="localhost",
                timestamp=start_time,
            )

        except Exception as e:
            return CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration=0,
                host="localhost",
                timestamp=start_time,
            )

    async def close_all_connections(self) -> None:
        """关闭所有SSH连接"""
        for executor in self._ssh_connections.values():
            await executor.close()
        self._ssh_connections.clear()

    async def __aenter__(self) -> "ToolExecutor":
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        await self.close_all_connections()
