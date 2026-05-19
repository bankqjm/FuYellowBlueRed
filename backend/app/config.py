from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


DEFAULT_SECRET_KEY = "your-super-secret-key-change-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite+aiosqlite:///./data.db"
    SECRET_KEY: str = DEFAULT_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024
    DEBUG: bool = True

    REDIS_URL: str = "redis://localhost:6379/0"
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"
    LOG_FILE_MAX_BYTES: int = 50 * 1024 * 1024
    LOG_FILE_BACKUP_COUNT: int = 30
    LOG_JSON_FORMAT: bool = False
    LOG_ERROR_FILE_ENABLED: bool = True

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
        if not self.DEBUG and self.SECRET_KEY == DEFAULT_SECRET_KEY:
            raise ValueError(
                "安全错误: 生产环境(DEBUG=False)必须通过环境变量 SECRET_KEY 设置自定义密钥。"
                "示例: SECRET_KEY=your-secure-random-256-bit-key python -m uvicorn ..."
            )

        if self.SECRET_KEY == DEFAULT_SECRET_KEY and os.environ.get("SECRET_KEY") is None:
            import logging
            logging.warning(
                "警告: 使用默认 SECRET_KEY！请在生产环境中设置自定义密钥。"
                "设置方式: export SECRET_KEY=your-secure-random-256-bit-key"
            )

    @property
    def cors_origins_list(self) -> List[str]:
        return [
            origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()
        ]


settings = Settings()
