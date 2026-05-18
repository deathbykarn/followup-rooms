"""
Pending forwards + WhatsApp link API.

POST /whatsapp/link-code   — generate 6-digit code + 30min expiry; returns
                              the FollowRoom WhatsApp number for the
                              dashboard's "send /link CODE to ..." copy.
GET  /whatsapp/link-status — is the current operator's wa_id linked?

GET  /pending-forwards               — list pending (default) + recent for the operator
POST /pending-forwards/{id}/confirm  — operator commits attribution; triggers Plan 2 extraction
POST /pending-forwards/{id}/discard  — operator rejects; no extraction
"""
import logging
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_current_operator_id
from app.core.config import get_settings
from app.core.supabase import get_service_client
from app.models.whatsapp import (
    ConfirmForwardRequest,
    DiscardForwardRequest,
    LinkCodeResponse,
    LinkStatusResponse,
    PendingForwardResponse,
)
from app.services.extraction_pipeline import ExtractionPipeline

router = APIRouter(tags=["whatsapp"])
logger = logging.getLogger(__name__)

LINK_CODE_TTL = timedelta(minutes=30)


def _now() -> datetime:
    return datetime.now(UTC)


# --- /whatsapp/link-code + link-status ---

@router.post("/whatsapp/link-code", response_model=LinkCodeResponse)
async def issue_link_code(
    operator_id: str = Depends(get_current_operator_id),
) -> LinkCodeResponse:
    """
    Generate a fresh 6-digit code, store on the operator's link row
    (upsert), return code + WhatsApp number + instructions.
    """
    settings = get_settings()
    code = f"{secrets.randbelow(1_000_000):06d}"
    expires_at = _now() + LINK_CODE_TTL

    db = get_service_client()
    existing = (
        db.table("operator_whatsapp_links")
        .select("id, wa_id")
        .eq("operator_id", operator_id)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    rows = existing.data or []

    payload = {
        "link_code": code,
        "link_code_expires_at": expires_at.isoformat(),
    }
    if rows:
        # If operator was already linked, this issues a new code that will
        # OVERWRITE the wa_id on next /link CODE — useful for "I changed
        # my phone number" flows. We don't null wa_id here; webhook update
        # will replace it on success.
        db.table("operator_whatsapp_links").update(payload).eq("id", rows[0]["id"]).execute()
    else:
        db.table("operator_whatsapp_links").insert({
            "operator_id": operator_id,
            **payload,
        }).execute()

    return LinkCodeResponse(
        code=code,
        expires_at=expires_at,
        whatsapp_number=settings.followroom_whatsapp_number,
        instructions=(
            f"From your WhatsApp, send the message `/link {code}` to "
            f"{settings.followroom_whatsapp_number}. The code expires in "
            f"30 minutes."
        ),
    )


@router.get("/whatsapp/link-status", response_model=LinkStatusResponse)
async def get_link_status(
    operator_id: str = Depends(get_current_operator_id),
) -> LinkStatusResponse:
    db = get_service_client()
    resp = (
        db.table("operator_whatsapp_links")
        .select("wa_id, linked_at")
        .eq("operator_id", operator_id)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    rows = resp.data or []
    if not rows or not rows[0].get("linked_at"):
        return LinkStatusResponse(is_linked=False, wa_id=None, linked_at=None)
    row = rows[0]
    return LinkStatusResponse(
        is_linked=True,
        wa_id=row["wa_id"],
        linked_at=row["linked_at"],
    )


# --- /pending-forwards ---

def _serialize_pending(row: dict, client_name_map: dict[str, str]) -> PendingForwardResponse:
    return PendingForwardResponse(
        id=row["id"],
        operator_id=row["operator_id"],
        wa_message_id=row["wa_message_id"],
        sender_wa_id=row["sender_wa_id"],
        forwarded_text=row["forwarded_text"],
        caption_text=row.get("caption_text"),
        wa_timestamp=row["wa_timestamp"],
        suggested_client_id=row.get("suggested_client_id"),
        suggested_client_name=client_name_map.get(row.get("suggested_client_id") or ""),
        suggested_confidence=row.get("suggested_confidence"),
        state=row["state"],
        committed_client_id=row.get("committed_client_id"),
        committed_event_id=row.get("committed_event_id"),
        committed_at=row.get("committed_at"),
        discarded_reason=row.get("discarded_reason"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.get("/pending-forwards", response_model=list[PendingForwardResponse])
async def list_pending(
    pending_only: bool = Query(True),
    operator_id: str = Depends(get_current_operator_id),
) -> list[PendingForwardResponse]:
    db = get_service_client()
    query = (
        db.table("pending_forwards")
        .select("*")
        .eq("operator_id", operator_id)
        .order("created_at", desc=True)
        .limit(50)
    )
    if pending_only:
        query = query.eq("state", "pending")
    resp = query.execute()
    rows = resp.data or []

    # Resolve suggested_client_id → client_name in one batched query
    suggested_ids = list({r.get("suggested_client_id") for r in rows if r.get("suggested_client_id")})
    name_map: dict[str, str] = {}
    if suggested_ids:
        clients_resp = (
            db.table("clients")
            .select("id, client_name")
            .in_("id", suggested_ids)
            .execute()
        )
        name_map = {c["id"]: c["client_name"] for c in (clients_resp.data or [])}

    return [_serialize_pending(r, name_map) for r in rows]


def _build_pipeline() -> ExtractionPipeline:
    """Factory — fresh pipeline per request with service-role supabase."""
    return ExtractionPipeline(supabase=get_service_client())


@router.post(
    "/pending-forwards/{forward_id}/confirm",
    status_code=status.HTTP_200_OK,
    response_model=PendingForwardResponse,
)
async def confirm_forward(
    forward_id: str,
    payload: ConfirmForwardRequest,
    operator_id: str = Depends(get_current_operator_id),
) -> PendingForwardResponse:
    db = get_service_client()

    pending = (
        db.table("pending_forwards")
        .select("*")
        .eq("id", forward_id)
        .eq("operator_id", operator_id)
        .maybe_single()
        .execute()
    )
    if not pending or not pending.data:
        raise HTTPException(status_code=404, detail="pending forward not found")
    row = pending.data
    if row["state"] != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"pending forward is already in state '{row['state']}'",
        )

    # Compose the event raw_text: forwarded message + caption context.
    caption = row.get("caption_text") or ""
    raw_text = row["forwarded_text"]
    if caption:
        raw_text = f"{raw_text}\n\n[Operator caption: {caption}]"

    pipeline = _build_pipeline()
    result = pipeline.ingest_and_extract(
        operator_id=operator_id,
        client_id=payload.client_id,
        source_type="whatsapp_forward_shape_x",
        raw_text=raw_text,
    )

    now = _now().isoformat()
    upd = (
        db.table("pending_forwards")
        .update({
            "state": "confirmed",
            "committed_client_id": payload.client_id,
            "committed_event_id": result.event_id,
            "committed_at": now,
        })
        .eq("id", forward_id)
        .execute()
    )
    updated_row = upd.data[0] if upd.data else {**row, "state": "confirmed",
                                                  "committed_client_id": payload.client_id,
                                                  "committed_event_id": result.event_id,
                                                  "committed_at": now}

    # Resolve suggested_client_name + committed name (best-effort)
    name_map: dict[str, str] = {}
    return _serialize_pending(updated_row, name_map)


@router.post(
    "/pending-forwards/{forward_id}/discard",
    status_code=status.HTTP_200_OK,
    response_model=PendingForwardResponse,
)
async def discard_forward(
    forward_id: str,
    payload: DiscardForwardRequest,
    operator_id: str = Depends(get_current_operator_id),
) -> PendingForwardResponse:
    db = get_service_client()

    pending = (
        db.table("pending_forwards")
        .select("*")
        .eq("id", forward_id)
        .eq("operator_id", operator_id)
        .maybe_single()
        .execute()
    )
    if not pending or not pending.data:
        raise HTTPException(status_code=404, detail="pending forward not found")
    if pending.data["state"] != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"pending forward is already in state '{pending.data['state']}'",
        )

    upd = (
        db.table("pending_forwards")
        .update({
            "state": "discarded",
            "discarded_reason": payload.reason,
        })
        .eq("id", forward_id)
        .execute()
    )
    return _serialize_pending(upd.data[0] if upd.data else pending.data, {})
