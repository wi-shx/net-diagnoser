"""
日志解析器模块
"""

from typing import List, Optional
from dataclasses import dataclass
from collections import Counter
from datetime import datetime

from src.parsers.base import BaseParser, LogEntry
from src.parsers.nginx_parser import NginxParser
from src.parsers.haproxy_parser import HAProxyParser
from src.parsers.syslog_parser import SyslogParser
from src.utils.exceptions import ParseError, FileError
from src.utils.file_handler import read_lines


@dataclass
class LogStatistics:
    """日志统计信息"""

    total_lines: int = 0  # 总行数
    error_lines: int = 0  # 错误行数
    warning_lines: int = 0  # 警告行数
    error_rate: float = 0.0  # 错误率（百分比）
    level_counts: dict = None  # 按级别统计
    error_types: dict = None  # 按错误类型统计
    time_range: tuple = None  # 时间范围（开始、结束）

    def __post_init__(self):
        if self.level_counts is None:
            self.level_counts = {}
        if self.error_types is None:
            self.error_types = {}


class LogParser:
    """日志解析器"""

    PARSER_MAP = {
        "nginx": NginxParser,
        "haproxy": HAProxyParser,
        "syslog": SyslogParser,
    }

    def __init__(self, format: Optional[str] = None):
        """
        初始化日志解析器

        Args:
            format: 日志格式（nginx/haproxy/syslog），None表示自动检测

        Raises:
            ValueError: 格式参数无效
        """
        if format is not None and format not in self.PARSER_MAP:
            raise ValueError(f"Unsupported log format: {format}")

        self.format = format
        self.parser: Optional[BaseParser] = None

    def parse_file(self, file_path: str) -> List[LogEntry]:
        """
        解析日志文件

        Args:
            file_path: 日志文件路径

        Returns:
            日志条目列表

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持
            ParseError: 解析失败
        """
        # 检测格式
        if self.format is None:
            self.format = self.detect_format(file_path)

        if self.format == "unknown":
            raise ValueError(f"Unable to detect log format for: {file_path}")

        # 创建解析器
        parser_class = self.PARSER_MAP[self.format]
        self.parser = parser_class()

        # 解析日志
        try:
            lines = list(read_lines(file_path))
            entries = self.parser.parse_lines(lines)
        except Exception as e:
            raise ParseError(f"Failed to parse file: {e}") from e

        return entries

    def detect_format(self, file_path: str) -> str:
        """
        自动检测日志格式

        Args:
            file_path: 日志文件路径

        Returns:
            日志格式（nginx/haproxy/syslog/unknown）

        Raises:
            FileNotFoundError: 文件不存在
        """
        # 按顺序检测
        for format_name, parser_class in self.PARSER_MAP.items():
            if parser_class.detect(file_path):
                return format_name

        return "unknown"

    def get_statistics(self, entries: List[LogEntry]) -> LogStatistics:
        """
        获取日志统计信息

        Args:
            entries: 日志条目列表

        Returns:
            统计信息对象

        Raises:
            ValueError: entries为空列表
        """
        if not entries:
            raise ValueError("No log entries to analyze")

        # 基本统计
        total_lines = len(entries)
        level_counts = Counter(entry.level for entry in entries)
        error_lines = level_counts.get("ERROR", 0)
        warning_lines = level_counts.get("WARN", 0)
        error_rate = (error_lines / total_lines) * 100 if total_lines > 0 else 0.0

        # 时间范围
        timestamps = [entry.timestamp for entry in entries if entry.timestamp]
        time_range = (
            (min(timestamps), max(timestamps)) if timestamps else (None, None)
        )

        # 错误类型统计
        error_entries = [entry for entry in entries if entry.level == "ERROR"]
        error_types = Counter()
        for entry in error_entries:
            # 使用消息的前50个字符作为错误类型
            error_type = entry.message[:50]
            error_types[error_type] += 1

        return LogStatistics(
            total_lines=total_lines,
            error_lines=error_lines,
            warning_lines=warning_lines,
            error_rate=round(error_rate, 2),
            level_counts=dict(level_counts),
            error_types=dict(error_types.most_common(10)),
            time_range=time_range,
        )
