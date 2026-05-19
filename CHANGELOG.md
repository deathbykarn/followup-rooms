# Changelog

All notable changes to FollowRoom will be documented here. Plain language for the builder, not commit messages.

Format: `## [SemVer] — YYYY-MM-DD`. Most recent first.

---

## [0.4.0] — 2026-05-19

**WhatsApp ingestion — forward a client message, see it land in their KB.**

What you can now do, end-to-end:

- Link your WhatsApp once: dashboard → **Settings → WhatsApp** → generate a 6-digit code → send `/link <CODE>` from your WhatsApp to the FollowRoom number → settings flips to "Linked".
- Forward any client message in WhatsApp to the FollowRoom number with a name caption (e.g., "Sarah Tan"). Within seconds, a pending forward appears in your dashboard's **Pending** tray (header badge shows the count).
- The system suggests which client the forward is about, using a two-pass match: exact name/alias match first (95% confidence), then Haiku-disambiguation if there's ambiguity. You see the suggested client + confidence on the pending card.
- Click **Confirm Sarah Tan** (or **Change** to pick a different client) → extraction runs against the forwarded text (with caption inlined as context) → new facts appear on the client's Facts tab.
- Discard ignores the forward; no extraction runs, no client KB is touched.

Under the hood:

- `POST /whatsapp/webhook` verifies Meta's HMAC-SHA256 signature on every inbound, dedupes by `wa_message_id` (UNIQUE constraint at DB level — webhook retries are safe), handles the `/link CODE` handshake, inserts pending forwards, and pairs captions to forwards within a 60-second same-sender window.
- ClientMatcher runs in a BackgroundTask after the webhook returns 200 — so Meta gets a fast ack while attribution suggestion happens asynchronously.
- Operator commit is the canonical attribution authority — the system never auto-confirms (even at 95% confidence). Plan 2's "zero misattribution" rule preserved structurally.
- Two new tables: `operator_whatsapp_links` (wa_id ↔ operator_id with `/link CODE` handshake fields) and `pending_forwards` (state machine + LLM suggestion + commit audit).
- Backend deployed to **Render** (free tier; flag to upgrade before external onboarding because of 15-min spindown) at `https://followup-rooms-backend.onrender.com`.

Known limitation (read this before celebrating):

- **Real-world end-to-end smoke is gated on Meta Business Verification.** Meta test phone numbers are not addressable from arbitrary WhatsApp users on the consumer network — they only accept inbound from pre-registered test recipients, and appear as "Invite to WhatsApp" to ordinary users. Plan 4 ships with the full code path validated via unit + integration tests + a live webhook handshake against the deployed Render endpoint, but the actual "forward from your phone → see it in the tray" loop requires a production phone number, which requires Meta Business Verification (1-2 wk review with ACRA docs).
- Plan 4.5 will kick off verification and unblock real-world testing. See `docs/findings/2026-05-19-meta-test-number-limitations.md` for the full debrief.

Testing the seam:

- 130 backend pytest (42 new for Plan 4)
- 15 web Vitest unit tests (5 new for PendingForwardCard)
- 4 Playwright E2E specs (1 new — `whatsapp-forward.spec.ts` uses an operator-session-inserted pending_forwards row as fixture, bypasses Meta delivery)

Known quirks:

- The System User access token we generated doesn't have WhatsApp asset scope (we skipped that step during setup). Plan 4 doesn't need it (inbound-only), but Plan 4.5 (outbound notifications + media download) will. Quick fix when we get there: add the WABA as an asset on the System User in Business Settings.
- `OPENAI_API_KEY` is still required by `Settings` even though we never call OpenAI. Should be made optional; flagged as Plan 4.5 cleanup.
- `requirements.txt` drifted from `pyproject.toml` between Plan 3 and Plan 4 deployment (missing `assemblyai` + `aiofiles`). Fixed; needs a CI check that fails on drift OR migration to `uv` as a single source.
- Render free tier 15-min spindown caused at least one missed smoke attempt during this session. Upgrade to Starter ($7/mo) before any real external testing.

---

## [0.3.0] — 2026-05-19

**Ingestion — drop a transcript or voice memo, get a profile update.**

What you can now do, end-to-end:

- Open a client → Upload tab → drop a transcript file (`.txt` / `.vtt` / `.srt`) or an audio file (`.mp3` / `.m4a` / `.wav` / `.ogg` / `.webm`) → the system stores it, transcribes if audio, extracts structured facts, regenerates the profile. A status card walks you through Queued → Transcribing → Extracting → Done so you can leave the page and come back.
- For multi-party transcripts (meetings, viewings), pick the **Transcript** option — AssemblyAI's diarization labels speakers and the extractor knows to prefer the client's own words over the operator's claims about the client when writing source spans.
- For solo reflections (the voice memo you record walking back to the car), pick the **Voice memo** option — diarization is skipped (one speaker) and the prompt treats your words as the source.
- When extraction finishes, the status card links straight to the Facts tab so you can accept/reject the new facts and see the updated profile.

Under the hood:

- AssemblyAI Universal-2 for transcription (October 2025 added mid-utterance code-switching — handles English / Mandarin / Singlish mixes cleanly). Wrapped in a `TranscriptionService` so swapping to Whisper / Deepgram is a constructor change.
- Async pipeline: POST /uploads stores to Supabase Storage, inserts an `ingestion_jobs` row, schedules a FastAPI BackgroundTask. The job table IS the durability layer — if a worker dies mid-flight, the row stays at its last set state (a Plan 3.5 watchdog will surface stuck jobs for retry).
- Text transcripts skip transcription; the worker downloads the bytes from Storage and goes straight to extraction.
- Audio uploads use signed Supabase URLs to feed AssemblyAI — no streaming bytes through the backend (keeps memory low on Render).
- `ExtractionPipeline` gained a new `extract_for_event()` entry so the ingestion worker can reuse Plan 2's match/persist/profile-regen path without re-inserting the event.
- New migrations: `0011_ingestion_jobs` (state machine + RLS), `0012_ingestion_uploads_bucket` (Supabase Storage bucket with 100MB cap, mime allowlist, per-operator folder RLS).

Testing the seam:

- 88 backend pytest (31 new)
- 10 web Vitest unit tests (4 new)
- 3 Playwright E2E specs (1 new — `upload-extraction.spec.ts`; skip in CI, run locally with real keys)

Known quirks:

- AssemblyAI is US-only (no APAC region). Plan 3.5 will add a one-line PDPA disclosure to operator onboarding when the first external SG agent signs up.
- AssemblyAI key needs to be in `backend/.env` as `ASSEMBLYAI_API_KEY`. Same `load_dotenv` precedence gotcha as `ANTHROPIC_API_KEY` — if your shell has the var exported with an old value, `.env` is ignored. `unset ASSEMBLYAI_API_KEY` before starting the backend, or rely on Render setting it in prod.
- Multi-party audio diarization quality depends on recording conditions; speaker labels are A/B/C (no name mapping). Operator-vs-client attribution uses a "most words wins" heuristic in the prompt — works for typical viewings but may be wrong if the operator talks less.

---

## [0.2.0] — 2026-05-18

**Core Knowledge Base — operator can teach the system, the system synthesizes a profile.**

What you can now do, end-to-end:

- Open a client → write a note about what you just learned → the system pulls Claude in, extracts structured facts (budget, viewing preference, objections, family dynamics, decision blockers, etc.) with verbatim citations back to your note, and tells you what changed (X added · Y updated · Z no-op · profile refreshed) in one receipt.
- Review each extracted fact on a Facts tab — accept the keepers, reject the wrong ones. Rejected facts soft-delete and stop influencing the profile.
- Read a synthesized profile of the client in two views — **Internal** (operator-only; includes sensitive sections like spouse/family factors, emotional hesitation, decision blockers) and **Client-facing** (filtered to shareable content). Toggle between them. Hit Regenerate to refresh either view from the current accepted facts.

Under the hood:

- Real Anthropic extraction (Sonnet 4.6 via `instructor` for typed output) with mandatory source spans on every fact — no fact exists without a citation back to the event it came from.
- ADD / UPDATE / NOOP / DELETE matching per extracted fact against existing active facts of the same type. Updates supersede instead of overwrite — the prior fact stays in history with `superseded_by` pointing to the new one.
- Two profile views stored as separate columns on the client (`internal_profile_md`, `client_facing_profile_md`); the sensitive-fact filter lives in code, backed by tests, so the client view is structurally guaranteed to never leak operator-only fact types.
- Synchronous extraction in the POST /events handler for Phase 2 (queue deferred to Phase 3 when volume justifies — see decision ledger).
- Migration 0010 ships the profile columns; `apply_migrations.py` now tracks applied files in `public._migrations` so re-runs are idempotent.

Testing the seam:

- 57 backend pytest (mocked Anthropic + supabase)
- 6 web Vitest unit tests (FactCard interactions)
- 2 Playwright E2E specs (skip in CI; locally exercise the full note → extract → reject loop with real Anthropic)

Known quirks:

- Backend URL is read from `NEXT_PUBLIC_BACKEND_API_URL` on the frontend (client components forward your Supabase JWT to FastAPI directly). Set this in `web/.env.local`.
- `load_dotenv()` doesn't override existing shell env vars — if your shell has an old `ANTHROPIC_API_KEY` exported, the `.env` value is ignored. `unset ANTHROPIC_API_KEY` before starting the backend, or rely on Render setting it directly in prod.

---

## [0.1.0] — 2026-05-18

**Foundation — deployable shells + schema + first user can sign up.**

- Backend FastAPI shell deployable to Render; web Next.js 16 + Tailwind 4 + shadcn shell deployable to Vercel.
- Supabase schema: 7 tables + 1 placeholder view across 9 migrations (operators, clients, events, facts, room_attachments, attributions, visibility_promotions, rooms_public view). RLS enabled per-operator everywhere.
- Forward-compat hooks baked in from day one per the design doc: append-only triggers on `events.raw_text` and attachment file identity, soft-delete + bi-temporal columns, per-principal attribution table, single `store()` write path, vendor-agnostic `AgentDispatcher`, three visibility tiers.
- Auth: Supabase Auth + `@supabase/ssr` with request-scoped client factories (no cross-user session leaks on serverless).
- First user flow: signup → email verify (off in dev) → log in → create client with required ≥20-char `short_context` → see client on dashboard.
- `DESIGN.md` + `PRODUCT.md` authored as brand/voice memory (Impeccable tooling deferred to Phase 1.5).
- CI: backend + web GitHub Actions; ruff + mypy + pytest on backend, tsc + vitest + next build on web.

---

## [0.0.1-foundation] — 2026-05-16

Repo doctrine and folder structure established. PRD v0.2 imported. `PROJECT_DEV_SOUL.md` adapted from Decades. `.husky/pre-commit` blocks direct commits to `main` and symlinks under `docs/` / `.claude/`.
