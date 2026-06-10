from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Bean(Base):
    __tablename__ = "beans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    roaster: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    process: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    roast_level: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    roast_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    brew_logs: Mapped[list["BrewLog"]] = relationship("BrewLog", back_populates="bean")


class BrewLog(Base):
    __tablename__ = "brew_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bean_id: Mapped[int] = mapped_column(ForeignKey("beans.id"), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    days_from_roast: Mapped[int] = mapped_column(Integer, nullable=False)

    elapsed_time_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    max_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    powder_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    extract_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    yield_ey: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    brew_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    grind_size: Mapped[str] = mapped_column(String(80), default="")
    dripper: Mapped[str] = mapped_column(String(80), default="")
    acidity: Mapped[int] = mapped_column(Integer, default=3)
    sweetness: Mapped[int] = mapped_column(Integer, default=3)
    body: Mapped[int] = mapped_column(Integer, default=3)
    rating: Mapped[int] = mapped_column(Integer, default=3)
    notes: Mapped[str] = mapped_column(Text, default="")

    timeseries_json: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)

    bean: Mapped[Bean] = relationship("Bean", back_populates="brew_logs")
