"""
Agent工具函数

提供Agent可以调用的诊断工具
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Callable
import asyncio

from src.core.ai_analyzer import AIAnalyzer, AnalysisResult, SuggestedCommand
from src.core.log_parser import LogParser, LogEntry, LogStatistics
from src.core.command_whitelist import CommandWhitelist, WhitelistedCommand
from src.core.ssh_executor import SSHExecutor, SSHConfig, CommandResult, MockSSHExecutor
from src.core.audit_logger import get_audit_logger, AuditLogger
from src.utils.exceptions import CommandNotAllowedError, SSHError


@dataclass
class ToolResult:
    """工具执行结果"""

    success: bool
    data: Any
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data if not isinstance(self.data, str) else self.data,
            "error": self.error,
        }


class AgentTools:
    """
    Agent可用的工具集

    封装各种诊断操作为可调用的工具
    """

    def __init__(
        self,
        ai_analyzer: AIAnalyzer,
        whitelist: Optional[CommandWhitelist] = None,
        audit_logger: Optional[AuditLogger] = None,
        ssh_configs: Optional[Dict[str, SSHConfig]] = None,
        mock_mode: bool = False,
    ):
        """
        初始化工具集

        Args:
            ai_analyzer: AI分析器
            whitelist: 命令白名单
            audit_logger: 审计日志记录器
            ssh_configs: SSH配置字典
            mock_mode: 是否使用模拟模式
        """
        self.ai_analyzer = ai_analyzer
        self.whitelist = whitelist or CommandWhitelist()
        self.audit_logger = audit_logger or get_audit_logger()
        self.ssh_configs = ssh_configs or {}
        self.mock_mode = mock_mode

        # SSH连接缓存
        self._ssh_connections: Dict[str, SSHExecutor] = {}

        # 工具注册表
        self._tools: Dict[str, Callable] = {
            "analyze_logs": self.analyze_logs,
            "execute_command": self.execute_command,
            "validate_command": self.validate_command,
            "ping_host": self.ping_host,
            "check_port": self.check_port,
            "check_dns": self.check_dns,
            "check_service": self.check_service,
            "get_network_stats": self.get_network_stats,
        }

    def get_available_tools(self) -> List[str]:
        """获取可用工具列表"""
        return list(self._tools.keys())

    async def call_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """
        调用工具

        Args:
            tool_name: 工具名称
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        if tool_name not in self._tools:
            return ToolResult(
                success=False,
                data=None,
                error=f"Unknown tool: {tool_name}",
            )

        try:
            result = await self._tools[tool_name](**kwargs)
            return result
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    async def analyze_logs(
        self,
        entries: List[LogEntry],
        statistics: LogStatistics,
    ) -> ToolResult:
        """
        分析日志

        Args:
            entries: 日志条目
            statistics: 统计信息

        Returns:
            分析结果
        """
        try:
            result = await self.ai_analyzer.analyze(entries, statistics)
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    async def execute_command(
        self,
        command: str,
        host: str = "localhost",
        validate: bool = True,
        timeout: float = 30.0,
    ) -> ToolResult:
        """
        执行命令

        Args:
            command: 要执行的命令
            host: 目标主机
            validate: 是否验证白名单
            timeout: 超时时间

        Returns:
            命令执行结果
        """
        # 验证命令
        if validate:
            try:
                self.whitelist.validate_or_raise(command)
            except CommandNotAllowedError as e:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Command not allowed: {e.message}",
                )

        try:
            # 获取或创建SSH连接
            executor = await self._get_executor(host)

            # 执行命令
            result = await executor.execute(command, timeout=timeout)

            return ToolResult(
                success=result.success,
                data={
                    "exit_code": result.exit_code,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "duration": result.duration,
                },
                error=result.stderr if not result.success else None,
            )
        except SSHError as e:
            return ToolResult(success=False, data=None, error=str(e))

    async def validate_command(self, command: str) -> ToolResult:
        """
        验证命令是否在白名单中

        Args:
            command: 命令字符串

        Returns:
            验证结果
        """
        is_valid, cmd_info = self.whitelist.validate(command)

        return ToolResult(
            success=True,
            data={
                "valid": is_valid,
                "command": command,
                "info": {
                    "description": cmd_info.description if cmd_info else None,
                    "category": cmd_info.category if cmd_info else None,
                    "risk_level": cmd_info.risk_level if cmd_info else None,
                }
                if cmd_info
                else None,
            },
        )

    async def ping_host(self, host: str, count: int = 3) -> ToolResult:
        """
        Ping主机

        Args:
            host: 目标主机
            count: Ping次数

        Returns:
            Ping结果
        """
        command = f"ping -c {count} {host}"
        return await self.execute_command(command, validate=True)

    async def check_port(self, host: str, port: int, timeout: float = 5.0) -> ToolResult:
        """
        检查端口是否开放

        Args:
            host: 目标主机
            port: 端口号
            timeout: 超时时间

        Returns:
            检查结果
        """
        command = f"nc -zv -w {int(timeout)} {host} {port}"
        return await self.execute_command(command, validate=True)

    async def check_dns(self, domain: str, dns_server: Optional[str] = None) -> ToolResult:
        """
        检查DNS解析

        Args:
            domain: 域名
            dns_server: DNS服务器

        Returns:
            DNS查询结果
        """
        if dns_server:
            command = f"dig @{dns_server} {domain} +short"
        else:
            command = f"dig {domain} +short"

        return await self.execute_command(command, validate=True)

    async def check_service(self, service_name: str, host: str = "localhost") -> ToolResult:
        """
        检查服务状态

        Args:
            service_name: 服务名称
            host: 目标主机

        Returns:
            服务状态
        """
        command = f"systemctl status {service_name}"
        return await self.execute_command(command, host=host, validate=True)

    async def get_network_stats(self, host: str = "localhost") -> ToolResult:
        """
        获取网络统计

        Args:
            host: 目标主机

        Returns:
            网络统计信息
        """
        results = {}

        # 获取连接状态
        ss_result = await self.execute_command("ss -tulpn", host=host)
        if ss_result.success:
            results["sockets"] = ss_result.data

        # 获取路由表
        route_result = await self.execute_command("ip route show", host=host)
        if route_result.success:
            results["routes"] = route_result.data

        # 获取ARP缓存
        arp_result = await self.execute_command("arp -a -n", host=host)
        if arp_result.success:
            results["arp"] = arp_result.data

        return ToolResult(success=True, data=results)

    async def _get_executor(self, host: str) -> SSHExecutor:
        """获取SSH执行器"""
        if host in self._ssh_connections:
            executor = self._ssh_connections[host]
            if executor.is_connected:
                return executor

        # 创建新连接
        if host == "localhost":
            # 本地使用Mock执行器
            config = SSHConfig(host="localhost")
            executor = MockSSHExecutor(config, self.audit_logger)
            await executor.connect()
        else:
            config = self.ssh_configs.get(
                host,
                SSHConfig(host=host),
            )
            if self.mock_mode:
                executor = MockSSHExecutor(config, self.audit_logger)
            else:
                executor = SSHExecutor(config, self.audit_logger)
            await executor.connect()

        self._ssh_connections[host] = executor
        return executor

    async def close_all(self) -> None:
        """关闭所有连接"""
        for executor in self._ssh_connections.values():
            await executor.close()
        self._ssh_connections.clear()

    async def __aenter__(self) -> "AgentTools":
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        await self.close_all()
