import pytest


def _actions_of_kind(data, kind):
    return [a for a in data["actions"] if a["kind"] == kind]


def test_dashboard_totals(client):
    response = client.get("/dashboard/today")
    assert response.status_code == 200
    data = response.json()
    assert data["expected_inflows"] == pytest.approx(5540.50)
    assert data["upcoming_bills"] == pytest.approx(1929.00)
    assert data["overdue_bills"] == pytest.approx(245.75)
    assert data["net_outlook"] == pytest.approx(3365.75)


def test_dashboard_actions_priority_order(client):
    data = client.get("/dashboard/today").json()
    assert isinstance(data["actions"], list)
    priorities = [a["priority"] for a in data["actions"]]
    assert priorities == sorted(priorities)


def test_dashboard_overdue_invoice_action(client):
    data = client.get("/dashboard/today").json()
    matches = [
        a for a in data["actions"]
        if a["kind"] == "follow_up" and "Maple Street Bakery" in a["message"] and a["priority"] == 1
    ]
    assert matches


def test_dashboard_overdue_bill_action(client):
    data = client.get("/dashboard/today").json()
    matches = [
        a for a in data["actions"]
        if a["kind"] == "pay" and "Electricity" in a["message"] and a["priority"] == 1
    ]
    assert matches


def test_dashboard_action_refs(client):
    data = client.get("/dashboard/today").json()
    follow_ups = [
        a for a in data["actions"]
        if a["kind"] == "follow_up" and "Maple Street Bakery" in a["message"]
    ]
    assert follow_ups
    assert follow_ups[0]["ref_type"] == "invoice"
    assert isinstance(follow_ups[0]["ref_id"], int)

    pays = [
        a for a in data["actions"]
        if a["kind"] == "pay" and "Electricity" in a["message"]
    ]
    assert pays
    assert pays[0]["ref_type"] == "bill"
    assert isinstance(pays[0]["ref_id"], int)


def test_dashboard_collect_actions(client):
    data = client.get("/dashboard/today").json()
    collect_messages = [a["message"] for a in _actions_of_kind(data, "collect")]
    assert any("Riverside Dental" in m for m in collect_messages)
    assert any("Northwind Landscaping" in m for m in collect_messages)
    assert not any("Acme Print Shop" in m for m in collect_messages)


def test_dashboard_cash_gap(client):
    invoices = client.get("/invoices").json()
    for invoice in invoices:
        response = client.patch(f"/invoices/{invoice['id']}", json={"status": "paid"})
        assert response.status_code == 200

    data = client.get("/dashboard/today").json()
    assert data["expected_inflows"] == pytest.approx(0.0)
    assert _actions_of_kind(data, "cash_gap")
    assert data["net_outlook"] < 0


def test_dashboard_empty_state(empty_db):
    data = empty_db.get("/dashboard/today").json()
    assert data["expected_inflows"] == pytest.approx(0.0)
    assert data["upcoming_bills"] == pytest.approx(0.0)
    assert data["net_outlook"] == pytest.approx(0.0)
    assert len(data["actions"]) == 1
    assert data["actions"][0]["kind"] == "none"
    assert data["actions"][0]["priority"] == 5
