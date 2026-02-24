"""
CLI入口模块
"""

import os
import sys
from typing import Optional
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.config import Config
from src.core.log_parser import LogParser
from src.core.ai_analyzer import AIAnalyzer
from src.core.report_generator import ReportGenerator
from src.utils.logger import setup_logger
from src.utils.exceptions import NetDiagnoserError, FileError, ConfigError, APIError

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


if __name__ == "__main__":
    app()
