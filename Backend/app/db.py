import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema(bind_engine):
    """Add columns that create_all() cannot add to existing tables (SQLite only)."""
    if bind_engine.dialect.name != "sqlite":
        return
    with bind_engine.begin() as conn:
        for table in ("invoices", "bills"):
            columns = conn.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
            names = {row[1] for row in columns}
            if "currency" not in names:
                conn.exec_driver_sql(
                    f"ALTER TABLE {table} ADD COLUMN currency VARCHAR(3) NOT NULL DEFAULT 'USD'"
                )

