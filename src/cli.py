"""
CLI入口模块
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, List

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel

from src.config import Config
from src.core.log_parser import LogParser
from src.core.ai_analyzer import AIAnalyzer
from src.core.report_generator import ReportGenerator
from src.core.command_whitelist import CommandWhitelist, default_whitelist
from src.core.audit_logger import AuditLogger, get_audit_logger
from src.core.ssh_executor import SSHConfig
from src.core.tool_executor import ToolExecutor, ExecutionPlan
from src.agent.diagnostic_agent import DiagnosticAgent
from src.utils.logger import setup_logger
from src.utils.exceptions import (
    NetDiagnoserError,
    FileError,
    ConfigError,
    APIError,
    CommandNotAllowedError,
)

app = typer.Typer(
    name="netdiagnoser",
    help="AI驱动的网络故障诊断工具",
    no_args_is_help=True,
)

console = Console()
logger = setup_logger()


@app.command()
def analyze(
    log: str = typer.Option(..., "--log", "-l", help="日志文件路径"),
    format: Optional[str] = typer.Option(None, "--format", "-f", help="日志格式（nginx/haproxy/syslog）"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="AI模型（glm-4.7/glm-5.0）"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="报告输出路径"),
):
    """
    分析日志文件
    """
    import asyncio

    try:
        # 加载配置
        Config.load()

        # 验证日志文件
        if not os.path.exists(log):
            raise FileError(f"日志文件不存在: {log}")

        file_size = os.path.getsize(log)
        if file_size > Config.MAX_LOG_SIZE:
            raise FileError(f"文件过大: {file_size} bytes (最大 {Config.MAX_LOG_SIZE})")

        console.print(f"\n📁 正在分析日志文件: [bold cyan]{log}[/bold cyan]")
        console.print(f"📊 文件大小: {file_size:,} bytes\n")

        # 解析日志
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("正在解析日志...", total=None)

            parser = LogParser(format=format)
            entries = parser.parse_file(log)
            statistics = parser.get_statistics(entries)

            progress.update(task, description="[green]✓[/green] 日志解析完成")

        console.print(f"\n📈 日志统计:")
        console.print(f"  • 总行数: {statistics.total_lines:,}")
        console.print(f"  • 错误行数: {statistics.error_lines:,}")
        console.print(f"  • 错误率: {statistics.error_rate}%\n")

        # AI分析
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("正在AI分析...", total=None)

            analyzer = AIAnalyzer(
                api_key=Config.GLM_API_KEY,
                model=model or Config.DEFAULT_MODEL,
            )
            analysis = asyncio.run(analyzer.analyze(entries, statistics))

            progress.update(task, description="[green]✓[/green] AI分析完成")

        console.print(f"\n🤖 AI分析结果:")
        console.print(f"  • 问题类型: [bold yellow]{analysis.problem_type}[/bold yellow]")
        console.print(f"  • 风险等级: {analysis.risk_level}")
        console.print(f"  • 置信度: {analysis.confidence*100:.1f}%\n")

        # 生成报告
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("正在生成报告...", total=None)

            generator = ReportGenerator()
            report = generator.generate(log, entries, statistics, analysis)

            # 保存报告
            if output is None:
                output_dir = Config.REPORTS_DIR
                os.makedirs(output_dir, exist_ok=True)
                output = os.path.join(
                    output_dir,
                    f"diagnosis_report_{os.path.splitext(os.path.basename(log))[0]}_{os.urandom(4).hex()}.md",
                )

            generator.save(report, output)

            progress.update(task, description="[green]✓[/green] 报告生成完成")

        console.print(f"\n✅ 分析完成！")
        console.print(f"📄 报告已保存到: [bold green]{output}[/bold green]\n")

    except ConfigError as e:
        console.print(f"[red]配置错误: {e.message}[/red]")
        sys.exit(1)
    except FileError as e:
        console.print(f"[red]文件错误: {e.message}[/red]")
        sys.exit(1)
    except APIError as e:
        console.print(f"[red]API调用失败: {e.message}[/red]")
        sys.exit(1)
    except NetDiagnoserError as e:
        console.print(f"[red]错误: {e.message}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]未知错误: {e}[/red]")
        logger.exception("Unknown error occurred")
        sys.exit(1)


@app.command()
def version():
    """显示版本信息"""
    import src
    __version__ = src.__version__

    console.print(f"NetDiagnoser v{__version__}")
    console.print("AI驱动的网络故障诊断工具")


@app.command()
def execute(
    log: str = typer.Option(..., "--log", "-l", help="日志文件路径"),
    hosts: List[str] = typer.Option([], "--host", "-h", help="目标主机（可多次指定）"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="仅预览，不实际执行"),
    auto_approve: bool = typer.Option(False, "--auto-approve", "-y", help="自动批准所有命令"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="报告输出路径"),
):
    """
    分析日志并执行建议的诊断命令
    """
    async def run_execute():
        # 加载配置
        Config.load()

        # 验证日志文件
        if not os.path.exists(log):
            raise FileError(f"日志文件不存在: {log}")

        # 解析日志
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("正在解析日志...", total=None)
            parser = LogParser()
            entries = parser.parse_file(log)
            statistics = parser.get_statistics(entries)
            progress.update(task, description="[green]✓[/green] 日志解析完成")

        # AI分析
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("正在AI分析...", total=None)
            analyzer = AIAnalyzer(
                api_key=Config.GLM_API_KEY,
                model=Config.DEFAULT_MODEL,
            )
            analysis = await analyzer.analyze(entries, statistics)
            progress.update(task, description="[green]✓[/green] AI分析完成")

        console.print(f"\n🤖 AI分析结果:")
        console.print(f"  • 问题类型: [bold yellow]{analysis.problem_type}[/bold yellow]")
        console.print(f"  • 风险等级: {analysis.risk_level}")
        console.print(f"  • 置信度: {analysis.confidence*100:.1f}%\n")

        # 创建执行计划
        tool_executor = ToolExecutor(auto_approve_low_risk=auto_approve)
        plan = tool_executor.create_plan(
            commands=analysis.suggested_commands,
            hosts=hosts or ["localhost"],
        )

        # 预览执行计划
        console.print(tool_executor.preview(plan))

        if dry_run:
            console.print("\n[yellow]干运行模式 - 不会实际执行命令[/yellow]\n")
            session = await tool_executor.execute_dry_run(plan)
        else:
            # 执行
            def approval_callback(p: ExecutionPlan) -> bool:
                if auto_approve:
                    return True
                console.print(f"\n[yellow]需要审批执行计划 ({p.total_commands} 个命令)[/yellow]")
                response = typer.confirm("是否执行?")
                return response

            console.print("\n[cyan]开始执行诊断命令...[/cyan]\n")
            session = await tool_executor.execute_with_approval(
                plan,
                approval_callback=approval_callback,
            )

        # 显示结果
        console.print(f"\n📊 执行结果:")
        console.print(f"  • 状态: {'✓ 完成' if session.status == 'completed' else '✗ 失败'}")
        console.print(f"  • 执行命令数: {len(session.results)}")

        if session.errors:
            console.print(f"\n[red]错误:[/red]")
            for err in session.errors:
                console.print(f"  • {err}")

        # 保存结果
        if output:
            with open(output, "w", encoding="utf-8") as f:
                import json
                json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
            console.print(f"\n📄 结果已保存到: [bold green]{output}[/bold green]")

        await tool_executor.close_all_connections()

    try:
        asyncio.run(run_execute())
    except CommandNotAllowedError as e:
        console.print(f"[red]命令验证失败: {e.message}[/red]")
        sys.exit(1)
    except NetDiagnoserError as e:
        console.print(f"[red]错误: {e.message}[/red]")
        sys.exit(1)


@app.command()
def agent(
    log: str = typer.Option(..., "--log", "-l", help="日志文件路径"),
    hosts: List[str] = typer.Option([], "--host", "-h", help="目标主机（可多次指定）"),
    max_rounds: int = typer.Option(5, "--max-rounds", "-r", help="最大执行轮次"),
    mock_mode: bool = typer.Option(False, "--mock", help="使用模拟模式（用于测试）"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="报告输出路径"),
):
    """
    运行AI代理进行多轮自主诊断
    """
    async def run_agent():
        # 加载配置
        Config.load()

        # 验证日志文件
        if not os.path.exists(log):
            raise FileError(f"日志文件不存在: {log}")

        console.print(f"\n🤖 启动诊断代理...")
        console.print(f"  • 日志文件: {log}")
        console.print(f"  • 目标主机: {hosts or ['localhost']}")
        console.print(f"  • 最大轮次: {max_rounds}")
        console.print(f"  • 模拟模式: {'是' if mock_mode else '否'}\n")

        # 解析日志
        parser = LogParser()
        entries = parser.parse_file(log)
        statistics = parser.get_statistics(entries)

        # 创建诊断代理
        analyzer = AIAnalyzer(
            api_key=Config.GLM_API_KEY,
            model=Config.DEFAULT_MODEL,
        )

        agent = DiagnosticAgent(
            ai_analyzer=analyzer,
            max_rounds=max_rounds,
            mock_mode=mock_mode,
        )

        # 执行诊断
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("代理正在诊断...", total=None)

            result = await agent.diagnose(
                log_file=log,
                entries=entries,
                statistics=statistics,
                hosts=hosts or ["localhost"],
            )

            progress.update(task, description="[green]✓[/green] 诊断完成")

        # 显示结果
        console.print(f"\n📊 诊断结果:")
        console.print(f"  • 状态: {'✓ 成功' if result.success else '✗ 失败'}")
        console.print(f"  • 执行轮次: {result.rounds_completed}")
        console.print(f"  • 执行命令数: {len(result.command_results)}")
        console.print(f"  • 总耗时: {result.total_duration:.2f}s")

        if result.diagnosis:
            console.print(f"\n🎯 问题诊断:")
            console.print(f"  • 问题类型: [bold yellow]{result.diagnosis.problem_type}[/bold yellow]")
            console.print(f"  • 风险等级: {result.diagnosis.risk_level}")
            console.print(f"  • 置信度: {result.diagnosis.confidence*100:.1f}%")

        if result.errors:
            console.print(f"\n[red]错误:[/red]")
            for err in result.errors:
                console.print(f"  • {err}")

        # 显示报告
        console.print(Panel(result.final_report, title="诊断报告", expand=False))

        # 保存结果
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(result.final_report)
            console.print(f"\n📄 报告已保存到: [bold green]{output}[/bold green]")

        await agent.close()

    try:
        asyncio.run(run_agent())
    except NetDiagnoserError as e:
        console.print(f"[red]错误: {e.message}[/red]")
        sys.exit(1)


@app.command("audit")
def audit_cmd(
    query: bool = typer.Option(False, "--query", "-q", help="查询审计日志"),
    export: Optional[str] = typer.Option(None, "--export", "-e", help="导出审计日志"),
    format: str = typer.Option("json", "--format", "-f", help="导出格式（json/csv）"),
    limit: int = typer.Option(50, "--limit", "-l", help="查询数量限制"),
    action: Optional[str] = typer.Option(None, "--action", "-a", help="过滤操作类型"),
    hours: int = typer.Option(24, "--hours", help="查询最近N小时的日志"),
):
    """
    查看或导出审计日志
    """
    audit_logger = get_audit_logger()

    if export:
        # 导出审计日志
        start_time = datetime.now() - timedelta(hours=hours)
        count = audit_logger.export(
            path=export,
            format=format,
            start_time=start_time,
        )
        console.print(f"✅ 已导出 {count} 条审计日志到: [bold green]{export}[/bold green]")
        return

    if query or True:
        # 查询审计日志
        start_time = datetime.now() - timedelta(hours=hours)
        entries = audit_logger.query(
            start_time=start_time,
            action=action,
            limit=limit,
        )

        if not entries:
            console.print("[yellow]没有找到匹配的审计日志[/yellow]")
            return

        # 显示统计
        stats = audit_logger.get_statistics()
        console.print(f"\n📊 审计日志统计:")
        console.print(f"  • 总记录数: {stats['total']}")
        console.print(f"  • 按操作: {stats['by_action']}")
        console.print(f"  • 按结果: {stats['by_result']}\n")

        # 显示表格
        table = Table(title=f"审计日志 (最近{hours}小时)")
        table.add_column("时间", style="cyan")
        table.add_column("操作", style="green")
        table.add_column("结果", style="yellow")
        table.add_column("主机", style="blue")
        table.add_column("命令/详情")

        for entry in entries[:limit]:
            table.add_row(
                entry.timestamp.strftime("%m-%d %H:%M:%S"),
                entry.action,
                entry.result,
                entry.host or "-",
                (entry.command or entry.details.get("log_file", "-"))[:40],
            )

        console.print(table)


@app.command("whitelist")
def whitelist_cmd(
    list_all: bool = typer.Option(False, "--list", "-l", help="列出所有白名单命令"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="按分类过滤"),
    check: Optional[str] = typer.Option(None, "--check", help="检查命令是否在白名单中"),
):
    """
    查看命令白名单
    """
    whitelist = default_whitelist

    if check:
        # 检查命令
        is_valid, cmd_info = whitelist.validate(check)
        if is_valid:
            console.print(f"[green]✓ 命令在白名单中[/green]")
            if cmd_info:
                console.print(f"  • 描述: {cmd_info.description}")
                console.print(f"  • 分类: {cmd_info.category}")
                console.print(f"  • 风险等级: {cmd_info.risk_level}")
        else:
            console.print(f"[red]✗ 命令不在白名单中[/red]")
        return

    # 列出命令
    if category:
        commands = whitelist.get_by_category(category)
    else:
        commands = whitelist.get_all()

    if not commands:
        console.print("[yellow]没有找到匹配的命令[/yellow]")
        return

    # 分类显示
    categories = {}
    for cmd in commands:
        if cmd.category not in categories:
            categories[cmd.category] = []
        categories[cmd.category].append(cmd)

    console.print(f"\n📋 命令白名单 ({len(commands)} 个命令)\n")

    for cat, cmds in sorted(categories.items()):
        console.print(f"[bold cyan]{cat.upper()}[/bold cyan]")

        table = Table(show_header=True, header_style="bold")
        table.add_column("命令", style="green")
        table.add_column("描述")
        table.add_column("风险")
        table.add_column("允许参数")

        for cmd in cmds:
            risk_color = {"low": "green", "medium": "yellow", "high": "red"}.get(
                cmd.risk_level, "white"
            )
            table.add_row(
                cmd.command,
                cmd.description,
                f"[{risk_color}]{cmd.risk_level}[/{risk_color}]",
                ", ".join(cmd.allowed_args[:5]) + ("..." if len(cmd.allowed_args) > 5 else ""),
            )

        console.print(table)
        console.print()


if __name__ == "__main__":
    app()
