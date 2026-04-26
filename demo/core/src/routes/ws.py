"""WebSocket broadcast hub.

All backend events (layer activation, signal frames, taskspec, bt ticks,
five-factor updates, audit log) fan out through `manager.broadcast(...)`.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self._active: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._active.add(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._active.discard(ws)

    async def broadcast(self, event: str, data: Any) -> None:
        payload = json.dumps({"event": event, "data": data}, ensure_ascii=False, default=str)
        async with self._lock:
            stale: list[WebSocket] = []
            for ws in self._active:
                try:
                    await ws.send_text(payload)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("ws send failed, dropping: %s", exc)
                    stale.append(ws)
            for ws in stale:
                self._active.discard(ws)

    @property
    def size(self) -> int:
        return len(self._active)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await manager.connect(ws)
    try:
        await manager.broadcast("session.hello", {"connected": manager.size})
        while True:
            # Keep the connection alive; we don't expect incoming messages in v0.1
            msg = await ws.receive_text()
            logger.debug("ws received (ignored): %s", msg)
    except WebSocketDisconnect:
        await manager.disconnect(ws)
