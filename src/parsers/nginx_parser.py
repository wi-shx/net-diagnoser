"""
Nginx日志解析器
"""

import re
from typing import Optional
from src.parsers.base import BaseParser, LogEntry


class NginxParser(BaseParser):
    """Nginx日志解析器"""

    # Nginx访问日志格式（combined）
    # 127.0.0.1 - - [15/Feb/2026:10:00:00 +0800] "GET /api HTTP/1.1" 200 123 "-" "Mozilla/5.0"
    PATTERN = re.compile(
        r'^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) (\S+) HTTP/\d\.\d" (\d{3}) (\d+)'
    )

    # Nginx错误日志格式
    # 2026/02/15 10:00:00 [error] 123#123: connection timeout
    ERROR_PATTERN = re.compile(r'^\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2} \[(\w+)\]')

    def parse_line(self, line: str) -> Optional[LogEntry]:
        """
        解析Nginx日志行

        Args:
            line: 日志行

        Returns:
            LogEntry对象，解析失败返回None
        """
        line = line.strip()
        if not line:
            return None

        # 尝试匹配访问日志
        match = self.PATTERN.match(line)
        if match:
            ip, timestamp, method, url, status, size = match.groups()
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
                message=f"{method} {url} - {status}",
                raw=line,
                fields={
                    "size": int(size),
                },
                ip_address=ip,
                request_method=method,
                request_url=url,
                status_code=int(status),
            )

        # 尝试匹配错误日志
        error_match = self.ERROR_PATTERN.match(line)
        if error_match:
            level = error_match.group(1)
            timestamp_str = line[:19]  # 2026/02/15 10:00:00
            timestamp = self.extract_timestamp(timestamp_str.replace("/", "-"))
            message = line.split(":", 1)[1].strip() if ":" in line else line

            return LogEntry(
                timestamp=timestamp,
                level=self.normalize_level(level),
                message=message,
                raw=line,
                fields={},
            )

        return None

    @staticmethod
    def detect(file_path: str) -> bool:
        """
        检测是否为Nginx日志

        Args:
            file_path: 文件路径

        Returns:
            是否为Nginx日志
        """
        from src.utils.file_handler import read_lines

        for i, line in enumerate(read_lines(file_path)):
            if i >= 10:  # 只检查前10行
                break
            if NginxParser.PATTERN.match(line) or NginxParser.ERROR_PATTERN.match(
                line
            ):
                return True
        return False
