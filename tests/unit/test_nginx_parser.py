"""
测试Nginx解析器
"""

import pytest
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from parsers.nginx_parser import NginxParser


class TestNginxParser:
    """Nginx解析器测试"""

    def test_parse_access_log(self):
        """测试解析访问日志"""
        parser = NginxParser()
        line = '127.0.0.1 - - [15/Feb/2026:10:00:00 +0800] "GET /api HTTP/1.1" 200 1234 "-" "Mozilla/5.0"'
        entry = parser.parse_line(line)

        assert entry is not None
        assert entry.ip_address == "127.0.0.1"
        assert entry.request_method == "GET"
        assert entry.request_url == "/api"
        assert entry.status_code == 200
        assert entry.level == "INFO"

    def test_parse_error_log(self):
        """测试解析错误日志"""
        parser = NginxParser()
        line = '2026/02/15 10:00:00 [error] 123#123: connection timeout'
        entry = parser.parse_line(line)

        assert entry is not None
        assert entry.level == "ERROR"
        assert "connection timeout" in entry.message

    def test_parse_500_status(self):
        """测试500状态码"""
        parser = NginxParser()
        line = '127.0.0.1 - - [15/Feb/2026:10:00:00 +0800] "GET /api HTTP/1.1" 500 567 "-" "curl/7.68.0"'
        entry = parser.parse_line(line)

        assert entry.status_code == 500
        assert entry.level == "ERROR"

    def test_parse_400_status(self):
        """测试400状态码"""
        parser = NginxParser()
        line = '127.0.0.1 - - [15/Feb/2026:10:00:00 +0800] "GET /api HTTP/1.1" 404 123 "-" "Mozilla/5.0"'
        entry = parser.parse_line(line)

        assert entry.status_code == 404
        assert entry.level == "WARN"

    def test_parse_empty_line(self):
        """测试空行"""
        parser = NginxParser()
        entry = parser.parse_line("")

        assert entry is None

    def test_parse_invalid_line(self):
        """测试无效行"""
        parser = NginxParser()
        entry = parser.parse_line("invalid log line")

        assert entry is None

    def test_detect(self):
        """测试格式检测"""
        assert NginxParser.detect("samples/nginx_sample.log")
