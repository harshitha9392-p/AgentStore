import json
from typing import Any, Optional
import redis.asyncio as aioredis
from backend.app.core.config import settings

class InMemoryRedis:
    """Zero-dependency fallback in-memory cache when standalone without external Redis."""
    def __init__(self):
        self._store = {}
        self._ttls = {}

    async def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        self._store[key] = value
        return True

    async def setex(self, key: str, time: int, value: str) -> bool:
        self._store[key] = value
        return True

    async def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if k in self._store:
                del self._store[k]
                count += 1
        return count

    async def exists(self, key: str) -> bool:
        return key in self._store

    async def flushdb(self):
        self._store.clear()

class RedisManager:
    def __init__(self):
        self.client = None
        self._is_mock = False

    async def connect(self):
        try:
            r = aioredis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=1.0)
            await r.ping()
            self.client = r
            self._is_mock = False
        except Exception:
            self.client = InMemoryRedis()
            self._is_mock = True

    async def get_client(self):
        if self.client is None:
            await self.connect()
        return self.client

    async def get_json(self, key: str) -> Optional[Any]:
        client = await self.get_client()
        val = await client.get(key)
        if val:
            return json.loads(val)
        return None

    async def set_json(self, key: str, value: Any, ex: int = 3600):
        client = await self.get_client()
        serialized = json.dumps(value)
        if hasattr(client, "setex"):
            await client.setex(key, ex, serialized)
        else:
            await client.set(key, serialized, ex=ex)

    async def set_idempotency_lock(self, key: str, ttl_seconds: int = 60) -> bool:
        client = await self.get_client()
        if await client.exists(key):
            return False
        await client.set(key, "LOCKED", ex=ttl_seconds)
        return True

redis_manager = RedisManager()
