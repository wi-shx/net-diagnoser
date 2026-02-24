"""
审计日志模块

记录所有诊断操作的审计日志
"""

import json
import os
import csv
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
import threading


@dataclass
class AuditEntry:
    """审计日志条目"""

    id: str  # UUID
    timestamp: datetime  # 时间戳
    action: str  # 操作类型
    result: str  # 结果: success, failure
    host: Optional[str] = None  # 目标主机
    command: Optional[str] = None  # 执行的命令
    error_message: Optional[str] = None  # 错误信息
    duration_ms: int = 0  # 执行时长(毫秒)
    user: Optional[str] = None  # 执行用户
    source_ip: Optional[str] = None  # 来源IP
    details: Dict[str, Any] = field(default_factory=dict)  # 额外详情

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEntry":
        """从字典创建"""
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class AuditLogger:
    """
    审计日志记录器

    记录所有诊断操作的审计日志，支持查询和导出
    """

    # 操作类型常量
    ACTION_SSH_CONNECT = "ssh_connect"
    ACTION_SSH_DISCONNECT = "ssh_disconnect"
    ACTION_COMMAND_EXECUTE = "command_execute"
    ACTION_COMMAND_BATCH = "command_batch"
    ACTION_LOG_ANALYZE = "log_analyze"
    ACTION_REPORT_GENERATE = "report_generate"
    ACTION_AGENT_DIAGNOSE = "agent_diagnose"
    ACTION_AGENT_ACTION = "agent_action"
    ACTION_WHITELIST_CHECK = "whitelist_check"
    ACTION_PLAN_CREATE = "plan_create"
    ACTION_PLAN_EXECUTE = "plan_execute"

    # 结果常量
    RESULT_SUCCESS = "success"
    RESULT_FAILURE = "failure"
    RESULT_TIMEOUT = "timeout"
    RESULT_CANCELLED = "cancelled"

    def __init__(self, log_dir: str = "logs/audit", max_entries: int = 10000):
        """
        初始化审计日志记录器

        Args:
            log_dir: 日志目录
            max_entries: 内存中最大条目数
        """
        self.log_dir = log_dir
        self.max_entries = max_entries
        self._entries: List[AuditEntry] = []
        self._lock = threading.Lock()
        self._current_file: Optional[str] = None

        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)

    def log(
        self,
        action: str,
        result: str,
        host: Optional[str] = None,
        command: Optional[str] = None,
        error_message: Optional[str] = None,
        duration_ms: int = 0,
        user: Optional[str] = None,
        source_ip: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        记录审计日志

        Args:
            action: 操作类型
            result: 结果
            host: 目标主机
            command: 执行的命令
            error_message: 错误信息
            duration_ms: 执行时长(毫秒)
            user: 执行用户
            source_ip: 来源IP
            details: 额外详情

        Returns:
            日志条目ID
        """
        entry = AuditEntry(
            id=str(uuid4()),
            timestamp=datetime.now(),
            action=action,
            result=result,
            host=host,
            command=command,
            error_message=error_message,
            duration_ms=duration_ms,
            user=user,
            source_ip=source_ip,
            details=details or {},
        )

        with self._lock:
            self._entries.append(entry)

            # 如果超过最大条目数，写入文件并清理内存
            if len(self._entries) > self.max_entries:
                self._flush_to_file()

        return entry.id

    def log_command(
        self,
        command: str,
        host: str,
        result: str,
        exit_code: int = 0,
        duration_ms: int = 0,
        stdout_preview: Optional[str] = None,
        stderr_preview: Optional[str] = None,
    ) -> str:
        """
        记录命令执行

        Args:
            command: 执行的命令
            host: 目标主机
            result: 执行结果
            exit_code: 退出码
            duration_ms: 执行时长
            stdout_preview: stdout预览
            stderr_preview: stderr预览

        Returns:
            日志条目ID
        """
        details = {
            "exit_code": exit_code,
        }
        if stdout_preview:
            details["stdout_preview"] = stdout_preview[:500]
        if stderr_preview:
            details["stderr_preview"] = stderr_preview[:500]

        return self.log(
            action=self.ACTION_COMMAND_EXECUTE,
            result=result,
            host=host,
            command=command,
            duration_ms=duration_ms,
            details=details,
        )

    def log_ssh_connect(
        self,
        host: str,
        result: str,
        username: Optional[str] = None,
        port: int = 22,
        error_message: Optional[str] = None,
        duration_ms: int = 0,
    ) -> str:
        """
        记录SSH连接

        Args:
            host: 目标主机
            result: 连接结果
            username: 用户名
            port: 端口
            error_message: 错误信息
            duration_ms: 连接时长

        Returns:
            日志条目ID
        """
        return self.log(
            action=self.ACTION_SSH_CONNECT,
            result=result,
            host=host,
            user=username,
            error_message=error_message,
            duration_ms=duration_ms,
            details={"port": port},
        )

    def log_analyze(
        self,
        log_file: str,
        result: str,
        problem_type: Optional[str] = None,
        error_message: Optional[str] = None,
        duration_ms: int = 0,
    ) -> str:
        """
        记录日志分析

        Args:
            log_file: 日志文件
            result: 分析结果
            problem_type: 问题类型
            error_message: 错误信息
            duration_ms: 分析时长

        Returns:
            日志条目ID
        """
        details = {}
        if problem_type:
            details["problem_type"] = problem_type

        return self.log(
            action=self.ACTION_LOG_ANALYZE,
            result=result,
            error_message=error_message,
            duration_ms=duration_ms,
            details={"log_file": log_file, **details},
        )

    def log_agent_action(
        self,
        action_type: str,
        result: str,
        round_num: int,
        host: Optional[str] = None,
        command: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        记录Agent操作

        Args:
            action_type: 操作类型
            result: 结果
            round_num: 轮次
            host: 目标主机
            command: 执行的命令
            details: 额外详情

        Returns:
            日志条目ID
        """
        full_details = {"round": round_num, "action_type": action_type}
        if details:
            full_details.update(details)

        return self.log(
            action=self.ACTION_AGENT_ACTION,
            result=result,
            host=host,
            command=command,
            details=full_details,
        )

    def query(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        action: Optional[str] = None,
        result: Optional[str] = None,
        host: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """
        查询审计日志

        Args:
            start_time: 开始时间
            end_time: 结束时间
            action: 操作类型
            result: 结果
            host: 目标主机
            limit: 最大返回数量

        Returns:
            匹配的日志条目列表
        """
        with self._lock:
            entries = list(self._entries)

        # 过滤
        filtered = []
        for entry in entries:
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            if action and entry.action != action:
                continue
            if result and entry.result != result:
                continue
            if host and entry.host != host:
                continue
            filtered.append(entry)

        # 按时间倒序排序
        filtered.sort(key=lambda x: x.timestamp, reverse=True)

        return filtered[:limit]

    def get_entry(self, entry_id: str) -> Optional[AuditEntry]:
        """
        获取单个日志条目

        Args:
            entry_id: 条目ID

        Returns:
            日志条目，不存在返回None
        """
        with self._lock:
            for entry in self._entries:
                if entry.id == entry_id:
                    return entry
        return None

    def export(
        self,
        path: str,
        format: str = "json",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """
        导出审计日志

        Args:
            path: 导出文件路径
            format: 格式 (json, csv)
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            导出的条目数量
        """
        entries = self.query(start_time=start_time, end_time=end_time, limit=10000)

        if format == "json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump([e.to_dict() for e in entries], f, ensure_ascii=False, indent=2)
        elif format == "csv":
            with open(path, "w", newline="", encoding="utf-8") as f:
                if entries:
                    fieldnames = list(asdict(entries[0]).keys())
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for entry in entries:
                        row = entry.to_dict()
                        row["details"] = json.dumps(row.get("details", {}), ensure_ascii=False)
                        writer.writerow(row)
        else:
            raise ValueError(f"Unsupported format: {format}")

        return len(entries)

    def _flush_to_file(self) -> None:
        """将内存中的日志写入文件"""
        if not self._entries:
            return

        # 按日期创建文件
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"audit_{today}.jsonl"
        filepath = os.path.join(self.log_dir, filename)

        with open(filepath, "a", encoding="utf-8") as f:
            for entry in self._entries:
                f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

        # 清空内存
        self._entries.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计数据
        """
        with self._lock:
            entries = list(self._entries)

        if not entries:
            return {
                "total": 0,
                "by_action": {},
                "by_result": {},
                "by_host": {},
            }

        by_action: Dict[str, int] = {}
        by_result: Dict[str, int] = {}
        by_host: Dict[str, int] = {}

        for entry in entries:
            by_action[entry.action] = by_action.get(entry.action, 0) + 1
            by_result[entry.result] = by_result.get(entry.result, 0) + 1
            if entry.host:
                by_host[entry.host] = by_host.get(entry.host, 0) + 1

        return {
            "total": len(entries),
            "by_action": by_action,
            "by_result": by_result,
            "by_host": by_host,
        }

    def clear(self) -> None:
        """清空内存中的日志"""
        with self._lock:
            self._entries.clear()


# 全局默认实例
_default_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """获取全局审计日志记录器"""
    global _default_logger
    if _default_logger is None:
        _default_logger = AuditLogger()
    return _default_logger


def set_audit_logger(logger: AuditLogger) -> None:
    """设置全局审计日志记录器"""
    global _default_logger
    _default_logger = logger
