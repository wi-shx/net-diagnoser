"""
Agent基类和数据结构
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from uuid import uuid4

from src.core.ai_analyzer import AnalysisResult, SuggestedCommand
from src.core.ssh_executor import CommandResult


class AgentStatus(str, Enum):
    """Agent状态"""

    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    OBSERVING = "observing"
    COMPLETED = "completed"
    FAILED = "failed"


class ActionType(str, Enum):
    """操作类型"""

    ANALYZE = "analyze"  # 分析日志
    EXECUTE = "execute"  # 执行命令
    OBSERVE = "observe"  # 观察结果
    DECIDE = "decide"  # 做出决定
    REPORT = "report"  # 生成报告
    ASK = "ask"  # 询问用户


@dataclass
class AgentState:
    """Agent状态"""

    status: AgentStatus = AgentStatus.IDLE
    current_round: int = 0
    max_rounds: int = 5
    current_step: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status.value,
            "current_round": self.current_round,
            "max_rounds": self.max_rounds,
            "current_step": self.current_step,
            "context": self.context,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class AgentAction:
    """Agent操作"""

    id: str
    type: ActionType
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    success: bool = False
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "description": self.description,
            "parameters": self.parameters,
            "result": str(self.result) if self.result else None,
            "success": self.success,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AgentResult:
    """Agent诊断结果"""

    success: bool
    diagnosis: Optional[AnalysisResult] = None
    actions_taken: List[AgentAction] = field(default_factory=list)
    command_results: List[CommandResult] = field(default_factory=list)
    final_report: str = ""
    rounds_completed: int = 0
    total_duration: float = 0.0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "diagnosis": self.diagnosis.to_dict() if self.diagnosis else None,
            "actions_taken": [a.to_dict() for a in self.actions_taken],
            "command_results": [r.to_dict() for r in self.command_results],
            "final_report": self.final_report,
            "rounds_completed": self.rounds_completed,
            "total_duration": self.total_duration,
            "errors": self.errors,
        }


class BaseAgent(ABC):
    """
    Agent基类

    定义Agent的基本接口和生命周期
    """

    def __init__(self, max_rounds: int = 5):
        """
        初始化Agent

        Args:
            max_rounds: 最大执行轮数
        """
        self.state = AgentState(max_rounds=max_rounds)
        self.actions: List[AgentAction] = []
        self.memory: List[Dict[str, Any]] = []

    @abstractmethod
    async def think(self, context: Dict[str, Any]) -> AgentAction:
        """
        思考：根据当前上下文决定下一步操作

        Args:
            context: 当前上下文

        Returns:
            决定的操作
        """
        pass

    @abstractmethod
    async def act(self, action: AgentAction) -> Any:
        """
        执行操作

        Args:
            action: 要执行的操作

        Returns:
            操作结果
        """
        pass

    @abstractmethod
    async def observe(self, action: AgentAction, result: Any) -> Dict[str, Any]:
        """
        观察结果并更新上下文

        Args:
            action: 执行的操作
            result: 操作结果

        Returns:
            新的观察结果
        """
        pass

    async def run_cycle(self) -> AgentAction:
        """
        执行一个思考-行动-观察循环

        Returns:
            最后执行的操作
        """
        # 更新状态
        self.state.status = AgentStatus.THINKING
        self.state.updated_at = datetime.now()

        # 思考
        action = await self.think({"memory": self.memory, "state": self.state})

        # 执行
        self.state.status = AgentStatus.EXECUTING
        result = await self.act(action)
        action.result = result
        action.success = result is not None

        # 观察
        self.state.status = AgentStatus.OBSERVING
        observation = await self.observe(action, result)

        # 记录
        self.actions.append(action)
        self.memory.append(
            {
                "action": action.to_dict(),
                "observation": observation,
                "round": self.state.current_round,
            }
        )

        self.state.current_round += 1
        self.state.updated_at = datetime.now()

        return action

    def get_state(self) -> AgentState:
        """获取当前状态"""
        return self.state

    def get_actions(self) -> List[AgentAction]:
        """获取所有操作记录"""
        return self.actions

    def reset(self) -> None:
        """重置Agent状态"""
        self.state = AgentState(max_rounds=self.state.max_rounds)
        self.actions = []
        self.memory = []

    def _create_action(
        self,
        action_type: ActionType,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> AgentAction:
        """创建操作"""
        return AgentAction(
            id=str(uuid4()),
            type=action_type,
            description=description,
            parameters=parameters or {},
        )
