from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from fastapi import WebSocket


@dataclass(eq=False)
class WebSocketClient:
    websocket: WebSocket
    queue: asyncio.Queue[dict] = field(default_factory=lambda: asyncio.Queue(maxsize=1))


class WebSocketHub:
    def __init__(self) -> None:
        self._clients: set[WebSocketClient] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> WebSocketClient:
        client = WebSocketClient(websocket=websocket)
        async with self._lock:
            self._clients.add(client)
        return client

    async def disconnect(self, client: WebSocketClient) -> None:
        async with self._lock:
            self._clients.discard(client)

    async def publish(self, message: dict) -> None:
        async with self._lock:
            clients = list(self._clients)
        for client in clients:
            try:
                if client.queue.full():
                    try:
                        client.queue.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                client.queue.put_nowait(message)
            except asyncio.QueueFull:
                pass
