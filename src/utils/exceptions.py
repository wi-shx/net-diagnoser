"""
自定义异常定义
"""


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
