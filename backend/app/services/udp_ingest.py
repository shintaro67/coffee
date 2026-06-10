from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime

from .brew_session import BrewSessionService
from .flow import FlowSample, compute_flow_rate
from .ws_hub import WebSocketHub
from ..core.config import settings


def parse_payload(payload: str) -> FlowSample | None:
    parts = [part.strip() for part in payload.split(",")]
    if len(parts) < 2:
        return None
    try:
        elapsed = float(parts[0])
        weight = float(parts[1])
        temp_kettle = float(parts[2]) if len(parts) >= 3 else 0.0
        temp_dripper = float(parts[3]) if len(parts) >= 4 else 0.0
        return FlowSample(
            elapsed=elapsed,
            weight=weight,
            temp_kettle=temp_kettle,
            temp_dripper=temp_dripper,
            ts=datetime.utcnow().timestamp(),
        )
    except ValueError:
        return None


@dataclass
class TelemetryPacket:
    telemetry: dict
    session: dict


class TelemetryProtocol(asyncio.DatagramProtocol):
    def __init__(self, hub: WebSocketHub, session_service: BrewSessionService, relay) -> None:
        self.hub = hub
        self.session_service = session_service
        self.relay = relay
        self.transport: asyncio.DatagramTransport | None = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport  # type: ignore[assignment]

    def datagram_received(self, data: bytes, addr) -> None:
        message = data.decode("utf-8", errors="ignore").strip()
        if message.startswith("announce,"):
            parts = message.split(",")
            if len(parts) >= 2:
                self.relay.update_target(parts[1])
            return

        sample = parse_payload(message)
        if sample is None:
            return

        session = self.session_service.ingest(sample)
        sample.flow_rate = compute_flow_rate(session.samples, settings.flow_rate_window_seconds)
        if session.samples:
            session.samples[-1].flow_rate = sample.flow_rate

        packet = {
            "type": "telemetry",
            "telemetry": {
                "elapsed": sample.elapsed,
                "weight": sample.weight,
                "temp_kettle": sample.temp_kettle,
                "temp_dripper": sample.temp_dripper,
                "raw_flow_rate": sample.flow_rate,
                "received_at": sample.ts,
                "sender_ip": addr[0],
            },
            "session": session.summary(),
        }
        asyncio.get_running_loop().create_task(self.hub.publish(packet))


async def start_udp_receiver(hub: WebSocketHub, session_service: BrewSessionService, relay):
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: TelemetryProtocol(hub, session_service, relay),
        local_addr=(settings.udp_listen_host, settings.udp_listen_port),
    )
    return transport, protocol
