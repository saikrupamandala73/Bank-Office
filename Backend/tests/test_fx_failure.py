import app.fx as fx


def _offline():
    raise RuntimeError("offline")


def test_dashboard_503_when_rates_unavailable_in_inr(client, monkeypatch):
    monkeypatch.setattr(fx, "fetch_remote_rates", _offline)
    response = client.patch("/settings", json={"display_currency": "INR"})
    assert response.status_code == 200

    response = client.get("/dashboard/today")
    assert response.status_code == 503


def test_invoices_keep_original_amounts_when_rates_unavailable(client, monkeypatch):
    monkeypatch.setattr(fx, "fetch_remote_rates", _offline)
    assert client.patch("/settings", json={"display_currency": "INR"}).status_code == 200

    response = client.get("/invoices")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 5
    for item in items:
        assert item["amount_display"] is None
        assert item["display_currency"] == "INR"

    maple = [i for i in items if i["client_name"] == "Maple Street Bakery"]
    assert maple
    assert maple[0]["currency"] == "USD"
    assert maple[0]["amount"] == 850.5


def test_bills_keep_original_amounts_when_rates_unavailable(client, monkeypatch):
    monkeypatch.setattr(fx, "fetch_remote_rates", _offline)
    assert client.patch("/settings", json={"display_currency": "INR"}).status_code == 200

    response = client.get("/bills")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 4
    for item in items:
        assert item["amount_display"] is None

    rent = [b for b in items if b["title"] == "Office rent"]
    assert rent
    assert rent[0]["currency"] == "USD"
    assert rent[0]["amount"] == 1800.0


def test_settings_persist_when_rates_unavailable(client, monkeypatch):
    monkeypatch.setattr(fx, "fetch_remote_rates", _offline)
    assert client.patch("/settings", json={"display_currency": "INR"}).status_code == 200

    response = client.get("/settings")
    assert response.status_code == 200
    assert response.json()["display_currency"] == "INR"
