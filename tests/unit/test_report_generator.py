"""
测试报告生成器
"""

import pytest
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from core.report_generator import ReportGenerator
from core.log_parser import LogStatistics
from core.ai_analyzer import AnalysisResult, SuggestedCommand


class TestReportGenerator:
    """报告生成器测试"""

    def test_init(self):
        """测试初始化"""
        generator = ReportGenerator()
        assert generator.template_path is None

    def test_init_with_template(self):
        """测试使用模板初始化"""
        generator = ReportGenerator(template_path="template.md")
        assert generator.template_path == "template.md"

    def test_generate_report(self):
        """测试生成报告"""
        generator = ReportGenerator()

        # 准备测试数据
        statistics = LogStatistics(
            total_lines=100,
            error_lines=10,
            warning_lines=20,
            error_rate=10.0,
            level_counts={"INFO": 70, "WARN": 20, "ERROR": 10},
            error_types={"connection timeout": 5, "server error": 5},
            time_range=(datetime(2026, 2, 15, 10, 0), datetime(2026, 2, 15, 11, 0)),
        )

        analysis = AnalysisResult(
            problem_type="连接超时",
            possible_causes=["防火墙限制", "服务未启动", "网络路由问题"],
            risk_level="P0",
            suggested_commands=[
                SuggestedCommand(
                    category="网络",
                    description="测试网络连通性",
                    command="ping target-server.com",
                )
            ],
            confidence=0.95,
        )

        # 生成报告
        report = generator.generate(
            log_file="test.log",
            entries=[],
            statistics=statistics,
            analysis=analysis,
        )

        # 验证报告内容
        assert "# 网络诊断报告" in report
        assert "连接超时" in report
        assert "P0" in report
        assert "95.0%" in report
        assert "ping target-server.com" in report

    def test_save_report(self):
        """测试保存报告"""
        import os
        import tempfile

        generator = ReportGenerator()

        # 准备测试数据
        statistics = LogStatistics(
            total_lines=100,
            error_lines=10,
            warning_lines=20,
            error_rate=10.0,
            level_counts={"INFO": 70, "WARN": 20, "ERROR": 10},
            error_types={},
            time_range=(datetime(2026, 2, 15, 10, 0), datetime(2026, 2, 15, 11, 0)),
        )

        analysis = AnalysisResult(
            problem_type="连接超时",
            possible_causes=["防火墙限制"],
            risk_level="P0",
            suggested_commands=[],
            confidence=0.95,
        )

        # 生成并保存报告
        report = generator.generate(
            log_file="test.log",
            entries=[],
            statistics=statistics,
            analysis=analysis,
        )

        # 临时文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            output_path = f.name

        try:
            generator.save(report, output_path)

            # 验证文件存在
            assert os.path.exists(output_path)

            # 验证文件内容
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert "# 网络诊断报告" in content
        finally:
            # 清理
            if os.path.exists(output_path):
                os.remove(output_path)
