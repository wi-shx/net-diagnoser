"""
命令白名单模块

定义允许执行的诊断命令及其参数限制
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import re
import shlex

from src.utils.exceptions import CommandNotAllowedError, CommandArgumentNotAllowedError


@dataclass
class WhitelistedCommand:
    """白名单命令定义"""

    command: str  # 命令名称
    description: str  # 命令描述
    category: str  # 命令分类
    allowed_args: List[str] = field(default_factory=list)  # 允许的参数
    risk_level: str = "low"  # 风险等级: low, medium, high
    requires_sudo: bool = False  # 是否需要sudo
    allowed_patterns: List[str] = field(default_factory=list)  # 允许的参数模式


class CommandWhitelist:
    """
    命令白名单管理器

    管理允许执行的安全诊断命令
    """

    DEFAULT_WHITELIST: List[WhitelistedCommand] = [
        # 网络诊断命令
        WhitelistedCommand(
            command="ping",
            description="测试网络连通性",
            category="network",
            allowed_args=["-c", "-w", "-W", "-i", "-s", "-q", "-n"],
            risk_level="low",
            allowed_patterns=[r"-c\s+\d+", r"-w\s+\d+", r"-W\s+\d+"],
        ),
        WhitelistedCommand(
            command="traceroute",
            description="路由追踪",
            category="network",
            allowed_args=["-n", "-m", "-w", "-q", "-I", "-T", "-U"],
            risk_level="low",
            allowed_patterns=[r"-m\s+\d+", r"-w\s+\d+"],
        ),
        WhitelistedCommand(
            command="tracepath",
            description="MTU路径发现",
            category="network",
            allowed_args=["-n", "-m", "-p", "-l"],
            risk_level="low",
            allowed_patterns=[r"-m\s+\d+", r"-p\s+\d+"],
        ),
        WhitelistedCommand(
            command="mtr",
            description="网络诊断工具",
            category="network",
            allowed_args=["-r", "-c", "-n", "-s", "-p", "-T", "-u"],
            risk_level="low",
            allowed_patterns=[r"-c\s+\d+", r"-s\s+\d+", r"-p\s+\d+"],
        ),
        WhitelistedCommand(
            command="curl",
            description="HTTP请求测试",
            category="network",
            allowed_args=[
                "-I",
                "-i",
                "-s",
                "-S",
                "-o",
                "-O",
                "-w",
                "-H",
                "-X",
                "-m",
                "--connect-timeout",
                "--max-time",
                "-k",
                "-L",
                "-v",
                "-d",
            ],
            risk_level="low",
            allowed_patterns=[
                r"-m\s+\d+",
                r"--connect-timeout\s+\d+",
                r"--max-time\s+\d+",
                r"-H\s+['\"][^'\"]+['\"]",
                r"-w\s+['\"][^'\"]+['\"]",
            ],
        ),
        WhitelistedCommand(
            command="wget",
            description="HTTP下载测试",
            category="network",
            allowed_args=[
                "-q",
                "-O",
                "-o",
                "-T",
                "-t",
                "--spider",
                "-S",
                "--no-check-certificate",
            ],
            risk_level="low",
            allowed_patterns=[r"-T\s+\d+", r"-t\s+\d+"],
        ),
        WhitelistedCommand(
            command="nc",
            description="Netcat网络工具",
            category="network",
            allowed_args=["-z", "-v", "-w", "-u", "-l"],
            risk_level="medium",
            allowed_patterns=[r"-w\s+\d+"],
        ),
        # 端口和连接命令
        WhitelistedCommand(
            command="netstat",
            description="网络连接统计",
            category="port",
            allowed_args=["-t", "-u", "-l", "-n", "-p", "-a", "-r", "-i", "-s"],
            risk_level="low",
            requires_sudo=False,
        ),
        WhitelistedCommand(
            command="ss",
            description="Socket统计",
            category="port",
            allowed_args=[
                "-t",
                "-u",
                "-l",
                "-n",
                "-p",
                "-a",
                "-r",
                "-s",
                "-o",
                "-m",
                "-i",
                "-4",
                "-6",
            ],
            risk_level="low",
        ),
        WhitelistedCommand(
            command="lsof",
            description="列出打开文件",
            category="port",
            allowed_args=["-i", "-P", "-n", "-p", "-u", "-t"],
            risk_level="low",
            requires_sudo=True,
            allowed_patterns=[r"-i\s*(:\d+|tcp|udp)", r"-p\s+\d+"],
        ),
        # DNS命令
        WhitelistedCommand(
            command="dig",
            description="DNS查询",
            category="dns",
            allowed_args=[
                "@",
                "+short",
                "+trace",
                "+recurse",
                "+norecurse",
                "ANY",
                "A",
                "AAAA",
                "MX",
                "NS",
                "TXT",
                "SOA",
                "CNAME",
                "PTR",
                "-x",
            ],
            risk_level="low",
        ),
        WhitelistedCommand(
            command="nslookup",
            description="DNS查询工具",
            category="dns",
            allowed_args=["-type", "-query", "-debug"],
            risk_level="low",
            allowed_patterns=[r"-type=\w+", r"-query=\w+"],
        ),
        WhitelistedCommand(
            command="host",
            description="DNS查询",
            category="dns",
            allowed_args=["-t", "-a", "-v", "-w", "-W", "-R"],
            risk_level="low",
            allowed_patterns=[r"-t\s+\w+", r"-R\s+\d+"],
        ),
        # 服务状态命令
        WhitelistedCommand(
            command="systemctl",
            description="系统服务管理",
            category="service",
            allowed_args=["status", "is-active", "is-enabled", "list-units", "show"],
            risk_level="low",
            allowed_patterns=[r"status\s+\S+"],
        ),
        WhitelistedCommand(
            command="service",
            description="服务状态",
            category="service",
            allowed_args=["status"],
            risk_level="low",
        ),
        # 防火墙命令
        WhitelistedCommand(
            command="iptables",
            description="防火墙规则查看",
            category="firewall",
            allowed_args=["-L", "-n", "-v", "-t", "-S", "--line-numbers"],
            risk_level="low",
            requires_sudo=True,
        ),
        WhitelistedCommand(
            command="ip6tables",
            description="IPv6防火墙规则",
            category="firewall",
            allowed_args=["-L", "-n", "-v", "-t", "-S", "--line-numbers"],
            risk_level="low",
            requires_sudo=True,
        ),
        WhitelistedCommand(
            command="ufw",
            description="UFW防火墙状态",
            category="firewall",
            allowed_args=["status", "status numbered"],
            risk_level="low",
            requires_sudo=True,
        ),
        WhitelistedCommand(
            command="firewall-cmd",
            description="firewalld管理",
            category="firewall",
            allowed_args=["--list-all", "--list-services", "--list-ports", "--state"],
            risk_level="low",
            requires_sudo=True,
        ),
        # 系统诊断命令
        WhitelistedCommand(
            command="dmesg",
            description="内核消息",
            category="system",
            allowed_args=["-T", "-w", "-n", "-l", "-f"],
            risk_level="low",
            allowed_patterns=[r"-n\s+\d+", r"-l\s+[\w,]+", r"-f\s+\w+"],
        ),
        WhitelistedCommand(
            command="journalctl",
            description="系统日志",
            category="system",
            allowed_args=[
                "-u",
                "-n",
                "-f",
                "--since",
                "--until",
                "-p",
                "-k",
                "-b",
                "--no-pager",
            ],
            risk_level="low",
            allowed_patterns=[
                r"-u\s+\S+",
                r"-n\s+\d+",
                r"-p\s+\w+",
                r"--since\s+['\"][^'\"]+['\"]",
            ],
        ),
        WhitelistedCommand(
            command="top",
            description="进程监控",
            category="system",
            allowed_args=["-b", "-n", "-p", "-u"],
            risk_level="low",
            allowed_patterns=[r"-n\s+\d+", r"-p\s+\d+"],
        ),
        WhitelistedCommand(
            command="ps",
            description="进程状态",
            category="system",
            allowed_args=["aux", "-ef", "-eo", "--sort"],
            risk_level="low",
        ),
        WhitelistedCommand(
            command="free",
            description="内存状态",
            category="system",
            allowed_args=["-h", "-m", "-g", "-b", "-t", "-s"],
            risk_level="low",
        ),
        WhitelistedCommand(
            command="vmstat",
            description="虚拟内存统计",
            category="system",
            allowed_args=["-a", "-s", "-d", "-p"],
            risk_level="low",
        ),
        WhitelistedCommand(
            command="iostat",
            description="IO统计",
            category="system",
            allowed_args=["-c", "-d", "-k", "-m", "-x", "-t"],
            risk_level="low",
        ),
        WhitelistedCommand(
            command="df",
            description="磁盘使用",
            category="system",
            allowed_args=["-h", "-H", "-T", "-i", "-l", "-a"],
            risk_level="low",
        ),
        WhitelistedCommand(
            command="du",
            description="目录大小",
            category="system",
            allowed_args=["-h", "-s", "-a", "-d", "--max-depth"],
            risk_level="low",
            allowed_patterns=[r"-d\s+\d+", r"--max-depth=\d+"],
        ),
        WhitelistedCommand(
            command="uptime",
            description="系统运行时间",
            category="system",
            allowed_args=[],
            risk_level="low",
        ),
        WhitelistedCommand(
            command="hostname",
            description="主机名",
            category="system",
            allowed_args=["-f", "-i", "-I", "-s"],
            risk_level="low",
        ),
        WhitelistedCommand(
            command="ip",
            description="网络配置",
            category="network",
            allowed_args=["addr", "link", "route", "show", "list"],
            risk_level="low",
        ),
        WhitelistedCommand(
            command="ifconfig",
            description="网络接口配置",
            category="network",
            allowed_args=["-a"],
            risk_level="low",
        ),
        WhitelistedCommand(
            command="arp",
            description="ARP缓存",
            category="network",
            allowed_args=["-a", "-n", "-e"],
            risk_level="low",
        ),
        WhitelistedCommand(
            command="route",
            description="路由表",
            category="network",
            allowed_args=["-n", "-ee"],
            risk_level="low",
        ),
        WhitelistedCommand(
            command="ethtool",
            description="网卡工具",
            category="network",
            allowed_args=["-i", "-k", "-S", "-s", "-a", "-c", "-g"],
            risk_level="low",
            requires_sudo=False,
        ),
        WhitelistedCommand(
            command="tcpdump",
            description="网络抓包",
            category="network",
            allowed_args=[
                "-i",
                "-n",
                "-nn",
                "-c",
                "-w",
                "-r",
                "-v",
                "-vv",
                "-X",
                "-s",
                "-e",
            ],
            risk_level="medium",
            requires_sudo=True,
            allowed_patterns=[
                r"-i\s+\w+",
                r"-c\s+\d+",
                r"-w\s+\S+",
                r"-s\s+\d+",
            ],
        ),
    ]

    def __init__(self, custom_commands: Optional[List[WhitelistedCommand]] = None):
        """
        初始化命令白名单

        Args:
            custom_commands: 自定义命令列表，会与默认白名单合并
        """
        self._commands: dict[str, WhitelistedCommand] = {}

        # 加载默认白名单
        for cmd in self.DEFAULT_WHITELIST:
            self._commands[cmd.command] = cmd

        # 加载自定义命令
        if custom_commands:
            for cmd in custom_commands:
                self._commands[cmd.command] = cmd

    def validate(self, command_str: str) -> Tuple[bool, Optional[WhitelistedCommand]]:
        """
        验证命令是否在白名单中

        Args:
            command_str: 完整的命令字符串

        Returns:
            (是否通过, 命令定义)
        """
        try:
            parts = shlex.split(command_str)
        except ValueError:
            return False, None

        if not parts:
            return False, None

        # 处理sudo前缀
        if parts[0] == "sudo":
            parts = parts[1:]
            if not parts:
                return False, None

        command = parts[0]
        args = parts[1:]

        # 检查命令是否在白名单中
        if command not in self._commands:
            return False, None

        cmd_def = self._commands[command]

        # 检查参数
        for arg in args:
            if not self._validate_argument(cmd_def, arg, args):
                return False, cmd_def

        return True, cmd_def

    def _validate_argument(
        self, cmd_def: WhitelistedCommand, arg: str, all_args: List[str]
    ) -> bool:
        """
        验证单个参数

        Args:
            cmd_def: 命令定义
            arg: 当前参数
            all_args: 所有参数列表

        Returns:
            是否允许
        """
        # 非选项参数（如主机名、IP）通常是允许的
        if not arg.startswith("-"):
            return True

        # 检查精确匹配
        if arg in cmd_def.allowed_args:
            return True

        # 检查组合短参数（如 -tulpn 分解为 -t -u -l -p -n）
        if arg.startswith("-") and not arg.startswith("--") and len(arg) > 2:
            # 可能是组合参数，检查每个字母
            combined_args = arg[1:]  # 移除开头的 '-'
            all_valid = True
            for char in combined_args:
                single_arg = f"-{char}"
                if single_arg not in cmd_def.allowed_args:
                    all_valid = False
                    break
            if all_valid:
                return True

        # 检查模式匹配
        for pattern in cmd_def.allowed_patterns:
            if re.match(pattern, arg):
                return True

        # 检查带值的参数 (如 -c 5, --timeout=10)
        if "=" in arg:
            base_arg = arg.split("=")[0] + "="
            if any(a.startswith(base_arg.rstrip("=")) for a in cmd_def.allowed_args):
                return True
            # 检查模式
            for pattern in cmd_def.allowed_patterns:
                if re.match(pattern, arg):
                    return True

        return False

    def validate_or_raise(self, command_str: str) -> WhitelistedCommand:
        """
        验证命令，不通过则抛出异常

        Args:
            command_str: 完整的命令字符串

        Returns:
            命令定义

        Raises:
            CommandNotAllowedError: 命令不在白名单中
            CommandArgumentNotAllowedError: 参数不允许
        """
        is_valid, cmd_def = self.validate(command_str)

        if cmd_def is None:
            raise CommandNotAllowedError(command_str, list(self._commands.keys()))

        if not is_valid:
            raise CommandArgumentNotAllowedError(
                command_str, "", cmd_def.allowed_args
            )

        return cmd_def

    def get_command(self, command: str) -> Optional[WhitelistedCommand]:
        """
        获取命令定义

        Args:
            command: 命令名称

        Returns:
            命令定义，不存在返回None
        """
        return self._commands.get(command)

    def get_all(self) -> List[WhitelistedCommand]:
        """
        获取所有白名单命令

        Returns:
            命令列表
        """
        return list(self._commands.values())

    def get_by_category(self, category: str) -> List[WhitelistedCommand]:
        """
        按分类获取命令

        Args:
            category: 分类名称

        Returns:
            该分类下的命令列表
        """
        return [cmd for cmd in self._commands.values() if cmd.category == category]

    def get_categories(self) -> List[str]:
        """
        获取所有分类

        Returns:
            分类列表
        """
        return list(set(cmd.category for cmd in self._commands.values()))

    def add_command(self, command: WhitelistedCommand) -> None:
        """
        添加命令到白名单

        Args:
            command: 命令定义
        """
        self._commands[command.command] = command

    def remove_command(self, command: str) -> bool:
        """
        从白名单移除命令

        Args:
            command: 命令名称

        Returns:
            是否成功移除
        """
        if command in self._commands:
            del self._commands[command]
            return True
        return False


# 全局默认实例
default_whitelist = CommandWhitelist()
