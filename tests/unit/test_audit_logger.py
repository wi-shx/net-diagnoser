"""
审计日志模块测试
"""

import pytest
import os
import json
import tempfile
from datetime import datetime, timedelta

from src.core.audit_logger import (
    AuditLogger,
    AuditEntry,
    get_audit_logger,
    set_audit_logger,
)


class TestAuditEntry:
    """AuditEntry测试"""

    def test_create_entry(self):
        """测试创建审计条目"""
        entry = AuditEntry(
            id="test-id-123",
            timestamp=datetime.now(),
            action="test_action",
            result="success",
        )

        assert entry.id == "test-id-123"
        assert entry.action == "test_action"
        assert entry.result == "success"

    def test_to_dict(self):
        """测试转换为字典"""
        timestamp = datetime(2026, 2, 24, 10, 0, 0)
        entry = AuditEntry(
            id="test-id",
            timestamp=timestamp,
            action="execute",
            result="success",
            command="ping localhost",
            host="server1",
        )

        data = entry.to_dict()

        assert data["id"] == "test-id"
        assert data["action"] == "execute"
        assert data["timestamp"] == "2026-02-24T10:00:00"
        assert data["command"] == "ping localhost"
        assert data["host"] == "server1"

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "id": "test-id",
            "timestamp": "2026-02-24T10:00:00",
            "action": "analyze",
            "result": "success",
            "command": None,
            "host": None,
            "error_message": None,
            "duration_ms": 100,
            "user": None,
            "source_ip": None,
            "details": {},
        }

        entry = AuditEntry.from_dict(data)

        assert entry.id == "test-id"
        assert entry.timestamp == datetime(2026, 2, 24, 10, 0, 0)
        assert entry.action == "analyze"


class TestAuditLogger:
    """AuditLogger测试"""

    def test_create_logger(self):
        """测试创建日志记录器"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)
            assert logger.log_dir == tmpdir

    def test_log_basic(self):
        """测试基本日志记录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)

            entry_id = logger.log(
                action="test_action",
                result="success",
            )

            assert entry_id is not None
            assert len(entry_id) > 0

    def test_log_command(self):
        """测试命令执行日志"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)

            entry_id = logger.log_command(
                command="ping localhost",
                host="server1",
                result="success",
                exit_code=0,
                duration_ms=50,
                stdout_preview="PING localhost",
            )

            assert entry_id is not None

            # 验证日志条目
            entries = logger.query(limit=10)
            assert len(entries) == 1
            assert entries[0].action == "command_execute"
            assert entries[0].command == "ping localhost"
            assert entries[0].host == "server1"

    def test_log_ssh_connect(self):
        """测试SSH连接日志"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)

            entry_id = logger.log_ssh_connect(
                host="server1",
                result="success",
                username="root",
                port=22,
            )

            assert entry_id is not None

            entries = logger.query(action="ssh_connect")
            assert len(entries) == 1
            assert entries[0].host == "server1"

    def test_query_by_action(self):
        """测试按操作类型查询"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)

            logger.log(action="action_a", result="success")
            logger.log(action="action_b", result="success")
            logger.log(action="action_a", result="failure")

            entries = logger.query(action="action_a")
            assert len(entries) == 2

    def test_query_by_time_range(self):
        """测试按时间范围查询"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)

            # 记录一些日志
            logger.log(action="test1", result="success")
            logger.log(action="test2", result="success")

            # 查询最近1小时
            start = datetime.now() - timedelta(hours=1)
            end = datetime.now() + timedelta(hours=1)

            entries = logger.query(start_time=start, end_time=end)
            assert len(entries) == 2

    def test_query_by_result(self):
        """测试按结果查询"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)

            logger.log(action="test", result="success")
            logger.log(action="test", result="failure")
            logger.log(action="test", result="success")

            success_entries = logger.query(result="success")
            assert len(success_entries) == 2

            failure_entries = logger.query(result="failure")
            assert len(failure_entries) == 1

    def test_export_json(self):
        """测试导出为JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)

            logger.log(action="test", result="success", command="echo hello")

            export_path = os.path.join(tmpdir, "audit_export.json")
            count = logger.export(export_path, format="json")

            assert count == 1
            assert os.path.exists(export_path)

            # 验证导出内容
            with open(export_path, "r") as f:
                data = json.load(f)
                assert len(data) == 1
                assert data[0]["action"] == "test"

    def test_export_csv(self):
        """测试导出为CSV"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)

            logger.log(action="test", result="success")

            export_path = os.path.join(tmpdir, "audit_export.csv")
            count = logger.export(export_path, format="csv")

            assert count == 1
            assert os.path.exists(export_path)

    def test_get_statistics(self):
        """测试获取统计信息"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)

            logger.log(action="action_a", result="success", host="host1")
            logger.log(action="action_b", result="failure", host="host1")
            logger.log(action="action_a", result="success", host="host2")

            stats = logger.get_statistics()

            assert stats["total"] == 3
            assert stats["by_action"]["action_a"] == 2
            assert stats["by_action"]["action_b"] == 1
            assert stats["by_result"]["success"] == 2
            assert stats["by_result"]["failure"] == 1

    def test_get_entry(self):
        """测试获取单个条目"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)

            entry_id = logger.log(action="test", result="success")

            entry = logger.get_entry(entry_id)
            assert entry is not None
            assert entry.id == entry_id

            # 不存在的ID
            entry = logger.get_entry("non-existent-id")
            assert entry is None

    def test_clear(self):
        """测试清空日志"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)

            logger.log(action="test", result="success")
            assert len(logger.query(limit=100)) == 1

            logger.clear()
            assert len(logger.query(limit=100)) == 0


class TestAuditLoggerGlobal:
    """全局审计日志测试"""

    def test_get_audit_logger(self):
        """测试获取全局日志记录器"""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()

        assert logger1 is logger2

    def test_set_audit_logger(self):
        """测试设置全局日志记录器"""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_logger = AuditLogger(log_dir=tmpdir)
            set_audit_logger(custom_logger)

            logger = get_audit_logger()
            assert logger is custom_logger


class TestAuditLoggerConcurrency:
    """审计日志并发测试"""

    def test_concurrent_logging(self):
        """测试并发日志记录"""
        import threading

        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)

            def log_entries(count: int):
                for i in range(count):
                    logger.log(action=f"thread_action_{i}", result="success")

            threads = [
                threading.Thread(target=log_entries, args=(10,))
                for _ in range(5)
            ]

            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # 应该有50条记录
            entries = logger.query(limit=100)
            assert len(entries) == 50
