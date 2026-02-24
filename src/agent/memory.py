"""
Agent记忆模块

管理Agent的上下文和记忆
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import json


@dataclass
class MemoryEntry:
    """记忆条目"""

    id: int
    timestamp: datetime
    round: int
    action_type: str
    action_description: str
    observation: str
    result_summary: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "round": self.round,
            "action_type": self.action_type,
            "action_description": self.action_description,
            "observation": self.observation,
            "result_summary": self.result_summary,
            "metadata": self.metadata,
        }


class AgentMemory:
    """
    Agent记忆管理器

    维护诊断过程中的上下文和历史记录
    """

    def __init__(self, max_entries: int = 100):
        """
        初始化记忆管理器

        Args:
            max_entries: 最大条目数
        """
        self.max_entries = max_entries
        self.entries: List[MemoryEntry] = []
        self._next_id = 1

        # 上下文变量
        self.context: Dict[str, Any] = {}
        self.facts: Dict[str, Any] = {}
        self.hypotheses: List[Dict[str, Any]] = []
        self.decisions: List[Dict[str, Any]] = []

    def add_entry(
        self,
        round: int,
        action_type: str,
        action_description: str,
        observation: str,
        result_summary: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryEntry:
        """
        添加记忆条目

        Args:
            round: 当前轮次
            action_type: 操作类型
            action_description: 操作描述
            observation: 观察结果
            result_summary: 结果摘要
            metadata: 额外元数据

        Returns:
            创建的记忆条目
        """
        entry = MemoryEntry(
            id=self._next_id,
            timestamp=datetime.now(),
            round=round,
            action_type=action_type,
            action_description=action_description,
            observation=observation,
            result_summary=result_summary,
            metadata=metadata or {},
        )

        self.entries.append(entry)
        self._next_id += 1

        # 如果超过最大条目数，移除旧的
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries :]

        return entry

    def get_recent(self, count: int = 5) -> List[MemoryEntry]:
        """
        获取最近的记忆

        Args:
            count: 数量

        Returns:
            记忆条目列表
        """
        return self.entries[-count:]

    def get_by_round(self, round: int) -> List[MemoryEntry]:
        """
        获取指定轮次的记忆

        Args:
            round: 轮次

        Returns:
            记忆条目列表
        """
        return [e for e in self.entries if e.round == round]

    def set_context(self, key: str, value: Any) -> None:
        """
        设置上下文变量

        Args:
            key: 键
            value: 值
        """
        self.context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """
        获取上下文变量

        Args:
            key: 键
            default: 默认值

        Returns:
            变量值
        """
        return self.context.get(key, default)

    def add_fact(self, fact: str, source: str, confidence: float = 1.0) -> None:
        """
        添加事实

        Args:
            fact: 事实描述
            source: 来源
            confidence: 置信度
        """
        self.facts[fact] = {
            "source": source,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        }

    def get_facts(self) -> Dict[str, Any]:
        """获取所有事实"""
        return self.facts

    def add_hypothesis(
        self,
        hypothesis: str,
        evidence: List[str],
        confidence: float = 0.5,
    ) -> int:
        """
        添加假设

        Args:
            hypothesis: 假设描述
            evidence: 支持证据
            confidence: 置信度

        Returns:
            假设ID
        """
        hypothesis_entry = {
            "id": len(self.hypotheses),
            "hypothesis": hypothesis,
            "evidence": evidence,
            "confidence": confidence,
            "status": "active",
            "created_at": datetime.now().isoformat(),
        }
        self.hypotheses.append(hypothesis_entry)
        return hypothesis_entry["id"]

    def update_hypothesis(
        self,
        hypothesis_id: int,
        status: str = None,
        confidence: float = None,
        new_evidence: List[str] = None,
    ) -> None:
        """
        更新假设

        Args:
            hypothesis_id: 假设ID
            status: 新状态
            confidence: 新置信度
            new_evidence: 新证据
        """
        for h in self.hypotheses:
            if h["id"] == hypothesis_id:
                if status:
                    h["status"] = status
                if confidence is not None:
                    h["confidence"] = confidence
                if new_evidence:
                    h["evidence"].extend(new_evidence)
                break

    def get_active_hypotheses(self) -> List[Dict[str, Any]]:
        """获取活跃的假设"""
        return [h for h in self.hypotheses if h["status"] == "active"]

    def add_decision(
        self,
        decision: str,
        reasoning: str,
        alternatives: List[str],
    ) -> None:
        """
        添加决策

        Args:
            decision: 决策内容
            reasoning: 推理过程
            alternatives: 备选方案
        """
        self.decisions.append(
            {
                "decision": decision,
                "reasoning": reasoning,
                "alternatives": alternatives,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def get_decisions(self) -> List[Dict[str, Any]]:
        """获取所有决策"""
        return self.decisions

    def build_summary(self) -> str:
        """
        构建记忆摘要

        Returns:
            摘要文本
        """
        lines = ["# 诊断记忆摘要", ""]

        # 事实
        if self.facts:
            lines.append("## 发现的事实")
            for fact, info in self.facts.items():
                lines.append(f"- {fact} (来源: {info['source']}, 置信度: {info['confidence']:.0%})")
            lines.append("")

        # 假设
        if self.hypotheses:
            lines.append("## 假设")
            for h in self.hypotheses:
                status_icon = "✓" if h["status"] == "confirmed" else ("✗" if h["status"] == "rejected" else "?")
                lines.append(f"- [{status_icon}] {h['hypothesis']} (置信度: {h['confidence']:.0%})")
            lines.append("")

        # 决策
        if self.decisions:
            lines.append("## 做出的决策")
            for d in self.decisions:
                lines.append(f"- {d['decision']}")
            lines.append("")

        # 最近操作
        if self.entries:
            lines.append("## 最近操作")
            for entry in self.get_recent(10):
                lines.append(f"- Round {entry.round}: [{entry.action_type}] {entry.action_description}")
            lines.append("")

        return "\n".join(lines)

    def to_json(self) -> str:
        """导出为JSON"""
        return json.dumps(
            {
                "entries": [e.to_dict() for e in self.entries],
                "context": self.context,
                "facts": self.facts,
                "hypotheses": self.hypotheses,
                "decisions": self.decisions,
            },
            ensure_ascii=False,
            indent=2,
        )

    def from_json(self, json_str: str) -> None:
        """从JSON导入"""
        data = json.loads(json_str)
        self.entries = []
        for e in data.get("entries", []):
            entry = MemoryEntry(
                id=e["id"],
                timestamp=datetime.fromisoformat(e["timestamp"]),
                round=e["round"],
                action_type=e["action_type"],
                action_description=e["action_description"],
                observation=e["observation"],
                result_summary=e["result_summary"],
                metadata=e.get("metadata", {}),
            )
            self.entries.append(entry)
        self.context = data.get("context", {})
        self.facts = data.get("facts", {})
        self.hypotheses = data.get("hypotheses", [])
        self.decisions = data.get("decisions", [])

        if self.entries:
            self._next_id = max(e.id for e in self.entries) + 1

    def clear(self) -> None:
        """清空记忆"""
        self.entries = []
        self.context = {}
        self.facts = {}
        self.hypotheses = []
        self.decisions = []
        self._next_id = 1
