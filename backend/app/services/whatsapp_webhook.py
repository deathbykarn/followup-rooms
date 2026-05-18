"""
WhatsApp WebhookService — verifies inbound Meta webhooks and walks the
attribution pipeline.

Responsibilities:
1. verify_signature() — HMAC-SHA256 of raw request body using app secret;
   compared against X-Hub-Signature-256 header. Rejects on mismatch.
2. handle_payload() — for each message in entry[].changes[].value.messages[]:
     a. dedupe by wa_message_id (pending_forwards.wa_message_id UNIQUE)
     b. /link CODE handshake: parse 6-digit code, mark operator linked
     c. forwarded text from a linked wa_id: insert pending_forwards row
     d. non-forwarded text from a linked wa_id (within 60s of a pending
        forward with caption_text IS NULL): update caption_text on most
        recent pending row

The webhook always returns 200 to Meta (no retries triggered), even on
internal errors — we've already dedupe-keyed on wa_message_id.
"""
import hashlib
import hmac
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from supabase import Client

from app.models.whatsapp import WhatsAppInboundMessage, WhatsAppWebhookPayload

logger = logging.getLogger(__name__)

LINK_PREFIX = "/link "
LINK_CODE_PATTERN = re.compile(r"^/link\s+(\d{6})\s*$")
CAPTION_PAIRING_WINDOW = timedelta(seconds=60)


@dataclass
class HandleResult:
    """Summary of what the webhook processing did. Useful for tests + logs."""

    forwards_inserted: int = 0
    captions_paired: int = 0
    links_completed: int = 0
    duplicates_skipped: int = 0
    unlinked_skipped: int = 0
    ignored_other: int = 0


class WebhookService:
    """Stateless service — construct per-request with a service-role supabase client."""

    def __init__(self, supabase: Client, app_secret: str) -> None:
        self._db = supabase
        self._app_secret = app_secret

    # --- signature ---

    def verify_signature(self, payload_bytes: bytes, signature_header: str) -> bool:
        """
        Meta sends `X-Hub-Signature-256: sha256=<hex>`. We compute HMAC-SHA256
        of the raw body using the app secret and compare in constant time.
        """
        if not signature_header.startswith("sha256="):
            return False
        expected = signature_header.removeprefix("sha256=")
        actual = hmac.new(
            self._app_secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, actual)

    # --- payload handling ---

    def handle_payload(self, payload: WhatsAppWebhookPayload) -> HandleResult:
        result = HandleResult()
        for entry in payload.entry:
            for change in entry.changes:
                messages = change.value.get("messages") or []
                for raw_msg in messages:
                    try:
                        msg = WhatsAppInboundMessage.model_validate(raw_msg)
                    except Exception:
                        logger.warning("could not parse message: %r", raw_msg)
                        result.ignored_other += 1
                        continue
                    self._handle_one_message(msg, raw_msg, result)
        return result

    def _handle_one_message(
        self,
        msg: WhatsAppInboundMessage,
        raw_msg: dict[str, Any],
        result: HandleResult,
    ) -> None:
        # Only text messages are in scope for Plan 4
        if msg.type != "text" or msg.text is None:
            result.ignored_other += 1
            return

        body = msg.text.body or ""

        # Dedupe by wa_message_id (pending_forwards.wa_message_id UNIQUE)
        # Cheap-check first — confirmed-duplicate inserts would error on the
        # UNIQUE constraint anyway, but a SELECT keeps logs clean.
        if self._is_duplicate(msg.id):
            result.duplicates_skipped += 1
            return

        # Branch 1 — /link CODE handshake (not a forward; from any wa_id,
        # linked or not yet)
        link_match = LINK_CODE_PATTERN.match(body)
        if link_match:
            if self._complete_link(code=link_match.group(1), wa_id=msg.from_):
                result.links_completed += 1
            else:
                # Wrong / expired / used code — silently ignore for security
                # (don't leak which codes are valid via response timing)
                result.ignored_other += 1
            return

        # Branch 2/3 require the sender to be a linked operator
        operator_id = self._resolve_operator(msg.from_)
        if operator_id is None:
            result.unlinked_skipped += 1
            logger.info("inbound from unlinked wa_id=%s; ignoring", msg.from_)
            return

        is_forwarded = bool(msg.context and msg.context.forwarded)

        if is_forwarded:
            self._insert_pending_forward(operator_id, msg, raw_msg)
            result.forwards_inserted += 1
        else:
            # Branch 3 — caption pairing
            paired = self._try_pair_caption(operator_id, msg)
            if paired:
                result.captions_paired += 1
            else:
                # Unattached non-forward from linked operator. Ignore
                # silently in Plan 4 — operator may have just sent a stray
                # message. Plan 4.5 may surface these as "uncategorized."
                result.ignored_other += 1

    # --- DB helpers ---

    def _is_duplicate(self, wa_message_id: str) -> bool:
        resp = (
            self._db.table("pending_forwards")
            .select("id")
            .eq("wa_message_id", wa_message_id)
            .limit(1)
            .execute()
        )
        return bool(resp.data)

    def _complete_link(self, code: str, wa_id: str) -> bool:
        """
        Find an active operator_whatsapp_links row with this code that
        hasn't expired and hasn't been used yet. Fill wa_id + linked_at,
        null the code. Returns True if a row was updated.
        """
        # Find the candidate row
        resp = (
            self._db.table("operator_whatsapp_links")
            .select("id, link_code_expires_at, linked_at, is_active")
            .eq("link_code", code)
            .is_("linked_at", "null")
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        if not rows:
            return False
        row = rows[0]

        # Check expiry
        expires_at_str = row.get("link_code_expires_at")
        if expires_at_str:
            expires = _parse_ts(expires_at_str)
            if expires < datetime.now(UTC):
                return False

        # Update — wa_id is UNIQUE so if this operator's wa_id is already
        # linked to a different account, the update will fail and the link
        # won't complete. That's the right behavior.
        upd = (
            self._db.table("operator_whatsapp_links")
            .update({
                "wa_id": wa_id,
                "linked_at": datetime.now(UTC).isoformat(),
                "link_code": None,
                "link_code_expires_at": None,
            })
            .eq("id", row["id"])
            .execute()
        )
        return bool(upd.data)

    def _resolve_operator(self, wa_id: str) -> str | None:
        resp = (
            self._db.table("operator_whatsapp_links")
            .select("operator_id")
            .eq("wa_id", wa_id)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        return rows[0]["operator_id"] if rows else None

    def _insert_pending_forward(
        self,
        operator_id: str,
        msg: WhatsAppInboundMessage,
        raw_msg: dict[str, Any],
    ) -> None:
        wa_ts = datetime.fromtimestamp(int(msg.timestamp), tz=UTC).isoformat()
        self._db.table("pending_forwards").insert({
            "operator_id": operator_id,
            "wa_message_id": msg.id,
            "sender_wa_id": msg.from_,
            "forwarded_text": msg.text.body if msg.text else "",
            "wa_timestamp": wa_ts,
            "raw_payload": raw_msg,
        }).execute()

    def _try_pair_caption(
        self,
        operator_id: str,
        msg: WhatsAppInboundMessage,
    ) -> bool:
        """
        Look for the most recent pending_forwards row with caption_text=NULL
        from this sender within the pairing window. If found, set caption_text.
        """
        cutoff = (datetime.now(UTC) - CAPTION_PAIRING_WINDOW).isoformat()
        resp = (
            self._db.table("pending_forwards")
            .select("id, created_at")
            .eq("operator_id", operator_id)
            .eq("sender_wa_id", msg.from_)
            .is_("caption_text", "null")
            .eq("state", "pending")
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        if not rows:
            return False

        caption = msg.text.body if msg.text else ""
        self._db.table("pending_forwards").update({
            "caption_text": caption,
        }).eq("id", rows[0]["id"]).execute()
        return True


def _parse_ts(value: str) -> datetime:
    """Parse Postgres timestamptz string into a tz-aware datetime."""
    # supabase-py returns ISO format with timezone
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
