"""
SSH执行器模块测试
"""

import pytest
import asyncio
from datetime import datetime

from src.core.ssh_executor import (
    SSHConfig,
    CommandResult,
    SSHExecutor,
    MockSSHExecutor,
)
from src.utils.exceptions import SSHError, SSHConnectionError, SSHCommandError


class TestSSHConfig:
    """SSHConfig测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = SSHConfig(host="example.com")

        assert config.host == "example.com"
        assert config.port == 22
        assert config.username == "root"
        assert config.timeout == 30.0

    def test_custom_config(self):
        """测试自定义配置"""
        config = SSHConfig(
            host="server.example.com",
            port=2222,
            username="admin",
            private_key_path="/home/user/.ssh/id_rsa",
            timeout=60.0,
        )

        assert config.host == "server.example.com"
        assert config.port == 2222
        assert config.username == "admin"
        assert config.private_key_path == "/home/user/.ssh/id_rsa"
        assert config.timeout == 60.0


class TestCommandResult:
    """CommandResult测试"""

    def test_create_result(self):
        """测试创建命令结果"""
        result = CommandResult(
            command="echo hello",
            exit_code=0,
            stdout="hello\n",
            stderr="",
            duration=0.1,
            host="localhost",
            timestamp=datetime.now(),
        )

        assert result.command == "echo hello"
        assert result.exit_code == 0
        assert result.stdout == "hello\n"
        assert result.success is True

    def test_failed_result(self):
        """测试失败的命令结果"""
        result = CommandResult(
            command="false",
            exit_code=1,
            stdout="",
            stderr="command failed",
            duration=0.05,
            host="localhost",
            timestamp=datetime.now(),
        )

        assert result.success is False
        assert result.exit_code == 1

    def test_to_dict(self):
        """测试转换为字典"""
        timestamp = datetime(2026, 2, 24, 10, 0, 0)
        result = CommandResult(
            command="test",
            exit_code=0,
            stdout="output",
            stderr="",
            duration=0.1,
            host="server1",
            timestamp=timestamp,
        )

        data = result.to_dict()

        assert data["command"] == "test"
        assert data["exit_code"] == 0
        assert data["host"] == "server1"


class TestMockSSHExecutor:
    """MockSSHExecutor测试"""

    @pytest.fixture
    def mock_executor(self):
        """创建模拟执行器"""
        config = SSHConfig(host="mock-server")
        return MockSSHExecutor(config, simulate_failures=False)

    @pytest.mark.asyncio
    async def test_connect(self, mock_executor):
        """测试模拟连接"""
        await mock_executor.connect()

        assert mock_executor.is_connected is True

        await mock_executor.close()

    @pytest.mark.asyncio
    async def test_execute_ping(self, mock_executor):
        """测试执行ping命令"""
        await mock_executor.connect()

        result = await mock_executor.execute("ping -c 3 localhost")

        assert result.success is True
        assert "PING localhost" in result.stdout
        assert result.exit_code == 0

        await mock_executor.close()

    @pytest.mark.asyncio
    async def test_execute_netstat(self, mock_executor):
        """测试执行netstat命令"""
        await mock_executor.connect()

        result = await mock_executor.execute("netstat -tulpn")

        assert result.success is True
        assert "Active Internet connections" in result.stdout

        await mock_executor.close()

    @pytest.mark.asyncio
    async def test_execute_systemctl(self, mock_executor):
        """测试执行systemctl命令"""
        await mock_executor.connect()

        result = await mock_executor.execute("systemctl status nginx")

        assert result.success is True
        assert "nginx.service" in result.stdout

        await mock_executor.close()

    @pytest.mark.asyncio
    async def test_execute_batch(self, mock_executor):
        """测试批量执行命令"""
        await mock_executor.connect()

        commands = [
            "ping -c 1 localhost",
            "netstat -tulpn",
            "df -h",
        ]

        results = await mock_executor.execute_batch(commands)

        assert len(results) == 3
        for r in results:
            assert r.success is True

        await mock_executor.close()

    @pytest.mark.asyncio
    async def test_execute_batch_stop_on_error(self, mock_executor):
        """测试批量执行遇错停止"""
        await mock_executor.connect()

        # 设置一个会失败的命令模拟
        mock_executor.set_mock_response(
            "fail_command",
            CommandResult(
                command="fail_command",
                exit_code=1,
                stdout="",
                stderr="Failed",
                duration=0,
                host="mock-server",
                timestamp=datetime.now(),
            ),
        )

        commands = [
            "ping localhost",
            "fail_command",
            "df -h",
        ]

        results = await mock_executor.execute_batch(commands, stop_on_error=True)

        # 应该在第二个命令失败后停止
        assert len(results) == 2

        await mock_executor.close()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_executor):
        """测试上下文管理器"""
        async with mock_executor as executor:
            assert executor.is_connected is True
            result = await executor.execute("echo test")
            assert result.success is True

        assert mock_executor.is_connected is False

    @pytest.mark.asyncio
    async def test_simulated_failure(self):
        """测试模拟故障"""
        config = SSHConfig(host="fail-server")
        executor = MockSSHExecutor(
            config,
            simulate_failures=True,
            failure_rate=1.0,  # 100% 失败率
        )

        with pytest.raises((SSHConnectionError, SSHCommandError)):
            await executor.connect()
            await executor.execute("ping localhost")

    @pytest.mark.asyncio
    async def test_simulated_latency(self):
        """测试模拟延迟"""
        config = SSHConfig(host="slow-server")
        executor = MockSSHExecutor(
            config,
            simulate_latency=True,
            min_latency=0.1,
            max_latency=0.2,
        )

        await executor.connect()

        import time
        start = time.time()
        await executor.execute("ping localhost")
        duration = time.time() - start

        # 应该有至少0.1秒的延迟
        assert duration >= 0.1

        await executor.close()

    @pytest.mark.asyncio
    async def test_connection_info(self, mock_executor):
        """测试连接信息"""
        await mock_executor.connect()

        info = mock_executor.connection_info

        assert info["host"] == "mock-server"
        assert info["connected"] is True
        assert info["connection_time"] is not None

        await mock_executor.close()


class TestMockSSHExecutorCustomResponses:
    """自定义响应测试"""

    @pytest.mark.asyncio
    async def test_custom_response(self):
        """测试自定义响应"""
        config = SSHConfig(host="custom-server")
        executor = MockSSHExecutor(config)

        # 设置自定义响应
        executor.set_mock_response(
            "custom_command",
            CommandResult(
                command="custom_command",
                exit_code=0,
                stdout="Custom output",
                stderr="",
                duration=0.5,
                host="custom-server",
                timestamp=datetime.now(),
            ),
        )

        await executor.connect()
        result = await executor.execute("custom_command")

        assert result.stdout == "Custom output"

        await executor.close()

    @pytest.mark.asyncio
    async def test_unknown_command(self):
        """测试未知命令的默认响应"""
        config = SSHConfig(host="test-server")
        executor = MockSSHExecutor(config)

        await executor.connect()
        result = await executor.execute("some_unknown_command arg1 arg2")

        assert result.success is True
        assert "some_unknown_command" in result.stdout

        await executor.close()


class TestSSHExecutorErrors:
    """SSH执行器错误测试"""

    @pytest.mark.asyncio
    async def test_execute_without_connection(self):
        """测试未连接时执行命令"""
        config = SSHConfig(host="test-server")
        executor = MockSSHExecutor(config)

        with pytest.raises(SSHError):
            await executor.execute("ping localhost")

    @pytest.mark.asyncio
    async def test_connection_info_before_connect(self):
        """测试连接前获取连接信息"""
        config = SSHConfig(host="test-server")
        executor = MockSSHExecutor(config)

        info = executor.connection_info

        assert info["connected"] is False
        assert info["connection_time"] is None
