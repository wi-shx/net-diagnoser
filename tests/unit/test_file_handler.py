"""
测试文件处理器
"""

import pytest
import os
import tempfile
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.file_handler import read_file, write_file, read_lines


class TestFileHandler:
    """文件处理器测试"""

    def test_read_file(self):
        """测试读取文件"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("line1\nline2\nline3\n")
            temp_path = f.name

        try:
            # 读取文件
            lines = read_file(temp_path)

            # 验证
            assert len(lines) == 3
            assert lines[0] == "line1\n"
            assert lines[1] == "line2\n"
            assert lines[2] == "line3\n"
        finally:
            # 清理
            os.remove(temp_path)

    def test_write_file(self):
        """测试写入文件"""
        import tempfile

        # 临时文件
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            temp_path = f.name

        try:
            # 写入文件
            content = "test content"
            write_file(temp_path, content)

            # 验证文件存在
            assert os.path.exists(temp_path)

            # 验证文件内容
            with open(temp_path, "r", encoding="utf-8") as f:
                assert f.read() == content
        finally:
            # 清理
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_write_file_create_directory(self):
        """测试写入文件时创建目录"""
        import tempfile

        # 临时目录
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, "subdir", "file.txt")

        try:
            # 写入文件（目录不存在）
            write_file(temp_path, "test content")

            # 验证文件存在
            assert os.path.exists(temp_path)
        finally:
            # 清理
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_read_lines_generator(self):
        """测试逐行读取（生成器）"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("line1\nline2\nline3\n")
            temp_path = f.name

        try:
            # 逐行读取
            lines = list(read_lines(temp_path))

            # 验证
            assert len(lines) == 3
            assert lines[0] == "line1"
            assert lines[1] == "line2"
            assert lines[2] == "line3"
        finally:
            # 清理
            os.remove(temp_path)

    def test_read_file_not_found(self):
        """测试文件不存在"""
        with pytest.raises(FileNotFoundError):
            read_file("nonexistent.txt")

    def test_write_file_invalid_path(self):
        """测试写入无效路径"""
        with pytest.raises(IOError):
            # Windows下可能失败
            write_file("/invalid/path/file.txt", "content")
