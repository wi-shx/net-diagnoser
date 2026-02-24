"""
配置管理模块
"""

import os
from typing import Any, Optional
from dotenv import load_dotenv


class Config:
    """配置类"""

    # GLM API配置
    GLM_API_KEY: str
    GLM_API_URL: str = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"
    DEFAULT_MODEL: str = "glm-4-flash"

    # 文件配置
    MAX_LOG_SIZE: int = 100 * 1024 * 1024  # 100MB

    # 输出配置
    REPORTS_DIR: str = "reports"

    # AI配置
    AI_TEMPERATURE: float = 0.3
    AI_TOP_P: float = 0.9
    AI_TIMEOUT: float = 120.0  # 增加超时时间

    _loaded: bool = False

    @classmethod
    def load(cls, env_file: str = ".env") -> None:
        """
        加载配置

        Args:
            env_file: 环境变量文件路径

        Raises:
            FileNotFoundError: .env文件不存在
            ValueError: 必需配置项缺失
        """
        if not os.path.exists(env_file):
            raise FileNotFoundError(f"Config file not found: {env_file}")

        load_dotenv(env_file, override=True)  # 覆盖已有环境变量

        # 验证必需配置项
        api_key = os.getenv("GLM_API_KEY")
        if not api_key or (isinstance(api_key, str) and api_key.strip() == ""):
            raise ValueError("GLM_API_KEY is required in .env file")

        cls.GLM_API_KEY = api_key

        # 加载可选配置项
        if model := os.getenv("DEFAULT_MODEL"):
            cls.DEFAULT_MODEL = model

        if api_url := os.getenv("GLM_API_URL"):
            cls.GLM_API_URL = api_url

        cls._loaded = True

    @classmethod
    def get(cls, key: str, default: Optional[Any] = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值

        Raises:
            KeyError: 配置项不存在且未提供默认值
        """
        if hasattr(cls, key):
            return getattr(cls, key)

        if default is not None:
            return default

        raise KeyError(f"Config key not found: {key}")

    @classmethod
    def is_loaded(cls) -> bool:
        """检查配置是否已加载"""
        return cls._loaded
