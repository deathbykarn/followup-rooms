import json
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.whatsapp import (
    PendingForwardResponse,
    WhatsAppInboundMessage,
    WhatsAppWebhookPayload,
)


# Sample inbound payload matching Meta's documented schema for a
# forwarded text message. Phone numbers are fake.
SAMPLE_FORWARDED_TEXT = {
    "object": "whatsapp_business_account",
    "entry": [
        {
            "id": "WABA_ID_HERE",
            "changes": [
                {
                    "field": "messages",
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15551234567",
                            "phone_number_id": "PHONE_ID",
                        },
                        "messages": [
                            {
                                "id": "wamid.abc123",
                                "from": "6591234567",
                                "timestamp": "1716100000",
                                "type": "text",
                                "text": {"body": "I want to view this weekend"},
                                "context": {"forwarded": True},
                            }
                        ],
                    },
                }
            ],
        }
    ],
}


def test_payload_parses_minimal_forwarded_text():
    payload = WhatsAppWebhookPayload.model_validate(SAMPLE_FORWARDED_TEXT)
    msg = payload.entry[0].changes[0].value["messages"][0]
    parsed = WhatsAppInboundMessage.model_validate(msg)
    assert parsed.id == "wamid.abc123"
    assert parsed.from_ == "6591234567"
    assert parsed.type == "text"
    assert parsed.text is not None and parsed.text.body == "I want to view this weekend"
    assert parsed.context is not None and parsed.context.forwarded is True


def test_payload_rejects_wrong_object_type():
    bad = {"object": "instagram", "entry": []}
    with pytest.raises(ValidationError):
        WhatsAppWebhookPayload.model_validate(bad)


def test_inbound_message_allows_unknown_type_for_forward_compat():
    # Meta keeps adding message types. We should accept e.g. 'order' without
    # crashing — we just won't process it. type is plain str by design.
    msg = WhatsAppInboundMessage.model_validate({
        "id": "wamid.x",
        "from": "6599999999",
        "timestamp": "1716100000",
        "type": "order",
    })
    assert msg.type == "order"
    assert msg.text is None


def test_inbound_message_from_alias_round_trip():
    raw = json.dumps({
        "id": "wamid.x",
        "from": "6591234567",
        "timestamp": "1716100000",
        "type": "text",
        "text": {"body": "hi"},
    })
    msg = WhatsAppInboundMessage.model_validate_json(raw)
    assert msg.from_ == "6591234567"


def test_inbound_message_context_optional():
    # Regular (non-forwarded) text has no context. Should parse fine.
    msg = WhatsAppInboundMessage.model_validate({
        "id": "wamid.x",
        "from": "6591234567",
        "timestamp": "1716100000",
        "type": "text",
        "text": {"body": "/link 482917"},
    })
    assert msg.context is None


def test_pending_forward_response_minimal():
    now = datetime.now(UTC)
    resp = PendingForwardResponse(
        id="p1",
        operator_id="op-1",
        wa_message_id="wamid.x",
        sender_wa_id="6591234567",
        forwarded_text="hi",
        caption_text=None,
        wa_timestamp=now,
        suggested_client_id=None,
        suggested_client_name=None,
        suggested_confidence=None,
        state="pending",
        committed_client_id=None,
        committed_event_id=None,
        committed_at=None,
        discarded_reason=None,
        created_at=now,
        updated_at=now,
    )
    assert resp.state == "pending"


def test_pending_forward_response_rejects_bogus_state():
    now = datetime.now(UTC)
    with pytest.raises(ValidationError):
        PendingForwardResponse(
            id="p1", operator_id="op-1", wa_message_id="x", sender_wa_id="x",
            forwarded_text="x", caption_text=None, wa_timestamp=now,
            suggested_client_id=None, suggested_client_name=None,
            suggested_confidence=None, state="something_else",
            committed_client_id=None, committed_event_id=None, committed_at=None,
            discarded_reason=None, created_at=now, updated_at=now,
        )
