from datetime import date, timedelta


def _future(days):
    return (date.today() + timedelta(days=days)).isoformat()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_health(client):
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_demo_reset(client):
    response = client.post("/demo/reset")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "reset"
    assert body["invoices"] == 5
    assert body["bills"] == 4


def test_users_create_list_get_and_duplicate(empty_db):
    client = empty_db

    created = client.post("/users", json={"email": "a@example.com"})
    assert created.status_code == 201
    body = created.json()
    assert "id" in body
    assert body["email"] == "a@example.com"
    user_id = body["id"]

    duplicate = client.post("/users", json={"email": "a@example.com"})
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Email already registered"

    listed = client.get("/users")
    assert listed.status_code == 200
    assert "a@example.com" in [u["email"] for u in listed.json()]

    fetched = client.get(f"/users/{user_id}")
    assert fetched.status_code == 200

    assert client.get("/users/999999").status_code == 404
    assert client.post("/users", json={}).status_code == 422


def test_invoice_crud(client):
    created = client.post(
        "/invoices",
        json={"client_name": "Test Client", "amount": 100.0, "due_date": _future(10)},
    )
    assert created.status_code == 201
    invoice = created.json()
    assert invoice["status"] == "pending"
    invoice_id = invoice["id"]

    assert client.get(f"/invoices/{invoice_id}").status_code == 200

    patched = client.patch(f"/invoices/{invoice_id}", json={"status": "paid"})
    assert patched.status_code == 200
    assert patched.json()["status"] == "paid"

    assert client.delete(f"/invoices/{invoice_id}").status_code == 204
    assert client.get(f"/invoices/{invoice_id}").status_code == 404

    assert client.patch(f"/invoices/{invoice_id}", json={"status": "paid"}).status_code == 404
    assert client.delete(f"/invoices/{invoice_id}").status_code == 404


def test_invoice_rejects_non_positive_amount(client):
    response = client.post(
        "/invoices",
        json={"client_name": "Bad", "amount": -1, "due_date": _future(10)},
    )
    assert response.status_code == 422


def test_bill_crud(client):
    created = client.post(
        "/bills",
        json={"title": "Test Vendor", "amount": 50.0, "due_date": _future(10)},
    )
    assert created.status_code == 201
    bill = created.json()
    assert bill["status"] == "unpaid"
    bill_id = bill["id"]

    assert client.get(f"/bills/{bill_id}").status_code == 200

    patched = client.patch(f"/bills/{bill_id}", json={"status": "paid"})
    assert patched.status_code == 200
    assert patched.json()["status"] == "paid"

    assert client.delete(f"/bills/{bill_id}").status_code == 204
    assert client.get(f"/bills/{bill_id}").status_code == 404

    assert client.patch(f"/bills/{bill_id}", json={"status": "paid"}).status_code == 404
    assert client.delete(f"/bills/{bill_id}").status_code == 404


def test_list_invoices_and_bills(client):
    invoices = client.get("/invoices")
    assert invoices.status_code == 200
    assert len(invoices.json()) == 5

    bills = client.get("/bills")
    assert bills.status_code == 200
    assert len(bills.json()) == 4
