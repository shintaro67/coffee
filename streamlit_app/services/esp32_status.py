from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Esp32Status:
    ok: bool = False
    state: str = "unknown"
    elapsed_ms: int = 0
    weight: float = 0.0
    temp_kettle: float = 0.0
    temp_dripper: float = 0.0

    @classmethod
    def from_payload(cls, payload: dict) -> "Esp32Status":
        return cls(
            ok=bool(payload.get("ok", False)),
            state=str(payload.get("state", "unknown")),
            elapsed_ms=int(payload.get("elapsed_ms", 0)),
            weight=float(payload.get("weight", 0.0)),
            temp_kettle=float(payload.get("temp_kettle", 0.0)),
            temp_dripper=float(payload.get("temp_dripper", 0.0)),
        )