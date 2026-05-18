from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.ai.profile import ProfileService
from app.core.auth import get_current_operator_id
from app.core.supabase import get_service_client

router = APIRouter(prefix="/clients", tags=["profile"])


class ProfileResponse(BaseModel):
    client_id: str
    view: Literal["internal", "client_facing"]
    markdown: str
    profile_regenerated_at: datetime | None


@router.get("/{client_id}/profile", response_model=ProfileResponse)
async def get_profile(
    client_id: str,
    view: Literal["internal", "client_facing"] = Query("internal"),
    operator_id: str = Depends(get_current_operator_id),
) -> ProfileResponse:
    db = get_service_client()
    resp = (
        db.table("clients")
        .select("id, internal_profile_md, client_facing_profile_md, profile_regenerated_at")
        .eq("id", client_id)
        .eq("operator_id", operator_id)
        .maybe_single()
        .execute()
    )
    if not resp or not resp.data:
        raise HTTPException(status_code=404, detail="client not found")

    column = "internal_profile_md" if view == "internal" else "client_facing_profile_md"
    markdown = resp.data.get(column) or ""
    return ProfileResponse(
        client_id=client_id,
        view=view,
        markdown=markdown,
        profile_regenerated_at=resp.data.get("profile_regenerated_at"),
    )


class RegenerateResponse(BaseModel):
    client_id: str
    profile_regenerated_at: datetime
    internal_chars: int
    client_facing_chars: int


def _build_profile_service() -> ProfileService:
    return ProfileService()


@router.post(
    "/{client_id}/profile/regenerate",
    status_code=status.HTTP_200_OK,
    response_model=RegenerateResponse,
)
async def regenerate_profile(
    client_id: str,
    operator_id: str = Depends(get_current_operator_id),
) -> RegenerateResponse:
    db = get_service_client()

    client_row = (
        db.table("clients")
        .select("client_name, short_context")
        .eq("id", client_id)
        .eq("operator_id", operator_id)
        .maybe_single()
        .execute()
    )
    if not client_row or not client_row.data:
        raise HTTPException(status_code=404, detail="client not found")

    facts_resp = (
        db.table("facts")
        .select("type, value, visibility, source_event_ids")
        .eq("client_id", client_id)
        .eq("operator_id", operator_id)
        .eq("is_deleted", False)
        .is_("superseded_by", "null")
        .execute()
    )
    facts = facts_resp.data or []

    service = _build_profile_service()
    internal = service.regenerate(
        client_name=client_row.data["client_name"],
        short_context=client_row.data["short_context"],
        facts=facts,
        view="internal",
    )
    client_facing = service.regenerate(
        client_name=client_row.data["client_name"],
        short_context=client_row.data["short_context"],
        facts=facts,
        view="client_facing",
    )
    regenerated_at = datetime.now(UTC)

    (
        db.table("clients")
        .update({
            "internal_profile_md": internal.markdown,
            "client_facing_profile_md": client_facing.markdown,
            "profile_regenerated_at": regenerated_at.isoformat(),
        })
        .eq("id", client_id)
        .execute()
    )

    return RegenerateResponse(
        client_id=client_id,
        profile_regenerated_at=regenerated_at,
        internal_chars=len(internal.markdown),
        client_facing_chars=len(client_facing.markdown),
    )
