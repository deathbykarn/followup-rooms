from unittest.mock import MagicMock

import pytest

from app.models.attribution import Attribution
from app.services.store import StoredArtifact, store


def test_store_returns_stored_artifact_with_id():
    fake_supabase = MagicMock()
    fake_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "art-uuid"}]
    )

    attribution = Attribution(surface="web_dashboard")
    result = store(
        supabase=fake_supabase,
        operator_id="op-uuid",
        domain="client:abc",
        artifact_type="event",
        payload={"client_id": "cli-uuid", "source_type": "manual_note", "raw_text": "test"},
        attribution=attribution,
    )

    assert isinstance(result, StoredArtifact)
    assert result.artifact_id == "art-uuid"
    assert result.artifact_type == "event"
    # Verify both inserts happened: artifact + attribution
    assert fake_supabase.table.call_count == 2


def test_store_rejects_invalid_artifact_type():
    fake_supabase = MagicMock()
    attribution = Attribution(surface="web_dashboard")
    with pytest.raises(ValueError, match="invalid artifact_type"):
        store(
            supabase=fake_supabase,
            operator_id="op-uuid",
            domain="client:abc",
            artifact_type="invalid_type",
            payload={},
            attribution=attribution,
        )
