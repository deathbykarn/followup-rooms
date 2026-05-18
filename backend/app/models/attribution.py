from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


Surface = Literal[
    "web_dashboard", "whatsapp_webhook", "voice_upload",
    "file_drop", "manual_note", "system_cron",
]


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Attribution(BaseModel):
    """Attribution metadata for every write to durable memory (§8.2)."""

    agent_id: str = Field(default="operator")
    surface: Surface
    session_id: str | None = None
    turn_index: int | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reason: str | None = None
    timestamp: datetime = Field(default_factory=_utcnow)
