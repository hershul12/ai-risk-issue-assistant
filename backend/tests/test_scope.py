"""Scope check and category enforcement for /suggest, with the AI mocked (never calls Azure)."""

import pytest

from app.main import OUT_OF_SCOPE_MESSAGE

DRAFT = {
    "standardised_description": "The payments vendor may miss the integration milestone.",
    "suggested_category": "Vendor",
    "suggested_mitigation": "Agree a recovery plan with the vendor.",
    "follow_up_actions": ["Weekly vendor call"],
    "cause": "Too few vendor engineers.",
    "potential_impact": "Go-live slips.",
    "warning_indicators": ["Missed sprint goals"],
    "preventive_actions": ["Add vendor engineers"],
    "corrective_actions": ["Re-plan the release"],
    "contingency_plan": "Keep the legacy system running.",
}
CANTEEN = {"title": "Canteen menu change",
           "description": "The office canteen will serve a new lunch menu with more salads."}
VENDOR = {"title": "Vendor delay",
          "description": "The payments vendor may miss the integration milestone."}


@pytest.fixture
def no_retrieval(monkeypatch):
    """Fail the test if retrieval runs."""
    def boom(*args, **kwargs):
        raise AssertionError("retrieval must not run for out-of-scope text")
    monkeypatch.setattr("app.main.search_similar", boom)
    monkeypatch.setattr("app.main.search_policies", boom)


@pytest.mark.parametrize("scope_reply", ['{"in_scope": false}', '{"in_scope": "false"}',
                                         'Sure: {"in_scope": "No"}'])
def test_out_of_scope_returns_fallback_without_retrieval_or_draft(client, fake_ai, no_retrieval, scope_reply):
    calls = fake_ai(scope_reply=scope_reply, draft_reply=DRAFT)
    res = client.post("/suggest", json=CANTEEN)
    assert res.status_code == 200
    body = res.json()
    assert body["found"] is False
    assert body["message"] == OUT_OF_SCOPE_MESSAGE
    assert body["result"] == {}
    assert body["similar"] == []
    assert body["policies"] == []
    assert body["citation_warnings"] == []
    # Only the scope check ran: no draft call, and it saw only the user's text.
    assert [kind for kind, _ in calls] == ["scope"]
    assert "Similar past risks" not in calls[0][1]
    assert "Extracts from the bank's own policies" not in calls[0][1]


def test_in_scope_behaves_as_before(client, fake_ai):
    calls = fake_ai(scope_reply='{"in_scope": true}', draft_reply=DRAFT)
    res = client.post("/suggest", json=VENDOR)
    assert res.status_code == 200
    body = res.json()
    assert body["found"] is True
    assert body["result"] == DRAFT
    assert isinstance(body["similar"], list)
    assert isinstance(body["policies"], list)
    assert body["citation_warnings"] == []
    assert "message" not in body
    assert [kind for kind, _ in calls] == ["scope", "draft"]


def test_unreadable_scope_reply_does_not_block_a_draft(client, fake_ai):
    calls = fake_ai(scope_reply="I am not sure.", draft_reply=DRAFT)
    body = client.post("/suggest", json=VENDOR).json()
    assert body["found"] is True
    assert [kind for kind, _ in calls] == ["scope", "draft"]


@pytest.mark.parametrize("category", ["Operational", "vendor", "", None, ["Vendor"]])
def test_invalid_category_is_dropped(client, fake_ai, category):
    fake_ai(draft_reply={**DRAFT, "suggested_category": category})
    result = client.post("/suggest", json=VENDOR).json()["result"]
    assert "suggested_category" not in result
    assert result["suggested_mitigation"] == DRAFT["suggested_mitigation"]


def test_valid_category_is_kept(client, fake_ai):
    fake_ai(draft_reply={**DRAFT, "suggested_category": "Compliance"})
    assert client.post("/suggest", json=VENDOR).json()["result"]["suggested_category"] == "Compliance"


def test_scope_check_failure_returns_safe_error(client, monkeypatch, no_retrieval):
    def boom(title, description):
        raise RuntimeError("INTERNAL-DETAIL")
    monkeypatch.setattr("app.main.check_scope", boom)
    res = client.post("/suggest", json=CANTEEN)
    assert res.status_code == 502
    assert "INTERNAL-DETAIL" not in res.text


def test_import_from_text_is_not_scope_gated(client, fake_ai):
    """Import from text keeps its own behaviour: one extraction call, no scope check, and
    entries without a usable title and description are ignored."""
    calls = fake_ai(draft_reply={"items": [
        {"title": "Vendor API docs late", "description": "The gateway vendor has not shared the final API docs.",
         "item_type": "Risk", "category": "Vendor", "suggested_mitigation": "Escalate."},
        {"title": "", "description": "Canteen menu changes on Monday."},
        "not an item",
    ]})
    res = client.post("/extract", json={"text": "Vendor API docs are late. Also the canteen menu changes on Monday."})
    assert res.status_code == 200
    items = res.json()["items"]
    assert [i["title"] for i in items] == ["Vendor API docs late"]
    assert [kind for kind, _ in calls] == ["draft"]
