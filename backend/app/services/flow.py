from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass
class FlowSample:
    elapsed: float
    weight: float
    temp_kettle: float = 0.0
    temp_dripper: float = 0.0
    flow_rate: float = 0.0
    ts: float = 0.0


def compute_flow_rate(samples: deque[FlowSample], window_seconds: float) -> float:
    if len(samples) < 2:
        return 0.0
    newest = samples[-1]
    recent = [sample for sample in samples if newest.ts - sample.ts <= window_seconds]
    if len(recent) < 2:
        recent = list(samples)[-2:]
    first = recent[0]
    last = recent[-1]
    dt = max(last.ts - first.ts, 1e-6)
    return (last.weight - first.weight) / dt
