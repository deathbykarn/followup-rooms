"""
Single governed write path for durable memory.

Phase 1: thin wrapper over Supabase insert + attribution log.
Phase 3: same signature; implementation expands to add scoping,
dedup, redaction, multi-agent attribution checks per Hivemind doc §8.3.
"""
from dataclasses import dataclass
from typing import Any

from supabase import Client

from app.models.attribution import Attribution


_VALID_ARTIFACT_TYPES = {
    "event", "fact", "room_attachment", "room_update_draft",
    "client", "operator",
}

# Map artifact_type → Supabase table name
_TABLE_FOR_ARTIFACT: dict[str, str] = {
    "event": "events",
    "fact": "facts",
    "room_attachment": "room_attachments",
    "room_update_draft": "room_update_drafts",  # added in Plan 7
    "client": "clients",
    "operator": "operators",
}


@dataclass(frozen=True)
class StoredArtifact:
    artifact_id: str
    artifact_type: str
    domain: str


def store(
    supabase: Client,
    operator_id: str,
    domain: str,
    artifact_type: str,
    payload: dict[str, Any],
    attribution: Attribution,
) -> StoredArtifact:
    """
    Insert an artifact + record attribution. Phase 1 implementation.

    Args:
      supabase: request-scoped Supabase client
      operator_id: the operator owning this write
      domain: scope identifier (e.g., 'client:<slug>'); Phase 3 uses this for federation
      artifact_type: one of ArtifactType literals
      payload: row data for the artifact table (must include operator_id)
      attribution: who/what/when/why metadata

    Returns:
      StoredArtifact with the inserted ID.

    Raises:
      ValueError: invalid artifact_type
    """
    if artifact_type not in _VALID_ARTIFACT_TYPES:
        raise ValueError(f"invalid artifact_type: {artifact_type}")

    table_name = _TABLE_FOR_ARTIFACT[artifact_type]

    # Ensure operator_id is in the payload (enforces RLS at write time)
    payload_with_op = {**payload, "operator_id": operator_id}

    # Insert the artifact
    artifact_response = (
        supabase.table(table_name)
        .insert(payload_with_op)
        .execute()
    )
    artifact_id = artifact_response.data[0]["id"]

    # Insert the attribution record
    supabase.table("attributions").insert({
        "operator_id": operator_id,
        "artifact_id": artifact_id,
        "artifact_type": artifact_type,
        "agent_id": attribution.agent_id,
        "surface": attribution.surface,
        "session_id": attribution.session_id,
        "turn_index": attribution.turn_index,
        "confidence": attribution.confidence,
        "reason": attribution.reason,
        "timestamp": attribution.timestamp.isoformat(),
    }).execute()

    return StoredArtifact(
        artifact_id=artifact_id,
        artifact_type=artifact_type,
        domain=domain,
    )
