# Meta WhatsApp Cloud API test number — limitations discovered during Plan 4 smoke

**Date:** 2026-05-19
**Context:** Plan 4 smoke test attempted live forwarded-message flow from operator's personal WhatsApp to FollowRoom's test number. Webhook never fired despite all config being correct.

## Root cause

**Meta test phone numbers are not addressable from the consumer WhatsApp network.** When a real WhatsApp user tries to message a test number, the WhatsApp app shows "Invite to WhatsApp" — the number isn't registered as a regular WhatsApp account.

Test numbers exist for **outbound testing only**: you can send messages FROM the test number TO pre-registered test recipients (subject to the 5-recipient cap). You cannot send TO the test number FROM arbitrary WhatsApp users.

This isn't documented prominently in Meta's getting-started flow, and is easy to assume otherwise given that:
- The dashboard shows webhook configuration for `messages` field (suggesting inbound works)
- The test number has a real `+1 555-XXX-XXXX` display number that looks like a regular WhatsApp number
- WABA-level `subscribed_apps` succeeds and indicates the WABA is wired for inbound delivery

The inbound-receive capability only activates with a **production phone number**, which requires Meta Business Verification.

## What worked in Plan 4 testing despite this

- Webhook handshake (`GET /whatsapp/webhook` with `hub.mode=subscribe`) — verified via direct curl
- Backend `/health` reachable on Render production
- WABA → app subscription succeeded (`{"success": true}` from `POST /v21.0/<WABA_ID>/subscribed_apps`)
- All Plan 4 unit + integration tests pass (130 backend + 15 web)
- Code path for inbound webhook is unit-tested with crafted-payload signatures (`test_whatsapp_webhook_api`)

## What's NOT validated end-to-end

- Real Meta payload schema matches our `WhatsAppInboundMessage` Pydantic model in production
- Caption pairing heuristic (within-60s, same-sender) under real two-message delivery timing
- ClientMatcher's Haiku branch with real ambiguous captions

## Path to full validation

**Option 1 (recommended): Meta Business Verification + production phone number.** 1-2 week review. Required for production anyway. Once cleared, the test we couldn't do today becomes trivial.

**Option 2: Twilio Sandbox.** Bidirectional without verification. Different payload schema — would require a parallel `TwilioWebhookService` (config-swap, same interface as `WhatsAppWebhookService`). Useful as a parallel path if Twilio is preferred long-term.

**Option 3: Simulated payload via curl.** Construct a Meta-shaped JSON payload, sign with app secret, POST to `/whatsapp/webhook`. Validates our code with realistic input but doesn't exercise the real Meta delivery chain. Captured in Plan 4.5 as a developer-tooling task if Business Verification keeps slipping.

## Plan 4.5 implications

The deferred items from Plan 4 should bundle with this:

- Business Verification kickoff (whenever first external SG agent is ready) — necessary prerequisite for both outbound notifications + real inbound from arbitrary senders
- PDPA disclosure copy in operator onboarding (still pending from Plan 3 AssemblyAI decision)
- Forwarded voice/image/document handling (download from Meta CDN)
- Outbound "you have 1 pending forward" reply
- Session-lock variant
- Add `system_user_whatsapp_asset` to the System User → enables Plan 4.5's outbound + media-download API calls

## Render deployment as part of Plan 4

Backend deployed to Render free tier as part of this session. URL: `https://followup-rooms-backend.onrender.com`. Tracking the `feat/whatsapp-plan-4` branch for the smoke window; flips to `main` post-merge.

Free tier has a 15-min spindown which masked one of the smoke test attempts (webhook arrived during cold start, Meta timed out). Upgrade to Starter ($7/mo) is the right call before real external testing — flagged in Plan 4.5.
