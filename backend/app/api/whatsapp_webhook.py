"""
WhatsApp webhook endpoints — Meta's `messages` field receiver.

GET  /whatsapp/webhook  — Meta verification handshake (subscribe + token)
POST /whatsapp/webhook  — signed inbound delivery

Both endpoints handle anonymous requests (Meta is the caller); auth is via
HMAC signature for POST, verify_token for GET. No FastAPI Depends() on
get_current_operator_id here.

After accepting a payload, the POST handler schedules a BackgroundTask that
runs ClientMatcher against any new pending_forwards rows so the dashboard
sees the suggestion populated within seconds — without making Meta wait on
the LLM call.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.supabase import get_service_client
from app.models.whatsapp import WhatsAppWebhookPayload
from app.services.client_matcher import ClientMatcher
from app.services.whatsapp_webhook import WebhookService

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])
logger = logging.getLogger(__name__)


def _build_webhook_service() -> WebhookService:
    """Factory — request-scoped service-role client."""
    settings = get_settings()
    return WebhookService(
        supabase=get_service_client(),
        app_secret=settings.meta_whatsapp_app_secret,
    )


def _run_client_matcher_for_recent_pending() -> None:
    """
    BackgroundTask body: scans for recently-inserted pending_forwards
    rows that have no suggested_client_id yet, runs ClientMatcher per
    operator, persists suggestion + confidence.

    Bounds the work to the last 60s so we don't re-scan history on
    every webhook (most webhooks deliver exactly one new pending row).
    """
    from datetime import UTC, datetime, timedelta

    db = get_service_client()
    cutoff = (datetime.now(UTC) - timedelta(seconds=60)).isoformat()
    resp = (
        db.table("pending_forwards")
        .select("id, operator_id, caption_text, forwarded_text")
        .is_("suggested_client_id", "null")
        .eq("state", "pending")
        .gte("created_at", cutoff)
        .execute()
    )
    rows = resp.data or []
    if not rows:
        return

    matcher = ClientMatcher(supabase=db)
    for row in rows:
        try:
            suggestion = matcher.suggest(
                operator_id=row["operator_id"],
                caption_text=row.get("caption_text") or "",
                forwarded_text=row.get("forwarded_text") or "",
            )
        except Exception:
            logger.exception("ClientMatcher failed for pending_forward=%s", row["id"])
            continue

        if suggestion.client_id:
            db.table("pending_forwards").update({
                "suggested_client_id": suggestion.client_id,
                "suggested_confidence": suggestion.confidence,
            }).eq("id", row["id"]).execute()


@router.get("/webhook")
async def verify(
    hub_mode: Annotated[str, Query(alias="hub.mode")] = "",
    hub_verify_token: Annotated[str, Query(alias="hub.verify_token")] = "",
    hub_challenge: Annotated[str, Query(alias="hub.challenge")] = "",
) -> PlainTextResponse:
    """
    Meta's webhook verification handshake. When you set the callback URL in
    the Meta dashboard, Meta calls this endpoint with hub.mode=subscribe +
    hub.verify_token=<the token you configured>. We must echo back the
    hub.challenge value as plain text to confirm.
    """
    settings = get_settings()
    if hub_mode != "subscribe" or hub_verify_token != settings.meta_whatsapp_verify_token:
        raise HTTPException(status_code=403, detail="verification failed")
    return PlainTextResponse(hub_challenge)


@router.post("/webhook", status_code=200)
async def receive(
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """
    Meta inbound message delivery. We:
    1. Read the raw body ONCE (needed for both signature verify + parse).
    2. Verify the X-Hub-Signature-256 HMAC. Reject 401 on mismatch.
    3. Parse the payload; tolerate non-message envelopes by ignoring.
    4. Hand the payload to WebhookService for dedup / link / forward /
       caption pairing.
    5. Schedule the ClientMatcher BackgroundTask to fill suggestions.
    6. Return 200 ALWAYS so Meta doesn't retry — we've dedupe-keyed
       on wa_message_id at the DB layer.
    """
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    svc = _build_webhook_service()
    if not svc.verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="invalid signature")

    try:
        payload = WhatsAppWebhookPayload.model_validate_json(body)
    except ValidationError:
        # Meta sends non-message events too (delivery / read receipts /
        # status updates). Acknowledge 200 so they don't retry.
        logger.info("non-message webhook event; ignoring")
        return {"status": "ok"}

    try:
        result = svc.handle_payload(payload)
        logger.info(
            "webhook processed: forwards=%d captions=%d links=%d dup=%d unlinked=%d",
            result.forwards_inserted, result.captions_paired,
            result.links_completed, result.duplicates_skipped,
            result.unlinked_skipped,
        )
    except Exception:
        logger.exception("WebhookService.handle_payload failed")
        # Still return 200 — the failure is logged and we don't want Meta
        # to spam retries. Dedupe key protects future retries from dupes.
        return {"status": "ok"}

    background_tasks.add_task(_run_client_matcher_for_recent_pending)
    return {"status": "ok"}
