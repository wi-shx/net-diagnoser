"""
自定义日志解析器框架

允许用户通过配置文件定义自定义日志格式
"""

import re
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path

import yaml

from src.parsers.base import BaseParser, LogEntry
from src.utils.exceptions import ParseError


@dataclass
class FieldMapping:
    """字段映射配置"""

    name: str  # 字段名称
    pattern_group: int  # 正则表达式捕获组索引
    transform: Optional[str] = None  # 转换函数: int, float, str, bool
    default: Optional[Any] = None  # 默认值


@dataclass
class CustomParserConfig:
    """自定义解析器配置"""

    name: str  # 解析器名称
    description: str = ""  # 描述
    pattern: str = ""  # 主正则表达式
    timestamp_format: str = "%Y-%m-%d %H:%M:%S"  # 时间戳格式
    timestamp_group: int = 1  # 时间戳捕获组
    level_group: Optional[int] = None  # 日志级别捕获组
    message_group: int = 2  # 消息捕获组
    field_mappings: List[FieldMapping] = field(default_factory=list)  # 字段映射
    level_mapping: Dict[str, str] = field(default_factory=dict)  # 级别映射
    sample_lines: List[str] = field(default_factory=list)  # 示例行
    multiline: bool = False  # 是否多行模式
    multiline_pattern: Optional[str] = None  # 多行起始模式
    detect_patterns: List[str] = field(default_factory=list)  # 检测模式


class CustomParser(BaseParser):
    """
    自定义日志解析器

    通过配置文件定义日志格式，支持灵活的正则表达式解析
    """

    def __init__(self, config: CustomParserConfig):
        """
        初始化自定义解析器

        Args:
            config: 解析器配置

        Raises:
            ParseError: 正则表达式无效
        """
        super().__init__()
        self.config = config

        try:
            self.pattern = re.compile(config.pattern)
        except re.error as e:
            raise ParseError(f"Invalid regex pattern: {e}")

        if config.multiline and config.multiline_pattern:
            try:
                self.multiline_start = re.compile(config.multiline_pattern)
            except re.error as e:
                raise ParseError(f"Invalid multiline pattern: {e}")
        else:
            self.multiline_start = None

        # 检测模式
        self._detect_patterns = []
        for p in config.detect_patterns:
            try:
                self._detect_patterns.append(re.compile(p))
            except re.error:
                pass

    def parse_line(self, line: str) -> Optional[LogEntry]:
        """
        解析单行日志

        Args:
            line: 日志行

        Returns:
            LogEntry对象，解析失败返回None
        """
        line = line.strip()
        if not line:
            return None

        match = self.pattern.match(line)
        if not match:
            return None

        groups = match.groups()

        # 提取时间戳
        timestamp = self._extract_timestamp(groups)

        # 提取日志级别
        level = "INFO"
        if self.config.level_group and self.config.level_group <= len(groups):
            raw_level = groups[self.config.level_group - 1] or ""
            level = self._map_level(raw_level)

        # 提取消息
        message = ""
        if self.config.message_group <= len(groups):
            message = groups[self.config.message_group - 1] or ""

        # 提取额外字段
        fields: Dict[str, Any] = {}
        for mapping in self.config.field_mappings:
            value = self._extract_field(groups, mapping)
            if value is not None:
                fields[mapping.name] = value

        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            raw=line,
            fields=fields,
        )

    def _extract_timestamp(self, groups: tuple) -> datetime:
        """提取时间戳"""
        if self.config.timestamp_group <= len(groups):
            ts_str = groups[self.config.timestamp_group - 1]
            if ts_str:
                try:
                    return datetime.strptime(ts_str, self.config.timestamp_format)
                except ValueError:
                    pass

        return datetime.now()

    def _map_level(self, raw_level: str) -> str:
        """映射日志级别"""
        if not raw_level:
            return "INFO"

        raw_level = raw_level.strip().upper()

        # 使用自定义映射
        if raw_level in self.config.level_mapping:
            return self.config.level_mapping[raw_level]

        # 使用默认映射
        return self.normalize_level(raw_level)

    def _extract_field(self, groups: tuple, mapping: FieldMapping) -> Any:
        """提取字段值"""
        if mapping.pattern_group > len(groups):
            return mapping.default

        value = groups[mapping.pattern_group - 1]
        if value is None:
            return mapping.default

        # 应用转换
        if mapping.transform:
            try:
                if mapping.transform == "int":
                    return int(value)
                elif mapping.transform == "float":
                    return float(value)
                elif mapping.transform == "bool":
                    return value.lower() in ("true", "1", "yes", "on")
                elif mapping.transform == "str":
                    return str(value)
            except (ValueError, TypeError):
                return mapping.default

        return value

    @classmethod
    def from_yaml(cls, path: str) -> "CustomParser":
        """
        从YAML文件加载配置

        Args:
            path: YAML配置文件路径

        Returns:
            CustomParser实例

        Raises:
            ParseError: 配置文件无效
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            raise ParseError(f"Config file not found: {path}")
        except yaml.YAMLError as e:
            raise ParseError(f"Invalid YAML: {e}")

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CustomParser":
        """
        从字典创建解析器

        Args:
            data: 配置字典

        Returns:
            CustomParser实例

        Raises:
            ParseError: 配置无效
        """
        # 解析字段映射
        field_mappings = []
        for fm in data.get("field_mappings", []):
            field_mappings.append(
                FieldMapping(
                    name=fm.get("name", ""),
                    pattern_group=fm.get("pattern_group", 0),
                    transform=fm.get("transform"),
                    default=fm.get("default"),
                )
            )

        config = CustomParserConfig(
            name=data.get("name", "custom"),
            description=data.get("description", ""),
            pattern=data.get("pattern", ""),
            timestamp_format=data.get("timestamp_format", "%Y-%m-%d %H:%M:%S"),
            timestamp_group=data.get("timestamp_group", 1),
            level_group=data.get("level_group"),
            message_group=data.get("message_group", 2),
            field_mappings=field_mappings,
            level_mapping=data.get("level_mapping", {}),
            sample_lines=data.get("sample_lines", []),
            multiline=data.get("multiline", False),
            multiline_pattern=data.get("multiline_pattern"),
            detect_patterns=data.get("detect_patterns", []),
        )

        return cls(config)

    def detect(self, file_path: str) -> bool:
        """
        检测文件是否匹配此解析器

        Args:
            file_path: 文件路径

        Returns:
            是否匹配
        """
        # 如果有检测模式，使用检测模式
        if self._detect_patterns:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for _ in range(20):
                        line = f.readline()
                        if not line:
                            break

                        for pattern in self._detect_patterns:
                            if pattern.search(line):
                                return True

                return False
            except Exception:
                return False

        # 否则检查解析成功率
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                total = 0
                matched = 0

                for _ in range(20):
                    line = f.readline()
                    if not line:
                        break

                    line = line.strip()
                    if not line:
                        continue

                    total += 1
                    if self.pattern.match(line):
                        matched += 1

                # 如果超过50%的行匹配，认为是匹配的
                return total > 0 and matched / total > 0.5

        except Exception:
            return False


# 预定义的自定义解析器模板
BUILTIN_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "apache_access": {
        "name": "Apache Access Log",
        "description": "Apache HTTP Server access log format",
        "pattern": r'^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) ([^"]+) HTTP/[^"]+" (\d+) (\d+)',
        "timestamp_format": "%d/%b/%Y:%H:%M:%S %z",
        "timestamp_group": 2,
        "level_group": None,
        "message_group": 3,
        "field_mappings": [
            {"name": "ip_address", "pattern_group": 1},
            {"name": "request_method", "pattern_group": 3},
            {"name": "request_url", "pattern_group": 4},
            {"name": "status_code", "pattern_group": 5, "transform": "int"},
            {"name": "response_size", "pattern_group": 6, "transform": "int"},
        ],
        "detect_patterns": [r'^\d+\.\d+\.\d+\.\d+.*\] "[A-Z]+ .*HTTP'],
    },
    "apache_error": {
        "name": "Apache Error Log",
        "description": "Apache HTTP Server error log format",
        "pattern": r'^\[([^\]]+)\] \[(\w+)\] (\[client [^\]]+\] )?(.+)$',
        "timestamp_format": "%a %b %d %H:%M:%S.%f %Y",
        "timestamp_group": 1,
        "level_group": 2,
        "message_group": 4,
        "level_mapping": {
            "EMERG": "FATAL",
            "ALERT": "FATAL",
            "CRIT": "FATAL",
            "ERROR": "ERROR",
            "WARN": "WARN",
            "NOTICE": "INFO",
            "INFO": "INFO",
            "DEBUG": "DEBUG",
        },
        "detect_patterns": [r'^\[[A-Za-z]{3} [A-Za-z]{3} \d+.*\] \[\w+\]'],
    },
    "json_log": {
        "name": "JSON Log",
        "description": "JSON format log (one JSON object per line)",
        "pattern": r'^(\{.*\})$',
        "timestamp_format": "%Y-%m-%dT%H:%M:%S",
        "timestamp_group": 1,
        "level_group": None,
        "message_group": 1,
        "detect_patterns": [r'^\{.*"[tT]ime"'],
    },
    "csv_log": {
        "name": "CSV Log",
        "description": "CSV format log",
        "pattern": r'^([^,]+),([^,]+),(.*)$',
        "timestamp_format": "%Y-%m-%d %H:%M:%S",
        "timestamp_group": 1,
        "level_group": 2,
        "message_group": 3,
    },
    "generic_log": {
        "name": "Generic Log",
        "description": "Generic log with timestamp and level",
        "pattern": r'^(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})\s*(\w+)?\s*[:\-\]]?\s*(.+)$',
        "timestamp_format": "%Y-%m-%d %H:%M:%S",
        "timestamp_group": 1,
        "level_group": 2,
        "message_group": 3,
    },
}


def load_custom_parsers(directory: str) -> List[CustomParser]:
    """
    从目录加载所有自定义解析器

    Args:
        directory: 配置文件目录

    Returns:
        解析器列表
    """
    parsers = []
    dir_path = Path(directory)

    if not dir_path.exists():
        return parsers

    for file_path in dir_path.glob("*.yaml"):
        try:
            parser = CustomParser.from_yaml(str(file_path))
            parsers.append(parser)
        except ParseError:
            continue

    for file_path in dir_path.glob("*.yml"):
        try:
            parser = CustomParser.from_yaml(str(file_path))
            parsers.append(parser)
        except ParseError:
            continue

    return parsers


def get_builtin_parser(template_name: str) -> Optional[CustomParser]:
    """
    获取内置解析器模板

    Args:
        template_name: 模板名称

    Returns:
        CustomParser实例，不存在返回None
    """
    if template_name in BUILTIN_TEMPLATES:
        return CustomParser.from_dict(BUILTIN_TEMPLATES[template_name])
    return None


def list_builtin_templates() -> List[str]:
    """列出所有内置模板"""
    return list(BUILTIN_TEMPLATES.keys())
