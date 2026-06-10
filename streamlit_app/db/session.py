from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DB_PATH

DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    future=True,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def init_db() -> None:
    from db.models import Bean, BrewLog  # noqa: F401

    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        inspector = inspect(conn)
        bean_columns = {column["name"] for column in inspector.get_columns("beans")}
        if "notes" not in bean_columns:
            conn.execute(text("ALTER TABLE beans ADD COLUMN notes TEXT NOT NULL DEFAULT ''"))
        conn.execute(text("PRAGMA journal_mode=WAL"))
        conn.execute(text("PRAGMA synchronous=NORMAL"))
        conn.commit()
