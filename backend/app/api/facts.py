from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_current_operator_id
from app.core.supabase import get_service_client
from app.models.fact import FactResponse, FactStanceUpdate

router = APIRouter(prefix="/facts", tags=["facts"])


@router.get("", response_model=list[FactResponse])
async def list_facts(
    client_id: str = Query(..., description="UUID of the client to list facts for"),
    include_superseded: bool = Query(False),
    include_rejected: bool = Query(False),
    operator_id: str = Depends(get_current_operator_id),
) -> list[FactResponse]:
    db = get_service_client()
    query = (
        db.table("facts")
        .select("*")
        .eq("operator_id", operator_id)
        .eq("client_id", client_id)
        .eq("is_deleted", False)
        .order("created_at", desc=True)
    )
    if not include_superseded:
        query = query.is_("superseded_by", "null")
    if not include_rejected:
        query = query.neq("user_stance", "rejected")
    resp = query.execute()
    return [FactResponse(**row) for row in (resp.data or [])]


@router.post("/{fact_id}/stance", status_code=status.HTTP_200_OK, response_model=FactResponse)
async def update_stance(
    fact_id: str,
    payload: FactStanceUpdate,
    operator_id: str = Depends(get_current_operator_id),
) -> FactResponse:
    if payload.stance == "reframed" and not payload.value:
        raise HTTPException(
            status_code=400,
            detail="stance='reframed' requires a new 'value'",
        )

    db = get_service_client()
    existing = (
        db.table("facts")
        .select("*")
        .eq("id", fact_id)
        .eq("operator_id", operator_id)
        .maybe_single()
        .execute()
    )
    if not existing or not existing.data:
        raise HTTPException(status_code=404, detail="fact not found")

    update_payload: dict = {
        "user_stance": payload.stance,
        "updated_at": datetime.now(UTC).isoformat(),
    }
    if payload.stance in ("rejected",):
        update_payload["is_deleted"] = True
    if payload.stance == "reframed":
        update_payload["value"] = payload.value
        update_payload["provenance"] = "operator_edited"

    updated = (
        db.table("facts")
        .update(update_payload)
        .eq("id", fact_id)
        .execute()
    )
    return FactResponse(**updated.data[0])
