"""
SSE manager for FastAPI (in-memory).

Usage:
- import notify from app.sse and call notify({...}) from synchronous code
- or import manager and await manager.broadcast(...) from async code
- expose /events endpoint using manager.subscribe() + manager.event_generator()
"""
import asyncio
import json
from typing import Dict, List, Any, AsyncIterator

class EventManager:
    def __init__(self):
        # store asyncio.Queues for each client
        self.connections: List[asyncio.Queue] = []
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        async with self._lock:
            self.connections.append(q)
        return q

    async def unsubscribe(self, q: asyncio.Queue) -> None:
        async with self._lock:
            if q in self.connections:
                self.connections.remove(q)

    async def broadcast(self, payload: Dict[str, Any]) -> None:
        """
        Put payload (dict) into every subscriber queue as a JSON string.
        """
        data = json.dumps(payload)
        async with self._lock:
            conns = list(self.connections)
        for q in conns:
            try:
                q.put_nowait(data)
            except asyncio.QueueFull:
                # skip if queue cannot accept new messages
                pass

    async def event_generator(self, q: asyncio.Queue) -> AsyncIterator[bytes]:
        """
        Yields SSE-formatted bytes given a queue for a subscriber.
        The HTTP response media_type should be text/event-stream.
        """
        try:
            # initial keep-alive / welcome event
            yield b'event: welcome\ndata: {"msg":"connected"}\n\n'
            while True:
                data = await q.get()
                chunk = f"data: {data}\n\n"
                yield chunk.encode("utf-8")
        finally:
            return

# single global manager to import elsewhere
manager = EventManager()

def notify(payload: Dict[str, Any]) -> None:
    """
    Sync-friendly helper to schedule a broadcast from synchronous code.

    Usage (sync code):
      from app.sse import notify
      notify({"type":"progress", "task":"preprocess", "pct": 10, "msg": "loaded"})
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # no running loop in this thread; we can't schedule. Best-effort no-op.
        return
    # schedule the coroutine, fire-and-forget
    loop.create_task(manager.broadcast(payload))