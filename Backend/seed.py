import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from datetime import date, timedelta

from app.db import Base, SessionLocal, engine
from app.models import Bill, Invoice


def reset_and_seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    today = date.today()

    invoices = [
        Invoice(client_name="Harbor Coffee Co.", amount=1200.00, due_date=today - timedelta(days=20), status="paid"),
        Invoice(client_name="Maple Street Bakery", amount=850.50, due_date=today - timedelta(days=3), status="overdue"),
        Invoice(client_name="Riverside Dental", amount=2300.00, due_date=today + timedelta(days=2), status="pending"),
        Invoice(client_name="Northwind Landscaping", amount=1750.00, due_date=today + timedelta(days=5), status="pending"),
        Invoice(client_name="Acme Print Shop", amount=640.00, due_date=today + timedelta(days=25), status="pending"),
    ]

    bills = [
        Bill(title="Office rent", amount=1800.00, due_date=today + timedelta(days=1), status="unpaid"),
        Bill(title="Electricity - City Power", amount=245.75, due_date=today - timedelta(days=1), status="unpaid"),
        Bill(title="Payroll software", amount=129.00, due_date=today + timedelta(days=4), status="unpaid"),
        Bill(title="Supplies - Paper & Ink Co.", amount=312.40, due_date=today - timedelta(days=15), status="paid"),
    ]

    db = SessionLocal()
    try:
        db.add_all(invoices)
        db.add_all(bills)
        db.commit()
        return {"invoices": len(invoices), "bills": len(bills)}
    finally:
        db.close()


if __name__ == "__main__":
    counts = reset_and_seed()
    print("Seeded demo data:", counts)
