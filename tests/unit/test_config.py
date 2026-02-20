"""
测试配置模块
"""

import pytest
import os
import tempfile
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from config import Config


class TestConfig:
    """配置模块测试"""

    def test_load_config_file(self):
        """测试加载配置文件"""
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".env") as f:
            f.write("GLM_API_KEY=test_api_key\n")
            f.write("DEFAULT_MODEL=glm-5.0\n")
            temp_path = f.name

        try:
            # 加载配置
            Config.load(temp_path)

            # 验证
            assert Config.is_loaded()
            assert Config.GLM_API_KEY == "test_api_key"
            assert Config.DEFAULT_MODEL == "glm-5.0"
        finally:
            # 清理
            if os.path.exists(temp_path):
                os.remove(temp_path)
            Config._loaded = False  # 重置状态

    def test_load_config_file_not_found(self):
        """测试配置文件不存在"""
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            Config.load("nonexistent.env")

    def test_load_config_missing_api_key(self):
        """测试缺少API密钥"""
        # 重置状态
        Config._loaded = False

        # 清理可能存在的环境变量
        if "GLM_API_KEY" in os.environ:
            del os.environ["GLM_API_KEY"]

        # 创建临时配置文件（没有API密钥）
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".env") as f:
            f.write("DEFAULT_MODEL=glm-5.0\n")
            temp_path = f.name

        try:
            # 加载配置
            with pytest.raises(ValueError, match="GLM_API_KEY is required"):
                Config.load(temp_path)
        finally:
            # 清理
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_get_config(self):
        """测试获取配置"""
        # 设置默认值
        Config.GLM_API_KEY = "test_key"

        # 获取存在的配置
        assert Config.get("GLM_API_KEY") == "test_key"

        # 获取不存在的配置（有默认值）
        assert Config.get("NON_EXISTENT", "default") == "default"

        # 获取不存在的配置（无默认值）
        with pytest.raises(KeyError, match="Config key not found"):
            Config.get("NON_EXISTENT")

    def test_get_config_attribute(self):
        """测试通过属性访问配置"""
        # 设置默认值
        Config.GLM_API_KEY = "test_key"
        Config.DEFAULT_MODEL = "glm-4.7"

        # 验证
        assert Config.GLM_API_KEY == "test_key"
        assert Config.DEFAULT_MODEL == "glm-4.7"
