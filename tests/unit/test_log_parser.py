"""
测试日志解析器
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.log_parser import LogParser, LogStatistics
from parsers.base import LogEntry


class TestLogParser:
    """日志解析器测试"""

    def test_init_without_format(self):
        """测试不指定格式初始化"""
        parser = LogParser()
        assert parser.format is None

    def test_init_with_format(self):
        """测试指定格式初始化"""
        parser = LogParser(format="nginx")
        assert parser.format == "nginx"

    def test_init_with_invalid_format(self):
        """测试无效格式"""
        with pytest.raises(ValueError, match="Unsupported log format"):
            LogParser(format="invalid")

    def test_detect_nginx_format(self):
        """测试检测Nginx格式"""
        parser = LogParser()
        format_type = parser.detect_format("samples/nginx_sample.log")
        assert format_type == "nginx"

    def test_detect_haproxy_format(self):
        """测试检测HAProxy格式"""
        parser = LogParser()
        format_type = parser.detect_format("samples/haproxy_sample.log")
        assert format_type == "haproxy"

    def test_detect_syslog_format(self):
        """测试检测Syslog格式"""
        parser = LogParser()
        format_type = parser.detect_format("samples/syslog_sample.log")
        assert format_type == "syslog"

    def test_parse_nginx_file(self):
        """测试解析Nginx文件"""
        parser = LogParser(format="nginx")
        entries = parser.parse_file("samples/nginx_sample.log")

        assert len(entries) > 0
        # entries可能是list，也可能不是，所以先转换
        entries_list = list(entries) if not isinstance(entries, list) else entries
        assert all(isinstance(entry, LogEntry) for entry in entries_list)
        assert all(entry.level in ["INFO", "WARN", "ERROR"] for entry in entries_list)

    def test_get_statistics(self):
        """测试获取统计信息"""
        parser = LogParser(format="nginx")
        entries = parser.parse_file("samples/nginx_sample.log")
        stats = parser.get_statistics(entries)

        assert isinstance(stats, LogStatistics)
        assert stats.total_lines == len(entries)
        assert stats.error_lines >= 0
        assert stats.error_rate >= 0
        assert len(stats.level_counts) > 0
