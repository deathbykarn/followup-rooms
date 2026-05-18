from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def _mock_auth(monkeypatch, operator_id="op-uuid"):
    fake_user = MagicMock()
    fake_user.id = operator_id

    def fake_get_anon_client():
        c = MagicMock()
        c.auth.get_user.return_value = MagicMock(user=fake_user)
        return c

    monkeypatch.setattr("app.core.auth.get_anon_client", fake_get_anon_client)


def _pending_row(**overrides):
    now = datetime.now(UTC).isoformat()
    base = {
        "id": "p1",
        "operator_id": "op-uuid",
        "wa_message_id": "wamid.abc",
        "sender_wa_id": "6591234567",
        "forwarded_text": "I want Marine Parade this weekend",
        "caption_text": "Sarah",
        "wa_timestamp": now,
        "suggested_client_id": None,
        "suggested_confidence": None,
        "state": "pending",
        "committed_client_id": None,
        "committed_event_id": None,
        "committed_at": None,
        "discarded_reason": None,
        "created_at": now,
        "updated_at": now,
    }
    base.update(overrides)
    return base


# --- /whatsapp/link-code + link-status ---

def test_link_code_requires_auth(client):
    resp = client.post("/whatsapp/link-code")
    assert resp.status_code == 401


def test_link_code_issues_6_digit_code(client, monkeypatch):
    _mock_auth(monkeypatch)
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[]
    )
    db.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[])

    with patch("app.api.pending_forwards.get_service_client", return_value=db):
        resp = client.post(
            "/whatsapp/link-code",
            headers={"Authorization": "Bearer t"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["code"]) == 6
    assert body["code"].isdigit()
    assert "+" in body["whatsapp_number"]
    assert "instructions" in body
    assert body["code"] in body["instructions"]


def test_link_status_returns_unlinked_when_no_row(client, monkeypatch):
    _mock_auth(monkeypatch)
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[]
    )
    with patch("app.api.pending_forwards.get_service_client", return_value=db):
        resp = client.get(
            "/whatsapp/link-status",
            headers={"Authorization": "Bearer t"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_linked"] is False


def test_link_status_returns_linked_when_linked_at_set(client, monkeypatch):
    _mock_auth(monkeypatch)
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[{"wa_id": "6591234567", "linked_at": datetime.now(UTC).isoformat()}]
    )
    with patch("app.api.pending_forwards.get_service_client", return_value=db):
        resp = client.get(
            "/whatsapp/link-status",
            headers={"Authorization": "Bearer t"},
        )
    body = resp.json()
    assert body["is_linked"] is True
    assert body["wa_id"] == "6591234567"


# --- /pending-forwards ---

def test_list_pending_returns_operator_scoped_pending(client, monkeypatch):
    _mock_auth(monkeypatch)
    db = MagicMock()
    rows = [_pending_row(), _pending_row(id="p2", suggested_client_id="c1")]
    db.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.eq.return_value.execute.return_value = MagicMock(
        data=rows
    )
    # Resolve suggested client names
    db.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(
        data=[{"id": "c1", "client_name": "Sarah Tan"}]
    )

    with patch("app.api.pending_forwards.get_service_client", return_value=db):
        resp = client.get(
            "/pending-forwards",
            headers={"Authorization": "Bearer t"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    p2 = next(p for p in body if p["id"] == "p2")
    assert p2["suggested_client_name"] == "Sarah Tan"


def test_confirm_pending_404_for_strangers_pending(client, monkeypatch):
    _mock_auth(monkeypatch)
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data=None
    )
    with patch("app.api.pending_forwards.get_service_client", return_value=db):
        resp = client.post(
            "/pending-forwards/p1/confirm",
            headers={"Authorization": "Bearer t"},
            json={"client_id": "00000000-0000-0000-0000-000000000001"},
        )
    assert resp.status_code == 404


def test_confirm_pending_409_when_already_confirmed(client, monkeypatch):
    _mock_auth(monkeypatch)
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data=_pending_row(state="confirmed")
    )
    with patch("app.api.pending_forwards.get_service_client", return_value=db):
        resp = client.post(
            "/pending-forwards/p1/confirm",
            headers={"Authorization": "Bearer t"},
            json={"client_id": "00000000-0000-0000-0000-000000000001"},
        )
    assert resp.status_code == 409


def test_confirm_pending_runs_extraction_and_marks_confirmed(client, monkeypatch):
    _mock_auth(monkeypatch)
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data=_pending_row()
    )
    db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[_pending_row(state="confirmed", committed_event_id="evt-1",
                           committed_client_id="cli-1",
                           committed_at=datetime.now(UTC).isoformat())]
    )

    from app.services.extraction_pipeline import PipelineResult
    fake_pipeline = MagicMock()
    fake_pipeline.ingest_and_extract.return_value = PipelineResult(
        event_id="evt-1", facts_added=2, profile_regenerated=True,
    )

    with patch("app.api.pending_forwards.get_service_client", return_value=db), \
         patch("app.api.pending_forwards._build_pipeline", return_value=fake_pipeline):
        resp = client.post(
            "/pending-forwards/p1/confirm",
            headers={"Authorization": "Bearer t"},
            json={"client_id": "00000000-0000-0000-0000-000000000001"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "confirmed"
    assert body["committed_event_id"] == "evt-1"
    # extraction was called with whatsapp source_type + combined raw_text
    _, kwargs = fake_pipeline.ingest_and_extract.call_args
    assert kwargs["source_type"] == "whatsapp_forward_shape_x"
    assert "Marine Parade" in kwargs["raw_text"]
    assert "Operator caption" in kwargs["raw_text"]  # caption was inlined


def test_discard_pending_marks_discarded(client, monkeypatch):
    _mock_auth(monkeypatch)
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data=_pending_row()
    )
    db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[_pending_row(state="discarded", discarded_reason="not a real client")]
    )

    with patch("app.api.pending_forwards.get_service_client", return_value=db):
        resp = client.post(
            "/pending-forwards/p1/discard",
            headers={"Authorization": "Bearer t"},
            json={"reason": "not a real client"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "discarded"
    assert body["discarded_reason"] == "not a real client"
