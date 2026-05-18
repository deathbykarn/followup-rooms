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


def _fact_row(fact_id="f1", stance="unreviewed"):
    return {
        "id": fact_id,
        "client_id": "00000000-0000-0000-0000-000000000001",
        "type": "property_preference",
        "value": "Marine Parade preferred",
        "confidence_score": 0.9,
        "visibility": "operator_only",
        "provenance": "llm_generated",
        "user_stance": stance,
        "source_event_ids": ["evt-1"],
        "source_spans": [{"event_id": "evt-1", "snippet": "wants Marine Parade"}],
        "superseded_by": None,
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }


def test_list_facts_requires_auth(client):
    response = client.get("/facts?client_id=00000000-0000-0000-0000-000000000001")
    assert response.status_code == 401


def test_list_facts_filters_rejected_and_superseded_by_default(client, monkeypatch):
    _mock_auth(monkeypatch)

    fake_db = MagicMock()
    chain = fake_db.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.order.return_value
    chain.is_.return_value.neq.return_value.execute.return_value = MagicMock(
        data=[_fact_row()]
    )

    with patch("app.api.facts.get_service_client", return_value=fake_db):
        response = client.get(
            "/facts?client_id=00000000-0000-0000-0000-000000000001",
            headers={"Authorization": "Bearer t"},
        )
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_update_stance_rejected_marks_deleted(client, monkeypatch):
    _mock_auth(monkeypatch)
    fake_db = MagicMock()
    existing_row = _fact_row()
    updated_row = {**_fact_row(stance="rejected")}

    fake_db.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data=existing_row
    )
    fake_db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[updated_row]
    )

    with patch("app.api.facts.get_service_client", return_value=fake_db):
        response = client.post(
            "/facts/f1/stance",
            headers={"Authorization": "Bearer t"},
            json={"stance": "rejected"},
        )
    assert response.status_code == 200
    assert response.json()["user_stance"] == "rejected"


def test_update_stance_reframed_requires_value(client, monkeypatch):
    _mock_auth(monkeypatch)
    with patch("app.api.facts.get_service_client", return_value=MagicMock()):
        response = client.post(
            "/facts/f1/stance",
            headers={"Authorization": "Bearer t"},
            json={"stance": "reframed"},
        )
    assert response.status_code == 400


def test_update_stance_returns_404_when_missing(client, monkeypatch):
    _mock_auth(monkeypatch)
    fake_db = MagicMock()
    fake_db.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data=None
    )

    with patch("app.api.facts.get_service_client", return_value=fake_db):
        response = client.post(
            "/facts/nonexistent/stance",
            headers={"Authorization": "Bearer t"},
            json={"stance": "accepted"},
        )
    assert response.status_code == 404
