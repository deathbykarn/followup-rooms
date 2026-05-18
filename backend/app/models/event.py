from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SourceType = Literal[
    "meeting_transcript",
    "voice_memo",
    "whatsapp_forward_shapeX",
    "whatsapp_coexistence",
    "manual_note",
    "file_drop",
]


class EventCreate(BaseModel):
    """Operator-submitted event for ingestion (Plan 2: manual_note only)."""

    client_id: str = Field(..., description="UUID of the client this event belongs to")
    source_type: SourceType
    raw_text: str = Field(..., min_length=1, max_length=50000)


class EventResponse(BaseModel):
    id: str
    client_id: str
    operator_id: str
    source_type: str
    raw_text: str
    created_at: datetime
