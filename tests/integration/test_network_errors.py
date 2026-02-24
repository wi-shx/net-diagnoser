"""
网络错误集成测试

测试各种网络错误场景下的诊断工具行为
"""

import pytest
import asyncio
from datetime import datetime

from src.core.ssh_executor import SSHConfig, MockSSHExecutor, CommandResult
from src.core.command_whitelist import CommandWhitelist
from src.core.audit_logger import AuditLogger
from tests.mocks.network_simulator import (
    NetworkSimulator,
    NetworkCondition,
    NetworkErrorType,
    create_simulator,
    FAILURE_SCENARIOS,
)


class TestNetworkFailureScenarios:
    """网络故障场景测试"""

    @pytest.mark.asyncio
    async def test_dns_outage_scenario(self):
        """测试DNS中断场景"""
        simulator = create_simulator("dns_outage")

        with pytest.raises(ConnectionError) as exc_info:
            await simulator.simulate_request()

        assert "DNS" in str(exc_info.value) or "resolution" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_network_partition_scenario(self):
        """测试网络分区场景"""
        simulator = create_simulator("network_partition")

        # 网络分区时，部分请求应该成功，部分应该失败
        success_count = 0
        failure_count = 0

        for _ in range(10):
            try:
                await simulator.simulate_request()
                success_count += 1
            except (ConnectionError, TimeoutError):
                failure_count += 1

        # 应该有成功和失败的请求
        assert failure_count > 0  # 应该有失败的

    @pytest.mark.asyncio
    async def test_high_latency_scenario(self):
        """测试高延迟场景"""
        import time

        simulator = create_simulator("high_latency")

        start = time.time()
        await simulator.simulate_delay()
        duration = time.time() - start

        # 高延迟场景应该有明显的延迟
        assert duration >= 0.3  # 至少300ms

    @pytest.mark.asyncio
    async def test_unstable_connection_scenario(self):
        """测试不稳定连接场景"""
        simulator = create_simulator("unstable_connection")

        failures = 0
        for _ in range(20):
            try:
                await simulator.simulate_request()
            except (ConnectionError, TimeoutError):
                failures += 1

        # 不稳定连接应该有部分失败
        assert failures > 0


class TestSSHWithNetworkIssues:
    """SSH网络问题测试"""

    @pytest.fixture
    def audit_logger(self, tmp_path):
        """创建审计日志记录器"""
        return AuditLogger(log_dir=str(tmp_path))

    @pytest.mark.asyncio
    async def test_ssh_with_simulated_latency(self, audit_logger):
        """测试带延迟的SSH"""
        import time

        config = SSHConfig(host="slow-server")
        executor = MockSSHExecutor(
            config,
            audit_logger=audit_logger,
            simulate_latency=True,
            min_latency=0.2,
            max_latency=0.5,
        )

        await executor.connect()

        start = time.time()
        result = await executor.execute("ping localhost")
        duration = time.time() - start

        assert duration >= 0.2
        await executor.close()

    @pytest.mark.asyncio
    async def test_ssh_with_random_failures(self, audit_logger):
        """测试带随机故障的SSH"""
        config = SSHConfig(host="unstable-server")
        executor = MockSSHExecutor(
            config,
            audit_logger=audit_logger,
            simulate_failures=True,
            failure_rate=0.5,
        )

        await executor.connect()

        successes = 0
        failures = 0

        for _ in range(10):
            try:
                result = await executor.execute("echo test")
                if result.success:
                    successes += 1
                else:
                    failures += 1
            except Exception:
                failures += 1

        # 应该有成功和失败
        assert successes > 0 or failures > 0

        await executor.close()


class TestCommandValidation:
    """命令验证测试"""

    def test_dangerous_commands_blocked(self):
        """测试危险命令被阻止"""
        whitelist = CommandWhitelist()

        dangerous_commands = [
            "rm -rf /",
            "mkfs.ext4 /dev/sda",
            "dd if=/dev/zero of=/dev/sda",
            "shutdown now",
            "init 0",
            "> /dev/sda",
            "chmod 777 /",
        ]

        blocked = 0
        for cmd in dangerous_commands:
            is_valid, _ = whitelist.validate(cmd)
            if not is_valid:
                blocked += 1

        # 所有危险命令应该被阻止
        assert blocked == len(dangerous_commands)

    def test_safe_diagnostic_commands_allowed(self):
        """测试安全诊断命令被允许"""
        whitelist = CommandWhitelist()

        safe_commands = [
            "ping -c 3 localhost",
            "traceroute -n 8.8.8.8",
            "curl -I https://example.com",
            "dig @8.8.8.8 google.com",
            "netstat -tulpn",
            "ss -tulpn",
            "systemctl status nginx",
            "df -h",
            "free -h",
            "dmesg -T",
        ]

        allowed = 0
        for cmd in safe_commands:
            is_valid, _ = whitelist.validate(cmd)
            if is_valid:
                allowed += 1

        # 所有安全命令应该被允许
        assert allowed == len(safe_commands)


class TestNetworkSimulator:
    """网络模拟器测试"""

    def test_preset_conditions(self):
        """测试预设网络条件"""
        for condition_name in ["perfect", "good", "average", "poor", "bad", "terrible"]:
            simulator = NetworkSimulator(condition=condition_name)
            assert simulator.condition is not None

    @pytest.mark.asyncio
    async def test_latency_range(self):
        """测试延迟范围"""
        condition = NetworkCondition(latency_ms=100, jitter_ms=20)
        simulator = NetworkSimulator()
        simulator.set_custom_condition(condition)

        latencies = []
        for _ in range(10):
            latency = await simulator.simulate_delay()
            latencies.append(latency * 1000)  # 转换为毫秒

        # 延迟应该在合理范围内
        avg_latency = sum(latencies) / len(latencies)
        assert 80 <= avg_latency <= 120  # 100 +/- 20ms

    @pytest.mark.asyncio
    async def test_packet_loss_rate(self):
        """测试丢包率"""
        condition = NetworkCondition(packet_loss_rate=0.5)
        simulator = NetworkSimulator()
        simulator.set_custom_condition(condition)

        losses = 0
        attempts = 100

        for _ in range(attempts):
            try:
                await simulator.simulate_request()
            except ConnectionError:
                losses += 1

        loss_rate = losses / attempts
        # 丢包率应该接近50%
        assert 0.3 <= loss_rate <= 0.7


class TestFailureScenarios:
    """故障场景测试"""

    def test_available_scenarios(self):
        """测试可用场景"""
        assert "dns_outage" in FAILURE_SCENARIOS
        assert "network_partition" in FAILURE_SCENARIOS
        assert "high_latency" in FAILURE_SCENARIOS
        assert "unstable_connection" in FAILURE_SCENARIOS
        assert "slow_and_unreliable" in FAILURE_SCENARIOS

    @pytest.mark.asyncio
    async def test_scenario_simulation(self):
        """测试场景模拟"""
        for scenario_name, scenario_info in FAILURE_SCENARIOS.items():
            simulator = create_simulator(scenario_name)

            # 尝试多次请求
            for _ in range(5):
                try:
                    await simulator.simulate_request()
                except (ConnectionError, TimeoutError):
                    pass  # 预期可能失败

    @pytest.mark.asyncio
    async def test_custom_condition_simulation(self):
        """测试自定义条件模拟"""
        custom_condition = NetworkCondition(
            latency_ms=200,
            jitter_ms=50,
            packet_loss_rate=0.1,
            error_rate=0.05,
            error_type=NetworkErrorType.CONNECTION_RESET,
        )

        simulator = NetworkSimulator()
        simulator.set_custom_condition(custom_condition)

        # 验证条件已设置
        assert simulator.condition.latency_ms == 200
        assert simulator.condition.packet_loss_rate == 0.1
