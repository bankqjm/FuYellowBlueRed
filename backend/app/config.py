from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


# 默认密钥（仅用于开发环境，生产环境必须通过环境变量设置自定义密钥）
DEFAULT_SECRET_KEY = "your-super-secret-key-change-in-production"


class Settings(BaseSettings):
    """
    应用配置类

    配置加载优先级（从高到低）：
      1. 系统环境变量
      2. .env.local 文件（本地开发专用，含数据库等敏感信息，不纳入版本控制）
      3. .env 文件（基础环境配置，不纳入版本控制）
      4. 代码中的默认值
    """

    model_config = SettingsConfigDict(
        env_file=[".env", ".env.local"],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 数据库连接配置
    # MySQL/OceanBase 格式：mysql+aiomysql://用户名:密码@主机地址:端口/数据库名
    # SQLite 本地格式：sqlite+aiosqlite:///./data.db
    DATABASE_URL: str = "sqlite+aiosqlite:///./data.db"

    # 认证配置
    SECRET_KEY: str = DEFAULT_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 跨域配置
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024

    # 调试模式（生产环境请设为 False）
    DEBUG: bool = True

    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # 接口限流配置
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"
    LOG_FILE_MAX_BYTES: int = 50 * 1024 * 1024
    LOG_FILE_BACKUP_COUNT: int = 30
    LOG_JSON_FORMAT: bool = False
    LOG_ERROR_FILE_ENABLED: bool = True

    # 存储配置（local 或 s3）
    STORAGE_TYPE: str = "local"
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET: str = "fyybr-uploads"
    S3_REGION: str = "us-east-1"
    S3_URL_PREFIX: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_config()

    def _validate_config(self):
        """校验配置项的合法性"""
        if not self.DEBUG and self.SECRET_KEY == DEFAULT_SECRET_KEY:
            raise ValueError(
                "安全错误：生产环境（DEBUG=False）必须通过环境变量 SECRET_KEY 设置自定义密钥。"
                "示例：SECRET_KEY=your-secure-random-256-bit-key python -m uvicorn ..."
            )

        if self.SECRET_KEY == DEFAULT_SECRET_KEY and os.environ.get("SECRET_KEY") is None:
            import logging
            logging.warning(
                "警告：正在使用默认 SECRET_KEY！请在生产环境中设置自定义密钥。"
                "设置方式：export SECRET_KEY=your-secure-random-256-bit-key"
            )

        if self.DATABASE_URL == "sqlite+aiosqlite:///./data.db" and not self.DEBUG:
            import logging
            logging.warning(
                "警告：生产环境正在使用 SQLite 数据库，建议在 .env.local 中配置 MySQL/OceanBase 连接。"
            )

    @property
    def cors_origins_list(self) -> List[str]:
        """获取跨域允许来源列表"""
        return [
            origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()
        ]


settings = Settings()
