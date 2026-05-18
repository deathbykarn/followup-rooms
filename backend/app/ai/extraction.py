"""
ExtractionService — event → typed facts with mandatory source spans.

Uses AgentDispatcher with LogicalRole.EXTRACTOR (Sonnet 4.6) and the
extraction prompt template. Returns an ExtractionResult containing
zero-or-more ExtractedFact instances.
"""
from pydantic import BaseModel, Field

from app.ai.dispatcher import AgentDispatcher, LogicalRole
from app.ai.prompts.extraction import EXTRACTION_SYSTEM, build_extraction_prompt
from app.models.fact import ExtractedFact


class ExtractionResult(BaseModel):
    """Structured output schema for the extractor model."""

    facts: list[ExtractedFact] = Field(default_factory=list)


class ExtractionService:
    """Extracts typed facts from a single event's raw_text."""

    def __init__(self, dispatcher: AgentDispatcher | None = None) -> None:
        self._dispatcher = dispatcher or AgentDispatcher()

    def extract(
        self,
        event_id: str,
        raw_text: str,
        client_context: str,
    ) -> ExtractionResult:
        user_prompt = build_extraction_prompt(
            event_id=event_id,
            raw_text=raw_text,
            client_context=client_context,
        )
        return self._dispatcher.structured_dispatch(
            role=LogicalRole.EXTRACTOR,
            system=EXTRACTION_SYSTEM,
            user_prompt=user_prompt,
            response_model=ExtractionResult,
        )
