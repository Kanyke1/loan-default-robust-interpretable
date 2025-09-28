"""
Redis-backed SSE manager.

Requires aioredis (pip install aioredis).
Environment variable REDIS_URL (e.g. redis://localhost:6379) or pass into constructor.

Design:
- publish messages to a Redis channel (default: sse_channel)
- each web worker subscribes to that channel and pushes received messages to its local subscriber queues
- this allows broadcasting across processes/machines

Usage:
- import RedisEventManager from app.sse_redis
- manager = RedisEventManager(redis_url=os.getenv("REDIS_URL"), channel="sse_channel")
- call await manager.publish(payload) from any process
- mount an /events endpoint that subscribes the local queue and streams via StreamingResponse(manager.event_generator(q))
"""
import asyncio
import json
import os
from typing import Any, Dict, List, AsyncIterator, Optional

try:
    import aioredis
except Exception as e:
    raise RuntimeError("aioredis is required for RedisEventManager. Install with: pip install aioredis") from e

class RedisEventManager:
    def __init__(self, redis_url: Optional[str] = None, channel: str = "sse_channel"):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.channel = channel
        self._subs: List[asyncio.Queue] = []
        self._lock = asyncio.Lock()
        self._redis = None
        self._task = None

    async def start(self):
        if self._task:
            return
        self._redis = await aioredis.create_redis(self.redis_url)
        self._task = asyncio.create_task(self._subscriber_loop())

    async def stop(self):
        if self._task:
            self._task.cancel()
            self._task = None
        if self._redis:
            self._redis.close()
            await self._redis.wait_closed()
            self._redis = None

    async def _subscriber_loop(self):
        """
        Subscribes to the Redis channel and pushes incoming messages to local queues.
        """
        pubsub = await aioredis.create_redis(self.redis_url)
        res = await pubsub.subscribe(self.channel)
        ch = res[0]
        try:
            while await ch.wait_message():
                raw = await ch.get(encoding="utf-8")
                # push to all local subscribers
                async with self._lock:
                    queues = list(self._subs)
                for q in queues:
                    try:
                        q.put_nowait(raw)
                    except asyncio.QueueFull:
                        # drop
                        pass
        finally:
            try:
                await pubsub.unsubscribe(self.channel)
            except Exception:
                pass
            pubsub.close()
            await pubsub.wait_closed()

    async def subscribe(self) -> asyncio.Queue:
        """
        Create a local asyncio.Queue for a new HTTP client; returned queue will receive JSON strings.
        """
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        async with self._lock:
            self._subs.append(q)
        # ensure subscriber loop is running
        if not self._task:
            await self.start()
        return q

    async def unsubscribe(self, q: asyncio.Queue) -> None:
        async with self._lock:
            if q in self._subs:
                self._subs.remove(q)

    async def publish(self, payload: Dict[str, Any]) -> None:
        """
        Publish payload (dict) to the Redis channel so all subscribers (across processes) get it.
        """
        if self._redis is None:
            # lazy connect
            self._redis = await aioredis.create_redis(self.redis_url)
        data = json.dumps(payload)
        await self._redis.publish(self.channel, data)

    async def event_generator(self, q: asyncio.Queue) -> AsyncIterator[bytes]:
        """
        Local SSE generator that yields events from the local queue (q).
        """
        try:
            # initial keep-alive
            yield b'event: welcome\ndata: {"msg":"connected"}\n\n'
            while True:
                data = await q.get()
                chunk = f"data: {data}\n\n"
                yield chunk.encode("utf-8")
        finally:
            return