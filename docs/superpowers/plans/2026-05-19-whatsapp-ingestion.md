# WhatsApp Ingestion (Shape X) — Implementation Plan (Plan 4)

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` (or `subagent-driven-development` if available) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** An operator forwards a client's WhatsApp message to FollowRoom's WhatsApp number with a short identifier as the caption (e.g., "Sarah" or "Sarah, East Coast"). The system surfaces the forward in a dashboard tray as a PENDING event. The operator confirms attribution (Confirm / Change / Discard). Confirm triggers the Plan 2 extraction pipeline; the new event lands in the client's KB.

**Architecture:** Inbound-only via Meta WhatsApp Cloud API test number. FastAPI webhook receives `messages` events, verifies Meta's HMAC signature, dedupes by `message_id`, persists to a new `pending_forwards` table, and matches operator by `from` (WhatsApp wa_id). Operator's wa_id is linked to their account during onboarding via a one-time `/link CODE` flow that uses the **same inbound webhook** (no outbound dependency). Pending forwards display in a dashboard tray (with caption-text best-match suggesting which client); operator clicks Confirm/Change/Discard; Confirm calls into Plan 2's `ExtractionPipeline.ingest_and_extract` with `source_type='whatsapp_forward_shape_x'`.

**Tech Stack:** `httpx` (already a dep) for any future outbound calls (Plan 4.5); FastAPI webhook for inbound; new `pending_forwards` + `operator_whatsapp_links` tables; reuse Plan 2 extraction.

**Out of scope (deferred):**
- Forwarded voice notes / images / documents (Plan 4.5)
- Outbound WhatsApp push notifications ("you have 1 pending forward" reply back to operator — Plan 4.5)
- Session-lock variant ("auto-attach next 5min to Sarah" — Plan 4.6)
- Meta Business verification + production phone number provisioning (do this whenever first external SG agent is ready; doesn't block Plan 4)
- Coexistence (Flavor 1) — Phase 2/3 per design doc
- WhatsApp Business app sync — Phase 3

---

## Pre-flight Research (Task 1)

Three things to validate before coding:

1. **Meta Business Manager + WhatsApp app creation steps.** Confirm the current 2026 path: developers.facebook.com → My Apps → Create App (type "Business") → Add Product "WhatsApp" → System creates a test WhatsApp Business Account + test phone number. No business verification needed for the test number. Capture the exact 8-step path in `docs/findings/2026-05-19-meta-cloud-api-setup.md` so future-us doesn't re-derive it.

2. **Webhook payload schema for a forwarded text message.** Send a real forwarded message from your personal WhatsApp to the test number; capture the actual JSON payload your webhook receives. Look specifically at:
   - `entry[].changes[].value.messages[].context.forwarded` (or `context.frequently_forwarded`) boolean — distinguishes forwards from regular messages
   - `entry[].changes[].value.messages[].text.body` — the forwarded text content
   - `entry[].changes[].value.messages[].from` — the OPERATOR's wa_id (the person who forwarded)
   - `entry[].changes[].value.messages[].id` — Meta's message ID for dedupe
   - `entry[].changes[].value.messages[].timestamp` — Unix seconds
   - Whether the forward caption arrives as a **separate message** (Meta's normal behavior: caption-on-forward sends two messages — the original forwarded text, then the operator's caption as a follow-up text in the same conversation within seconds) or as part of the same payload

   This research outcome determines the pairing logic (next paragraph). Document findings in `docs/findings/2026-05-19-whatsapp-webhook-schema.md`.

3. **Caption pairing strategy.** Meta delivers the forwarded message and the operator's caption as TWO separate inbound webhook events (the operator's caption goes to the original sender's conversation thread, then comes BACK to us when they hit Send on a follow-up message). Pair them in the webhook handler by: same `from` (operator wa_id) + arrival within 60 seconds + the second message has no `context.forwarded` flag. Document the chosen heuristic + an escape hatch (operator can manually associate caption-less forwards in the dashboard).

If schema research reveals Meta payload doesn't match expectations, plan pivots:
- No `context.forwarded` flag exists → fall back to "treat every inbound text from a linked operator as a candidate forward; require explicit Confirm in dashboard."
- Caption arrives in the same payload → simpler pairing logic; skip the 60s window.

---

## Data Model

### New table: `operator_whatsapp_links` (migration 0013)

```sql
CREATE TABLE operator_whatsapp_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,
    wa_id TEXT NOT NULL UNIQUE,           -- E.164 digits-only, e.g., '6591234567'
    link_code TEXT,                       -- 6-digit code shown in dashboard during onboarding; nulled after use
    link_code_expires_at TIMESTAMPTZ,     -- 30 min from issuance
    linked_at TIMESTAMPTZ,                -- when /link CODE arrived
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_operator_whatsapp_links_operator
    ON operator_whatsapp_links(operator_id) WHERE is_active;
-- wa_id has a UNIQUE constraint above — used by the webhook to resolve operator from sender.

-- RLS: operator sees only their own row
ALTER TABLE operator_whatsapp_links ENABLE ROW LEVEL SECURITY;
CREATE POLICY whatsapp_links_select ON operator_whatsapp_links
    FOR SELECT USING (operator_id = auth.uid());
CREATE POLICY whatsapp_links_insert ON operator_whatsapp_links
    FOR INSERT WITH CHECK (operator_id = auth.uid());
CREATE POLICY whatsapp_links_update ON operator_whatsapp_links
    FOR UPDATE USING (operator_id = auth.uid());
-- Webhook bypasses RLS via service-role client (it needs to find the operator
-- from a wa_id before any auth context exists).
```

### New table: `pending_forwards` (migration 0014)

```sql
CREATE TABLE pending_forwards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,

    -- Inbound message data (immutable — these are receipts from Meta)
    wa_message_id TEXT NOT NULL UNIQUE,        -- Meta's message id; dedupe key
    sender_wa_id TEXT NOT NULL,                -- the operator's wa_id (who forwarded)
    forwarded_text TEXT NOT NULL,              -- the content of the forwarded message
    caption_text TEXT,                         -- the operator's caption (paired with the forward); nullable
    wa_timestamp TIMESTAMPTZ NOT NULL,         -- when Meta says the forward arrived
    raw_payload JSONB NOT NULL,                -- the full webhook payload chunk for audit

    -- Suggested attribution (LLM-assisted; operator confirms)
    suggested_client_id UUID REFERENCES clients(id),
    suggested_confidence REAL CHECK (suggested_confidence >= 0 AND suggested_confidence <= 1),

    -- Operator commit
    state TEXT NOT NULL DEFAULT 'pending' CHECK (state IN (
        'pending', 'confirmed', 'discarded', 'expired'
    )),
    committed_client_id UUID REFERENCES clients(id),  -- populated on confirm
    committed_event_id UUID REFERENCES events(id),    -- populated on confirm (links to Plan 2 events)
    committed_at TIMESTAMPTZ,
    discarded_reason TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pending_forwards_operator_pending
    ON pending_forwards(operator_id, created_at DESC)
    WHERE state = 'pending';
CREATE INDEX idx_pending_forwards_operator_recent
    ON pending_forwards(operator_id, created_at DESC);

-- RLS per-operator
ALTER TABLE pending_forwards ENABLE ROW LEVEL SECURITY;
CREATE POLICY pending_forwards_select ON pending_forwards
    FOR SELECT USING (operator_id = auth.uid());
CREATE POLICY pending_forwards_insert ON pending_forwards
    FOR INSERT WITH CHECK (operator_id = auth.uid());
CREATE POLICY pending_forwards_update ON pending_forwards
    FOR UPDATE USING (operator_id = auth.uid());
```

### Event source_type extension

The `events.source_type` CHECK already includes `whatsapp_forward_shapeX`. Verify by reading migration 0003. If the value used in our code is `whatsapp_forward_shape_x` vs `whatsapp_forward_shapeX`, normalize to whatever the existing CHECK allows.

---

## File Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── whatsapp_webhook.py     [NEW] GET (verify) + POST (events) — Meta webhook endpoints
│   │   └── pending_forwards.py     [NEW] GET list, POST confirm/discard, POST /link-code
│   ├── models/
│   │   └── whatsapp.py             [NEW] Pydantic models for webhook payload + pending_forwards
│   ├── services/
│   │   ├── whatsapp_webhook.py     [NEW] WebhookService: dedup, link lookup, /link handling, pairing
│   │   └── client_matcher.py       [NEW] Suggests client from caption_text via fuzzy + LLM
│   └── core/
│       └── config.py               [MODIFY] add META_WHATSAPP_APP_SECRET + META_WHATSAPP_VERIFY_TOKEN
└── tests/
    ├── test_models_whatsapp.py     [NEW]
    ├── test_whatsapp_webhook_service.py [NEW]
    ├── test_client_matcher.py      [NEW]
    ├── test_whatsapp_webhook_api.py [NEW]
    └── test_pending_forwards_api.py [NEW]

supabase/migrations/
├── 0013_operator_whatsapp_links.sql [NEW]
└── 0014_pending_forwards.sql        [NEW]

web/
├── app/dashboard/
│   ├── pending/page.tsx            [NEW] Pending forwards tray (operator's homepage when there are any)
│   └── settings/whatsapp/page.tsx  [NEW] WhatsApp linking page (shows /link CODE + status)
├── components/whatsapp/
│   ├── pending-forward-card.tsx    [NEW] One pending forward + Confirm/Change/Discard
│   ├── client-picker.tsx           [NEW] Dropdown for "Change" — picks a client
│   └── link-instructions.tsx       [NEW] Onboarding card: shows code + WhatsApp number + steps
└── lib/api/
    ├── whatsapp-link.ts            [NEW] issueLinkCode, getLinkStatus
    └── pending-forwards.ts         [NEW] listPending, confirmForward, discardForward
```

---

## Task Breakdown

### Task 1: Branch + Meta Cloud API account setup + research findings

**Files:**
- Create: `docs/findings/2026-05-19-meta-cloud-api-setup.md`
- Create: `docs/findings/2026-05-19-whatsapp-webhook-schema.md`

- [ ] **Step 1:** Confirm on branch `feat/whatsapp-plan-4`.
- [ ] **Step 2:** Manual setup (user does this; document the exact path taken):
  - developers.facebook.com → My Apps → Create App → "Business" type
  - Add Product → WhatsApp → click Set Up
  - Save the auto-generated **test phone number ID** and **WhatsApp Business Account ID** (display them in the setup findings doc redacted; raw values go in `backend/.env`)
  - Generate a **System User Access Token** (permanent) under Business Settings → System Users → Generate Token → assign to WhatsApp app with `whatsapp_business_messaging` and `whatsapp_business_management` scopes
  - Add operator's personal WhatsApp number as a **test recipient** (Meta sends a verification code)
  - In the WhatsApp app's Configuration → Webhooks: leave blank for now (set after backend deploys in Task 9)
- [ ] **Step 3:** Send a forwarded message from operator's WhatsApp to the test number. Use Meta's "Test Webhooks" tool OR temporarily expose your local backend via ngrok to capture the payload. Save the raw JSON to `docs/findings/2026-05-19-whatsapp-webhook-schema.md` (redact phone numbers in checked-in copy).
- [ ] **Step 4:** Verify `context.forwarded` field presence and value in the payload. Document the exact schema we're going to depend on.
- [ ] **Step 5:** Commit: `chore(plan4): meta cloud api test number setup + webhook schema captured`.

### Task 2: Config + env

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/.env` (placeholder values)
- Modify: `.github/workflows/backend-ci.yml` (CI env)

- [ ] **Step 1:** Add to `Settings`:
  ```python
  meta_whatsapp_app_secret: str          # Meta app secret — used to verify webhook HMAC
  meta_whatsapp_verify_token: str        # Operator-chosen string — used in webhook verification handshake
  meta_whatsapp_phone_number_id: str     # Test number ID from Meta dashboard
  meta_whatsapp_access_token: str        # System user permanent token
  followroom_whatsapp_number: str        # Display E.164 (e.g., '+15551234567') — for operator-facing instructions
  ```
- [ ] **Step 2:** Add placeholder lines to `backend/.env`. Add CI env stubs.
- [ ] **Step 3:** Commit: `chore(config): META_WHATSAPP_* + FOLLOWROOM_WHATSAPP_NUMBER settings`.

### Task 3: Pydantic models for webhook payload + pending_forwards

**Files:**
- Create: `backend/app/models/whatsapp.py`
- Create: `backend/tests/test_models_whatsapp.py`

- [ ] **Step 1:** Model Meta's `messages` webhook payload minimally — only the fields we use:
  ```python
  class WhatsAppContext(BaseModel):
      forwarded: bool = False
      frequently_forwarded: bool = False

  class WhatsAppTextBody(BaseModel):
      body: str

  class WhatsAppInboundMessage(BaseModel):
      id: str                          # Meta message id
      from_: str = Field(alias="from") # sender wa_id
      timestamp: str                   # Unix seconds as string per Meta
      type: Literal["text", "image", "audio", "video", "document", "sticker", "location", "reaction"]
      text: WhatsAppTextBody | None = None
      context: WhatsAppContext | None = None

  class WhatsAppChange(BaseModel):
      value: dict[str, Any]            # raw — we extract messages[] manually for forward-compat
      field: str

  class WhatsAppEntry(BaseModel):
      id: str                          # WABA id
      changes: list[WhatsAppChange]

  class WhatsAppWebhookPayload(BaseModel):
      object: Literal["whatsapp_business_account"]
      entry: list[WhatsAppEntry]
  ```
- [ ] **Step 2:** Add `PendingForwardResponse` for API output (matches the table columns + a resolved `suggested_client_name` for the UI).
- [ ] **Step 3:** Tests: payload parses, required fields enforce, `from_` alias works, ignores extra fields gracefully.
- [ ] **Step 4:** Commit: `feat(models): WhatsApp webhook + PendingForward Pydantic models`.

### Task 4: Migration 0013 — operator_whatsapp_links

**Files:**
- Create: `supabase/migrations/0013_operator_whatsapp_links.sql`

- [ ] **Step 1:** Write the migration using the schema from the Data Model section. Include trigger for updated_at.
- [ ] **Step 2:** Apply via `python backend/scripts/apply_migrations.py`. Verify columns + indexes + RLS policies.
- [ ] **Step 3:** Commit: `feat(db): migration 0013 — operator_whatsapp_links with /link CODE flow`.

### Task 5: Migration 0014 — pending_forwards

**Files:**
- Create: `supabase/migrations/0014_pending_forwards.sql`

- [ ] **Step 1:** Write migration. Include trigger.
- [ ] **Step 2:** Apply + verify. Confirm `wa_message_id` UNIQUE constraint (dedupe at DB level — webhook retries are safe).
- [ ] **Step 3:** Commit: `feat(db): migration 0014 — pending_forwards with state machine + RLS`.

### Task 6: WebhookService — signature verification + dedup + /link handling

**Files:**
- Create: `backend/app/services/whatsapp_webhook.py`
- Create: `backend/tests/test_whatsapp_webhook_service.py`

- [ ] **Step 1:** `WebhookService.verify_signature(payload_bytes, signature_header) -> bool` — HMAC-SHA256 using `meta_whatsapp_app_secret` as key. Compare against `X-Hub-Signature-256` header value. **Refuse to process if signature invalid** (return 401 in the caller).
- [ ] **Step 2:** `WebhookService.handle_payload(payload: WhatsAppWebhookPayload) -> HandleResult`:
  - For each `entry.changes.value.messages[]`:
    - Extract `id`, `from`, `timestamp`, `text.body`, `context.forwarded`
    - Dedup: skip if `wa_message_id` already exists in `pending_forwards`
    - **Branch 1 — /link CODE handshake:** if text starts with `/link `, parse the 6-digit code. Look up in `operator_whatsapp_links` where `link_code = ... AND link_code_expires_at > NOW() AND is_active`. If found, fill `wa_id` + `linked_at`, null the code. **Do not create a pending_forwards row.**
    - **Branch 2 — forwarded message:** lookup `operator_whatsapp_links` by `wa_id = from`. If no link → log + ignore (or surface a "we got a forward from an unlinked number" alert in Plan 4.5). If linked, insert a `pending_forwards` row with `state='pending'`.
    - **Branch 3 — caption (non-forwarded text from a linked wa_id within 60s of a pending forward):** look up the most recent `pending_forwards` row by `sender_wa_id=from AND caption_text IS NULL AND created_at > NOW() - INTERVAL '60 seconds' AND state='pending'`. If found, UPDATE `caption_text = body`. (Don't insert a new pending_forwards row for caption messages.)
- [ ] **Step 3:** Tests with mocked supabase (8+):
  - signature verification passes on valid HMAC, fails on tampered
  - dedup: second call with same wa_message_id is no-op
  - /link CODE happy path: links operator's wa_id
  - /link CODE expired / wrong / used: silently ignored
  - forwarded text from linked wa_id inserts pending_forwards
  - forwarded text from unlinked wa_id: skipped (logged)
  - caption message updates most recent pending_forwards.caption_text
  - caption message outside 60s window: ignored
- [ ] **Step 4:** Commit: `feat(services): WhatsApp WebhookService — signature + dedup + /link + caption pairing`.

### Task 7: ClientMatcher service — suggest client from caption

**Files:**
- Create: `backend/app/services/client_matcher.py`
- Create: `backend/tests/test_client_matcher.py`

- [ ] **Step 1:** `ClientMatcher.suggest(operator_id, caption_text) -> tuple[client_id | None, confidence]`. Two-pass:
  - Fuzzy match caption against operator's active clients' `client_name` + `aliases[]`. If exact match (case-insensitive substring): confidence 0.95.
  - If no fuzzy hit OR multiple ties: call Haiku 4.5 via `AgentDispatcher.structured_dispatch` with a prompt that returns `{client_id, confidence}` where client_id ∈ the operator's client list. Default confidence 0.6 if Haiku is uncertain.
  - Return `(None, 0.0)` only if operator has zero clients.
- [ ] **Step 2:** Tests with mocked dispatcher (5+):
  - exact name match → 0.95 confidence
  - alias match → 0.95 confidence
  - ambiguous "Sarah" (two Sarahs in client list) → Haiku branch, returns chosen one
  - no clients → (None, 0.0)
  - Haiku returns invalid client_id → fall back to None
- [ ] **Step 3:** Commit: `feat(services): ClientMatcher — fuzzy + Haiku-assisted client attribution from caption`.

### Task 8: POST /whatsapp/webhook + GET /whatsapp/webhook (verification)

**Files:**
- Create: `backend/app/api/whatsapp_webhook.py`
- Modify: `backend/app/main.py` (register router)
- Create: `backend/tests/test_whatsapp_webhook_api.py`

- [ ] **Step 1:** Implement Meta's webhook verification handshake:
  ```python
  @router.get("/webhook")
  async def verify(
      hub_mode: str = Query(alias="hub.mode"),
      hub_verify_token: str = Query(alias="hub.verify_token"),
      hub_challenge: str = Query(alias="hub.challenge"),
  ) -> PlainTextResponse:
      if hub_mode != "subscribe" or hub_verify_token != settings.meta_whatsapp_verify_token:
          raise HTTPException(403, "verification failed")
      return PlainTextResponse(hub_challenge)
  ```
- [ ] **Step 2:** Implement POST:
  ```python
  @router.post("/webhook", status_code=200)
  async def receive(request: Request) -> dict:
      body = await request.body()
      sig = request.headers.get("X-Hub-Signature-256", "")
      svc = WebhookService(get_service_client())
      if not svc.verify_signature(body, sig):
          raise HTTPException(401, "invalid signature")
      # Parse with our Pydantic model; tolerate unknown event types (return 200 anyway)
      try:
          payload = WhatsAppWebhookPayload.model_validate_json(body)
          svc.handle_payload(payload)
      except ValidationError:
          logger.warning("non-message webhook event; ignoring")
      # ALWAYS return 200 so Meta doesn't retry; we've already done dedup
      return {"status": "ok"}

      # After-call: if attribution suggestion is enabled, run ClientMatcher
      # async in a BackgroundTask so the webhook returns quickly.
  ```
- [ ] **Step 3:** Tests (no real Meta calls; craft signed payloads with the same HMAC algo):
  - GET verification: correct token → returns challenge; wrong token → 403
  - POST with valid signature + forwarded text payload → 200 + pending_forwards inserted
  - POST with invalid signature → 401
  - POST with /link payload → 200 + operator_whatsapp_links updated
  - POST with malformed JSON → 200 (we swallow + log)
- [ ] **Step 4:** Register the router in main.py.
- [ ] **Step 5:** Commit: `feat(api): /whatsapp/webhook — Meta verification + signed POST handler`.

### Task 9: Local webhook smoke test (manual)

**Files:** none (verification only)

- [ ] **Step 1:** Run backend locally: `uvicorn app.main:app --reload`.
- [ ] **Step 2:** Expose via ngrok or similar: `ngrok http 8000` → copy public URL.
- [ ] **Step 3:** In Meta dashboard → WhatsApp → Configuration → Webhooks → set callback URL to `<ngrok>/whatsapp/webhook` and verify token to match `META_WHATSAPP_VERIFY_TOKEN` in `.env`. Subscribe to `messages` field.
- [ ] **Step 4:** From operator's WhatsApp (a registered test recipient), forward any text message to the test number with caption "Sarah Test".
- [ ] **Step 5:** Verify backend logs show: signature verified, forward received, pending_forwards row inserted, caption paired.
- [ ] **Step 6:** Document any deviations from Task 1 schema findings.

### Task 10: POST /whatsapp/link-code + GET /whatsapp/link-status

**Files:**
- Create: `backend/app/api/pending_forwards.py` (combined with link-code endpoints — small surface)
- Create: `backend/tests/test_pending_forwards_api.py`

- [ ] **Step 1:** `POST /whatsapp/link-code` → generates 6-digit code (cryptographic random), inserts/updates `operator_whatsapp_links` with code + 30min expiry. Returns `{code, expires_at, whatsapp_number}` (the WhatsApp number to send `/link CODE` to).
- [ ] **Step 2:** `GET /whatsapp/link-status` → returns `{is_linked, wa_id, linked_at}` for the current operator.
- [ ] **Step 3:** `GET /pending-forwards` → list pending forwards for the operator with `suggested_client_name` resolved from join.
- [ ] **Step 4:** `POST /pending-forwards/{id}/confirm` body `{client_id}` → marks state=confirmed, calls `ExtractionPipeline.ingest_and_extract(operator_id, client_id, source_type='whatsapp_forward_shape_x', raw_text=forwarded_text + caption)`. Stores the new event_id back into `committed_event_id`.
- [ ] **Step 5:** `POST /pending-forwards/{id}/discard` body `{reason?}` → state=discarded, no extraction.
- [ ] **Step 6:** Tests (6+): auth, link-code generation, link-status, list pending, confirm with attribution-correct client, confirm with wrong-operator's pending (404), discard.
- [ ] **Step 7:** Commit: `feat(api): /whatsapp/link-code + /pending-forwards CRUD endpoints`.

### Task 11: ClientMatcher background pass (async after webhook returns)

**Files:**
- Modify: `backend/app/api/whatsapp_webhook.py`

- [ ] **Step 1:** After the webhook POST handler responds 200, schedule a BackgroundTask that fetches all just-inserted pending_forwards (state=pending, suggested_client_id IS NULL) and runs `ClientMatcher.suggest()` against each. Persist suggestions into `pending_forwards.suggested_client_id + suggested_confidence`.
- [ ] **Step 2:** Test: webhook returns 200 quickly; background task fires; pending_forwards.suggested_client_id populated.
- [ ] **Step 3:** Commit: `feat(api): background client attribution suggestion for new pending_forwards`.

### Task 12: Web — WhatsApp settings + /link code page

**Files:**
- Create: `web/lib/api/whatsapp-link.ts`
- Create: `web/app/dashboard/settings/whatsapp/page.tsx`
- Create: `web/components/whatsapp/link-instructions.tsx`

- [ ] **Step 1:** Typed client: `issueLinkCode()` + `getLinkStatus()`.
- [ ] **Step 2:** Settings page server-fetches status. If unlinked: render `<LinkInstructions />` with a "Generate link code" button → calls issueLinkCode → shows the 6-digit code + WhatsApp number + "Send `/link 482917` to +65 X from your WhatsApp" copy.
- [ ] **Step 3:** If linked: shows "Linked to +65 91234567 since 2026-05-20".
- [ ] **Step 4:** Commit: `feat(web): WhatsApp settings page with /link code generation`.

### Task 13: Web — Pending forwards tray

**Files:**
- Create: `web/lib/api/pending-forwards.ts`
- Create: `web/app/dashboard/pending/page.tsx`
- Create: `web/components/whatsapp/pending-forward-card.tsx`
- Create: `web/components/whatsapp/client-picker.tsx`
- Modify: `web/app/dashboard/layout.tsx` (badge with pending count in header)
- Create: `web/tests/unit/pending-forward-card.test.tsx`

- [ ] **Step 1:** Typed client: `listPending`, `confirmForward(id, clientId)`, `discardForward(id, reason?)`.
- [ ] **Step 2:** `PendingForwardCard` shows forwarded text + caption + suggested client (if any) + confidence badge + three buttons (Confirm suggestion / Change / Discard). Change reveals `<ClientPicker />` dropdown.
- [ ] **Step 3:** Pending page fetches list, renders cards, polls every 10s to surface new arrivals.
- [ ] **Step 4:** Header badge: server-fetch pending count, render `<Link href="/dashboard/pending">{count}</Link>` if > 0.
- [ ] **Step 5:** Unit tests for PendingForwardCard: renders, Confirm button calls confirmForward with suggested id, Change shows picker, Discard fires discardForward.
- [ ] **Step 6:** Commit: `feat(web): pending forwards tray + header badge + Confirm/Change/Discard UI`.

### Task 14: E2E test (manual — needs real Meta test number)

**Files:**
- Create: `web/tests/e2e/whatsapp-forward.spec.ts` (skipped in CI; documented manual steps)

This is hard to automate fully because it requires a real WhatsApp client forwarding to the test number. Write the spec as a documented checklist that runs against a real setup:

1. Operator signs up, links WhatsApp via `/link CODE`
2. Operator forwards a real message + caption from their phone
3. Within 30s, pending forward appears in dashboard tray with suggested client
4. Operator clicks Confirm → event created, extraction runs, fact appears on client's Facts tab

The Playwright spec covers steps 3-4 (UI assertions) once a row exists in pending_forwards; the inbound delivery (step 2) is verified manually.

- [ ] **Step 1:** Spec uses a service-role-inserted pending_forwards row as the test fixture; assertion validates the operator's confirm flow ends with a fact visible on the client.
- [ ] **Step 2:** Commit: `test(e2e): pending forward confirm UI (manual webhook fixture)`.

### Task 15: SCHEMA_REFERENCE + decision ledger + CLAUDE.md

**Files:**
- Modify: `supabase/SCHEMA_REFERENCE.md`
- Modify: `docs/decisions/decision-ledger.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1:** SCHEMA: add `operator_whatsapp_links` + `pending_forwards` sections.
- [ ] **Step 2:** Decision ledger:
  - **AI: Meta Cloud API directly (defer Twilio + verification)** — rationale: same stack at scale, no per-message fee, test number is free for inbound-unlimited dev.
  - **UX: Caption pairing via second-message-within-60s heuristic** — rationale: Meta delivers forward + caption as two messages; pairing happens in the webhook, escape hatch is operator manually associating in dashboard.
  - **OPS: Operator WhatsApp linking via /link CODE inbound-only** — rationale: avoids requiring outbound message capability (not available on test number for >5 recipients); user types code from dashboard into their WhatsApp once.
- [ ] **Step 3:** CLAUDE.md status advances to Plan 4 complete; Next flips to Plan 4.5 (forwarded voice/images + outbound notifications) OR Plan 5 (file drop / room attachments).
- [ ] **Step 4:** Commit: `docs: Plan 4 completion — SCHEMA + decision ledger + CLAUDE.md`.

### Task 16: Local CI sweep + push + PR + v0.4.0 tag

**Files:** none (verification + release).

- [ ] **Step 1:** `cd backend && ruff check . && mypy app && pytest`. Fix anything red.
- [ ] **Step 2:** `cd web && npm test && npx tsc --noEmit && npm run build`. Fix anything red.
- [ ] **Step 3:** Push branch.
- [ ] **Step 4:** `gh pr create --base main` with body summarizing landed + test plan (manual webhook smoke test required before merge).
- [ ] **Step 5:** Wait for CI; merge when green.
- [ ] **Step 6:** Tag `v0.4.0` + push tag.
- [ ] **Step 7:** Update CHANGELOG via release branch + PR (same pattern as v0.3.0).

---

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Meta webhook payload schema differs from assumed shape | Med | Task 1 captures real payload before coding the parser; pivot documented |
| Caption pairing heuristic wrong (operator sends forwards + caption in unexpected order) | Med | 60s window is conservative; escape hatch = operator can re-associate in dashboard (Plan 4.5) |
| Operator forgets to send `/link CODE` → all their forwards silently dropped | Med | Settings page surfaces unlinked state prominently; webhook logs unlinked-sender forwards so we can detect + nudge |
| ClientMatcher suggests wrong client → operator confirms without thinking | Low | Confidence < 0.85 surfaces "Change" prominently; suggestion never auto-confirms (always requires click) |
| Webhook signature verification too strict (rejects valid Meta requests) | Low | Use Meta's `X-Hub-Signature-256` reference impl; smoke test in Task 9 validates against real delivery |
| Test number 5-recipient limit blocks demo to multiple agents simultaneously | Low | Pre-register up to 5; documented in Plan 4.5 trigger (Business verification kicks off when first non-tester agent signs up) |
| HTTP body re-read after signature verify breaks payload parse | Med | Use `await request.body()` once, store bytes, then `model_validate_json(bytes)` — same bytes for both signature + parse |

---

## Done Criteria

- Operator can sign up, navigate to Settings → WhatsApp, generate a /link CODE, send `/link CODE` from their WhatsApp to the test number, and see Settings flip to "Linked".
- Operator forwards a real WhatsApp message + caption "Sarah Tan" to the test number → within 30s a pending forward appears in the dashboard tray with "Sarah Tan" pre-suggested as the client (if a client by that name exists).
- Operator clicks Confirm → an event with `source_type='whatsapp_forward_shape_x'` is created on Sarah's client KB; extraction runs; new facts appear on the Facts tab.
- All backend tests pass; web build + Vitest pass; CI green.
- Plan 1-3 paths still work (regression: existing E2Es pass).
- `v0.4.0` tagged on `main`; CHANGELOG entry written.
