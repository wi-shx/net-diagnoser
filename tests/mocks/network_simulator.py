"""
网络错误模拟器

模拟各种网络错误场景用于测试
"""

import asyncio
import random
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum


class NetworkErrorType(str, Enum):
    """网络错误类型"""

    TIMEOUT = "timeout"
    CONNECTION_REFUSED = "connection_refused"
    DNS_FAILURE = "dns_failure"
    HOST_UNREACHABLE = "host_unreachable"
    NETWORK_UNREACHABLE = "network_unreachable"
    CONNECTION_RESET = "connection_reset"
    SLOW_NETWORK = "slow_network"
    PACKET_LOSS = "packet_loss"
    SSL_ERROR = "ssl_error"
    PROXY_ERROR = "proxy_error"


@dataclass
class NetworkCondition:
    """网络条件"""

    latency_ms: float = 0.0
    jitter_ms: float = 0.0
    packet_loss_rate: float = 0.0
    timeout_rate: float = 0.0
    error_rate: float = 0.0
    error_type: Optional[NetworkErrorType] = None


class NetworkSimulator:
    """
    网络模拟器

    模拟各种网络条件和错误
    """

    # 预设的网络条件
    CONDITIONS = {
        "perfect": NetworkCondition(latency_ms=1, jitter_ms=0.5),
        "good": NetworkCondition(latency_ms=50, jitter_ms=10),
        "average": NetworkCondition(latency_ms=100, jitter_ms=30),
        "poor": NetworkCondition(latency_ms=300, jitter_ms=100),
        "bad": NetworkCondition(latency_ms=500, jitter_ms=200, packet_loss_rate=0.05),
        "terrible": NetworkCondition(
            latency_ms=1000, jitter_ms=500, packet_loss_rate=0.2, timeout_rate=0.1
        ),
    }

    def __init__(self, condition: str = "good"):
        """
        初始化网络模拟器

        Args:
            condition: 网络条件名称
        """
        self.condition = self.CONDITIONS.get(condition, self.CONDITIONS["good"])
        self._error_injector: Optional[callable] = None

    def set_condition(self, condition: str) -> None:
        """设置网络条件"""
        self.condition = self.CONDITIONS.get(condition, self.condition)

    def set_custom_condition(self, condition: NetworkCondition) -> None:
        """设置自定义网络条件"""
        self.condition = condition

    async def simulate_delay(self) -> float:
        """
        模拟网络延迟

        Returns:
            实际延迟时间(秒)
        """
        latency = self.condition.latency_ms
        jitter = random.uniform(-self.condition.jitter_ms, self.condition.jitter_ms)
        actual_latency = max(0, latency + jitter)

        await asyncio.sleep(actual_latency / 1000)
        return actual_latency / 1000

    async def simulate_request(self) -> Dict[str, Any]:
        """
        模拟一次网络请求

        Returns:
            请求结果

        Raises:
            各种网络异常
        """
        # 检查是否应该丢包
        if random.random() < self.condition.packet_loss_rate:
            raise ConnectionError("Simulated packet loss")

        # 检查是否应该超时
        if random.random() < self.condition.timeout_rate:
            await asyncio.sleep(30)  # 模拟超时
            raise TimeoutError("Simulated network timeout")

        # 检查是否应该注入错误
        if self.condition.error_rate > 0 and random.random() < self.condition.error_rate:
            raise self._generate_error()

        # 模拟延迟
        latency = await self.simulate_delay()

        return {
            "success": True,
            "latency_ms": latency * 1000,
            "error": None,
        }

    def _generate_error(self) -> Exception:
        """生成模拟错误"""
        error_type = self.condition.error_type or random.choice(list(NetworkErrorType))

        error_messages = {
            NetworkErrorType.TIMEOUT: "Connection timed out",
            NetworkErrorType.CONNECTION_REFUSED: "Connection refused",
            NetworkErrorType.DNS_FAILURE: "DNS resolution failed",
            NetworkErrorType.HOST_UNREACHABLE: "Host unreachable",
            NetworkErrorType.NETWORK_UNREACHABLE: "Network unreachable",
            NetworkErrorType.CONNECTION_RESET: "Connection reset by peer",
            NetworkErrorType.SSL_ERROR: "SSL certificate error",
            NetworkErrorType.PROXY_ERROR: "Proxy connection failed",
        }

        return ConnectionError(error_messages.get(error_type, "Network error"))

    @staticmethod
    async def simulate_timeout(duration: float = 30.0) -> None:
        """模拟超时"""
        await asyncio.sleep(duration)
        raise TimeoutError(f"Connection timed out after {duration}s")

    @staticmethod
    async def simulate_connection_refused() -> None:
        """模拟连接被拒绝"""
        raise ConnectionError("Connection refused")

    @staticmethod
    async def simulate_dns_failure() -> None:
        """模拟DNS解析失败"""
        raise ConnectionError("DNS resolution failed: No such host is known")

    @staticmethod
    async def simulate_slow_network(
        min_latency: float = 1.0, max_latency: float = 5.0
    ) -> float:
        """
        模拟慢速网络

        Args:
            min_latency: 最小延迟(秒)
            max_latency: 最大延迟(秒)

        Returns:
            实际延迟时间
        """
        latency = random.uniform(min_latency, max_latency)
        await asyncio.sleep(latency)
        return latency

    @staticmethod
    async def simulate_packet_loss(loss_rate: float = 0.3) -> bool:
        """
        模拟丢包

        Args:
            loss_rate: 丢包率

        Returns:
            是否丢包
        """
        if random.random() < loss_rate:
            raise ConnectionError("Packet lost")
        return True


class MockNetworkClient:
    """
    模拟网络客户端

    使用网络模拟器模拟HTTP/SSH等客户端
    """

    def __init__(
        self,
        simulator: Optional[NetworkSimulator] = None,
        fail_mode: bool = False,
    ):
        """
        初始化模拟客户端

        Args:
            simulator: 网络模拟器
            fail_mode: 是否总是失败
        """
        self.simulator = simulator or NetworkSimulator()
        self.fail_mode = fail_mode
        self._call_history: List[Dict[str, Any]] = []

    async def request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        模拟HTTP请求

        Args:
            method: HTTP方法
            url: URL
            **kwargs: 其他参数

        Returns:
            响应数据
        """
        call_record = {
            "method": method,
            "url": url,
            "kwargs": kwargs,
            "timestamp": asyncio.get_event_loop().time(),
        }

        if self.fail_mode:
            call_record["result"] = "failed"
            self._call_history.append(call_record)
            raise ConnectionError("Simulated failure mode")

        try:
            result = await self.simulator.simulate_request()
            call_record["result"] = "success"
            call_record["latency_ms"] = result["latency_ms"]
            self._call_history.append(call_record)

            return {
                "status_code": 200,
                "body": f"Mock response for {method} {url}",
                "headers": {"content-type": "text/plain"},
                "latency_ms": result["latency_ms"],
            }
        except Exception as e:
            call_record["result"] = "error"
            call_record["error"] = str(e)
            self._call_history.append(call_record)
            raise

    async def connect(self, host: str, port: int) -> Dict[str, Any]:
        """
        模拟TCP连接

        Args:
            host: 主机
            port: 端口

        Returns:
            连接信息
        """
        if self.fail_mode:
            raise ConnectionError(f"Connection refused: {host}:{port}")

        await self.simulator.simulate_delay()

        return {
            "host": host,
            "port": port,
            "connected": True,
        }

    def get_call_history(self) -> List[Dict[str, Any]]:
        """获取调用历史"""
        return self._call_history

    def clear_history(self) -> None:
        """清空调用历史"""
        self._call_history.clear()


# 预设的网络故障场景
FAILURE_SCENARIOS = {
    "dns_outage": {
        "description": "DNS服务完全不可用",
        "condition": NetworkCondition(
            error_rate=1.0, error_type=NetworkErrorType.DNS_FAILURE
        ),
    },
    "network_partition": {
        "description": "网络分区 - 部分主机不可达",
        "condition": NetworkCondition(
            error_rate=0.5, error_type=NetworkErrorType.HOST_UNREACHABLE
        ),
    },
    "high_latency": {
        "description": "高延迟网络",
        "condition": NetworkCondition(latency_ms=500, jitter_ms=200),
    },
    "unstable_connection": {
        "description": "不稳定连接 - 频繁断开",
        "condition": NetworkCondition(
            packet_loss_rate=0.3, error_rate=0.2
        ),
    },
    "slow_and_unreliable": {
        "description": "慢速且不可靠",
        "condition": NetworkCondition(
            latency_ms=1000, jitter_ms=500, packet_loss_rate=0.1, timeout_rate=0.05
        ),
    },
}


def create_simulator(scenario: str = "good") -> NetworkSimulator:
    """
    创建网络模拟器

    Args:
        scenario: 场景名称

    Returns:
        网络模拟器
    """
    if scenario in FAILURE_SCENARIOS:
        sim = NetworkSimulator()
        sim.set_custom_condition(FAILURE_SCENARIOS[scenario]["condition"])
        return sim
    return NetworkSimulator(condition=scenario)
