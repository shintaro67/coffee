from datetime import date, datetime

from sqlalchemy import select

from db.models import Bean, BrewLog
from db.session import SessionLocal


def list_beans(include_archived: bool = True) -> list[Bean]:
    with SessionLocal() as session:
        stmt = select(Bean).order_by(Bean.roast_date.desc(), Bean.id.desc())
        if not include_archived:
            stmt = stmt.where(Bean.is_archived.is_(False))
        return list(session.scalars(stmt).all())


def create_bean(name: str, roaster: str, process: str, roast_level: str, roast_date: date, notes: str = "") -> Bean:
    with SessionLocal() as session:
        bean = Bean(
            name=name,
            roaster=roaster,
            process=process,
            roast_level=roast_level,
            roast_date=roast_date,
            notes=notes,
            is_archived=False,
        )
        session.add(bean)
        session.commit()
        session.refresh(bean)
        return bean


def set_bean_archived(bean_id: int, archived: bool) -> None:
    with SessionLocal() as session:
        bean = session.get(Bean, bean_id)
        if bean is None:
            return
        bean.is_archived = archived
        session.commit()


def update_bean(bean_id: int, name: str = None, roaster: str = None, process: str = None, roast_level: str = None, roast_date: date = None, notes: str = None, is_archived: bool = None) -> None:
    with SessionLocal() as session:
        bean = session.get(Bean, bean_id)
        if bean is None:
            return
        if name is not None:
            bean.name = name
        if roaster is not None:
            bean.roaster = roaster
        if process is not None:
            bean.process = process
        if roast_level is not None:
            bean.roast_level = roast_level
        if roast_date is not None:
            bean.roast_date = roast_date
        if notes is not None:
            bean.notes = notes
        if is_archived is not None:
            bean.is_archived = is_archived
        session.commit()


def create_brew_log(
    bean_id: int,
    days_from_roast: int,
    elapsed_time_total: float,
    max_weight: float,
    powder_weight: float,
    extract_weight: float,
    tds: float,
    yield_ey: float,
    brew_ratio: float,
    grind_size: str,
    dripper: str,
    acidity: int,
    sweetness: int,
    body: int,
    rating: int,
    notes: str,
    timeseries_json: list[dict],
) -> BrewLog:
    with SessionLocal() as session:
        log = BrewLog(
            bean_id=bean_id,
            date=datetime.utcnow(),
            days_from_roast=days_from_roast,
            elapsed_time_total=elapsed_time_total,
            max_weight=max_weight,
            powder_weight=powder_weight,
            extract_weight=extract_weight,
            tds=tds,
            yield_ey=yield_ey,
            brew_ratio=brew_ratio,
            grind_size=grind_size,
            dripper=dripper,
            acidity=acidity,
            sweetness=sweetness,
            body=body,
            rating=rating,
            notes=notes,
            timeseries_json=timeseries_json,
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        return log


def list_brew_logs(bean_id: int | None = None, rating: int | None = None) -> list[BrewLog]:
    with SessionLocal() as session:
        stmt = select(BrewLog).order_by(BrewLog.date.desc())
        if bean_id is not None:
            stmt = stmt.where(BrewLog.bean_id == bean_id)
        if rating is not None:
            stmt = stmt.where(BrewLog.rating == rating)
        return list(session.scalars(stmt).all())


def get_bean_map() -> dict[int, Bean]:
    beans = list_beans(include_archived=True)
    return {bean.id: bean for bean in beans}


def update_brew_log(log_id: int, notes: str | None = None, rating: int | None = None) -> None:
    """Update editable fields of a BrewLog. Currently supports notes and rating."""
    with SessionLocal() as session:
        log = session.get(BrewLog, log_id)
        if log is None:
            return
        if notes is not None:
            log.notes = notes
        if rating is not None:
            log.rating = rating
        session.commit()
