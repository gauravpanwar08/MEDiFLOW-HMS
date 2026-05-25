import json
import redis.asyncio as aioredis
from typing import Any, Optional
from app.core.config import settings

_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    return _redis_client


class CacheManager:
    def __init__(self, prefix: str = "hms"):
        self.prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        try:
            client = await get_redis()
            raw = await client.get(self._key(key))
            return json.loads(raw) if raw else None
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl: int = settings.REDIS_CACHE_TTL) -> bool:
        try:
            client = await get_redis()
            await client.setex(self._key(key), ttl, json.dumps(value, default=str))
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        try:
            client = await get_redis()
            await client.delete(self._key(key))
            return True
        except Exception:
            return False

    async def delete_pattern(self, pattern: str) -> int:
        try:
            client = await get_redis()
            keys = await client.keys(self._key(pattern))
            if keys:
                return await client.delete(*keys)
        except Exception:
            pass
        return 0

    async def publish(self, channel: str, message: dict):
        try:
            client = await get_redis()
            await client.publish(channel, json.dumps(message, default=str))
        except Exception:
            pass


cache = CacheManager()
