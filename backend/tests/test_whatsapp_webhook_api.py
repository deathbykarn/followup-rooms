import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

APP_SECRET = "ci-meta-secret"          # matches CI env in workflow + .env placeholder
VERIFY_TOKEN = "ci-meta-verify"        # matches CI env


@pytest.fixture
def client():
    return TestClient(app)


def _sign(body: bytes) -> str:
    return "sha256=" + hmac.new(
        APP_SECRET.encode(), body, hashlib.sha256,
    ).hexdigest()


def _forward_payload() -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WABA_ID",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "1", "phone_number_id": "p"},
                    "messages": [{
                        "id": "wamid.abc",
                        "from": "6591234567",
                        "timestamp": "1716100000",
                        "type": "text",
                        "text": {"body": "I want to view this weekend"},
                        "context": {"forwarded": True},
                    }],
                },
            }],
        }],
    }


# --- GET verification handshake ---

def test_get_webhook_returns_challenge_on_correct_token(client, monkeypatch):
    monkeypatch.setenv("META_WHATSAPP_VERIFY_TOKEN", VERIFY_TOKEN)
    from app.core import config
    config.get_settings.cache_clear()

    resp = client.get(
        "/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": VERIFY_TOKEN,
            "hub.challenge": "challenge-string-xyz",
        },
    )
    assert resp.status_code == 200
    assert resp.text == "challenge-string-xyz"


def test_get_webhook_rejects_wrong_token(client, monkeypatch):
    monkeypatch.setenv("META_WHATSAPP_VERIFY_TOKEN", VERIFY_TOKEN)
    from app.core import config
    config.get_settings.cache_clear()

    resp = client.get(
        "/whatsapp/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong",
            "hub.challenge": "x",
        },
    )
    assert resp.status_code == 403


def test_get_webhook_rejects_wrong_mode(client, monkeypatch):
    monkeypatch.setenv("META_WHATSAPP_VERIFY_TOKEN", VERIFY_TOKEN)
    from app.core import config
    config.get_settings.cache_clear()

    resp = client.get(
        "/whatsapp/webhook",
        params={
            "hub.mode": "unsubscribe",
            "hub.verify_token": VERIFY_TOKEN,
            "hub.challenge": "x",
        },
    )
    assert resp.status_code == 403


# --- POST signed delivery ---

def test_post_webhook_rejects_missing_signature(client, monkeypatch):
    monkeypatch.setenv("META_WHATSAPP_APP_SECRET", APP_SECRET)
    from app.core import config
    config.get_settings.cache_clear()

    body = json.dumps(_forward_payload()).encode()
    resp = client.post("/whatsapp/webhook", content=body)
    assert resp.status_code == 401


def test_post_webhook_rejects_invalid_signature(client, monkeypatch):
    monkeypatch.setenv("META_WHATSAPP_APP_SECRET", APP_SECRET)
    from app.core import config
    config.get_settings.cache_clear()

    body = json.dumps(_forward_payload()).encode()
    resp = client.post(
        "/whatsapp/webhook",
        content=body,
        headers={"X-Hub-Signature-256": "sha256=deadbeef"},
    )
    assert resp.status_code == 401


def test_post_webhook_accepts_valid_signature_and_returns_200(client, monkeypatch):
    monkeypatch.setenv("META_WHATSAPP_APP_SECRET", APP_SECRET)
    from app.core import config
    config.get_settings.cache_clear()

    fake_svc = MagicMock()
    fake_svc.verify_signature.return_value = True
    fake_svc.handle_payload.return_value = MagicMock(
        forwards_inserted=1, captions_paired=0, links_completed=0,
        duplicates_skipped=0, unlinked_skipped=0,
    )

    body = json.dumps(_forward_payload()).encode()
    with patch("app.api.whatsapp_webhook._build_webhook_service", return_value=fake_svc), \
         patch("app.api.whatsapp_webhook._run_client_matcher_for_recent_pending"):
        resp = client.post(
            "/whatsapp/webhook",
            content=body,
            headers={"X-Hub-Signature-256": _sign(body)},
        )

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    fake_svc.handle_payload.assert_called_once()


def test_post_webhook_returns_200_on_non_message_payload(client, monkeypatch):
    """Meta sends delivery + read receipts too; those don't have entry[].changes[].value.messages.
    The payload still parses; handle_payload finds no messages and returns ok counters."""
    monkeypatch.setenv("META_WHATSAPP_APP_SECRET", APP_SECRET)
    from app.core import config
    config.get_settings.cache_clear()

    fake_svc = MagicMock()
    fake_svc.verify_signature.return_value = True
    fake_svc.handle_payload.return_value = MagicMock(
        forwards_inserted=0, captions_paired=0, links_completed=0,
        duplicates_skipped=0, unlinked_skipped=0,
    )

    # Valid WhatsAppWebhookPayload but with statuses[] instead of messages[]
    body = json.dumps({
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WABA_ID",
            "changes": [{
                "field": "messages",
                "value": {"statuses": [{"id": "wamid.x", "status": "delivered"}]},
            }],
        }],
    }).encode()

    with patch("app.api.whatsapp_webhook._build_webhook_service", return_value=fake_svc), \
         patch("app.api.whatsapp_webhook._run_client_matcher_for_recent_pending"):
        resp = client.post(
            "/whatsapp/webhook",
            content=body,
            headers={"X-Hub-Signature-256": _sign(body)},
        )

    assert resp.status_code == 200


def test_post_webhook_returns_200_when_handle_payload_raises(client, monkeypatch):
    """Internal failures should not cause Meta to retry — we've already dedupe-keyed."""
    monkeypatch.setenv("META_WHATSAPP_APP_SECRET", APP_SECRET)
    from app.core import config
    config.get_settings.cache_clear()

    fake_svc = MagicMock()
    fake_svc.verify_signature.return_value = True
    fake_svc.handle_payload.side_effect = RuntimeError("db down")

    body = json.dumps(_forward_payload()).encode()
    with patch("app.api.whatsapp_webhook._build_webhook_service", return_value=fake_svc):
        resp = client.post(
            "/whatsapp/webhook",
            content=body,
            headers={"X-Hub-Signature-256": _sign(body)},
        )

    assert resp.status_code == 200
