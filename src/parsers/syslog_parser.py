"""
Syslog解析器
"""

import re
from typing import Optional
from src.parsers.base import BaseParser, LogEntry


class SyslogParser(BaseParser):
    """Syslog解析器"""

    # RFC3164格式: Feb 15 10:00:00 server kernel: message
    # RFC5424格式: <134>1 2026-02-15T10:00:00.123456+08:00 server kernel 1234 - - message
    PATTERN_RFC3164 = re.compile(r'^(\w+ \d+ \d{2}:\d{2}:\d{2}) (\S+) (\S+): (.+)')

    PATTERN_RFC5424 = re.compile(
        r'^<\d+>\d+ (\S+) (\S+) (\S+) \d+ - - (.+)', re.IGNORECASE
    )

    def parse_line(self, line: str) -> Optional[LogEntry]:
        """
        解析Syslog日志行

        Args:
            line: 日志行

        Returns:
            LogEntry对象，解析失败返回None
        """
        line = line.strip()
        if not line:
            return None

        # 尝试RFC3164格式
        match = self.PATTERN_RFC3164.match(line)
        if match:
            timestamp_str, host, process, message = match.groups()
            timestamp = self.extract_timestamp(timestamp_str)

            # 从消息中提取级别
            level = self._extract_level(message)

            return LogEntry(
                timestamp=timestamp,
                level=level,
                message=message,
                raw=line,
                fields={"host": host},
                process=process,
            )

        # 尝试RFC5424格式
        match = self.PATTERN_RFC5424.match(line)
        if match:
            timestamp_str, host, process, message = match.groups()
            # RFC5424使用ISO格式，去掉毫秒部分
            if "." in timestamp_str:
                timestamp_str = timestamp_str.split(".")[0].replace("T", " ")
            timestamp = self.extract_timestamp(timestamp_str)

            level = self._extract_level(message)

            return LogEntry(
                timestamp=timestamp,
                level=level,
                message=message,
                raw=line,
                fields={"host": host},
                process=process,
            )

        return None

    def _extract_level(self, message: str) -> str:
        """
        从消息中提取日志级别

        Args:
            message: 消息内容

        Returns:
            日志级别
        """
        message_lower = message.lower()

        if any(keyword in message_lower for keyword in ["error", "err", "failed", "fail"]):
            return "ERROR"
        elif any(keyword in message_lower for keyword in ["warn", "warning"]):
            return "WARN"
        elif any(keyword in message_lower for keyword in ["fatal", "crit", "critical"]):
            return "FATAL"
        elif "debug" in message_lower:
            return "DEBUG"
        else:
            return "INFO"

    @staticmethod
    def detect(file_path: str) -> bool:
        """
        检测是否为Syslog

        Args:
            file_path: 文件路径

        Returns:
            是否为Syslog
        """
        from src.utils.file_handler import read_lines

        for i, line in enumerate(read_lines(file_path)):
            if i >= 10:  # 只检查前10行
                break
            if SyslogParser.PATTERN_RFC3164.match(line) or SyslogParser.PATTERN_RFC5424.match(
                line
            ):
                return True
        return False
