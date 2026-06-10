from __future__ import annotations

import httpx

from ..core.config import settings


class Esp32Relay:
    def __init__(self) -> None:
        self._target_ip = settings.esp32_ip
        self._target_port = settings.esp32_http_port
        self._client: httpx.AsyncClient | None = None

    def update_target(self, ip: str) -> None:
        self._target_ip = ip

    async def start(self) -> None:
        if self._client is not None:
            return
        self._client = httpx.AsyncClient(timeout=3.0)

    async def stop(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def send_command(self, command: str) -> None:
        if self._client is None:
            await self.start()
        assert self._client is not None
        if command == "t":
            path = "/tare"
        elif command == "s":
            path = "/start"
        else:
            raise ValueError(f"Unsupported ESP32 command: {command}")

        url = f"http://{self._target_ip}:{self._target_port}{path}"
        await self._client.post(url)
