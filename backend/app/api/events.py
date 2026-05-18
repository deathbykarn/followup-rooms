from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.auth import get_current_operator_id
from app.core.supabase import get_service_client
from app.models.event import EventCreate
from app.services.extraction_pipeline import ExtractionPipeline, PipelineResult

router = APIRouter(prefix="/events", tags=["events"])


class IngestResponse(BaseModel):
    event_id: str
    facts_added: int
    facts_updated: int
    facts_noop: int
    facts_deleted: int
    profile_regenerated: bool


def _build_pipeline() -> ExtractionPipeline:
    """Factory — request-scoped to avoid module-scoped clients."""
    return ExtractionPipeline(supabase=get_service_client())


@router.post("", status_code=status.HTTP_201_CREATED, response_model=IngestResponse)
async def ingest_event(
    payload: EventCreate,
    operator_id: str = Depends(get_current_operator_id),
) -> IngestResponse:
    """
    Phase 2: accepts manual_note events only. Plan 3+ adds transcript
    upload, voice memo upload, WhatsApp ingestion — each may add its own
    upload-side endpoint that funnels into the same pipeline.
    """
    if payload.source_type != "manual_note":
        raise HTTPException(
            status_code=400,
            detail=(
                f"source_type '{payload.source_type}' not supported in Phase 2;"
                " only 'manual_note'"
            ),
        )

    pipeline = _build_pipeline()
    result: PipelineResult = pipeline.ingest_and_extract(
        operator_id=operator_id,
        client_id=payload.client_id,
        source_type=payload.source_type,
        raw_text=payload.raw_text,
    )

    return IngestResponse(
        event_id=result.event_id,
        facts_added=result.facts_added,
        facts_updated=result.facts_updated,
        facts_noop=result.facts_noop,
        facts_deleted=result.facts_deleted,
        profile_regenerated=result.profile_regenerated,
    )
