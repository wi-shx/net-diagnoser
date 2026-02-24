"""
自定义异常定义
"""

from typing import List, Optional


class NetDiagnoserError(Exception):
    """基础异常类"""

    def __init__(self, message: str, code: int = 0):
        self.message = message
        self.code = code
        super().__init__(self.message)


class FileError(NetDiagnoserError):
    """文件操作异常"""

    def __init__(self, message: str, code: int = 1000):
        super().__init__(message, code)


class ParseError(NetDiagnoserError):
    """解析异常"""

    def __init__(self, message: str, code: int = 2000):
        super().__init__(message, code)


class APIError(NetDiagnoserError):
    """API调用异常"""

    def __init__(self, message: str, code: int = 3000, status_code: int = 0):
        self.status_code = status_code
        super().__init__(message, code)


class ConfigError(NetDiagnoserError):
    """配置异常"""

    def __init__(self, message: str, code: int = 4000):
        super().__init__(message, code)


class ValidationError(NetDiagnoserError):
    """验证异常"""

    def __init__(self, message: str, code: int = 5000):
        super().__init__(message, code)


# ==================== SSH相关异常 ====================


class SSHError(NetDiagnoserError):
    """SSH错误基类"""

    def __init__(self, message: str, code: int = 6000, host: str = ""):
        self.host = host
        super().__init__(message, code)


class SSHConnectionError(SSHError):
    """SSH连接失败"""

    def __init__(self, message: str, host: str = ""):
        super().__init__(message, code=6100, host=host)


class SSHAuthenticationError(SSHError):
    """SSH认证失败"""

    def __init__(self, message: str, host: str = ""):
        super().__init__(message, code=6200, host=host)


class SSHTimeoutError(SSHError):
    """SSH超时"""

    def __init__(self, message: str, host: str = ""):
        super().__init__(message, code=6300, host=host)


class SSHCommandError(SSHError):
    """SSH命令执行失败"""

    def __init__(
        self,
        message: str,
        host: str = "",
        command: str = "",
        exit_code: int = -1,
    ):
        self.command = command
        self.exit_code = exit_code
        super().__init__(message, code=6400, host=host)


# ==================== 命令验证异常 ====================


class CommandNotAllowedError(ValidationError):
    """命令不在白名单中"""

    def __init__(self, command: str, allowed: Optional[List[str]] = None):
        self.command = command
        self.allowed = allowed or []
        msg = f"命令不允许: {command}"
        if self.allowed:
            msg += f"。允许的命令: {', '.join(self.allowed[:10])}"
            if len(self.allowed) > 10:
                msg += "..."
        super().__init__(msg, code=5200)


class CommandArgumentNotAllowedError(ValidationError):
    """命令参数不允许"""

    def __init__(self, command: str, arg: str, allowed_args: Optional[List[str]] = None):
        self.command = command
        self.arg = arg
        self.allowed_args = allowed_args or []
        msg = f"命令参数不允许: {command} {arg}"
        if self.allowed_args:
            msg += f"。允许的参数: {', '.join(self.allowed_args)}"
        super().__init__(msg, code=5210)


# ==================== 执行器异常 ====================


class ExecutionError(NetDiagnoserError):
    """执行错误基类"""

    def __init__(self, message: str, code: int = 7000):
        super().__init__(message, code)


class ExecutionPlanError(ExecutionError):
    """执行计划错误"""

    def __init__(self, message: str, plan_id: str = ""):
        self.plan_id = plan_id
        super().__init__(message, code=7100)


class ExecutionTimeoutError(ExecutionError):
    """执行超时"""

    def __init__(self, message: str, command: str = "", timeout: float = 0):
        self.command = command
        self.timeout = timeout
        super().__init__(message, code=7200)


class ApprovalRequiredError(ExecutionError):
    """需要审批"""

    def __init__(self, message: str, commands: Optional[List[str]] = None):
        self.commands = commands or []
        super().__init__(message, code=7300)


# ==================== Agent异常 ====================


class AgentError(NetDiagnoserError):
    """Agent错误基类"""

    def __init__(self, message: str, code: int = 8000):
        super().__init__(message, code)


class AgentMaxRoundsExceededError(AgentError):
    """Agent超过最大轮数"""

    def __init__(self, message: str, rounds: int = 0):
        self.rounds = rounds
        super().__init__(message, code=8100)


class AgentActionFailedError(AgentError):
    """Agent操作失败"""

    def __init__(self, message: str, action: str = ""):
        self.action = action
        super().__init__(message, code=8200)
