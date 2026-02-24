"""
dmesg日志解析器

解析Linux内核环形缓冲区日志
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any, List

from src.parsers.base import BaseParser, LogEntry


class DmesgParser(BaseParser):
    """
    dmesg日志解析器

    解析Linux内核消息，支持多种dmesg输出格式
    """

    # 带时间戳的格式: [    0.000000] message
    TIMESTAMP_PATTERN = re.compile(
        r"^\[\s*(\d+\.\d+)\]\s+(.+)$"
    )

    # 带时间戳和级别的格式: [    0.000000] [level] message
    # 或: [    0.000000] subsystem: message
    LEVEL_PATTERN = re.compile(
        r"^\[\s*(\d+\.\d+)\]\s*(?:\[(\w+)\]\s*)?(.+)$"
    )

    # 现代dmesg格式带人类可读时间: [Mon Feb 24 10:00:00 2026] message
    HUMAN_TIMESTAMP_PATTERN = re.compile(
        r"^\[([A-Za-z]{3}\s+[A-Za-z]{3}\s+\d+\s+\d+:\d+:\d+\s+\d+)\]\s*(.+)$"
    )

    # 子系统模式
    SUBSYSTEM_PATTERN = re.compile(
        r"^(\w+):\s*(.+)$"
    )

    # 错误级别关键词
    ERROR_KEYWORDS = [
        "error", "fail", "failed", "fatal", "critical", "panic",
        "exception", "warning", "warn", "timeout", "refused",
        "denied", "abort", "corruption", "bug", "unable",
        "flooding", "overflow", "killed", "out of memory", "unreachable",
    ]

    # 网络相关子系统
    NETWORK_SUBSYSTEMS = [
        "eth", "ens", "enp", "wlan", "wlp", "bond", "br",
        "docker", "veth", "tun", "tap", "bridge", "net",
        "tcp", "udp", "ip", "ipv6", "icmp", "dns",
    ]

    def __init__(self):
        """初始化dmesg解析器"""
        super().__init__()
        self._boot_time: Optional[datetime] = None

    def parse_line(self, line: str) -> Optional[LogEntry]:
        """
        解析单行dmesg日志

        Args:
            line: 日志行

        Returns:
            LogEntry对象，解析失败返回None
        """
        line = line.strip()
        if not line:
            return None

        timestamp: Optional[datetime] = None
        level = "INFO"
        message = line
        subsystem = ""
        fields: Dict[str, Any] = {}

        # 尝试匹配人类可读时间格式
        match = self.HUMAN_TIMESTAMP_PATTERN.match(line)
        if match:
            time_str, message = match.groups()
            try:
                timestamp = datetime.strptime(time_str, "%a %b %d %H:%M:%S %Y")
            except ValueError:
                pass
        else:
            # 尝试匹配标准时间戳格式
            match = self.LEVEL_PATTERN.match(line)
            if match:
                uptime_str, log_level, msg = match.groups()
                fields["uptime"] = float(uptime_str)

                if log_level:
                    # 检查是否是日志级别
                    if log_level.upper() in ["EMERG", "ALERT", "CRIT", "ERR", "WARN", "NOTICE", "INFO", "DEBUG"]:
                        level = self._map_kernel_level(log_level)
                    else:
                        # 可能是消息的一部分
                        msg = f"[{log_level}] {msg}"

                message = msg

        # 检测子系统
        sub_match = self.SUBSYSTEM_PATTERN.match(message)
        if sub_match:
            subsystem = sub_match.group(1).lower()
            message = sub_match.group(2)
            fields["subsystem"] = subsystem

        # 检测日志级别
        detected_level = self._detect_level(message, subsystem)
        if detected_level != "INFO":
            level = detected_level

        # 检测网络相关信息
        if self._is_network_related(message, subsystem):
            fields["network_related"] = True

            # 提取网络设备名
            device_match = re.search(r"\b(\w+\d+):\s", message)
            if device_match:
                fields["device"] = device_match.group(1)

            # 提取IP地址
            ip_match = re.search(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b", message)
            if ip_match:
                fields["ip_address"] = ip_match.group(1)

        # 如果没有时间戳，使用当前时间
        if timestamp is None:
            timestamp = datetime.now()

        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            raw=line,
            fields=fields,
            process=subsystem or "kernel",
        )

    def _map_kernel_level(self, level: str) -> str:
        """映射内核日志级别"""
        level_map = {
            "EMERG": "FATAL",
            "ALERT": "FATAL",
            "CRIT": "FATAL",
            "ERR": "ERROR",
            "WARN": "WARN",
            "NOTICE": "INFO",
            "INFO": "INFO",
            "DEBUG": "DEBUG",
        }
        return level_map.get(level.upper(), "INFO")

    def _detect_level(self, message: str, subsystem: str) -> str:
        """检测日志级别"""
        message_lower = message.lower()

        for keyword in self.ERROR_KEYWORDS:
            if keyword in message_lower:
                if keyword in ["fatal", "panic", "critical"]:
                    return "FATAL"
                elif keyword in ["error", "fail", "failed", "exception", "abort", "corruption", "bug"]:
                    return "ERROR"
                elif keyword in ["warning", "warn", "timeout"]:
                    return "WARN"

        return "INFO"

    def _is_network_related(self, message: str, subsystem: str) -> bool:
        """检查是否是网络相关的消息"""
        # 检查子系统
        if subsystem in self.NETWORK_SUBSYSTEMS:
            return True

        # 检查消息内容
        message_lower = message.lower()
        network_keywords = [
            "link", "network", "ethernet", "connection", "socket",
            "packet", "rx", "tx", "dhcp", "arp", "route", "dns",
            "tcp", "udp", "ip", "ipv6", "icmp", "port", "firewall",
        ]

        for keyword in network_keywords:
            if keyword in message_lower:
                return True

        return False

    @staticmethod
    def detect(file_path: str) -> bool:
        """
        检测文件是否是dmesg格式

        Args:
            file_path: 文件路径

        Returns:
            是否是dmesg格式
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                # 检查前10行
                for _ in range(10):
                    line = f.readline()
                    if not line:
                        break

                    line = line.strip()
                    if not line:
                        continue

                    # 检查典型的dmesg格式
                    if DmesgParser.TIMESTAMP_PATTERN.match(line):
                        return True
                    if DmesgParser.HUMAN_TIMESTAMP_PATTERN.match(line):
                        return True

                    # 检查内核消息特征
                    if re.match(r"^\[\s*\d+\.\d+\]", line):
                        return True

            return False
        except Exception:
            return False


# 解析器注册信息
PARSER_NAME = "dmesg"
PARSER_CLASS = DmesgParser
