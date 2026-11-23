from datetime import date, timedelta

NEW_ITEM = {
    "title": "Core banking vendor delay",
    "description": "Vendor may miss the integration milestone.",
    "item_type": "Risk",
    "category": "Vendor",
    "probability": 4,
    "impact": 5,
    "owner": "Alex",
    "due_date": (date.today() + timedelta(days=30)).isoformat(),
}


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_list_items(client):
    res = client.get("/items")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_dashboard_summary(client):
    assert client.get("/dashboard/summary").status_code == 200


def test_create_item_scores_and_logs(client):
    res = client.post("/items", json=NEW_ITEM, headers={"X-Role": "Project Manager"})
    assert res.status_code == 201
    item = res.json()
    assert item["score"] == 20
    assert item["priority"] == "Critical"
    assert item["status"] == "Open"

    audit = client.get(f"/items/{item['id']}/audit")
    assert audit.status_code == 200
    assert len(audit.json()) >= 1


def test_only_project_manager_can_create(client):
    res = client.post("/items", json=NEW_ITEM, headers={"X-Role": "Risk Owner"})
    assert res.status_code == 403


def test_invalid_role_rejected(client):
    res = client.post("/items", json=NEW_ITEM, headers={"X-Role": "Intern"})
    assert res.status_code == 400


def test_cannot_close_without_review(client):
    item = client.post(
        "/items", json=NEW_ITEM, headers={"X-Role": "Project Manager"}
    ).json()
    res = client.patch(
        f"/items/{item['id']}/status",
        json={"status": "Closed"},
        headers={"X-Role": "Programme Lead"},
    )
    assert res.status_code == 400


def test_ai_errors_do_not_leak_details(client, monkeypatch):
    def boom(_text):
        raise RuntimeError("INTERNAL-DETAIL-SHOULD-NOT-LEAK")

    monkeypatch.setattr("app.main.extract_items", boom)
    res = client.post("/extract", json={"text": "The vendor has missed the payments go-live date."})
    assert res.status_code == 502
    assert "INTERNAL-DETAIL" not in res.text


def test_missing_item_returns_404(client):
    assert client.get("/items/999999").status_code == 404
