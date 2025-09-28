"""
Simple in-memory TaskManager to track job ids, statuses and cancellation tokens.

This is suitable for single-process/demo use. For multi-worker, replace with Redis-backed manager.
"""
import asyncio
import uuid
from typing import Dict, Optional

class TaskManager:
    def __init__(self):
        # maps task_id -> { cancelled: bool, status: str, detail: str }
        self._tasks: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()

    async def create_task(self) -> str:
        tid = str(uuid.uuid4())
        async with self._lock:
            self._tasks[tid] = {"cancelled": False, "status": "created", "detail": ""}
        return tid

    async def set_status(self, tid: str, status: str, detail: str = "") -> None:
        async with self._lock:
            if tid in self._tasks:
                self._tasks[tid]["status"] = status
                self._tasks[tid]["detail"] = detail

    async def cancel(self, tid: str) -> bool:
        async with self._lock:
            if tid in self._tasks:
                self._tasks[tid]["cancelled"] = True
                self._tasks[tid]["status"] = "cancelled"
                return True
        return False

    async def is_cancelled(self, tid: str) -> bool:
        async with self._lock:
            return bool(self._tasks.get(tid, {}).get("cancelled", False))

    async def get(self, tid: str) -> Optional[Dict]:
        async with self._lock:
            return self._tasks.get(tid)

# single global manager
task_manager = TaskManager()