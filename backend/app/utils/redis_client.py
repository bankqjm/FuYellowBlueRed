import asyncio
from typing import Optional
from redis.asyncio import Redis
from app.config import settings


class RedisClient:
    _instance: Optional['RedisClient'] = None
    _client: Optional[Redis] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self):
        async with self._lock:
            if self._client is None:
                self._client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
                try:
                    await self._client.ping()
                except Exception:
                    self._client = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    @property
    def client(self) -> Redis:
        if self._client is None:
            raise RuntimeError("Redis未连接，请先调用connect()")
        return self._client

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None

    async def add_to_blacklist(self, token: str, expires_at: int):
        if not self.is_connected:
            return
        ttl = int(expires_at - (await self.client.time())[0])
        if ttl <= 0:
            return  # Token已过期，无需加入黑名单
        await self.client.setex(
            f"token:blacklist:{token}",
            ttl,
            "1"
        )

    async def is_blacklisted(self, token: str) -> bool:
        if not self.is_connected:
            return False
        result = await self.client.get(f"token:blacklist:{token}")
        return result is not None

    async def get_cache(self, key: str) -> Optional[str]:
        if not self.is_connected:
            return None
        return await self.client.get(f"cache:{key}")

    async def set_cache(self, key: str, value: str, ttl_seconds: int = 3600):
        if not self.is_connected:
            return
        await self.client.setex(f"cache:{key}", ttl_seconds, value)

    async def delete_cache(self, key: str):
        if not self.is_connected:
            return
        await self.client.delete(f"cache:{key}")

    async def incr_counter(self, key: str, expiration: int = 60) -> int:
        if not self.is_connected:
            return 0
        key = f"counter:{key}"
        value = await self.client.incr(key)
        if value == 1:
            await self.client.expire(key, expiration)
        return value

    async def get_counter(self, key: str) -> int:
        if not self.is_connected:
            return 0
        value = await self.client.get(f"counter:{key}")
        return int(value) if value else 0


redis_client = RedisClient()