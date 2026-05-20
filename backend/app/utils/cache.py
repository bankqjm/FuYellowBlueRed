"""Redis cache utility for hot data caching.

Provides high-level caching functions that gracefully degrade
when Redis is unavailable. Cache keys use the prefix 'cache:'
which is automatically prepended by redis_client.

Cache invalidation strategy:
- Read operations: check cache first, miss -> query DB -> set cache
- Write operations (create/update/delete): invalidate related cache keys
"""

import json
from typing import Optional, TypeVar, Type
from pydantic import BaseModel
from app.utils.redis_client import redis_client
from app.core.logger import get_logger

logger = get_logger("cache")

T = TypeVar("T", bound=BaseModel)

# TTL constants (seconds)
SHOP_DETAIL_TTL = 5 * 60        # 5 minutes
PRODUCT_DETAIL_TTL = 5 * 60    # 5 minutes
CONFIG_TTL = 30 * 60           # 30 minutes
SHOP_LIST_TTL = 2 * 60         # 2 minutes
ADMIN_STATS_TTL = 1 * 60       # 1 minute


async def get_cached(key: str) -> Optional[str]:
    """Get a cached value by key. Returns None on cache miss or Redis unavailable."""
    try:
        return await redis_client.get_cache(key)
    except Exception as e:
        logger.warning(f"Cache get failed for key '{key}': {e}")
        return None


async def set_cached(key: str, value: str, ttl: int = 300) -> bool:
    """Set a cache value with TTL. Returns False on failure."""
    try:
        await redis_client.set_cache(key, value, ttl)
        return True
    except Exception as e:
        logger.warning(f"Cache set failed for key '{key}': {e}")
        return False


async def delete_cached(key: str) -> bool:
    """Delete a cache key. Returns False on failure."""
    try:
        await redis_client.delete_cache(key)
        return True
    except Exception as e:
        logger.warning(f"Cache delete failed for key '{key}': {e}")
        return False


async def delete_cached_pattern(pattern: str) -> bool:
    """Delete all cache keys matching a pattern.

    Uses SCAN to find matching keys, then deletes them.
    Pattern should not include the 'cache:' prefix — it's added automatically.
    """
    try:
        if not redis_client.is_connected:
            return False
        full_pattern = f"cache:{pattern}"
        cursor = 0
        while True:
            cursor, keys = await redis_client.client.scan(
                cursor=cursor, match=full_pattern, count=100
            )
            if keys:
                await redis_client.client.delete(*keys)
            if cursor == 0:
                break
        return True
    except Exception as e:
        logger.warning(f"Cache pattern delete failed for '{pattern}': {e}")
        return False


async def get_cached_model(model_class: Type[T], key: str) -> Optional[T]:
    """Get a cached Pydantic model from cache.

    Deserializes JSON string back to model instance.
    Returns None on cache miss or deserialization failure.
    """
    cached = await get_cached(key)
    if cached is None:
        return None
    try:
        return model_class.model_validate_json(cached)
    except Exception as e:
        logger.warning(f"Cache deserialization failed for key '{key}': {e}")
        return None


async def set_cached_model(key: str, model: BaseModel, ttl: int = 300) -> bool:
    """Cache a Pydantic model as JSON string."""
    try:
        return await set_cached(key, model.model_dump_json(), ttl)
    except Exception as e:
        logger.warning(f"Cache serialization failed for key '{key}': {e}")
        return False


async def get_cached_dict(key: str) -> Optional[dict]:
    """Get a cached dict from cache.

    Deserializes JSON string back to dict.
    Returns None on cache miss or deserialization failure.
    """
    cached = await get_cached(key)
    if cached is None:
        return None
    try:
        return json.loads(cached)
    except Exception as e:
        logger.warning(f"Cache dict deserialization failed for key '{key}': {e}")
        return None


async def set_cached_dict(key: str, data: dict, ttl: int = 300) -> bool:
    """Cache a dict as JSON string."""
    try:
        return await set_cached(key, json.dumps(data, ensure_ascii=False, default=str), ttl)
    except Exception as e:
        logger.warning(f"Cache dict serialization failed for key '{key}': {e}")
        return False
