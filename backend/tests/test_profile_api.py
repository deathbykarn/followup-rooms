from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.ai.profile import ProfileResult
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


def test_get_profile_returns_internal_markdown_by_default(client, monkeypatch):
    _mock_auth(monkeypatch)
    fake_db = MagicMock()
    now = datetime.now(UTC).isoformat()
    fake_db.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data={
            "id": "cli-1",
            "internal_profile_md": "## Identity\nSarah",
            "client_facing_profile_md": "## Snapshot\nSarah",
            "profile_regenerated_at": now,
        }
    )

    with patch("app.api.profile.get_service_client", return_value=fake_db):
        response = client.get(
            "/clients/cli-1/profile",
            headers={"Authorization": "Bearer t"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["view"] == "internal"
    assert body["markdown"] == "## Identity\nSarah"


def test_get_profile_returns_client_facing_when_requested(client, monkeypatch):
    _mock_auth(monkeypatch)
    fake_db = MagicMock()
    fake_db.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data={
            "id": "cli-1",
            "internal_profile_md": "## Identity\nSarah",
            "client_facing_profile_md": "## Snapshot\nSarah",
            "profile_regenerated_at": None,
        }
    )

    with patch("app.api.profile.get_service_client", return_value=fake_db):
        response = client.get(
            "/clients/cli-1/profile?view=client_facing",
            headers={"Authorization": "Bearer t"},
        )
    assert response.status_code == 200
    assert response.json()["markdown"] == "## Snapshot\nSarah"


def test_get_profile_returns_404_when_missing(client, monkeypatch):
    _mock_auth(monkeypatch)
    fake_db = MagicMock()
    fake_db.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data=None
    )

    with patch("app.api.profile.get_service_client", return_value=fake_db):
        response = client.get(
            "/clients/missing/profile",
            headers={"Authorization": "Bearer t"},
        )
    assert response.status_code == 404


def test_regenerate_profile_calls_service_twice_and_persists(client, monkeypatch):
    _mock_auth(monkeypatch)
    fake_db = MagicMock()
    fake_db.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data={"client_name": "Sarah", "short_context": "HDB upgrade"}
    )
    fake_db.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.is_.return_value.execute.return_value = MagicMock(
        data=[]
    )

    fake_service = MagicMock()
    fake_service.regenerate.return_value = ProfileResult(markdown="## Identity\nSarah")

    with patch("app.api.profile.get_service_client", return_value=fake_db), \
         patch("app.api.profile._build_profile_service", return_value=fake_service):
        response = client.post(
            "/clients/cli-1/profile/regenerate",
            headers={"Authorization": "Bearer t"},
        )

    assert response.status_code == 200
    assert fake_service.regenerate.call_count == 2
    body = response.json()
    assert body["internal_chars"] > 0
    assert body["client_facing_chars"] > 0
