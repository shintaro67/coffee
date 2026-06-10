from __future__ import annotations

import asyncio
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router, get_db
from .core.config import settings
from .core.database import init_db
from .core.schemas import WebsocketCommand
from .services.brew_session import BrewSessionService
from .services.esp32_relay import Esp32Relay
from .services.ws_hub import WebSocketClient, WebSocketHub
from .services.udp_ingest import start_udp_receiver


app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

app.state.ws_hub = WebSocketHub()
app.state.brew_session_service = BrewSessionService()
app.state.esp32_relay = Esp32Relay()
app.state.udp_transport = None
app.state.udp_protocol = None


@app.on_event("startup")
async def on_startup() -> None:
    init_db()
    await app.state.esp32_relay.start()
    transport, protocol = await start_udp_receiver(app.state.ws_hub, app.state.brew_session_service, app.state.esp32_relay)
    app.state.udp_transport = transport
    app.state.udp_protocol = protocol


@app.on_event("shutdown")
async def on_shutdown() -> None:
    if app.state.udp_transport is not None:
        app.state.udp_transport.close()
    await app.state.esp32_relay.stop()


@app.get("/")
def root() -> dict:
    return {"name": settings.app_name, "status": "ok"}


@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket) -> None:
    await websocket.accept()
    hub: WebSocketHub = app.state.ws_hub
    client = await hub.connect(websocket)

    async def send_loop() -> None:
        while True:
            message = await client.queue.get()
            await websocket.send_text(json.dumps(message))

    sender = asyncio.create_task(send_loop())
    try:
        while True:
            text = await websocket.receive_text()
            relay: Esp32Relay = app.state.esp32_relay
            session_service: BrewSessionService = app.state.brew_session_service

            if text == "tare":
                await relay.send_command("t")
                session_service.mark_tare()
                await hub.publish({"type": "session", "session": session_service.snapshot().summary()})
                await websocket.send_text(json.dumps({"type": "ack", "command": "tare"}))
            elif text == "start":
                await relay.send_command("s")
                session_service.start(bean_id=None, bean_name=None, powder_weight=0.0, target_ratio=0.0)
                await hub.publish({"type": "session", "session": session_service.snapshot().summary()})
                await websocket.send_text(json.dumps({"type": "ack", "command": "start"}))
            else:
                try:
                    payload = WebsocketCommand.model_validate_json(text)
                except Exception:
                    await websocket.send_text(json.dumps({"type": "error", "message": "invalid command"}))
                    continue

                if payload.type == "tare":
                    await relay.send_command("t")
                    session_service.mark_tare()
                    await hub.publish({"type": "session", "session": session_service.snapshot().summary()})
                    await websocket.send_text(json.dumps({"type": "ack", "command": "tare"}))
                elif payload.type == "start":
                    await relay.send_command("s")
                    session_service.start(
                        bean_id=payload.bean_id,
                        bean_name=payload.bean_name,
                        powder_weight=payload.powder_weight or 0.0,
                        target_ratio=payload.target_ratio or 0.0,
                    )
                    await hub.publish({"type": "session", "session": session_service.snapshot().summary()})
                    await websocket.send_text(json.dumps({"type": "ack", "command": "start"}))
    except WebSocketDisconnect:
        pass
    finally:
        sender.cancel()
        await hub.disconnect(client)

