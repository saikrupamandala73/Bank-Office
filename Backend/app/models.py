from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Invoice(Base):
    __tablename__ = "invoices"

    # allowed values: "pending", "overdue", "paid"
    id: Mapped[int] = mapped_column(primary_key=True)
    client_name: Mapped[str] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Float)
    due_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    currency: Mapped[str] = mapped_column(String(3), default="USD", server_default="USD", nullable=False)


class Bill(Base):
    __tablename__ = "bills"

    # allowed values: "unpaid", "paid"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Float)
    due_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="unpaid")
    currency: Mapped[str] = mapped_column(String(3), default="USD", server_default="USD", nullable=False)


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[str] = mapped_column(String(200))


class FxRate(Base):
    __tablename__ = "fx_rates"

    # rate_per_usd: units of that currency per 1 USD
    code: Mapped[str] = mapped_column(String(3), primary_key=True)
    rate_per_usd: Mapped[float] = mapped_column(Float)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime)
