import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from app.config import settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1]:
            log_data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data
        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        base = f"{ts} | {record.levelname:<8} | {record.name} | {record.getMessage()}"
        if record.exc_info and record.exc_info[1]:
            base += "\n" + self.formatException(record.exc_info)
        return base


class AlertHandler(logging.Handler):
    def __init__(
        self,
        level: int = logging.ERROR,
        callbacks: Optional[List[Callable[[logging.LogRecord], None]]] = None,
    ):
        super().__init__(level)
        self.callbacks: List[Callable[[logging.LogRecord], None]] = callbacks or []

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno < self.level:
            return
        for callback in self.callbacks:
            try:
                callback(record)
            except Exception:
                pass


_alert_callbacks: List[Callable[[logging.LogRecord], None]] = []
_initialized = False


def register_alert_callback(callback: Callable[[logging.LogRecord], None]) -> None:
    _alert_callbacks.append(callback)


def _setup_logging() -> None:
    global _initialized
    if _initialized:
        return
    _initialized = True

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    formatter = JsonFormatter() if settings.LOG_JSON_FORMAT else TextFormatter()

    root_logger = logging.getLogger("fyybr")
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    os.makedirs(settings.LOG_DIR, exist_ok=True)

    app_log_path = os.path.join(settings.LOG_DIR, "app.log")
    file_handler = logging.handlers.RotatingFileHandler(
        app_log_path,
        maxBytes=settings.LOG_FILE_MAX_BYTES,
        backupCount=settings.LOG_FILE_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    if settings.LOG_ERROR_FILE_ENABLED:
        error_log_path = os.path.join(settings.LOG_DIR, "error.log")
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_path,
            maxBytes=settings.LOG_FILE_MAX_BYTES,
            backupCount=settings.LOG_FILE_BACKUP_COUNT,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)

    if _alert_callbacks:
        alert_handler = AlertHandler(level=logging.ERROR, callbacks=_alert_callbacks)
        alert_handler.setFormatter(formatter)
        root_logger.addHandler(alert_handler)

    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if log_level <= logging.DEBUG else logging.WARNING
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    _setup_logging()
    logger = logging.getLogger(f"fyybr.{name}" if name else "fyybr")
    return logger
