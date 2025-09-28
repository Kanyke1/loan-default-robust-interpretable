"""
Redis-backed TaskManager using simple Redis hashes and TTLs.

Requires aioredis.

Task keys:
- "task:{task_id}" -> hash with fields: status, detail, cancelled (0/1)

This supports cross-process cancellation and status queries.
"""
import asyncio
import os
import uuid
from typing import Optional, Dict

try:
    import aioredis
except Exception as e:
    raise RuntimeError("aioredis is required. Install with: pip install aioredis") from e

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
TASK_KEY_FMT = "task:{tid}"

class RedisTaskManager:
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or REDIS_URL
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            self._redis = await aioredis.create_redis(self.redis_url)
        return self._redis

    async def create_task(self) -> str:
        tid = str(uuid.uuid4())
        r = await self._get_redis()
        key = TASK_KEY_FMT.format(tid=tid)
        await r.hmset_dict(key, {"cancelled": "0", "status": "created", "detail": ""})
        # optionally set TTL for housekeeping, e.g., 7 days:
        await r.expire(key, 7 * 24 * 3600)
        return tid

    async def set_status(self, tid: str, status: str, detail: str = "") -> None:
        r = await self._get_redis()
        key = TASK_KEY_FMT.format(tid=tid)
        await r.hmset_dict(key, {"status": status, "detail": detail})

    async def cancel(self, tid: str) -> bool:
        r = await self._get_redis()
        key = TASK_KEY_FMT.format(tid=tid)
        exists = await r.exists(key)
        if not exists:
            return False
        await r.hset(key, "cancelled", "1")
        await r.hset(key, "status", "cancelled")
        return True

    async def is_cancelled(self, tid: str) -> bool:
        r = await self._get_redis()
        key = TASK_KEY_FMT.format(tid=tid)
        val = await r.hget(key, "cancelled", encoding="utf-8")
        return val == "1"

    async def get(self, tid: str) -> Optional[Dict]:
        r = await self._get_redis()
        key = TASK_KEY_FMT.format(tid=tid)
        if not await r.exists(key):
            return None
        res = await r.hgetall(key, encoding="utf-8")
        return res