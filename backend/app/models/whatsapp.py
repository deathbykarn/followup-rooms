"""
Pydantic models for the WhatsApp Cloud API webhook + pending_forwards.

Based on Meta's documented schema as of May 2026:
https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples

The webhook payload model intentionally narrows to fields we use; extras
flow through `extra='allow'` (Pattern: tolerate unknown future fields,
fail loud on missing required ones we depend on).
"""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

PendingState = Literal["pending", "confirmed", "discarded", "expired"]


# --- Meta inbound webhook payload (subset) ---------------------------------

class WhatsAppContext(BaseModel):
    """
    Present on forwarded messages, replies, and reactions. We use the
    `forwarded` flag to distinguish a forward from a regular message
    (matters for /link CODE handshake — those are not forwards).
    """
    model_config = ConfigDict(extra="allow")
    forwarded: bool = False
    frequently_forwarded: bool = False


class WhatsAppTextBody(BaseModel):
    model_config = ConfigDict(extra="allow")
    body: str


class WhatsAppInboundMessage(BaseModel):
    """One message in entry[].changes[].value.messages[]."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str
    from_: str = Field(alias="from")     # sender wa_id (E.164 digits, no '+')
    timestamp: str                       # Meta sends Unix seconds as a string
    # 'text', 'image', 'audio', 'video', 'document', 'reaction', etc.
    type: str
    text: WhatsAppTextBody | None = None
    context: WhatsAppContext | None = None


class WhatsAppChange(BaseModel):
    model_config = ConfigDict(extra="allow")
    value: dict[str, Any]                # raw — we extract messages[] manually for forward-compat
    field: str                           # typically 'messages'


class WhatsAppEntry(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str                              # WABA id
    changes: list[WhatsAppChange]


class WhatsAppWebhookPayload(BaseModel):
    """Top-level webhook envelope."""
    model_config = ConfigDict(extra="allow")
    object: Literal["whatsapp_business_account"]
    entry: list[WhatsAppEntry]


# --- API output models -----------------------------------------------------

class PendingForwardResponse(BaseModel):
    """A pending_forwards row enriched with the suggested client's name."""

    id: str
    operator_id: str
    wa_message_id: str
    sender_wa_id: str
    forwarded_text: str
    caption_text: str | None
    wa_timestamp: datetime
    suggested_client_id: str | None
    suggested_client_name: str | None    # resolved via join in the API layer
    suggested_confidence: float | None
    state: PendingState
    committed_client_id: str | None
    committed_event_id: str | None
    committed_at: datetime | None
    discarded_reason: str | None
    created_at: datetime
    updated_at: datetime


class LinkStatusResponse(BaseModel):
    is_linked: bool
    wa_id: str | None
    linked_at: datetime | None


class LinkCodeResponse(BaseModel):
    code: str                            # 6-digit
    expires_at: datetime
    whatsapp_number: str                 # the FollowRoom display E.164 to send /link CODE to
    instructions: str                    # human-readable copy for the dashboard


class ConfirmForwardRequest(BaseModel):
    client_id: str


class DiscardForwardRequest(BaseModel):
    reason: str | None = None
