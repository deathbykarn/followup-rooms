"""Pydantic models for the ingestion pipeline (transcript + voice upload)."""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

UploadType = Literal["transcript", "voice_memo"]
IngestionState = Literal["queued", "transcribing", "extracting", "done", "failed"]
ErrorCode = Literal[
    "transcription_failed",
    "extraction_failed",
    "storage_failed",
    "unknown",
]


class IngestionJobResponse(BaseModel):
    """Ingestion job row as returned to the operator dashboard."""

    id: str
    client_id: str
    upload_type: UploadType
    original_filename: str
    mime_type: str
    size_bytes: int
    state: IngestionState
    error_message: str | None = None
    error_code: ErrorCode | None = None
    transcript_text: str | None = None
    event_id: str | None = None
    transcription_metadata: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
