"""
HAProxy日志解析器
"""

import re
from typing import Optional
from src.parsers.base import BaseParser, LogEntry


class HAProxyParser(BaseParser):
    """HAProxy日志解析器"""

    # HAProxy日志格式
    # Feb 15 10:00:00 localhost haproxy[1234]: 127.0.0.1:12345 [15/Feb/2026:10:00:00.123] backend1 server1 0/0/0/1 500 0 - ----
    PATTERN = re.compile(
        r'^\w+ \d+ \d{2}:\d{2}:\d{2} \S+ \w+\[\d+\]: '
        r'(\S+):\d+ \[([^\]]+)\] (\S+) (\S+) '
        r'\d+/\d+/\d+/\d+ (\d{3})'
    )

    def parse_line(self, line: str) -> Optional[LogEntry]:
        """
        解析HAProxy日志行

        Args:
            line: 日志行

        Returns:
            LogEntry对象，解析失败返回None
        """
        line = line.strip()
        if not line:
            return None

        match = self.PATTERN.match(line)
        if not match:
            return None

        ip, timestamp, backend, server, status = match.groups()
        timestamp = self.extract_timestamp(timestamp)

        # 根据状态码判断级别
        if int(status) >= 500:
            level = "ERROR"
        elif int(status) >= 400:
            level = "WARN"
        else:
            level = "INFO"

        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=f"{backend} -> {server}: {status}",
            raw=line,
            fields={},
            ip_address=ip.split(":")[0],
            backend_name=backend,
            server_name=server,
            status_code=int(status),
        )

    @staticmethod
    def detect(file_path: str) -> bool:
        """
        检测是否为HAProxy日志

        Args:
            file_path: 文件路径

        Returns:
            是否为HAProxy日志
        """
        from src.utils.file_handler import read_lines

        for i, line in enumerate(read_lines(file_path)):
            if i >= 10:  # 只检查前10行
                break
            if HAProxyParser.PATTERN.match(line):
                return True
        return False
