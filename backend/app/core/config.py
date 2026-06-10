from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Coffee Brew Logger API")
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{Path(__file__).resolve().parents[3] / 'data' / 'coffee_brew_logger.db'}")
    udp_listen_host: str = os.getenv("UDP_LISTEN_HOST", "0.0.0.0")
    udp_listen_port: int = int(os.getenv("UDP_LISTEN_PORT", "5005"))
    esp32_http_port: int = int(os.getenv("ESP32_HTTP_PORT", "8080"))
    esp32_ip: str = os.getenv("ESP32_IP", "192.168.11.4")
    cors_origins: tuple[str, ...] = tuple(o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip())
    flow_rate_window_seconds: float = float(os.getenv("FLOW_RATE_WINDOW_SECONDS", "1.5"))
    brew_snapshot_max_points: int = int(os.getenv("BREW_SNAPSHOT_MAX_POINTS", "4000"))


settings = Settings()
