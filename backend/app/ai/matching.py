"""
MatchingService — ADD/UPDATE/DELETE/NOOP decision per extracted fact.

Phase 2 (this plan): naive string-equality match within the same type.
Sufficient for the ADD/UPDATE/NOOP distinction. DELETE detection (new
event explicitly negates an old fact) is deferred to Plan 2.5 once
real operator usage shows the need.

Phase 3 (Zettel link-graph) replaces string equality with semantic
similarity over the link-graph + Haiku-as-judge for ambiguous cases.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.models.fact import ExtractedFact


class MatchAction(str, Enum):
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"
    NOOP = "noop"


@dataclass(frozen=True)
class MatchDecision:
    action: MatchAction
    supersedes_id: str | None = None  # set when UPDATE
    matches_id: str | None = None  # set when NOOP (existing fact already covers it)


def _normalize(s: str) -> str:
    """Lowercase, collapse whitespace — for naive equality match."""
    return " ".join(s.lower().split())


class MatchingService:
    """Decides what to do with an extracted fact given the current KB state."""

    def decide(
        self,
        extracted: ExtractedFact,
        existing_facts: list[dict[str, Any]],
    ) -> MatchDecision:
        """
        Returns a MatchDecision.

        existing_facts is a list of dicts with at least:
          id, type, value, is_deleted, superseded_by

        Only ACTIVE facts (not deleted, not superseded) are considered.
        """
        active = [
            f for f in existing_facts
            if not f.get("is_deleted") and f.get("superseded_by") is None
        ]
        same_type = [f for f in active if f["type"] == extracted.type]

        norm_new = _normalize(extracted.value)

        # NOOP: identical value already exists
        for f in same_type:
            if _normalize(f["value"]) == norm_new:
                return MatchDecision(action=MatchAction.NOOP, matches_id=f["id"])

        # UPDATE: same type, different value (Phase 2 naive: just the first match)
        if same_type:
            return MatchDecision(
                action=MatchAction.UPDATE,
                supersedes_id=same_type[0]["id"],
            )

        # ADD: nothing matches
        return MatchDecision(action=MatchAction.ADD)
