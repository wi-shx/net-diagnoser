"""
日志解析器基类
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List
import re


@dataclass
class LogEntry:
    """日志条目"""

    timestamp: datetime  # 时间戳
    level: str  # 日志级别（INFO/WARN/ERROR/FATAL）
    message: str  # 日志消息
    raw: str  # 原始日志行
    fields: Dict[str, Any]  # 提取的字段

    # Nginx特有字段
    ip_address: Optional[str] = None
    request_method: Optional[str] = None
    request_url: Optional[str] = None
    status_code: Optional[int] = None

    # HAProxy特有字段
    backend_name: Optional[str] = None
    server_name: Optional[str] = None

    # Syslog特有字段
    process: Optional[str] = None
    pid: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogEntry":
        """从字典创建LogEntry"""
        return cls(**data)


class BaseParser(ABC):
    """解析器基类"""

    # 日志级别映射
    LEVEL_MAP = {
        "info": "INFO",
        "warn": "WARN",
        "warning": "WARN",
        "error": "ERROR",
        "err": "ERROR",
        "fatal": "FATAL",
        "crit": "FATAL",
        "critical": "FATAL",
        "debug": "DEBUG",
    }

    def __init__(self):
        """初始化解析器"""
        self.pattern = None  # 子类实现

    @abstractmethod
    def parse_line(self, line: str) -> Optional[LogEntry]:
        """
        解析单行日志

        Args:
            line: 日志行

        Returns:
            LogEntry对象，解析失败返回None
        """
        pass

    def parse_lines(self, lines: List[str]) -> List[LogEntry]:
        """
        解析多行日志

        Args:
            lines: 日志行列表

        Returns:
            LogEntry列表
        """
        entries = []
        for line in lines:
            entry = self.parse_line(line)
            if entry:
                entries.append(entry)
        return entries

    def normalize_level(self, level: str) -> str:
        """
        标准化日志级别

        Args:
            level: 原始级别

        Returns:
            标准化后的级别（INFO/WARN/ERROR/FATAL/DEBUG）
        """
        level_lower = level.lower()
        return self.LEVEL_MAP.get(level_lower, "INFO")

    def extract_timestamp(self, timestamp_str: str) -> datetime:
        """
        提取时间戳

        Args:
            timestamp_str: 时间戳字符串

        Returns:
            datetime对象
        """
        # 移除毫秒部分（如果有）
        if "." in timestamp_str and not timestamp_str.endswith("+") and not timestamp_str.endswith("-"):
            # 移除小数部分
            parts = timestamp_str.split(".")
            if len(parts) == 2:
                timestamp_str = parts[0]

        # 常见时间格式
        formats = [
            "%d/%b/%Y:%H:%M:%S %z",  # Nginx: 15/Feb/2026:10:00:00 +0800
            "%Y-%m-%d %H:%M:%S",  # 标准格式: 2026-02-15 10:00:00
            "%b %d %H:%M:%S",  # Syslog: Feb 15 10:00:00
            "%d/%b/%Y:%H:%M:%S",  # 无时区
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue

        raise ValueError(f"无法解析时间戳: {timestamp_str}")
