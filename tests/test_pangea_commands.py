#!/usr/bin/env python3
"""
Pangea 网络诊断命令测试脚本

验证所有诊断命令在白名单中，并测试本地可执行命令
"""

import subprocess
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.command_whitelist import CommandWhitelist


def test_whitelist_commands():
    """测试所有 pangea 诊断命令在白名单中"""
    whitelist = CommandWhitelist()

    # Pangea 场景诊断命令
    pangea_commands = [
        # 驱动诊断
        ("lsmod", "检查已加载模块"),
        ("lsmod | grep pangea", "过滤 pangea 模块"),
        ("modinfo pangea_drv", "查看驱动信息"),

        # 内核态诊断
        ("dmesg -T", "带时间戳的内核消息"),
        ("dmesg -T | grep pangea", "过滤 pangea 内核消息"),
        ("sysctl -a", "所有内核参数"),
        ("sysctl net.core.rmem_max", "查看网络缓冲区大小"),

        # 网卡固件/硬件
        ("ethtool -i eth0", "网卡驱动/固件信息"),
        ("ethtool -k eth0", "网卡特性"),
        ("ethtool -S eth0", "网卡统计"),
        ("lspci -v", "PCI 设备详情"),

        # 光模块
        ("ethtool -m eth0", "光模块信息"),

        # 网络配置
        ("ip addr show", "接口状态"),
        ("ip link show", "链路状态"),
        ("ip route show", "路由表"),
        ("ip maddr show", "组播地址"),

        # IP 配置
        ("ip -4 addr show", "IPv4 地址"),
        ("ip -6 addr show", "IPv6 地址"),

        # MAC 配置
        ("arp -a -n", "ARP 表"),

        # 网关配置
        ("ip route show default", "默认路由"),

        # DNS 配置
        ("cat /etc/resolv.conf", "DNS 配置"),

        # 连通性测试
        ("ping -c 3 localhost", "本地回环测试"),
        ("ping -c 3 127.0.0.1", "IP 本地测试"),

        # 服务状态
        ("systemctl status", "服务状态"),

        # 进程状态
        ("ps aux", "进程列表"),

        # 网络统计
        ("netstat -tulpn", "网络连接"),
        ("ss -tulpn", "Socket 统计"),

        # 文件查看
        ("head -n 10 /etc/hosts", "hosts 文件"),
        ("tail -n 10 /var/log/syslog", "系统日志"),

        # 其他
        ("hostname -I", "主机 IP"),
        ("uptime", "系统运行时间"),
        ("df -h", "磁盘使用"),
        ("free -h", "内存使用"),
    ]

    results = {
        "passed": [],
        "failed": [],
    }

    print("=" * 60)
    print("Pangea 网络诊断命令白名单验证")
    print("=" * 60)

    for cmd, desc in pangea_commands:
        is_valid, cmd_info = whitelist.validate(cmd)

        if is_valid:
            results["passed"].append((cmd, desc))
            status = "✓ PASS"
        else:
            results["failed"].append((cmd, desc))
            status = "✗ FAIL"

        print(f"{status}: {cmd[:50]:<50} ({desc})")

    print()
    print(f"通过: {len(results['passed'])}/{len(pangea_commands)}")
    print(f"失败: {len(results['failed'])}/{len(pangea_commands)}")

    if results["failed"]:
        print("\n失败的命令:")
        for cmd, desc in results["failed"]:
            print(f"  - {cmd} ({desc})")

    return len(results["failed"]) == 0


def test_local_commands():
    """测试本地可执行命令"""
    print("\n" + "=" * 60)
    print("本地命令执行测试")
    print("=" * 60)

    # 本地可安全执行的命令
    local_commands = [
        ("ip addr show", "网络接口状态"),
        ("ip route show", "路由表"),
        ("ip link show", "链路状态"),
        ("hostname", "主机名"),
        ("hostname -I", "IP 地址"),
        ("uptime", "运行时间"),
        ("cat /etc/resolv.conf", "DNS 配置"),
        ("lsmod | head -5", "已加载模块"),
        ("ps aux | head -5", "进程列表"),
    ]

    results = []
    for cmd, desc in local_commands:
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            success = result.returncode == 0
            output = result.stdout[:200] if result.stdout else result.stderr[:200]
            results.append((cmd, desc, success, output))
            status = "✓" if success else "✗"
            print(f"\n{status} {cmd} ({desc})")
            print(f"  输出: {output[:100]}...")
        except subprocess.TimeoutExpired:
            results.append((cmd, desc, False, "Timeout"))
            print(f"\n✗ {cmd} ({desc}) - 超时")
        except Exception as e:
            results.append((cmd, desc, False, str(e)))
            print(f"\n✗ {cmd} ({desc}) - 错误: {e}")

    passed = sum(1 for _, _, success, _ in results if success)
    print(f"\n通过: {passed}/{len(results)}")

    return passed == len(results)


def generate_test_report():
    """生成测试报告"""
    print("\n" + "=" * 60)
    print("Pangea 诊断场景命令汇总")
    print("=" * 60)

    scenarios = [
        ("场景1: 驱动问题", [
            "lsmod | grep pangea",
            "modinfo pangea_drv",
            "dmesg -T | grep pangea",
        ]),
        ("场景2: 内核态问题", [
            "cat /proc/modules | grep pangea",
            "sysctl -a | grep net.core",
            "dmesg -T | grep -i dropped",
        ]),
        ("场景3: 用户态软件", [
            "systemctl status pangea-agent",
            "ps aux | grep pangea",
            "journalctl -u pangea-agent -n 20",
        ]),
        ("场景4: 网卡固件", [
            "ethtool -i pangea0",
            "ethtool -k pangea0",
        ]),
        ("场景5: 网卡硬件", [
            "lspci -vvv -s 17:00.0",
            "ethtool -S pangea0",
        ]),
        ("场景6: 光模块", [
            "ethtool -m pangea0",
        ]),
        ("场景7: 网络配置", [
            "ip addr show pangea0",
            "ip link show pangea0",
        ]),
        ("场景8: IP配置", [
            "ip -4 addr show pangea0",
            "ip -6 addr show pangea0",
        ]),
        ("场景9: MAC配置", [
            "ip link show pangea0 | grep ether",
            "arp -a -n",
            "ip maddr show pangea0",
        ]),
        ("场景10: 网关配置", [
            "ip route show default",
            "ip route show",
            "ping -c 3 192.168.1.1",
        ]),
        ("场景11: 子网配置", [
            "ip addr show pangea0 | grep inet",
        ]),
        ("场景12: DNS配置", [
            "cat /etc/resolv.conf",
            "dig @192.168.1.1 localhost +short",
        ]),
    ]

    for scenario, commands in scenarios:
        print(f"\n{scenario}:")
        for cmd in commands:
            print(f"  - {cmd}")


if __name__ == "__main__":
    print("Pangea 网络诊断工具测试")
    print("=" * 60)

    # 测试1: 白名单验证
    whitelist_ok = test_whitelist_commands()

    # 测试2: 本地命令执行
    local_ok = test_local_commands()

    # 生成报告
    generate_test_report()

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"白名单验证: {'通过' if whitelist_ok else '失败'}")
    print(f"本地命令测试: {'通过' if local_ok else '部分通过'}")

    sys.exit(0 if whitelist_ok else 1)
