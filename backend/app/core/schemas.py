from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class BeanBase(BaseModel):
    name: str
    roaster: str = ""
    process: str = ""
    roast_level: str = ""
    roast_date: date


class BeanCreate(BeanBase):
    pass


class BeanRead(BeanBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_archived: bool
    days_from_roast: int | None = None


class TelemetryPoint(BaseModel):
    elapsed: float
    weight: float
    temp_kettle: float = 0.0
    temp_dripper: float = 0.0
    flow_rate: float = 0.0
    raw_flow_rate: float | None = None
    received_at: datetime | None = None


class BrewSessionSummary(BaseModel):
    active: bool
    completed: bool
    bean_id: int | None = None
    bean_name: str | None = None
    powder_weight: float = 0.0
    target_ratio: float = 0.0
    target_water: float = 0.0
    elapsed: float = 0.0
    weight: float = 0.0
    progress: float = 0.0
    flow_rate: float = 0.0
    current_state: Literal["idle", "waiting", "brewing", "finished"] = "idle"
    timeseries_length: int = 0


class BrewLogBase(BaseModel):
    bean_id: int
    days_from_roast: int
    elapsed_time_total: float = 0.0
    max_weight: float = 0.0
    powder_weight: float = 0.0
    extract_weight: float = 0.0
    tds: float = 0.0
    brew_ratio: float = 0.0
    grind_size: str = ""
    dripper: str = ""
    acidity: int = Field(default=3, ge=1, le=5)
    sweetness: int = Field(default=3, ge=1, le=5)
    body: int = Field(default=3, ge=1, le=5)
    rating: int = Field(default=3, ge=1, le=5)
    notes: str = ""
    timeseries_json: list[dict[str, Any]] | None = None


class BrewLogCreate(BrewLogBase):
    pass


class BrewLogListItem(BrewLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: datetime
    yield_ey: float
    bean_name: str | None = None
    timeseries_json: list[dict[str, Any]] | None = None


class BrewLogDetail(BrewLogListItem):
    timeseries_json: list[dict[str, Any]]
    bean: BeanRead | None = None


class WebsocketCommand(BaseModel):
    type: Literal["tare", "start"]
    bean_id: int | None = None
    bean_name: str | None = None
    powder_weight: float | None = None
    target_ratio: float | None = None
