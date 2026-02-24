"""
Agent提示词模板
"""

from typing import List, Dict, Any, Optional


class PromptTemplates:
    """提示词模板集合"""

    # 系统提示词
    SYSTEM_PROMPT = """你是一个网络诊断专家Agent。你的任务是分析日志，执行诊断命令，找出网络问题的根本原因。

你可以使用以下操作：
1. analyze - 分析日志，识别问题
2. execute - 执行诊断命令（必须是白名单中的安全命令）
3. observe - 观察命令执行结果
4. decide - 根据观察结果做出判断
5. report - 生成诊断报告

诊断原则：
- 先分析日志了解大致问题方向
- 从简单测试开始（如ping, curl）
- 逐步深入，使用更具体的诊断命令
- 每次只执行必要的命令
- 及时总结发现，形成假设并验证

安全原则：
- 只执行白名单中的命令
- 不执行任何修改系统状态的命令
- 不访问敏感文件"""

    # 初始分析提示词
    ANALYZE_PROMPT = """分析以下日志信息，识别问题：

## 日志摘要
{log_summary}

## 错误日志
{error_logs}

请分析：
1. 问题类型是什么？
2. 可能的原因有哪些（按可能性排序）？
3. 建议首先执行什么诊断命令？

请输出JSON格式：
{{
    "problem_type": "问题类型",
    "possible_causes": ["原因1", "原因2"],
    "confidence": 0.8,
    "next_action": "execute",
    "next_command": "建议执行的命令",
    "reasoning": "选择此命令的原因"
}}"""

    # 命令结果分析提示词
    OBSERVE_PROMPT = """分析命令执行结果：

## 执行的命令
{command}

## 输出结果
{output}

## 当前假设
{hypotheses}

请分析：
1. 这个结果告诉我们什么？
2. 是否支持或否定了某些假设？
3. 下一步应该做什么？

请输出JSON格式：
{{
    "observation": "观察结论",
    "hypothesis_update": {{"id": 0, "status": "confirmed/rejected/active", "confidence": 0.9}},
    "new_facts": ["发现的新事实"],
    "next_action": "execute/decide/report",
    "next_command": "下一个命令（如果需要）",
    "reasoning": "分析推理过程"
}}"""

    # 决策提示词
    DECIDE_PROMPT = """根据诊断过程做出判断：

## 收集的事实
{facts}

## 假设状态
{hypotheses}

## 执行的命令
{commands}

请判断：
1. 最可能的问题原因是什么？
2. 置信度如何？
3. 是否需要更多信息？

请输出JSON格式：
{{
    "root_cause": "根本原因",
    "confidence": 0.9,
    "need_more_info": false,
    "additional_commands": [],
    "reasoning": "判断依据"
}}"""

    # 报告生成提示词
    REPORT_PROMPT = """生成诊断报告：

## 问题描述
{problem}

## 诊断过程
{process}

## 发现的问题
{findings}

## 建议的解决方案
{solutions}

请生成一份完整的诊断报告（Markdown格式），包括：
1. 问题概述
2. 诊断过程
3. 发现的问题
4. 建议的解决方案
5. 预防措施"""

    # 命令选择提示词
    SELECT_COMMAND_PROMPT = """根据当前情况选择下一个要执行的命令：

## 当前问题
{problem}

## 已执行的命令
{executed_commands}

## 可用的诊断命令
{available_commands}

请选择：
1. 最可能帮助诊断问题的命令
2. 风险最低的命令
3. 信息收益最大的命令

请输出JSON格式：
{{
    "selected_command": "命令",
    "category": "命令分类",
    "reason": "选择原因",
    "expected_info": "期望获取的信息"
}}"""

    @classmethod
    def format_analyze_prompt(
        cls,
        log_summary: str,
        error_logs: str,
    ) -> str:
        """格式化分析提示词"""
        return cls.ANALYZE_PROMPT.format(
            log_summary=log_summary,
            error_logs=error_logs,
        )

    @classmethod
    def format_observe_prompt(
        cls,
        command: str,
        output: str,
        hypotheses: List[Dict[str, Any]],
    ) -> str:
        """格式化观察提示词"""
        hypotheses_str = "\n".join(
            f"- [{h['status']}] {h['hypothesis']} (置信度: {h['confidence']:.0%})"
            for h in hypotheses
        )
        return cls.OBSERVE_PROMPT.format(
            command=command,
            output=output,
            hypotheses=hypotheses_str or "暂无假设",
        )

    @classmethod
    def format_decide_prompt(
        cls,
        facts: Dict[str, Any],
        hypotheses: List[Dict[str, Any]],
        commands: List[str],
    ) -> str:
        """格式化决策提示词"""
        facts_str = "\n".join(f"- {k}: {v}" for k, v in facts.items())
        hypotheses_str = "\n".join(
            f"- [{h['status']}] {h['hypothesis']}"
            for h in hypotheses
        )
        commands_str = "\n".join(f"- {c}" for c in commands)

        return cls.DECIDE_PROMPT.format(
            facts=facts_str or "暂无",
            hypotheses=hypotheses_str or "暂无",
            commands=commands_str or "暂无",
        )

    @classmethod
    def format_select_command_prompt(
        cls,
        problem: str,
        executed_commands: List[str],
        available_commands: List[str],
    ) -> str:
        """格式化命令选择提示词"""
        return cls.SELECT_COMMAND_PROMPT.format(
            problem=problem,
            executed_commands="\n".join(f"- {c}" for c in executed_commands) or "无",
            available_commands="\n".join(f"- {c}" for c in available_commands),
        )
