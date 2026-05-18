from datetime import UTC, datetime
from io import BytesIO
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


def _job_row(**overrides):
    base = {
        "id": "job-1",
        "operator_id": "op-uuid",
        "client_id": "00000000-0000-0000-0000-000000000001",
        "upload_type": "transcript",
        "original_filename": "viewing.txt",
        "mime_type": "text/plain",
        "size_bytes": 42,
        "state": "queued",
        "transcription_metadata": {},
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }
    base.update(overrides)
    return base


def _mock_service_client_for_create():
    db = MagicMock()
    db.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[_job_row()],
    )
    db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[_job_row(storage_path="op-uuid/job-1/viewing.txt")],
    )
    return db


def test_post_upload_requires_auth(client):
    resp = client.post(
        "/uploads",
        files={"file": ("v.txt", b"x", "text/plain")},
        data={"client_id": "00000000-0000-0000-0000-000000000001", "upload_type": "transcript"},
    )
    assert resp.status_code == 401


def test_post_upload_rejects_unsupported_mime(client, monkeypatch):
    _mock_auth(monkeypatch)
    with patch("app.api.uploads.get_service_client", return_value=MagicMock()):
        resp = client.post(
            "/uploads",
            headers={"Authorization": "Bearer t"},
            files={"file": ("v.exe", b"x", "application/x-msdownload")},
            data={"client_id": "00000000-0000-0000-0000-000000000001", "upload_type": "transcript"},
        )
    assert resp.status_code == 415
    assert "Unsupported mime" in resp.json()["detail"]


def test_post_upload_rejects_empty_file(client, monkeypatch):
    _mock_auth(monkeypatch)
    with patch("app.api.uploads.get_service_client", return_value=MagicMock()):
        resp = client.post(
            "/uploads",
            headers={"Authorization": "Bearer t"},
            files={"file": ("v.txt", b"", "text/plain")},
            data={"client_id": "00000000-0000-0000-0000-000000000001", "upload_type": "transcript"},
        )
    assert resp.status_code == 400


def test_post_upload_happy_path_schedules_background_task(client, monkeypatch):
    _mock_auth(monkeypatch)
    db = _mock_service_client_for_create()
    fake_storage = MagicMock()
    fake_storage.upload.return_value = "op-uuid/job-1/viewing.txt"

    with patch("app.api.uploads.get_service_client", return_value=db), \
         patch("app.api.uploads.StorageService", return_value=fake_storage), \
         patch("app.api.uploads._run_worker") as mock_worker:
        resp = client.post(
            "/uploads",
            headers={"Authorization": "Bearer t"},
            files={"file": ("viewing.txt", b"hello world", "text/plain")},
            data={"client_id": "00000000-0000-0000-0000-000000000001", "upload_type": "transcript"},
        )

    assert resp.status_code == 202
    body = resp.json()
    assert body["id"] == "job-1"
    assert body["state"] == "queued"
    fake_storage.upload.assert_called_once()
    # TestClient triggers BackgroundTasks synchronously after response.
    mock_worker.assert_called_once_with("job-1")


def test_post_upload_storage_failure_marks_job_failed(client, monkeypatch):
    _mock_auth(monkeypatch)
    db = _mock_service_client_for_create()
    fake_storage = MagicMock()
    fake_storage.upload.side_effect = RuntimeError("bucket policy denied")

    with patch("app.api.uploads.get_service_client", return_value=db), \
         patch("app.api.uploads.StorageService", return_value=fake_storage):
        resp = client.post(
            "/uploads",
            headers={"Authorization": "Bearer t"},
            files={"file": ("viewing.txt", b"hello", "text/plain")},
            data={"client_id": "00000000-0000-0000-0000-000000000001", "upload_type": "transcript"},
        )
    assert resp.status_code == 502
    assert "Storage upload failed" in resp.json()["detail"]


def test_get_upload_returns_job_for_owner(client, monkeypatch):
    _mock_auth(monkeypatch)
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data=_job_row(state="done", transcript_text="hi", event_id="evt-1"),
    )

    with patch("app.api.uploads.get_service_client", return_value=db):
        resp = client.get("/uploads/job-1", headers={"Authorization": "Bearer t"})
    assert resp.status_code == 200
    assert resp.json()["state"] == "done"


def test_get_upload_404_when_stranger(client, monkeypatch):
    _mock_auth(monkeypatch)
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data=None,
    )
    with patch("app.api.uploads.get_service_client", return_value=db):
        resp = client.get("/uploads/job-1", headers={"Authorization": "Bearer t"})
    assert resp.status_code == 404


def test_list_uploads_returns_jobs_for_client(client, monkeypatch):
    _mock_auth(monkeypatch)
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[_job_row(), _job_row(id="job-2", state="extracting")],
    )

    with patch("app.api.uploads.get_service_client", return_value=db):
        resp = client.get(
            "/uploads?client_id=00000000-0000-0000-0000-000000000001",
            headers={"Authorization": "Bearer t"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert {b["state"] for b in body} == {"queued", "extracting"}
