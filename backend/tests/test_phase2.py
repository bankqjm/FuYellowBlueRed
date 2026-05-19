import pytest
import logging
import os
import json
from unittest.mock import patch, MagicMock

from app.core.logger import (
    JsonFormatter,
    TextFormatter,
    AlertHandler,
    register_alert_callback,
    get_logger,
    _setup_logging,
)
from app.core.metrics import (
    ORDER_CREATED,
    ORDER_COMPLETED,
    ORDER_CANCELLED,
    ACTIVE_ORDERS,
    ACTIVE_WEBSOCKET_CONNECTIONS,
    USER_REGISTRATIONS,
    API_REQUEST_DURATION,
    REDIS_OPERATIONS,
    PAYMENT_TRANSACTIONS,
)
from app.utils.storage import LocalStorage, S3Storage, get_storage


class TestJsonFormatter:
    def test_basic_format(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello world",
            args=None,
            exc_info=None,
        )
        result = formatter.format(record)
        data = json.loads(result)
        assert data["level"] == "INFO"
        assert data["logger"] == "test"
        assert data["message"] == "hello world"
        assert "timestamp" in data

    def test_format_with_exception(self):
        formatter = JsonFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="error occurred",
            args=None,
            exc_info=exc_info,
        )
        result = formatter.format(record)
        data = json.loads(result)
        assert data["level"] == "ERROR"
        assert "exception" in data
        assert "ValueError" in data["exception"]

    def test_format_with_extra_data(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test",
            args=None,
            exc_info=None,
        )
        record.extra_data = {"user_id": 123, "action": "login"}
        result = formatter.format(record)
        data = json.loads(result)
        assert data["data"]["user_id"] == 123
        assert data["data"]["action"] == "login"


class TestTextFormatter:
    def test_basic_format(self):
        formatter = TextFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="warning message",
            args=None,
            exc_info=None,
        )
        result = formatter.format(record)
        assert "WARNING" in result
        assert "test" in result
        assert "warning message" in result


class TestAlertHandler:
    def test_emit_calls_callbacks(self):
        received = []
        callback = lambda record: received.append(record)
        handler = AlertHandler(level=logging.ERROR, callbacks=[callback])
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="critical error",
            args=None,
            exc_info=None,
        )
        handler.emit(record)
        assert len(received) == 1
        assert received[0].getMessage() == "critical error"

    def test_handle_ignores_below_level(self):
        received = []
        callback = lambda record: received.append(record)
        handler = AlertHandler(level=logging.ERROR, callbacks=[callback])
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="info message",
            args=None,
            exc_info=None,
        )
        handler.handle(record)
        assert len(received) == 0

    def test_callback_exception_does_not_propagate(self):
        def bad_callback(record):
            raise RuntimeError("callback failed")

        handler = AlertHandler(level=logging.ERROR, callbacks=[bad_callback])
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="error",
            args=None,
            exc_info=None,
        )
        handler.emit(record)


class TestRegisterAlertCallback:
    def test_register_callback(self):
        import app.core.logger as logger_module

        original_count = len(logger_module._alert_callbacks)
        callback = lambda record: None
        register_alert_callback(callback)
        assert len(logger_module._alert_callbacks) == original_count + 1
        logger_module._alert_callbacks.pop()


class TestGetLogger:
    def test_get_logger_returns_logger(self):
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert "fyybr.test_module" in logger.name

    def test_get_logger_default_name(self):
        logger = get_logger()
        assert logger.name == "fyybr"


class TestMetricsDefinitions:
    def test_order_metrics_exist(self):
        assert ORDER_CREATED is not None
        assert ORDER_COMPLETED is not None
        assert ORDER_CANCELLED is not None
        assert ACTIVE_ORDERS is not None

    def test_websocket_metric_exists(self):
        assert ACTIVE_WEBSOCKET_CONNECTIONS is not None

    def test_user_metric_exists(self):
        assert USER_REGISTRATIONS is not None

    def test_api_duration_metric_exists(self):
        assert API_REQUEST_DURATION is not None

    def test_redis_operations_metric_exists(self):
        assert REDIS_OPERATIONS is not None

    def test_payment_metric_exists(self):
        assert PAYMENT_TRANSACTIONS is not None

    def test_metrics_can_increment(self):
        ORDER_CREATED.inc()
        ORDER_COMPLETED.inc()
        ORDER_CANCELLED.inc()
        USER_REGISTRATIONS.inc()

    def test_gauge_can_modify(self):
        initial = ACTIVE_WEBSOCKET_CONNECTIONS._value.get()
        ACTIVE_WEBSOCKET_CONNECTIONS.inc()
        assert ACTIVE_WEBSOCKET_CONNECTIONS._value.get() == initial + 1
        ACTIVE_WEBSOCKET_CONNECTIONS.dec()
        assert ACTIVE_WEBSOCKET_CONNECTIONS._value.get() == initial


class TestLocalStorage:
    @pytest.mark.asyncio
    async def test_save_and_get_url(self, tmp_path):
        storage = LocalStorage(upload_dir=str(tmp_path), url_prefix="/uploads")
        filename = await storage.save("test.jpg", b"fake image content", "image/jpeg")
        assert filename.endswith("_test.jpg")
        url = await storage.get_url(filename)
        assert url.startswith("/uploads/")
        assert filename in url

    @pytest.mark.asyncio
    async def test_save_creates_unique_names(self, tmp_path):
        storage = LocalStorage(upload_dir=str(tmp_path), url_prefix="/uploads")
        name1 = await storage.save("test.jpg", b"content1", "image/jpeg")
        name2 = await storage.save("test.jpg", b"content2", "image/jpeg")
        assert name1 != name2

    @pytest.mark.asyncio
    async def test_delete_existing_file(self, tmp_path):
        storage = LocalStorage(upload_dir=str(tmp_path), url_prefix="/uploads")
        filename = await storage.save("test.jpg", b"content", "image/jpeg")
        deleted = await storage.delete(filename)
        assert deleted is True
        assert not os.path.exists(os.path.join(str(tmp_path), filename))

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self, tmp_path):
        storage = LocalStorage(upload_dir=str(tmp_path), url_prefix="/uploads")
        deleted = await storage.delete("nonexistent.jpg")
        assert deleted is False


class TestS3Storage:
    def test_init_with_defaults(self):
        storage = S3Storage(
            endpoint_url="http://localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            bucket="test-bucket",
        )
        assert storage.endpoint_url == "http://localhost:9000"
        assert storage.bucket == "test-bucket"
        assert storage._client is None

    @pytest.mark.asyncio
    async def test_get_url_with_prefix(self):
        storage = S3Storage(url_prefix="https://cdn.example.com")
        url = await storage.get_url("test_file.jpg")
        assert url == "https://cdn.example.com/test_file.jpg"

    @pytest.mark.asyncio
    async def test_get_url_without_prefix(self):
        storage = S3Storage(endpoint_url="http://minio:9000", bucket="mybucket")
        url = await storage.get_url("test_file.jpg")
        assert url == "http://minio:9000/mybucket/test_file.jpg"


class TestGetStorage:
    def test_get_storage_returns_local_by_default(self):
        import app.utils.storage as storage_module
        storage_module._storage_instance = None
        storage = get_storage()
        assert isinstance(storage, LocalStorage)
        storage_module._storage_instance = None

    def test_get_storage_returns_s3_when_configured(self):
        import app.utils.storage as storage_module
        from app.config import settings
        original = settings.STORAGE_TYPE
        settings.STORAGE_TYPE = "s3"
        storage_module._storage_instance = None
        storage = get_storage()
        assert isinstance(storage, S3Storage)
        settings.STORAGE_TYPE = original
        storage_module._storage_instance = None

    def test_get_storage_caches_instance(self):
        import app.utils.storage as storage_module
        storage_module._storage_instance = None
        storage1 = get_storage()
        storage2 = get_storage()
        assert storage1 is storage2
        storage_module._storage_instance = None
