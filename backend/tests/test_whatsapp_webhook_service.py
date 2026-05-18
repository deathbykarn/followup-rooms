import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from app.models.whatsapp import WhatsAppWebhookPayload
from app.services.whatsapp_webhook import WebhookService

APP_SECRET = "test-app-secret"


def _payload_with_message(
    text: str,
    forwarded: bool = False,
    from_: str = "6591234567",
    msg_id: str = "wamid.abc",
) -> dict:
    context = {"forwarded": forwarded} if forwarded else None
    msg = {
        "id": msg_id,
        "from": from_,
        "timestamp": "1716100000",
        "type": "text",
        "text": {"body": text},
    }
    if context:
        msg["context"] = context
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WABA_ID",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "1", "phone_number_id": "p"},
                    "messages": [msg],
                },
            }],
        }],
    }


def _sign(body_bytes: bytes) -> str:
    sig = hmac.new(APP_SECRET.encode(), body_bytes, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def _mock_db():
    db = MagicMock()
    # Default behavior: dedup query returns no rows
    db.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
    return db


def test_verify_signature_accepts_valid_hmac():
    svc = WebhookService(supabase=MagicMock(), app_secret=APP_SECRET)
    body = b'{"hello":"world"}'
    assert svc.verify_signature(body, _sign(body)) is True


def test_verify_signature_rejects_tampered_body():
    svc = WebhookService(supabase=MagicMock(), app_secret=APP_SECRET)
    body = b'{"hello":"world"}'
    tampered = b'{"hello":"WORLD"}'
    assert svc.verify_signature(tampered, _sign(body)) is False


def test_verify_signature_rejects_missing_prefix():
    svc = WebhookService(supabase=MagicMock(), app_secret=APP_SECRET)
    body = b'{}'
    raw_sig = hmac.new(APP_SECRET.encode(), body, hashlib.sha256).hexdigest()
    assert svc.verify_signature(body, raw_sig) is False  # no 'sha256=' prefix


def test_forwarded_text_from_linked_operator_inserts_pending():
    db = _mock_db()
    # Link lookup → finds operator
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[{"operator_id": "op-1"}]
    )
    svc = WebhookService(supabase=db, app_secret=APP_SECRET)

    payload = WhatsAppWebhookPayload.model_validate(
        _payload_with_message("I want to view this weekend", forwarded=True)
    )
    result = svc.handle_payload(payload)

    assert result.forwards_inserted == 1
    assert result.unlinked_skipped == 0
    # Verify pending_forwards.insert was called
    insert_calls = [
        c for c in db.table.call_args_list if c.args == ("pending_forwards",)
    ]
    assert insert_calls  # at least one
    insert_payload = db.table.return_value.insert.call_args.args[0]
    assert insert_payload["operator_id"] == "op-1"
    assert insert_payload["sender_wa_id"] == "6591234567"
    assert insert_payload["forwarded_text"] == "I want to view this weekend"


def test_forwarded_text_from_unlinked_wa_id_is_skipped():
    db = _mock_db()
    # Operator-resolve lookup returns no rows
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
    svc = WebhookService(supabase=db, app_secret=APP_SECRET)

    payload = WhatsAppWebhookPayload.model_validate(
        _payload_with_message("hi from stranger", forwarded=True, from_="9999999999")
    )
    result = svc.handle_payload(payload)

    assert result.unlinked_skipped == 1
    assert result.forwards_inserted == 0


def test_duplicate_wa_message_id_is_skipped():
    db = _mock_db()
    # Dedup check returns an existing row
    db.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[{"id": "existing-pending-id"}]
    )
    svc = WebhookService(supabase=db, app_secret=APP_SECRET)

    payload = WhatsAppWebhookPayload.model_validate(
        _payload_with_message("dup", forwarded=True)
    )
    result = svc.handle_payload(payload)

    assert result.duplicates_skipped == 1
    assert result.forwards_inserted == 0


def test_link_code_handshake_completes_when_code_valid():
    db = _mock_db()
    future = (datetime.now(UTC) + timedelta(minutes=10)).isoformat()

    # is_duplicate check
    db.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
    # _complete_link select: finds a row
    db.table.return_value.select.return_value.eq.return_value.is_.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[{"id": "link-1", "link_code_expires_at": future, "linked_at": None, "is_active": True}]
    )
    # _complete_link update: returns updated row
    db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "link-1"}]
    )
    svc = WebhookService(supabase=db, app_secret=APP_SECRET)

    payload = WhatsAppWebhookPayload.model_validate(
        _payload_with_message("/link 482917", forwarded=False)
    )
    result = svc.handle_payload(payload)
    assert result.links_completed == 1


def test_link_code_handshake_ignored_when_code_expired():
    db = _mock_db()
    past = (datetime.now(UTC) - timedelta(minutes=10)).isoformat()
    db.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
    db.table.return_value.select.return_value.eq.return_value.is_.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[{"id": "link-1", "link_code_expires_at": past, "linked_at": None, "is_active": True}]
    )
    svc = WebhookService(supabase=db, app_secret=APP_SECRET)

    payload = WhatsAppWebhookPayload.model_validate(
        _payload_with_message("/link 482917", forwarded=False)
    )
    result = svc.handle_payload(payload)
    assert result.links_completed == 0
    assert result.ignored_other == 1


def test_link_code_handshake_ignored_when_no_match():
    db = _mock_db()
    db.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
    db.table.return_value.select.return_value.eq.return_value.is_.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
    svc = WebhookService(supabase=db, app_secret=APP_SECRET)

    payload = WhatsAppWebhookPayload.model_validate(
        _payload_with_message("/link 000000", forwarded=False)
    )
    result = svc.handle_payload(payload)
    assert result.links_completed == 0


def test_caption_pairs_with_recent_pending_forward():
    db = _mock_db()
    # Dedup: not seen before
    db.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
    # Resolve operator: linked
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[{"operator_id": "op-1"}]
    )
    # Caption pairing query: finds a recent pending row
    pending_row_id = "pending-123"
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.is_.return_value.eq.return_value.gte.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[{"id": pending_row_id, "created_at": datetime.now(UTC).isoformat()}]
    )
    svc = WebhookService(supabase=db, app_secret=APP_SECRET)

    payload = WhatsAppWebhookPayload.model_validate(
        _payload_with_message("Sarah Tan", forwarded=False, msg_id="wamid.caption")
    )
    result = svc.handle_payload(payload)
    assert result.captions_paired == 1
