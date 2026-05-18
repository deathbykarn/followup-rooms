from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.event import EventCreate, EventResponse


def test_event_create_requires_raw_text_and_source_type():
    e = EventCreate(
        client_id="00000000-0000-0000-0000-000000000001",
        raw_text="Sarah mentioned she wants Marine Parade.",
        source_type="manual_note",
    )
    assert e.raw_text == "Sarah mentioned she wants Marine Parade."
    assert e.source_type == "manual_note"


def test_event_create_rejects_invalid_source_type():
    with pytest.raises(ValidationError):
        EventCreate(
            client_id="00000000-0000-0000-0000-000000000001",
            raw_text="x",
            source_type="invalid_source",
        )


def test_event_response_shape():
    r = EventResponse(
        id="evt-1",
        client_id="cli-1",
        operator_id="op-1",
        source_type="manual_note",
        raw_text="hello",
        created_at=datetime(2026, 5, 18),
    )
    assert r.id == "evt-1"
