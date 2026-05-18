from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.ingestion import IngestionJobResponse


def _base() -> dict:
    now = datetime.now(UTC)
    return {
        "id": "j1",
        "client_id": "c1",
        "upload_type": "transcript",
        "original_filename": "viewing.txt",
        "mime_type": "text/plain",
        "size_bytes": 1024,
        "state": "queued",
        "created_at": now,
        "updated_at": now,
    }


def test_minimal_required_fields_validate():
    job = IngestionJobResponse(**_base())
    assert job.state == "queued"
    assert job.transcript_text is None
    assert job.transcription_metadata == {}


def test_rejects_bogus_state():
    payload = _base() | {"state": "not_a_state"}
    with pytest.raises(ValidationError):
        IngestionJobResponse(**payload)


def test_rejects_bogus_upload_type():
    payload = _base() | {"upload_type": "screenshot"}
    with pytest.raises(ValidationError):
        IngestionJobResponse(**payload)


def test_optional_fields_round_trip():
    payload = _base() | {
        "state": "done",
        "transcript_text": "Hi Sarah, just confirming the viewing.",
        "event_id": "e1",
        "transcription_metadata": {
            "provider": "assemblyai",
            "duration_seconds": 1830,
            "speaker_count": 2,
        },
        "started_at": datetime.now(UTC),
        "completed_at": datetime.now(UTC),
    }
    job = IngestionJobResponse(**payload)
    assert job.transcript_text is not None
    assert job.transcription_metadata["provider"] == "assemblyai"
    assert job.event_id == "e1"


def test_rejects_bogus_error_code():
    payload = _base() | {"state": "failed", "error_code": "made_up"}
    with pytest.raises(ValidationError):
        IngestionJobResponse(**payload)
