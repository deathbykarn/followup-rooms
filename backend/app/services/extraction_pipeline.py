"""
ExtractionPipeline — orchestrates the full event → facts → profile flow.

Inputs: operator_id, client_id, source_type, raw_text.
Steps:
  1. Insert event row (stable event_id)
  2. Fetch client context (name + short_context) for the extraction prompt
  3. ExtractionService.extract → ExtractionResult.facts
  4. For each extracted fact:
       a. Fetch active existing facts of same type for this client
       b. MatchingService.decide → ADD / UPDATE / NOOP / DELETE
       c. Apply: insert fact (ADD); insert+mark old superseded_by (UPDATE);
          append source_event_id (NOOP — TODO Phase 2.5); skip (DELETE — TODO)
  5. If any facts changed → regenerate both profile views via ProfileService;
     persist to clients.internal_profile_md + .client_facing_profile_md +
     profile_regenerated_at

Phase 2 uses service-role client for cross-RLS writes (operator_id is
explicit in every payload). Plan 7+ routes through governed store().
"""
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from supabase import Client

from app.ai.extraction import ExtractionService
from app.ai.matching import MatchAction, MatchingService
from app.ai.profile import ProfileService
from app.models.fact import ExtractedFact


@dataclass
class PipelineResult:
    event_id: str
    facts_added: int = 0
    facts_updated: int = 0
    facts_noop: int = 0
    facts_deleted: int = 0
    profile_regenerated: bool = False
    extracted_facts: list[ExtractedFact] = field(default_factory=list)


class ExtractionPipeline:
    """Orchestrate event ingestion + extraction + matching + profile regen."""

    def __init__(
        self,
        supabase: Client,
        extraction: ExtractionService | None = None,
        matching: MatchingService | None = None,
        profile: ProfileService | None = None,
    ) -> None:
        self._db = supabase
        self._extraction = extraction or ExtractionService()
        self._matching = matching or MatchingService()
        self._profile = profile or ProfileService()

    def ingest_and_extract(
        self,
        operator_id: str,
        client_id: str,
        source_type: str,
        raw_text: str,
    ) -> PipelineResult:
        """
        Manual-note style: insert the event row inline, then run extraction.
        Used by POST /events (Plan 2).
        """
        event_insert = (
            self._db.table("events")
            .insert({
                "operator_id": operator_id,
                "client_id": client_id,
                "source_type": source_type,
                "raw_text": raw_text,
            })
            .execute()
        )
        event_id = event_insert.data[0]["id"]
        return self.extract_for_event(
            operator_id=operator_id,
            client_id=client_id,
            event_id=event_id,
            raw_text=raw_text,
        )

    def extract_for_event(
        self,
        operator_id: str,
        client_id: str,
        event_id: str,
        raw_text: str,
        speaker_labels: str | None = None,
    ) -> PipelineResult:
        """
        Run extraction for an event the caller already inserted (Plan 3
        ingestion worker path). `speaker_labels`, when provided, is a
        formatted block prepended to the extraction prompt so Claude knows
        which speaker is the operator vs the client.
        """
        client_row = (
            self._db.table("clients")
            .select("client_name, short_context")
            .eq("id", client_id)
            .maybe_single()
            .execute()
        )
        client_context = (
            f"{client_row.data['client_name']} — {client_row.data['short_context']}"
            if client_row and client_row.data
            else ""
        )

        extraction_result = self._extraction.extract(
            event_id=event_id,
            raw_text=raw_text,
            client_context=client_context,
            speaker_labels=speaker_labels,
        )

        result = PipelineResult(
            event_id=event_id,
            extracted_facts=list(extraction_result.facts),
        )

        for extracted in extraction_result.facts:
            existing = self._fetch_active_facts_of_type(client_id, extracted.type)
            decision = self._matching.decide(extracted, existing)

            if decision.action is MatchAction.ADD:
                self._insert_fact(operator_id, client_id, event_id, extracted)
                result.facts_added += 1
            elif decision.action is MatchAction.UPDATE:
                new_id = self._insert_fact(operator_id, client_id, event_id, extracted)
                self._mark_superseded(decision.supersedes_id, new_id)
                result.facts_updated += 1
            elif decision.action is MatchAction.NOOP:
                # Phase 2.5: append event_id to source_event_ids of matched fact
                result.facts_noop += 1
            elif decision.action is MatchAction.DELETE:
                # Phase 2.5: mark prior fact superseded with deletion_reason
                result.facts_deleted += 1

        if result.facts_added or result.facts_updated or result.facts_deleted:
            self._regenerate_profile(client_id)
            result.profile_regenerated = True

        return result

    # --- helpers ---

    def _fetch_active_facts_of_type(self, client_id: str, fact_type: str) -> list[dict[str, Any]]:
        resp = (
            self._db.table("facts")
            .select("id, type, value, is_deleted, superseded_by")
            .eq("client_id", client_id)
            .eq("type", fact_type)
            .execute()
        )
        return resp.data or []

    def _insert_fact(
        self,
        operator_id: str,
        client_id: str,
        event_id: str,
        extracted: ExtractedFact,
    ) -> str:
        resp = (
            self._db.table("facts")
            .insert({
                "operator_id": operator_id,
                "client_id": client_id,
                "type": extracted.type,
                "value": extracted.value,
                "source_event_ids": [event_id],
                "source_spans": [s.model_dump() for s in extracted.source_spans],
                "confidence_score": extracted.confidence_score,
                "visibility": extracted.visibility,
                "provenance": "llm_generated",
                "user_stance": "unreviewed",
                "generation_metadata": {
                    "model_id": "claude-sonnet-4-6",
                    "prompt_version": "extraction.v1",
                    "generated_at": datetime.now(UTC).isoformat(),
                },
            })
            .execute()
        )
        return resp.data[0]["id"]

    def _mark_superseded(self, old_fact_id: str, new_fact_id: str) -> None:
        (
            self._db.table("facts")
            .update({"superseded_by": new_fact_id})
            .eq("id", old_fact_id)
            .execute()
        )

    def _regenerate_profile(self, client_id: str) -> None:
        # Fetch client info + all active facts
        client_row = (
            self._db.table("clients")
            .select("client_name, short_context")
            .eq("id", client_id)
            .maybe_single()
            .execute()
        )
        facts_resp = (
            self._db.table("facts")
            .select("type, value, visibility, source_event_ids")
            .eq("client_id", client_id)
            .eq("is_deleted", False)
            .is_("superseded_by", "null")
            .execute()
        )
        facts = facts_resp.data or []
        client_name = (client_row.data or {}).get("client_name", "")
        short_context = (client_row.data or {}).get("short_context", "")

        internal = self._profile.regenerate(
            client_name=client_name, short_context=short_context, facts=facts, view="internal",
        )
        client_facing = self._profile.regenerate(
            client_name=client_name, short_context=short_context, facts=facts, view="client_facing",
        )

        (
            self._db.table("clients")
            .update({
                "internal_profile_md": internal.markdown,
                "client_facing_profile_md": client_facing.markdown,
                "profile_regenerated_at": datetime.now(UTC).isoformat(),
            })
            .eq("id", client_id)
            .execute()
        )
