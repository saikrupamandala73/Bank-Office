from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.fx import (
    CURRENCIES,
    SUPPORTED_CODES,
    convert,
    format_money,
    get_display_currency,
    get_rates,
    set_display_currency,
)
from app.models import Bill, Invoice
from app.schemas import (
    BillCreate,
    BillRead,
    BillUpdate,
    CurrencyInfo,
    DashboardAction,
    DashboardToday,
    FxRatesRead,
    InvoiceCreate,
    InvoiceRead,
    InvoiceUpdate,
    SettingsRead,
    SettingsUpdate,
)

router = APIRouter()


def _get_or_404(db: Session, model, item_id: int, label: str):
    item = db.get(model, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return item


def _rates_for(db: Session, display: str, currencies: list[str]):
    """Rates needed to show these currencies in display; None if no lookup is needed or rates are unavailable."""
    if all(code == display for code in currencies):
        return None
    try:
        return get_rates(db)["rates"]
    except HTTPException:
        return None


def _amount_display(amount: float, currency: str, display: str, rates) -> float | None:
    if currency == display:
        return amount
    if rates is None:
        return None
    return convert(amount, currency, display, rates)


def _invoice_out(invoice: Invoice, display: str, rates) -> InvoiceRead:
    out = InvoiceRead.model_validate(invoice)
    out.display_currency = display
    out.amount_display = _amount_display(invoice.amount, invoice.currency, display, rates)
    return out


def _bill_out(bill: Bill, display: str, rates) -> BillRead:
    out = BillRead.model_validate(bill)
    out.display_currency = display
    out.amount_display = _amount_display(bill.amount, bill.currency, display, rates)
    return out


# ---------- Invoices (expected inflows) ----------


@router.post("/invoices", status_code=status.HTTP_201_CREATED, response_model=InvoiceRead)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)):
    invoice = Invoice(**payload.model_dump())
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    display = get_display_currency(db)
    return _invoice_out(invoice, display, _rates_for(db, display, [invoice.currency]))


@router.get("/invoices", response_model=list[InvoiceRead])
def list_invoices(db: Session = Depends(get_db)):
    invoices = db.scalars(select(Invoice).order_by(Invoice.id)).all()
    display = get_display_currency(db)
    rates = _rates_for(db, display, [i.currency for i in invoices])
    return [_invoice_out(i, display, rates) for i in invoices]


@router.get("/invoices/{invoice_id}", response_model=InvoiceRead)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = _get_or_404(db, Invoice, invoice_id, "Invoice")
    display = get_display_currency(db)
    return _invoice_out(invoice, display, _rates_for(db, display, [invoice.currency]))


@router.patch("/invoices/{invoice_id}", response_model=InvoiceRead)
def update_invoice(invoice_id: int, payload: InvoiceUpdate, db: Session = Depends(get_db)):
    invoice = _get_or_404(db, Invoice, invoice_id, "Invoice")
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(invoice, field, value)
    db.commit()
    db.refresh(invoice)
    display = get_display_currency(db)
    return _invoice_out(invoice, display, _rates_for(db, display, [invoice.currency]))


@router.delete("/invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = _get_or_404(db, Invoice, invoice_id, "Invoice")
    db.delete(invoice)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- Bills (upcoming outflows) ----------


@router.post("/bills", status_code=status.HTTP_201_CREATED, response_model=BillRead)
def create_bill(payload: BillCreate, db: Session = Depends(get_db)):
    bill = Bill(**payload.model_dump())
    db.add(bill)
    db.commit()
    db.refresh(bill)
    display = get_display_currency(db)
    return _bill_out(bill, display, _rates_for(db, display, [bill.currency]))


@router.get("/bills", response_model=list[BillRead])
def list_bills(db: Session = Depends(get_db)):
    bills = db.scalars(select(Bill).order_by(Bill.id)).all()
    display = get_display_currency(db)
    rates = _rates_for(db, display, [b.currency for b in bills])
    return [_bill_out(b, display, rates) for b in bills]


@router.get("/bills/{bill_id}", response_model=BillRead)
def get_bill(bill_id: int, db: Session = Depends(get_db)):
    bill = _get_or_404(db, Bill, bill_id, "Bill")
    display = get_display_currency(db)
    return _bill_out(bill, display, _rates_for(db, display, [bill.currency]))


@router.patch("/bills/{bill_id}", response_model=BillRead)
def update_bill(bill_id: int, payload: BillUpdate, db: Session = Depends(get_db)):
    bill = _get_or_404(db, Bill, bill_id, "Bill")
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(bill, field, value)
    db.commit()
    db.refresh(bill)
    display = get_display_currency(db)
    return _bill_out(bill, display, _rates_for(db, display, [bill.currency]))


@router.delete("/bills/{bill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bill(bill_id: int, db: Session = Depends(get_db)):
    bill = _get_or_404(db, Bill, bill_id, "Bill")
    db.delete(bill)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- Today's cash-flow summary ----------


@router.get("/dashboard/today", response_model=DashboardToday)
def dashboard_today(db: Session = Depends(get_db)):
    today = date.today()
    horizon = today + timedelta(days=7)
    display = get_display_currency(db)

    invoices = db.scalars(select(Invoice)).all()
    # Persist overdue status: unpaid invoices whose due date has passed.
    for invoice in invoices:
        if invoice.status != "paid" and invoice.due_date < today and invoice.status != "overdue":
            invoice.status = "overdue"
    db.commit()

    bills = db.scalars(select(Bill)).all()

    # Expected inflows: all unpaid invoices (pending or overdue), all dates.
    unpaid_invoices = [i for i in invoices if i.status in ("pending", "overdue")]
    # Upcoming bills: unpaid bills due today..today+7.
    unpaid_bills = [b for b in bills if b.status == "unpaid"]

    needs_rates = display != "USD" or any(
        r.currency != display for r in unpaid_invoices + unpaid_bills
    )
    fx = get_rates(db) if needs_rates else None
    rates = fx["rates"] if fx else None

    # Convert unpaid amounts to the display currency before any sum or message.
    inv_amount = {i.id: convert(i.amount, i.currency, display, rates) for i in unpaid_invoices}
    bill_amount = {b.id: convert(b.amount, b.currency, display, rates) for b in unpaid_bills}

    expected_inflows = sum(inv_amount[i.id] for i in unpaid_invoices)

    upcoming_bills_list = [b for b in unpaid_bills if today <= b.due_date <= horizon]
    upcoming_bills = sum(bill_amount[b.id] for b in upcoming_bills_list)

    # Overdue bills: unpaid bills whose due date has already passed.
    overdue_bills = sum(bill_amount[b.id] for b in unpaid_bills if b.due_date < today)

    net_outlook = expected_inflows - (upcoming_bills + overdue_bills)

    actions: list[DashboardAction] = []

    for invoice in invoices:
        if invoice.status == "overdue":
            actions.append(
                DashboardAction(
                    priority=1,
                    kind="follow_up",
                    message=f"Follow up with {invoice.client_name} on overdue invoice of {format_money(inv_amount[invoice.id], display)}",
                    ref_type="invoice",
                    ref_id=invoice.id,
                )
            )

    for bill in unpaid_bills:
        if bill.due_date <= today:
            actions.append(
                DashboardAction(
                    priority=1,
                    kind="pay",
                    message=f"Pay {bill.title} ({format_money(bill_amount[bill.id], display)}) — due today or overdue",
                    ref_type="bill",
                    ref_id=bill.id,
                )
            )

    for invoice in invoices:
        if invoice.status == "pending" and today <= invoice.due_date <= horizon:
            actions.append(
                DashboardAction(
                    priority=2,
                    kind="collect",
                    message=f"Expect {format_money(inv_amount[invoice.id], display)} from {invoice.client_name} by {invoice.due_date}",
                    ref_type="invoice",
                    ref_id=invoice.id,
                )
            )

    for bill in unpaid_bills:
        if today < bill.due_date <= horizon:
            actions.append(
                DashboardAction(
                    priority=3,
                    kind="prepare",
                    message=f"Set aside {format_money(bill_amount[bill.id], display)} for {bill.title} due {bill.due_date}",
                    ref_type="bill",
                    ref_id=bill.id,
                )
            )

    if net_outlook < 0:
        actions.append(
            DashboardAction(
                priority=1,
                kind="cash_gap",
                message=f"Projected shortfall of {format_money(abs(net_outlook), display)} in the next 7 days; chase collections or defer bills",
            )
        )

    if not actions:
        actions.append(
            DashboardAction(priority=5, kind="none", message="No urgent cash actions today")
        )

    actions.sort(key=lambda a: a.priority)

    return DashboardToday(
        as_of=today,
        expected_inflows=round(expected_inflows, 2),
        upcoming_bills=round(upcoming_bills, 2),
        overdue_bills=round(overdue_bills, 2),
        net_outlook=round(net_outlook, 2),
        actions=actions,
        display_currency=display,
        fx_last_updated=fx["source_updated_at"] if fx else None,
        fx_stale=fx["stale"] if fx else False,
    )


# ---------- Settings and exchange rates ----------


def _settings_read(db: Session) -> SettingsRead:
    return SettingsRead(
        display_currency=get_display_currency(db),
        supported_currencies=[
            CurrencyInfo(code=code, **CURRENCIES[code]) for code in SUPPORTED_CODES
        ],
    )


@router.get("/settings", response_model=SettingsRead)
def get_settings(db: Session = Depends(get_db)):
    return _settings_read(db)


@router.patch("/settings", response_model=SettingsRead)
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db)):
    set_display_currency(db, payload.display_currency)
    return _settings_read(db)


@router.get("/fx/rates", response_model=FxRatesRead)
def fx_rates(db: Session = Depends(get_db)):
    fx = get_rates(db)
    return FxRatesRead(
        last_updated=fx["source_updated_at"],
        fetched_at=fx["fetched_at"],
        stale=fx["stale"],
        rates={code: fx["rates"][code] for code in SUPPORTED_CODES},
    )

