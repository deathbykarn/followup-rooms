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


def test_post_event_returns_401_without_auth(client):
    response = client.post("/events", json={
        "client_id": "00000000-0000-0000-0000-000000000001",
        "source_type": "manual_note",
        "raw_text": "test",
    })
    assert response.status_code == 401


def test_post_event_rejects_invalid_source_type(client, monkeypatch):
    _mock_auth(monkeypatch)
    response = client.post(
        "/events",
        headers={"Authorization": "Bearer t"},
        json={
            "client_id": "00000000-0000-0000-0000-000000000001",
            "source_type": "not_a_type",
            "raw_text": "x",
        },
    )
    assert response.status_code == 422


def test_post_event_rejects_non_manual_note_source_in_phase2(client, monkeypatch):
    _mock_auth(monkeypatch)
    response = client.post(
        "/events",
        headers={"Authorization": "Bearer t"},
        json={
            "client_id": "00000000-0000-0000-0000-000000000001",
            "source_type": "meeting_transcript",
            "raw_text": "x",
        },
    )
    assert response.status_code == 400


def test_post_event_runs_pipeline_and_returns_summary(client, monkeypatch):
    _mock_auth(monkeypatch)

    from app.services.extraction_pipeline import PipelineResult
    fake_pipeline = MagicMock()
    fake_pipeline.ingest_and_extract.return_value = PipelineResult(
        event_id="evt-1",
        facts_added=2,
        facts_updated=0,
        facts_noop=1,
        profile_regenerated=True,
    )

    with patch("app.api.events._build_pipeline", return_value=fake_pipeline):
        response = client.post(
            "/events",
            headers={"Authorization": "Bearer t"},
            json={
                "client_id": "00000000-0000-0000-0000-000000000001",
                "source_type": "manual_note",
                "raw_text": "Sarah wants Marine Parade because parents nearby.",
            },
        )

    assert response.status_code == 201
    body = response.json()
    assert body["event_id"] == "evt-1"
    assert body["facts_added"] == 2
    assert body["facts_noop"] == 1
    assert body["profile_regenerated"] is True
