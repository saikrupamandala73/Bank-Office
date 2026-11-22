from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CurrencyCode = Literal["INR", "USD", "EUR", "GBP", "AED", "JPY"]


class UserCreate(BaseModel):
    email: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime


class InvoiceCreate(BaseModel):
    client_name: str
    amount: float = Field(gt=0)
    due_date: date
    status: Literal["pending", "overdue", "paid"] = "pending"
    currency: CurrencyCode = "USD"


class InvoiceUpdate(BaseModel):
    client_name: str | None = None
    amount: float | None = Field(default=None, gt=0)
    due_date: date | None = None
    status: Literal["pending", "overdue", "paid"] | None = None
    currency: CurrencyCode | None = None


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_name: str
    amount: float
    due_date: date
    status: str
    currency: str
    amount_display: float | None = None
    display_currency: str | None = None


class BillCreate(BaseModel):
    title: str
    amount: float = Field(gt=0)
    due_date: date
    status: Literal["unpaid", "paid"] = "unpaid"
    currency: CurrencyCode = "USD"


class BillUpdate(BaseModel):
    title: str | None = None
    amount: float | None = Field(default=None, gt=0)
    due_date: date | None = None
    status: Literal["unpaid", "paid"] | None = None
    currency: CurrencyCode | None = None


class BillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    amount: float
    due_date: date
    status: str
    currency: str
    amount_display: float | None = None
    display_currency: str | None = None


class CurrencyInfo(BaseModel):
    code: str
    name: str
    symbol: str
    decimals: int


class SettingsRead(BaseModel):
    display_currency: str
    supported_currencies: list[CurrencyInfo]


class SettingsUpdate(BaseModel):
    display_currency: CurrencyCode


class FxRatesRead(BaseModel):
    base: str = "USD"
    source: str = "open.er-api.com"
    last_updated: datetime | None
    fetched_at: datetime
    stale: bool
    rates: dict[str, float]


class DashboardAction(BaseModel):
    priority: int
    kind: str
    message: str
    ref_type: str | None = None
    ref_id: int | None = None


class DashboardToday(BaseModel):
    as_of: date
    expected_inflows: float
    upcoming_bills: float
    overdue_bills: float
    net_outlook: float
    actions: list[DashboardAction]
    display_currency: str
    fx_last_updated: datetime | None = None
    fx_stale: bool = False
