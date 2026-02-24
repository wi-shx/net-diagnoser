"""
SSH工作流集成测试
"""

import pytest
import asyncio
from datetime import datetime

from src.core.ssh_executor import SSHConfig, MockSSHExecutor, CommandResult
from src.core.command_whitelist import CommandWhitelist
from src.core.audit_logger import AuditLogger
from src.core.tool_executor import ToolExecutor, ExecutionPlan
from src.core.ai_analyzer import SuggestedCommand


class TestSSHWorkflow:
    """SSH工作流测试"""

    @pytest.fixture
    def audit_logger(self, tmp_path):
        """创建审计日志记录器"""
        return AuditLogger(log_dir=str(tmp_path))

    @pytest.fixture
    def mock_executor(self, audit_logger):
        """创建模拟SSH执行器"""
        config = SSHConfig(host="test-server.example.com")
        return MockSSHExecutor(config, audit_logger=audit_logger)

    @pytest.mark.asyncio
    async def test_full_diagnostic_workflow(self, mock_executor, audit_logger):
        """测试完整诊断工作流"""
        # 连接
        await mock_executor.connect()
        assert mock_executor.is_connected

        # 执行一系列诊断命令
        commands = [
            "ping -c 3 8.8.8.8",
            "traceroute -n google.com",
            "netstat -tulpn",
            "curl -I -m 10 https://google.com",
        ]

        results = []
        for cmd in commands:
            result = await mock_executor.execute(cmd)
            results.append(result)
            assert result.success

        # 验证审计日志
        entries = audit_logger.query(limit=10)
        assert len(entries) >= len(commands)

        # 关闭连接
        await mock_executor.close()
        assert not mock_executor.is_connected

    @pytest.mark.asyncio
    async def test_batch_execution_workflow(self, mock_executor, audit_logger):
        """测试批量执行工作流"""
        await mock_executor.connect()

        commands = [
            "df -h",
            "free -h",
            "uptime",
        ]

        results = await mock_executor.execute_batch(commands)

        assert len(results) == 3
        for r in results:
            assert r.success

        await mock_executor.close()

    @pytest.mark.asyncio
    async def test_failed_command_handling(self, mock_executor):
        """测试失败命令处理"""
        await mock_executor.connect()

        # 设置一个失败的响应
        mock_executor.set_mock_response(
            "failing_command",
            CommandResult(
                command="failing_command",
                exit_code=1,
                stdout="",
                stderr="Command failed",
                duration=0.1,
                host="test-server.example.com",
                timestamp=datetime.now(),
            ),
        )

        result = await mock_executor.execute("failing_command")

        assert result.success is False
        assert result.exit_code == 1

        await mock_executor.close()


class TestToolExecutorWorkflow:
    """工具执行器工作流测试"""

    @pytest.fixture
    def tool_executor(self, tmp_path):
        """创建工具执行器"""
        audit_logger = AuditLogger(log_dir=str(tmp_path))
        return ToolExecutor(audit_logger=audit_logger, auto_approve_low_risk=True)

    @pytest.fixture
    def sample_commands(self):
        """示例命令"""
        return [
            SuggestedCommand(
                category="network",
                description="测试网络连通性",
                command="ping -c 3 localhost",
            ),
            SuggestedCommand(
                category="port",
                description="检查网络端口",
                command="netstat -tulpn",
            ),
            SuggestedCommand(
                category="dns",
                description="检查DNS解析",
                command="dig localhost +short",
            ),
        ]

    def test_create_execution_plan(self, tool_executor, sample_commands):
        """测试创建执行计划"""
        plan = tool_executor.create_plan(
            commands=sample_commands,
            hosts=["localhost"],
        )

        assert plan is not None
        assert plan.total_commands == 3
        assert "localhost" in plan.targets

    def test_preview_plan(self, tool_executor, sample_commands):
        """测试预览执行计划"""
        plan = tool_executor.create_plan(
            commands=sample_commands,
            hosts=["server1", "server2"],
        )

        preview = tool_executor.preview(plan)

        assert "执行计划预览" in preview
        assert "ping" in preview
        assert "server1" in preview

    @pytest.mark.asyncio
    async def test_dry_run(self, tool_executor, sample_commands):
        """测试干运行"""
        plan = tool_executor.create_plan(
            commands=sample_commands,
            hosts=["localhost"],
        )

        session = await tool_executor.execute_dry_run(plan)

        assert session.status == "completed"
        assert len(session.results) == 3
        for r in session.results:
            assert "DRY RUN" in r["stdout"]


class TestNetworkErrorSimulation:
    """网络错误模拟测试"""

    @pytest.mark.asyncio
    async def test_connection_timeout_simulation(self):
        """测试连接超时模拟"""
        from tests.mocks.network_simulator import NetworkSimulator, NetworkCondition, NetworkErrorType

        condition = NetworkCondition(
            timeout_rate=1.0,
            error_type=NetworkErrorType.TIMEOUT,
        )

        simulator = NetworkSimulator()
        simulator.set_custom_condition(condition)

        with pytest.raises(TimeoutError):
            await simulator.simulate_request()

    @pytest.mark.asyncio
    async def test_packet_loss_simulation(self):
        """测试丢包模拟"""
        from tests.mocks.network_simulator import NetworkSimulator, NetworkCondition

        condition = NetworkCondition(packet_loss_rate=1.0)
        simulator = NetworkSimulator()
        simulator.set_custom_condition(condition)

        with pytest.raises(ConnectionError):
            await simulator.simulate_request()

    @pytest.mark.asyncio
    async def test_slow_network_simulation(self):
        """测试慢速网络模拟"""
        import time
        from tests.mocks.network_simulator import NetworkSimulator

        simulator = NetworkSimulator(condition="poor")

        start = time.time()
        await simulator.simulate_delay()
        duration = time.time() - start

        # 应该有一定的延迟
        assert duration >= 0.1  # 至少100ms


class TestAuditLoggingWorkflow:
    """审计日志工作流测试"""

    @pytest.fixture
    def audit_logger(self, tmp_path):
        """创建审计日志记录器"""
        return AuditLogger(log_dir=str(tmp_path))

    def test_command_execution_logging(self, audit_logger):
        """测试命令执行日志"""
        entry_id = audit_logger.log_command(
            command="ping localhost",
            host="server1",
            result="success",
            exit_code=0,
            duration_ms=50,
            stdout_preview="PING localhost",
        )

        assert entry_id is not None

        entries = audit_logger.query(action="command_execute")
        assert len(entries) == 1

    def test_ssh_connection_logging(self, audit_logger):
        """测试SSH连接日志"""
        audit_logger.log_ssh_connect(
            host="server1",
            result="success",
            username="root",
            port=22,
        )

        entries = audit_logger.query(action="ssh_connect")
        assert len(entries) == 1

    def test_log_analysis_logging(self, audit_logger):
        """测试日志分析记录"""
        audit_logger.log_analyze(
            log_file="/var/log/nginx/access.log",
            result="success",
            problem_type="connection_timeout",
            duration_ms=1500,
        )

        entries = audit_logger.query(action="log_analyze")
        assert len(entries) == 1

    def test_export_workflow(self, audit_logger, tmp_path):
        """测试导出工作流"""
        # 记录一些日志
        for i in range(5):
            audit_logger.log(
                action=f"test_action_{i}",
                result="success",
            )

        # 导出为JSON
        export_path = tmp_path / "audit_export.json"
        count = audit_logger.export(str(export_path), format="json")

        assert count == 5
        assert export_path.exists()
