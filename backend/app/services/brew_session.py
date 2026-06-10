from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
import threading
from typing import Any

from .flow import FlowSample, compute_flow_rate
from ..core.config import settings


@dataclass
class BrewSession:
    active: bool = False
    completed: bool = False
    bean_id: int | None = None
    bean_name: str | None = None
    powder_weight: float = 0.0
    target_ratio: float = 0.0
    target_water: float = 0.0
    started_at: datetime | None = None
    last_elapsed: float = 0.0
    last_weight: float = 0.0
    current_state: str = "idle"
    samples: deque[FlowSample] = field(default_factory=lambda: deque(maxlen=settings.brew_snapshot_max_points))

    def reset(self) -> None:
        self.active = False
        self.completed = False
        self.bean_id = None
        self.bean_name = None
        self.powder_weight = 0.0
        self.target_ratio = 0.0
        self.target_water = 0.0
        self.started_at = None
        self.last_elapsed = 0.0
        self.last_weight = 0.0
        self.current_state = "idle"
        self.samples.clear()

    def start(self, bean_id: int | None, bean_name: str | None, powder_weight: float, target_ratio: float) -> None:
        self.reset()
        self.active = True
        self.bean_id = bean_id
        self.bean_name = bean_name
        self.powder_weight = max(powder_weight, 0.0)
        self.target_ratio = max(target_ratio, 0.0)
        self.target_water = self.powder_weight * self.target_ratio
        self.started_at = datetime.utcnow()
        self.current_state = "waiting"

    def ingest(self, sample: FlowSample, flow_window_seconds: float) -> None:
        if not self.active or self.completed:
            return
        self.samples.append(sample)
        self.last_elapsed = sample.elapsed
        self.last_weight = sample.weight
        self.current_state = "brewing" if sample.weight >= self.powder_weight else self.current_state
        if self.target_water > 0 and sample.weight >= self.target_water:
            self.completed = True
            self.active = False
            self.current_state = "finished"

    def snapshot_timeseries(self) -> list[dict[str, Any]]:
        return [
            {
                "elapsed": sample.elapsed,
                "weight": sample.weight,
                "temp_kettle": sample.temp_kettle,
                "temp_dripper": sample.temp_dripper,
                "flow_rate": sample.flow_rate,
            }
            for sample in self.samples
        ]

    def summary(self) -> dict[str, Any]:
        latest_flow = compute_flow_rate(self.samples, settings.flow_rate_window_seconds)
        progress = (self.last_weight / self.target_water) if self.target_water > 0 else 0.0
        return {
            "active": self.active,
            "completed": self.completed,
            "bean_id": self.bean_id,
            "bean_name": self.bean_name,
            "powder_weight": self.powder_weight,
            "target_ratio": self.target_ratio,
            "target_water": self.target_water,
            "elapsed": self.last_elapsed,
            "weight": self.last_weight,
            "progress": min(max(progress, 0.0), 1.0),
            "flow_rate": latest_flow,
            "current_state": self.current_state,
            "timeseries_length": len(self.samples),
        }


class BrewSessionService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._session = BrewSession()

    def reset(self) -> BrewSession:
        with self._lock:
            self._session.reset()
            return self._session

    def start(self, bean_id: int | None, bean_name: str | None, powder_weight: float, target_ratio: float) -> BrewSession:
        with self._lock:
            self._session.start(bean_id, bean_name, powder_weight, target_ratio)
            return self._session

    def mark_tare(self) -> BrewSession:
        with self._lock:
            self._session.reset()
            return self._session

    def ingest(self, sample: FlowSample) -> BrewSession:
        with self._lock:
            self._session.ingest(sample, settings.flow_rate_window_seconds)
            return self._session

    def snapshot(self) -> BrewSession:
        with self._lock:
            return self._session

