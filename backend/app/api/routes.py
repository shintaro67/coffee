from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..core.database import SessionLocal
from ..core.models import Bean, BrewLog
from ..core.schemas import BeanCreate, BeanRead, BrewLogCreate, BrewLogDetail, BrewLogListItem, BrewSessionSummary
from ..services.brew_session import BrewSessionService


router = APIRouter(prefix="/api")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_app_services():
    raise RuntimeError("Dependency override not configured")


@router.get("/health")
def health() -> dict:
    return {"ok": True}


@router.get("/beans", response_model=list[BeanRead])
def list_beans(include_archived: bool = False, db: Session = Depends(get_db)):
    stmt = select(Bean).order_by(Bean.roast_date.desc(), Bean.id.desc())
    if not include_archived:
        stmt = stmt.where(Bean.is_archived.is_(False))
    beans = list(db.scalars(stmt).all())
    return [
        BeanRead.model_validate(
            {
                **bean.__dict__,
                "days_from_roast": (date.today() - bean.roast_date).days,
            }
        )
        for bean in beans
    ]


@router.get("/beans/{bean_id}", response_model=BeanRead)
def get_bean(bean_id: int, db: Session = Depends(get_db)):
    bean = db.get(Bean, bean_id)
    if bean is None:
        raise HTTPException(status_code=404, detail="Bean not found")
    return BeanRead.model_validate({**bean.__dict__, "days_from_roast": (date.today() - bean.roast_date).days})


@router.post("/beans", response_model=BeanRead)
def create_bean(payload: BeanCreate, db: Session = Depends(get_db)):
    bean = Bean(**payload.model_dump(), is_archived=False)
    db.add(bean)
    db.commit()
    db.refresh(bean)
    return BeanRead.model_validate({**bean.__dict__, "days_from_roast": (date.today() - bean.roast_date).days})


@router.patch("/beans/{bean_id}", response_model=BeanRead)
def archive_bean(bean_id: int, payload: dict, db: Session = Depends(get_db)):
    bean = db.get(Bean, bean_id)
    if bean is None:
        raise HTTPException(status_code=404, detail="Bean not found")
    if "is_archived" in payload:
        bean.is_archived = bool(payload["is_archived"])
        db.commit()
        db.refresh(bean)
    return BeanRead.model_validate({**bean.__dict__, "days_from_roast": (date.today() - bean.roast_date).days})


@router.get("/brew-session", response_model=BrewSessionSummary)
def get_brew_session(request: Request):
    session_service: BrewSessionService = request.app.state.brew_session_service
    return BrewSessionSummary.model_validate(session_service.snapshot().summary())


@router.post("/brew-logs", response_model=BrewLogDetail)
async def create_brew_log(payload: BrewLogCreate, request: Request, db: Session = Depends(get_db)):
    session_service: BrewSessionService = request.app.state.brew_session_service
    session = session_service.snapshot()
    bean = db.get(Bean, payload.bean_id)
    if bean is None:
        raise HTTPException(status_code=404, detail="Bean not found")
    timeseries_json = payload.timeseries_json or session.snapshot_timeseries()
    yield_ey = (payload.extract_weight * payload.tds) / payload.powder_weight if payload.powder_weight > 0 else 0.0
    log = BrewLog(
        bean_id=payload.bean_id,
        date=datetime.utcnow(),
        days_from_roast=payload.days_from_roast,
        elapsed_time_total=payload.elapsed_time_total,
        max_weight=payload.max_weight,
        powder_weight=payload.powder_weight,
        extract_weight=payload.extract_weight,
        tds=payload.tds,
        yield_ey=yield_ey,
        brew_ratio=payload.brew_ratio,
        grind_size=payload.grind_size,
        dripper=payload.dripper,
        acidity=payload.acidity,
        sweetness=payload.sweetness,
        body=payload.body,
        rating=payload.rating,
        notes=payload.notes,
        timeseries_json=timeseries_json,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    session_service.reset()
    await request.app.state.ws_hub.publish({"type": "session", "session": session_service.snapshot().summary()})
    return BrewLogDetail.model_validate({**log.__dict__, "bean_name": bean.name, "bean": BeanRead.model_validate({**bean.__dict__, "days_from_roast": (date.today() - bean.roast_date).days})})


@router.get("/brew-logs", response_model=list[BrewLogListItem])
def list_brew_logs(
    bean_id: int | None = None,
    bean_name: str | None = None,
    rating: int | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(BrewLog, Bean.name.label("bean_name")).join(Bean, BrewLog.bean_id == Bean.id).order_by(BrewLog.date.desc())
    if bean_id is not None:
        stmt = stmt.where(BrewLog.bean_id == bean_id)
    if bean_name:
        stmt = stmt.where(func.lower(Bean.name).like(f"%{bean_name.lower()}%"))
    if rating is not None:
        stmt = stmt.where(BrewLog.rating == rating)
    rows = db.execute(stmt).all()
    results = []
    for log, bean_name_value in rows:
        results.append(
            BrewLogListItem.model_validate(
                {
                    "bean_id": log.bean_id,
                    "days_from_roast": log.days_from_roast,
                    "elapsed_time_total": log.elapsed_time_total,
                    "max_weight": log.max_weight,
                    "powder_weight": log.powder_weight,
                    "extract_weight": log.extract_weight,
                    "tds": log.tds,
                    "brew_ratio": log.brew_ratio,
                    "grind_size": log.grind_size,
                    "dripper": log.dripper,
                    "acidity": log.acidity,
                    "sweetness": log.sweetness,
                    "body": log.body,
                    "rating": log.rating,
                    "notes": log.notes,
                    "id": log.id,
                    "date": log.date,
                    "yield_ey": log.yield_ey,
                    "bean_name": bean_name_value,
                }
            )
        )
    return results


@router.get("/brew-logs/{log_id}", response_model=BrewLogDetail)
def get_brew_log_detail(log_id: int, db: Session = Depends(get_db)):
    stmt = select(BrewLog).options(joinedload(BrewLog.bean)).where(BrewLog.id == log_id)
    log = db.scalars(stmt).first()
    if log is None:
        raise HTTPException(status_code=404, detail="Brew log not found")
    return BrewLogDetail.model_validate(
        {
            **log.__dict__,
            "bean_name": log.bean.name if log.bean else None,
            "bean": BeanRead.model_validate({**log.bean.__dict__, "days_from_roast": (date.today() - log.bean.roast_date).days}) if log.bean else None,
        }
    )
