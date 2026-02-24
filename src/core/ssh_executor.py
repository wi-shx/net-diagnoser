"""
SSH执行器模块

通过SSH远程执行诊断命令
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import time

from src.utils.exceptions import (
    SSHConnectionError,
    SSHAuthenticationError,
    SSHTimeoutError,
    SSHCommandError,
    SSHError,
)
from src.core.audit_logger import get_audit_logger, AuditLogger


@dataclass
class SSHConfig:
    """SSH连接配置"""

    host: str
    port: int = 22
    username: str = "root"
    password: Optional[str] = None
    private_key_path: Optional[str] = None
    private_key_passphrase: Optional[str] = None
    timeout: float = 30.0
    command_timeout: float = 60.0
    banner_timeout: float = 30.0
    keepalive_interval: float = 30.0
    known_hosts_file: Optional[str] = None
    allow_unknown_hosts: bool = True  # 开发环境使用，生产环境应设为False


@dataclass
class CommandResult:
    """命令执行结果"""

    command: str  # 执行的命令
    exit_code: int  # 退出码
    stdout: str  # 标准输出
    stderr: str  # 标准错误
    duration: float  # 执行时长(秒)
    host: str  # 目标主机
    timestamp: datetime  # 执行时间

    @property
    def success(self) -> bool:
        """是否执行成功"""
        return self.exit_code == 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "command": self.command,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration": self.duration,
            "host": self.host,
            "timestamp": self.timestamp.isoformat(),
        }


class SSHExecutor:
    """
    SSH命令执行器

    通过SSH协议在远程主机上执行命令
    """

    def __init__(
        self,
        config: SSHConfig,
        audit_logger: Optional[AuditLogger] = None,
    ):
        """
        初始化SSH执行器

        Args:
            config: SSH配置
            audit_logger: 审计日志记录器
        """
        self.config = config
        self.audit_logger = audit_logger or get_audit_logger()
        self._client = None
        self._connected = False
        self._connection_time: Optional[datetime] = None

    async def connect(self) -> None:
        """
        建立SSH连接

        Raises:
            SSHConnectionError: 连接失败
            SSHAuthenticationError: 认证失败
            SSHTimeoutError: 连接超时
        """
        start_time = time.time()

        try:
            # 尝试导入asyncssh
            import asyncssh

            # 构建连接参数
            connect_kwargs: Dict[str, Any] = {
                "host": self.config.host,
                "port": self.config.port,
                "username": self.config.username,
                "known_hosts": None if self.config.allow_unknown_hosts else self.config.known_hosts_file,
            }

            # 认证方式
            if self.config.private_key_path:
                connect_kwargs["client_keys"] = [self.config.private_key_path]
                if self.config.private_key_passphrase:
                    connect_kwargs["passphrase"] = self.config.private_key_passphrase
            elif self.config.password:
                connect_kwargs["password"] = self.config.password

            # 超时设置
            connect_kwargs["connect_timeout"] = self.config.timeout

            # 建立连接
            self._client = await asyncio.wait_for(
                asyncssh.connect(**connect_kwargs),
                timeout=self.config.timeout,
            )

            self._connected = True
            self._connection_time = datetime.now()

            duration_ms = int((time.time() - start_time) * 1000)
            self.audit_logger.log_ssh_connect(
                host=self.config.host,
                result="success",
                username=self.config.username,
                port=self.config.port,
                duration_ms=duration_ms,
            )

        except asyncio.TimeoutError as e:
            self.audit_logger.log_ssh_connect(
                host=self.config.host,
                result="timeout",
                username=self.config.username,
                port=self.config.port,
                error_message=f"Connection timeout after {self.config.timeout}s",
            )
            raise SSHTimeoutError(
                f"SSH connection timeout: {self.config.host}:{self.config.port}",
                host=self.config.host,
            ) from e

        except asyncssh.DisconnectError as e:
            self.audit_logger.log_ssh_connect(
                host=self.config.host,
                result="failure",
                username=self.config.username,
                port=self.config.port,
                error_message=str(e),
            )
            raise SSHConnectionError(
                f"SSH connection failed: {e.reason}",
                host=self.config.host,
            ) from e

        except asyncssh.PermissionDenied as e:
            self.audit_logger.log_ssh_connect(
                host=self.config.host,
                result="failure",
                username=self.config.username,
                port=self.config.port,
                error_message=str(e),
            )
            raise SSHAuthenticationError(
                f"SSH authentication failed: {e}",
                host=self.config.host,
            ) from e

        except Exception as e:
            error_msg = str(e)
            self.audit_logger.log_ssh_connect(
                host=self.config.host,
                result="failure",
                username=self.config.username,
                port=self.config.port,
                error_message=error_msg,
            )
            raise SSHConnectionError(
                f"SSH connection error: {error_msg}",
                host=self.config.host,
            ) from e

    async def execute(self, command: str, timeout: Optional[float] = None) -> CommandResult:
        """
        执行单个命令

        Args:
            command: 要执行的命令
            timeout: 超时时间(秒)，None使用默认值

        Returns:
            命令执行结果

        Raises:
            SSHError: 未连接
            SSHTimeoutError: 执行超时
            SSHCommandError: 执行失败
        """
        if not self._connected or self._client is None:
            raise SSHError("Not connected to SSH server", host=self.config.host)

        timeout = timeout or self.config.command_timeout
        start_time = time.time()
        timestamp = datetime.now()

        try:
            result = await asyncio.wait_for(
                self._client.run(command),
                timeout=timeout,
            )

            duration = time.time() - start_time
            duration_ms = int(duration * 1000)

            cmd_result = CommandResult(
                command=command,
                exit_code=result.exit_status,
                stdout=result.stdout,
                stderr=result.stderr,
                duration=duration,
                host=self.config.host,
                timestamp=timestamp,
            )

            # 记录审计日志
            self.audit_logger.log_command(
                command=command,
                host=self.config.host,
                result="success" if cmd_result.success else "failure",
                exit_code=cmd_result.exit_code,
                duration_ms=duration_ms,
                stdout_preview=cmd_result.stdout[:500] if cmd_result.stdout else None,
                stderr_preview=cmd_result.stderr[:500] if cmd_result.stderr else None,
            )

            return cmd_result

        except asyncio.TimeoutError as e:
            duration = time.time() - start_time
            self.audit_logger.log_command(
                command=command,
                host=self.config.host,
                result="timeout",
                exit_code=-1,
                duration_ms=int(duration * 1000),
                stderr_preview=f"Command timeout after {timeout}s",
            )
            raise SSHTimeoutError(
                f"Command execution timeout after {timeout}s: {command}",
                host=self.config.host,
            ) from e

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            self.audit_logger.log_command(
                command=command,
                host=self.config.host,
                result="failure",
                exit_code=-1,
                duration_ms=int(duration * 1000),
                stderr_preview=error_msg,
            )
            raise SSHCommandError(
                f"Command execution failed: {error_msg}",
                host=self.config.host,
                command=command,
            ) from e

    async def execute_batch(
        self,
        commands: List[str],
        timeout: Optional[float] = None,
        stop_on_error: bool = False,
    ) -> List[CommandResult]:
        """
        批量执行命令

        Args:
            commands: 命令列表
            timeout: 每个命令的超时时间
            stop_on_error: 遇到错误是否停止

        Returns:
            命令结果列表
        """
        results = []

        for command in commands:
            try:
                result = await self.execute(command, timeout=timeout)
                results.append(result)

                if stop_on_error and not result.success:
                    break

            except (SSHTimeoutError, SSHCommandError) as e:
                # 创建失败结果
                results.append(
                    CommandResult(
                        command=command,
                        exit_code=-1,
                        stdout="",
                        stderr=str(e),
                        duration=0,
                        host=self.config.host,
                        timestamp=datetime.now(),
                    )
                )

                if stop_on_error:
                    break

        return results

    async def execute_with_retry(
        self,
        command: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None,
    ) -> CommandResult:
        """
        带重试的命令执行

        Args:
            command: 要执行的命令
            max_retries: 最大重试次数
            retry_delay: 重试间隔(秒)
            timeout: 超时时间

        Returns:
            命令执行结果

        Raises:
            SSHCommandError: 所有重试都失败
        """
        last_error: Optional[Exception] = None

        for attempt in range(max_retries):
            try:
                return await self.execute(command, timeout=timeout)
            except (SSHTimeoutError, SSHCommandError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)

        raise SSHCommandError(
            f"Command failed after {max_retries} retries: {command}",
            host=self.config.host,
            command=command,
        ) from last_error

    async def close(self) -> None:
        """关闭SSH连接"""
        if self._client:
            self._client.close()
            await self._client.wait_closed()
            self._client = None
            self._connected = False

            self.audit_logger.log(
                action="ssh_disconnect",
                result="success",
                host=self.config.host,
            )

    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._connected and self._client is not None

    @property
    def connection_info(self) -> Dict[str, Any]:
        """连接信息"""
        return {
            "host": self.config.host,
            "port": self.config.port,
            "username": self.config.username,
            "connected": self._connected,
            "connection_time": self._connection_time.isoformat() if self._connection_time else None,
        }

    async def __aenter__(self) -> "SSHExecutor":
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        await self.close()


class MockSSHExecutor(SSHExecutor):
    """
    模拟SSH执行器

    用于测试，不进行真实的SSH连接
    """

    def __init__(
        self,
        config: SSHConfig,
        audit_logger: Optional[AuditLogger] = None,
        simulate_failures: bool = False,
        failure_rate: float = 0.0,
        simulate_latency: bool = True,
        min_latency: float = 0.01,
        max_latency: float = 0.5,
    ):
        """
        初始化模拟SSH执行器

        Args:
            config: SSH配置
            audit_logger: 审计日志记录器
            simulate_failures: 是否模拟故障
            failure_rate: 故障率 (0.0-1.0)
            simulate_latency: 是否模拟延迟
            min_latency: 最小延迟(秒)
            max_latency: 最大延迟(秒)
        """
        super().__init__(config, audit_logger)
        self.simulate_failures = simulate_failures
        self.failure_rate = failure_rate
        self.simulate_latency = simulate_latency
        self.min_latency = min_latency
        self.max_latency = max_latency

        # 模拟响应
        self._mock_responses: Dict[str, CommandResult] = {}
        self._default_responses: Dict[str, str] = {
            "ping": "PING localhost (127.0.0.1): 56 data bytes\n64 bytes from 127.0.0.1: icmp_seq=0 ttl=64 time=0.052 ms\n--- localhost ping statistics ---\n1 packets transmitted, 1 packets received, 0.0% packet loss",
            "netstat -tulpn": "Active Internet connections (only servers)\nProto Recv-Q Send-Q Local Address Foreign Address State PID/Program name\ntcp 0 0 0.0.0.0:22 0.0.0.0:* LISTEN 1234/sshd\ntcp 0 0 0.0.0.0:80 0.0.0.0:* LISTEN 5678/nginx",
            "ss -tulpn": "Netid State Recv-Q Send-Q Local Address:Port Peer Address:Port\ntcp LISTEN 0 128 0.0.0.0:22 0.0.0.0:* users:((\"sshd\",pid=1234,fd=3))\ntcp LISTEN 0 128 0.0.0.0:80 0.0.0.0:* users:((\"nginx\",pid=5678,fd=6))",
            "systemctl status nginx": "● nginx.service - A high performance web server and a reverse proxy server\n   Loaded: loaded (/lib/systemd/system/nginx.service; enabled; vendor preset: enabled)\n   Active: active (running) since Mon 2026-02-24 10:00:00 UTC; 1h ago\n Main PID: 5678 (nginx)\n   CGroup: /system.slice/nginx.service\n           ├─5678 nginx: master process /usr/sbin/nginx\n           └─5679 nginx: worker process",
            "curl -I http://localhost": "HTTP/1.1 200 OK\nServer: nginx\nDate: Mon, 24 Feb 2026 10:00:00 GMT\nContent-Type: text/html\nConnection: keep-alive",
            "dig localhost": "; <<>> DiG 9.16.1-Ubuntu <<>> localhost\n;; global options: +cmd\n;; Got answer:\n;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 12345\n;; flags: qr aa rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 0\n\n;; QUESTION SECTION:\n;localhost.            IN  A\n\n;; ANSWER SECTION:\nlocalhost.        604800  IN  A  127.0.0.1\n\n;; Query time: 0 msec\n;; SERVER: 127.0.0.1#53(127.0.0.1)\n;; WHEN: Mon Feb 24 10:00:00 UTC 2026\n;; MSG SIZE  rcvd: 60",
            "df -h": "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1        50G   20G   28G  42% /\ntmpfs           2.0G     0  2.0G   0% /dev/shm\n/dev/sda2       100G   10G   85G  11% /home",
            "free -h": "              total        used        free      shared  buff/cache   available\nMem:          3.8Gi       1.2Gi       2.0Gi       100Mi       600Mi       2.3Gi\nSwap:         2.0Gi          0B       2.0Gi",
            "iptables -L -n": "Chain INPUT (policy ACCEPT)\ntarget     prot opt source               destination\nACCEPT     tcp  --  anywhere             anywhere             tcp dpt:ssh\nACCEPT     tcp  --  anywhere             anywhere             tcp dpt:http\n\nChain FORWARD (policy ACCEPT)\ntarget     prot opt source               destination\n\nChain OUTPUT (policy ACCEPT)\ntarget     prot opt source               destination",
        }

    def set_mock_response(self, command: str, result: CommandResult) -> None:
        """设置命令的模拟响应"""
        self._mock_responses[command] = result

    async def connect(self) -> None:
        """模拟连接"""
        import random

        if self.simulate_latency:
            await asyncio.sleep(random.uniform(0.1, 0.5))

        if self.simulate_failures and random.random() < self.failure_rate:
            raise SSHConnectionError(
                "Simulated connection failure",
                host=self.config.host,
            )

        self._connected = True
        self._connection_time = datetime.now()
        self._client = True  # 设置一个非None值以满足 is_connected 检查

        self.audit_logger.log_ssh_connect(
            host=self.config.host,
            result="success",
            username=self.config.username,
            port=self.config.port,
        )

    async def execute(self, command: str, timeout: Optional[float] = None) -> CommandResult:
        """模拟命令执行"""
        import random

        if not self._connected:
            raise SSHError("Not connected to SSH server", host=self.config.host)

        start_time = time.time()

        # 模拟延迟
        if self.simulate_latency:
            latency = random.uniform(self.min_latency, self.max_latency)
            await asyncio.sleep(latency)

        # 模拟故障
        if self.simulate_failures and random.random() < self.failure_rate:
            raise SSHCommandError(
                "Simulated command failure",
                host=self.config.host,
                command=command,
            )

        # 检查是否有预设响应
        if command in self._mock_responses:
            return self._mock_responses[command]

        # 查找默认响应
        stdout = ""
        exit_code = 0

        for cmd_pattern, response in self._default_responses.items():
            if command.startswith(cmd_pattern):
                stdout = response
                break
        else:
            # 未找到匹配的默认响应，生成通用响应
            stdout = f"Command executed: {command}"
            exit_code = 0

        duration = time.time() - start_time

        result = CommandResult(
            command=command,
            exit_code=exit_code,
            stdout=stdout,
            stderr="",
            duration=duration,
            host=self.config.host,
            timestamp=datetime.now(),
        )

        self.audit_logger.log_command(
            command=command,
            host=self.config.host,
            result="success",
            exit_code=exit_code,
            duration_ms=int(duration * 1000),
        )

        return result

    async def close(self) -> None:
        """模拟关闭连接"""
        self._connected = False
        self._client = None

        self.audit_logger.log(
            action="ssh_disconnect",
            result="success",
            host=self.config.host,
        )
