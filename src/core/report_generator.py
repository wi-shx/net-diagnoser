"""
报告生成器模块
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List

from src.core.log_parser import LogEntry, LogStatistics
from src.core.ai_analyzer import AnalysisResult


@dataclass
class ReportData:
    """报告数据"""

    # 文件信息
    file_name: str
    file_size: int
    file_format: str
    analysis_time: datetime

    # 日志统计
    statistics: LogStatistics

    # 分析结果
    analysis: AnalysisResult


class ReportGenerator:
    """报告生成器"""

    def __init__(self, template_path: str = None):
        """
        初始化报告生成器

        Args:
            template_path: 报告模板路径（可选），None使用默认模板
        """
        self.template_path = template_path

    def generate(
        self, log_file: str, entries: List[LogEntry], statistics: LogStatistics, analysis: AnalysisResult
    ) -> str:
        """
        生成报告

        Args:
            log_file: 日志文件路径
            entries: 日志条目列表
            statistics: 统计信息
            analysis: 分析结果

        Returns:
            Markdown格式报告字符串
        """
        import os

        file_name = os.path.basename(log_file)
        file_size = os.path.getsize(log_file) if os.path.exists(log_file) else 0

        report_data = ReportData(
            file_name=file_name,
            file_size=file_size,
            file_format=self._detect_format(entries),
            analysis_time=datetime.now(),
            statistics=statistics,
            analysis=analysis,
        )

        return self._generate_markdown(report_data)

    def save(self, content: str, output_path: str) -> None:
        """
        保存报告

        Args:
            content: 报告内容
            output_path: 输出路径
        """
        import os

        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _generate_markdown(self, data: ReportData) -> str:
        """
        生成Markdown格式报告

        Args:
            data: 报告数据

        Returns:
            Markdown字符串
        """
        report = []
        report.append("# 网络诊断报告\n")
        report.append(f"**生成时间**: {data.analysis_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 文件信息
        report.append("## 📄 文件信息\n")
        report.append(f"- **文件名**: `{data.file_name}`")
        report.append(f"- **文件大小**: {self._format_size(data.file_size)}")
        report.append(f"- **日志格式**: {data.file_format}")
        report.append(f"- **分析时间**: {data.analysis_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 日志概览
        report.append("## 📊 日志概览\n")
        stats = data.statistics
        report.append(f"- **总日志行数**: {stats.total_lines:,}")
        report.append(f"- **错误行数**: {stats.error_lines:,}")
        report.append(f"- **警告行数**: {stats.warning_lines:,}")
        report.append(f"- **错误率**: {stats.error_rate}%")

        report.append("\n### 日志级别分布\n")
        for level, count in stats.level_counts.items():
            percentage = (count / stats.total_lines) * 100 if stats.total_lines > 0 else 0
            bar = "█" * int(percentage / 5)
            report.append(f"- **{level}**: {count:,} ({percentage:.1f}%) {bar}")

        report.append("\n### 时间范围\n")
        if stats.time_range[0] and stats.time_range[1]:
            report.append(f"- **开始**: {stats.time_range[0]}")
            report.append(f"- **结束**: {stats.time_range[1]}")
            duration = (stats.time_range[1] - stats.time_range[0]).total_seconds()
            report.append(f"- **时长**: {self._format_duration(duration)}")

        report.append("\n### 错误类型（Top 10）\n")
        if stats.error_types:
            for i, (error_type, count) in enumerate(stats.error_types.items(), 1):
                report.append(f"{i}. `{error_type}` - {count}次")
        else:
            report.append("无错误日志")

        # AI分析结果
        report.append("\n## 🤖 AI分析结果\n")

        analysis = data.analysis
        report.append(f"### 问题类型\n")
        report.append(f"**{analysis.problem_type}**")

        report.append("\n### 可能原因\n")
        for i, cause in enumerate(analysis.possible_causes, 1):
            report.append(f"{i}. {cause}")

        report.append(f"\n### 风险等级\n")
        risk_level = analysis.risk_level
        if risk_level == "P0":
            risk_emoji = "🔴"
            risk_desc = "服务完全不可用"
        elif risk_level == "P1":
            risk_emoji = "🟡"
            risk_desc = "部分功能受影响"
        else:
            risk_emoji = "🟢"
            risk_desc = "偶发问题"
        report.append(f"{risk_emoji} **{risk_level}** - {risk_desc}")

        report.append(f"\n### 置信度\n")
        confidence = analysis.confidence * 100
        report.append(f"**{confidence:.1f}%**")

        # 建议的排查命令
        report.append("\n## 🔧 建议的排查命令\n")

        if analysis.suggested_commands:
            # 按分类分组
            commands_by_category = {}
            for cmd in analysis.suggested_commands:
                if cmd.category not in commands_by_category:
                    commands_by_category[cmd.category] = []
                commands_by_category[cmd.category].append(cmd)

            # 输出命令
            for category, commands in commands_by_category.items():
                report.append(f"\n### {category}\n")
                for cmd in commands:
                    report.append(f"#### {cmd.description}\n")
                    report.append(f"```bash\n{cmd.command}\n```\n")
        else:
            report.append("无建议命令")

        # 下一步
        report.append("\n## 📝 下一步\n")
        report.append("1. 执行上述命令收集更多信息")
        report.append("2. 根据结果调整排查方向")
        report.append("3. 如需进一步分析，可提供更多日志")

        # 报告尾
        report.append("\n---\n")
        report.append(
            "*本报告由 NetDiagnoser 自动生成 | Powered by GLM AI*\n"
        )

        return "\n".join(report)

    def _detect_format(self, entries) -> str:
        """检测日志格式"""
        if not entries:
            return "unknown"
        return "Nginx" if entries[0].ip_address else "Syslog"

    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _format_duration(self, seconds: float) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}分钟"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}小时"
