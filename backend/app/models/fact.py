from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


FactType = Literal[
    "goal",
    "budget_constraint",
    "timeline_signal",
    "objection",
    "spouse_family_factor",
    "emotional_hesitation",
    "document_request",
    "follow_up_promise",
    "viewing_preference",
    "property_preference",
    "decision_blocker",
    "buying_intent_signal",
    "market_signal",
    "content_opportunity",
]

Visibility = Literal["operator_only", "client_facing_safe", "agency_visible"]
UserStance = Literal[
    "unreviewed", "accepted", "rejected", "reframed", "operator_curated",
]
Provenance = Literal[
    "llm_generated", "operator_curated", "operator_edited", "regenerable", "canonical",
]


class SourceSpan(BaseModel):
    """A verbatim citation: which event, what exact text."""

    event_id: str
    snippet: str = Field(..., min_length=1, max_length=2000)


class ExtractedFact(BaseModel):
    """A single fact emitted by ExtractionService — pre-storage shape."""

    type: FactType
    value: str = Field(..., min_length=1, max_length=2000)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    visibility: Visibility = "operator_only"
    source_spans: list[SourceSpan] = Field(..., min_length=1)


class FactResponse(BaseModel):
    """Fact row as returned to the operator dashboard."""

    id: str
    client_id: str
    type: str
    value: str
    confidence_score: float
    visibility: str
    provenance: str
    user_stance: str
    source_event_ids: list[str]
    source_spans: list[SourceSpan] = Field(default_factory=list)
    superseded_by: str | None = None
    created_at: datetime
    updated_at: datetime


class FactStanceUpdate(BaseModel):
    """Operator override of a fact's stance (accept/reject/edit/reframe)."""

    stance: Literal["accepted", "rejected", "reframed", "operator_curated"]
    value: str | None = Field(
        default=None,
        description="Required when stance='reframed'; operator's rewritten fact value.",
        max_length=2000,
    )
