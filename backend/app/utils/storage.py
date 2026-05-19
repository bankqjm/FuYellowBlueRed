import os
import uuid
from abc import ABC, abstractmethod
from typing import Optional

import aiofiles

from app.config import settings
from app.core import get_logger

logger = get_logger("storage")


class StorageBackend(ABC):
    @abstractmethod
    async def save(self, filename: str, content: bytes, content_type: str = "") -> str:
        ...

    @abstractmethod
    async def delete(self, file_path: str) -> bool:
        ...

    @abstractmethod
    async def get_url(self, file_path: str) -> str:
        ...


class LocalStorage(StorageBackend):
    def __init__(self, upload_dir: str = "", url_prefix: str = "/uploads"):
        self.upload_dir = upload_dir or settings.UPLOAD_DIR
        self.url_prefix = url_prefix
        os.makedirs(self.upload_dir, exist_ok=True)

    async def save(self, filename: str, content: bytes, content_type: str = "") -> str:
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(self.upload_dir, unique_name)
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)
        return unique_name

    async def delete(self, file_path: str) -> bool:
        full_path = os.path.join(self.upload_dir, file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False

    async def get_url(self, file_path: str) -> str:
        return f"{self.url_prefix}/{file_path}"


class S3Storage(StorageBackend):
    def __init__(
        self,
        endpoint_url: str = "",
        access_key: str = "",
        secret_key: str = "",
        bucket: str = "",
        region: str = "",
        url_prefix: str = "",
    ):
        self.endpoint_url = endpoint_url or settings.S3_ENDPOINT_URL
        self.access_key = access_key or settings.S3_ACCESS_KEY
        self.secret_key = secret_key or settings.S3_SECRET_KEY
        self.bucket = bucket or settings.S3_BUCKET
        self.region = region or settings.S3_REGION
        self.url_prefix = url_prefix or settings.S3_URL_PREFIX
        self._client = None

    def _get_client(self):
        if self._client is None:
            import boto3
            from botocore.config import Config as BotoConfig

            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                config=BotoConfig(signature_version="s3v4"),
            )
        return self._client

    async def save(self, filename: str, content: bytes, content_type: str = "") -> str:
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        client = self._get_client()
        client.put_object(
            Bucket=self.bucket,
            Key=unique_name,
            Body=content,
            ContentType=content_type or "application/octet-stream",
        )
        return unique_name

    async def delete(self, file_path: str) -> bool:
        try:
            client = self._get_client()
            client.delete_object(Bucket=self.bucket, Key=file_path)
            return True
        except Exception as e:
            logger.error(f"S3 delete failed: {e}")
            return False

    async def get_url(self, file_path: str) -> str:
        if self.url_prefix:
            return f"{self.url_prefix}/{file_path}"
        return f"{self.endpoint_url}/{self.bucket}/{file_path}"


_storage_instance: Optional[StorageBackend] = None


def get_storage() -> StorageBackend:
    global _storage_instance
    if _storage_instance is not None:
        return _storage_instance

    storage_type = settings.STORAGE_TYPE.lower()

    if storage_type == "s3":
        _storage_instance = S3Storage()
        logger.info("Storage backend: S3/MinIO")
    else:
        _storage_instance = LocalStorage()
        logger.info("Storage backend: Local filesystem")

    return _storage_instance
