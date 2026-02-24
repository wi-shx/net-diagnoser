"""
AI分析器模块
"""

import json
from dataclasses import dataclass, asdict
from typing import List, Optional
import httpx

from src.core.log_parser import LogEntry, LogStatistics
from src.config import Config
from src.utils.exceptions import APIError


@dataclass
class SuggestedCommand:
    """建议命令"""

    category: str  # 命令分类（网络/端口/DNS/服务/防火墙）
    description: str  # 命令说明
    command: str  # 命令本身


@dataclass
class AnalysisResult:
    """AI分析结果"""

    problem_type: str  # 问题类型
    possible_causes: List[str]  # 可能原因（Top 3）
    risk_level: str  # 风险等级（P0/P1/P2）
    suggested_commands: List[SuggestedCommand]  # 建议的排查命令
    confidence: float  # 置信度（0.0-1.0）

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)


class AIAnalyzer:
    """AI分析器"""

    # 支持的模型列表
    SUPPORTED_MODELS = [
        "glm-4.7",
        "glm-5.0",
        "glm-5",
        "glm-4-plus",
        "glm-4-flash",
        "glm-4-flash-250414",
        "glm-4",
        "glm-z1-flash",
    ]

    def __init__(self, api_key: str, model: str = "glm-4.7"):
        """
        初始化AI分析器

        Args:
            api_key: GLM API密钥
            model: 模型名称

        Raises:
            ValueError: api_key为空或model不支持
        """
        if not api_key:
            raise ValueError("API key is required")

        if model not in self.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model: {model}. Supported: {', '.join(self.SUPPORTED_MODELS)}")

        self.api_key = api_key
        self.model = model
        self.api_url = Config.GLM_API_URL

    async def analyze(
        self, entries: List[LogEntry], statistics: LogStatistics
    ) -> AnalysisResult:
        """
        分析日志

        Args:
            entries: 日志条目列表
            statistics: 统计信息

        Returns:
            分析结果对象

        Raises:
            APIError: API调用失败
            ValueError: entries或statistics无效
        """
        if not entries:
            raise ValueError("No log entries to analyze")

        if not statistics:
            raise ValueError("Statistics are required")

        # 构建prompt
        prompt = self.build_prompt(entries, statistics)

        # 调用API
        try:
            response = await self._call_api(prompt)
            result_json = self._parse_response(response)
        except Exception as e:
            raise APIError(f"Failed to analyze logs: {e}") from e

        # 解析结果
        return self._parse_analysis_result(result_json)

    def build_prompt(self, entries: List[LogEntry], statistics: LogStatistics) -> str:
        """
        构建AI prompt

        Args:
            entries: 日志条目列表
            statistics: 统计信息

        Returns:
            AI prompt字符串
        """
        # 只显示错误日志（最多100条）
        error_entries = [e for e in entries if e.level in ["ERROR", "FATAL"]][:100]

        prompt = f"""你是一个网络诊断专家，请分析以下日志：

## 日志摘要
- 总行数: {statistics.total_lines}
- 错误行数: {statistics.error_lines}
- 警告行数: {statistics.warning_lines}
- 错误率: {statistics.error_rate}%
- 时间范围: {statistics.time_range[0]} - {statistics.time_range[1]}

## 日志级别分布
"""

        for level, count in statistics.level_counts.items():
            prompt += f"- {level}: {count}\n"

        prompt += "\n## 错误类型（Top 10）\n"
        for error_type, count in statistics.error_types.items():
            prompt += f"- {error_type}: {count}次\n"

        prompt += "\n## 错误日志（最近100条）\n"
        for entry in error_entries:
            prompt += f"[{entry.timestamp}] {entry.message}\n"

        prompt += """
## 分析要求
请分析上述日志，找出网络问题的原因。

请输出JSON格式：
{
  "problem_type": "问题类型",
  "possible_causes": ["原因1", "原因2", "原因3"],
  "risk_level": "P0/P1/P2",
  "suggested_commands": [
    {
      "category": "命令分类",
      "description": "命令说明",
      "command": "命令本身"
    }
  ],
  "confidence": 0.95
}

问题类型包括：连接超时、DNS解析失败、端口不可达、高延迟、服务异常、无问题
风险等级：P0（服务完全不可用）、P1（部分功能受影响）、P2（偶发问题）
命令分类包括：网络、端口、DNS、服务、防火墙
"""

        return prompt

    async def _call_api(self, prompt: str) -> dict:
        """
        调用GLM API

        Args:
            prompt: AI prompt

        Returns:
            API响应

        Raises:
            APIError: API调用失败
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": Config.AI_TEMPERATURE,
            "top_p": Config.AI_TOP_P,
        }

        try:
            async with httpx.AsyncClient(timeout=Config.AI_TIMEOUT) as client:
                response = await client.post(self.api_url, headers=headers, json=data)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise APIError(
                f"API call failed with status {e.response.status_code}: {e.response.text}",
                status_code=e.response.status_code,
            )
        except httpx.TimeoutException:
            raise APIError("API call timed out")
        except Exception as e:
            raise APIError(f"API call failed: {e}")

    def _parse_response(self, response: dict) -> dict:
        """
        解析API响应

        Args:
            response: API响应

        Returns:
            解析后的JSON

        Raises:
            APIError: 响应格式错误
        """
        try:
            content = response["choices"][0]["message"]["content"]
            # 尝试提取JSON
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content

            return json.loads(json_str)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise APIError(f"Failed to parse API response: {e}")

    def _parse_analysis_result(self, result_json: dict) -> AnalysisResult:
        """
        解析分析结果

        Args:
            result_json: JSON格式的分析结果

        Returns:
            AnalysisResult对象
        """
        # 解析命令建议
        commands = []
        for cmd_data in result_json.get("suggested_commands", []):
            commands.append(
                SuggestedCommand(
                    category=cmd_data.get("category", "其他"),
                    description=cmd_data.get("description", ""),
                    command=cmd_data.get("command", ""),
                )
            )

        return AnalysisResult(
            problem_type=result_json.get("problem_type", "未知"),
            possible_causes=result_json.get("possible_causes", []),
            risk_level=result_json.get("risk_level", "P2"),
            suggested_commands=commands,
            confidence=result_json.get("confidence", 0.5),
        )
