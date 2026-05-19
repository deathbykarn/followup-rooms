# ROADMAP — FollowRoom

**Sources of truth:** PRD v0.2 §23 for product phases; `docs/superpowers/plans/` for execution plans; `CHANGELOG.md` for shipped versions; `docs/decisions/decision-ledger.md` for the why behind every deviation.

This file reconciles the two views: PRD phase progress (the product north star) on one axis, execution plans (how we actually shipped it) on the other.

Status legend: `□ pending` · `◐ in progress` · `■ shipped` · `⊘ deferred (with rationale)`

---

## Where we are right now (2026-05-19)

**Current version:** `v0.4.0` on `main`. Backend deployed to Render at `https://followup-rooms-backend.onrender.com`. Web app deployable to Vercel (run locally for now).

**What an operator can do end-to-end today:**

1. Sign up → land in the dashboard → create a client with a short_context
2. Add a manual note about that client → Claude extracts typed facts → review on Facts tab → accept/reject
3. Upload a transcript (.txt/.vtt/.srt) or voice memo (.mp3/.m4a/.wav/.ogg) → status card walks queued → transcribing → extracting → done
4. (Pending Meta Business Verification) Forward a WhatsApp client message + name caption → see it in the Pending tray → click Confirm → extraction runs → facts land in the client KB
5. View synthesized profile in two views (internal + client-facing) → toggle + regenerate

**What's NOT yet built (the gap to full PRD Phase 1):**

- Client-facing dynamic HTML room (Plan 6 / PRD Phase 1 "Client-facing dynamic HTML room")
- Room update approval flow (PRD Phase 1)
- Suggested-reply generation (PRD Phase 1)
- Generic review queue (we have a pending-forwards tray; the broader low-confidence review queue is Plan 5)
- File drop / room attachments (Plan 5; PRD design doc §5.5)
- Cross-relationship meta insights (PRD Phase 2 territory)

**Stack snapshot:**
- Backend: FastAPI on Render (free tier; upgrade to Starter before external onboarding)
- Web: Next.js 16 + Tailwind 4 + shadcn/ui; Vercel target
- Data: Supabase Postgres (14 migrations applied, RLS per-operator everywhere)
- AI: Anthropic Sonnet 4.6 for extraction/profile/matching; Haiku 4.5 for ClientMatcher; AssemblyAI Universal-2 for transcription
- Ingestion: manual note, transcript/voice upload, WhatsApp Shape X forward
- Tests: 130 backend pytest, 15 web Vitest, 4 Playwright E2E (E2E skip in CI)

---

## Execution plans (chronological)

| # | Plan | Tag | Status | Doc |
|---|------|-----|--------|-----|
| 1 | Foundation — deployable shells + schema + first user flow | `v0.1.0` | ■ shipped 2026-05-18 | `docs/superpowers/plans/2026-05-18-foundation.md` |
| 2 | Core KB Layer — extraction → facts → profile | `v0.2.0` | ■ shipped 2026-05-18 | `docs/superpowers/plans/2026-05-18-core-kb-layer.md` |
| 3 | Ingestion: transcript + voice upload | `v0.3.0` | ■ shipped 2026-05-19 | `docs/superpowers/plans/2026-05-18-ingestion-transcript-voice.md` |
| 4 | WhatsApp Shape X ingestion (inbound) | `v0.4.0` | ■ shipped 2026-05-19 (smoke gated on Meta Business Verification) | `docs/superpowers/plans/2026-05-19-whatsapp-ingestion.md` |
| 4.5 | WhatsApp Plan 4 follow-ups + ops debt | — | □ queued | TBD |
| 5 | File drop / room attachments | — | □ queued | TBD |
| 6 | Client-facing room (slug + PIN) + room update approval | — | □ queued | TBD |
| 7+ | Suggested reply, review queue, vertical templates, integrations | — | □ queued | TBD |

---

## Plan 4.5 — WhatsApp follow-ups + accumulated ops debt

**Why this plan exists:** Plan 4 shipped with a real smoke-test gap (Meta test number can't receive from arbitrary WhatsApp users) and a handful of small debts accumulated across Plans 3-4. Bundle them so we ship a "WhatsApp actually works in the real world" version + clean the dust.

**Goal:** real operator can use WhatsApp forwarding end-to-end against a verified production number, with outbound notifications and rich-media handling.

Trigger: kick off when first external SG agent is ready to test (the verification gate is the natural moment).

Items:

- □ **Meta Business Verification kickoff** — submit ACRA docs to Business Manager. 1-2 wk review. Required for production phone number, which is required for inbound from arbitrary WhatsApp users.
- □ **Production phone number provisioning** — once verified, register a real WhatsApp Business number; swap in `.env` + Render
- □ **WABA asset assignment on permanent System User token** — currently missing; blocks outbound + media downloads
- □ **Outbound "you have N pending" push back to operator's WhatsApp** — uses the same Cloud API, incremental work on top of inbound
- □ **Forwarded voice notes** — download from Meta CDN → reuse Plan 3 ingestion pipeline (`source_type='whatsapp_forward_shape_x'` with audio)
- □ **Forwarded images** — download → store in `room_attachments` (Plan 5 schema, partial reuse)
- □ **Forwarded documents (PDF, etc.)** — same as images path
- □ **Session-lock variant** — "auto-attach next 5min to Sarah Tan" after operator confirms once, to reduce per-forward tap cost
- □ **PDPA disclosure in operator onboarding** — one-line copy about AssemblyAI (US) + Meta (US) data processing. Carried over from Plan 3.
- □ **Upgrade Render from free → Starter ($7/mo)** — eliminates 15-min spindown that masks webhook delivery
- □ **Make `OPENAI_API_KEY` optional in Settings** — we don't use OpenAI; this was the "extra field" that blocked deploy twice during the smoke session
- □ **CI check: `pyproject.toml` ↔ `requirements.txt` drift** — Plan 3 added `assemblyai` to pyproject but not requirements.txt, which broke Plan 4 deploy. Either add a drift check OR migrate to `uv` as single source.
- □ **Render auto-deploy from `main`** — currently tracks `feat/whatsapp-plan-4`; flip after Plan 4 merge stabilizes
- □ **Watchdog endpoint for stuck ingestion jobs** — pending_forwards / ingestion_jobs rows can get stuck if BackgroundTask dies mid-flight. Surface in UI for operator retry.

---

## Plan 5 — File drop / room attachments (operator → client)

**Why:** Per the design doc §5.5, file drop is a peer ingestion channel to transcripts/voice, not a footnote. Property agents drop floor plans, comparables, MyAnchor links, calculators, viewing photos constantly. **This is the bridge to Plan 6 (client-facing room)** — without attachments, the room is just text.

Goal: operator drops a file against a client with a pending-action type → file lands in `room_attachments` (visibility=operator_only by default) → operator can promote to client_facing_safe → file becomes visible in the client's room.

Items (sketch — needs its own plan doc):

- □ Mobile camera capture / file picker upload
- □ Desktop drag-and-drop
- □ iOS / Android Share Sheet integration ("Share to FollowRoom")
- □ URL paste (property listings, Google Drive shares)
- □ Operator note + pending_action_type (for_review / for_signature / for_consideration / for_payment / informational)
- □ Visibility tier promotion flow
- □ PDF text extraction for in-room search
- □ Image OCR for property docs

Reuses: existing `room_attachments` table (Plan 1 forward-compat hook), Plan 3 storage upload pattern, Plan 2 extraction prompt for OCR'd text.

---

## Plan 6 — Client-facing rooms + room update approval

**Why:** The headline promise — *"meeting transcripts become meeting rooms"* — isn't real until clients can actually open a room. Without this, FollowRoom is half a product. Per the design doc, this is the moment the marketing pitch becomes demonstrable.

Goal: every client has a private shareable URL (word-phrase slug + optional 6-digit PIN); operator can preview the room, approve updates that change what's visible; client visits the URL on any device + sees a polished page with their docs, key facts, and progress.

Items (per design doc §6.8 + §11.15-16):

- □ `rooms` table with `public_slug` (forest-river-amber style) + `passcode_hash` + room metadata
- □ Public `/r/<slug>` route (anonymous; passes PIN check if set)
- □ `rooms_public` view materialization (currently a Phase 1 placeholder)
- □ Room layout: client name header, key facts surfaced from `client_facing_profile_md`, attached docs from `room_attachments` (filtered to `client_facing_safe`), pending actions
- □ Room update draft → operator review → approve/edit/discard
- □ Per-attachment visibility promotion UI (operator clicks "show in room")
- □ Revoke + regenerate slug (with 24h grace screen for already-shared links)
- □ Optional 6-digit PIN with rate-limited brute-force protection
- □ Aggregate view tracking (yes/no, last-seen relative dates; per §11.16 decision — never raw timestamps without explicit drill)
- □ Client-side transparency footer ("Learn what's tracked")
- □ WhatsApp send helper ("send room link to client" copy-button)

---

## Plan 7+ (sketched, sequencing TBD)

- **Suggested reply generation** — Sonnet-drafted WhatsApp follow-up text the operator copy-pastes from dashboard (no outbound from us; the operator hits Send themselves)
- **Generic review queue** — beyond pending forwards: low-confidence facts, ambiguous client matches, room updates pending operator approval
- **Cross-relationship meta insights** — "you promised floor plans to 3 clients this week" / "Marine Parade interest cluster across 5 clients"
- **Vertical templates** — real estate buyer, seller, commercial property, etc. (PRD Phase 3)
- **Integrations** — Google Calendar, Drive, Zoom, Otter, HubSpot, Zapier (PRD Phase 5)
- **WhatsApp Coexistence (Flavor 1)** — auto-sync WhatsApp Business app conversations into FollowRoom KB (Phase 3 design doc; requires WhatsApp Business app on operator's side)
- **Optional bot layer** — slash commands, confirmation replies, proactive reminders (PRD Phase 6; only if user demand proves it)
- **Hivemind tier** — agency multi-operator, shared client visibility, team templates (PRD Phase 4 + design doc §3.3)

---

## PRD phase mapping (where we stand against the canonical scope)

PRD v0.2 §23 has 5 phases. Our execution plans cut across them differently — most of Plans 1-4 ship Phase 1 + 1.5 items, and a few Phase 2 items snuck in early (extraction with provenance, fact memory).

### Phase 0 — Prototype  ⊘ (skipped — went straight to MVP)

Per PRD: "prove output quality" with throwaway code. We made the call early to skip this and validate against real architecture from Plan 1. Reason: doctrine debt — using throwaway code would have undermined the forward-compat hooks in Plan 1 (append-only triggers, RLS, attribution).

### Phase 1 — Web-First MVP  ◐ in progress (~70% shipped)

| Item | Status | Notes |
|------|--------|-------|
| Operator dashboard (home + client list + tabs) | ■ | Plans 1-2-3 |
| Client creation (manual) | ■ | Plan 1 |
| Client creation (from transcript) | ■ | Plan 3 (transcript upload + auto-extract to existing client) |
| Client creation (from forwarded snippet) | ◐ | Plan 4 confirms forward against existing client; new-client-from-forward UX is Plan 4.5 |
| Internal memory (relationship summary, facts, events, tasks) | ■ for summary/facts/events; □ tasks (Plan 7) | Plan 2 |
| Client-facing dynamic HTML room | □ | Plan 6 |
| Transcript upload / paste | ■ | Plan 3 |
| WhatsApp snippet paste (manual into dashboard) | ■ | Plan 2 (manual note flow works for this) |
| Generic event ingestion model (polymorphic) | ■ | Plan 1 schema; Plans 2-4 extend |
| AI extraction with confidence scores | ■ | Plan 2 |
| Client matching (rules first) | ■ | Plan 4 ClientMatcher (fuzzy + Haiku); pgvector deferred to Plan 7+ |
| Review queue | ◐ | Plan 4 has pending-forwards tray; broader review queue (low-conf facts, ambiguous matches, room update pending) is Plan 5/6 |
| Suggested reply | □ | Plan 7 |
| Room update approval flow | □ | Plan 6 |
| Basic cross-relationship meta insights | □ | Plan 7+ |
| Supabase schema + RLS | ■ | All 14 migrations have per-operator RLS |
| Architecture ready for WhatsApp webhook | ■ | Built into the schema from Plan 1; activated in Plan 4 |

### Phase 1.5 — Silent WhatsApp Forwarding Inbox  ◐ ~80% shipped

| Item | Status | Notes |
|------|--------|-------|
| WhatsApp Business Platform number provisioned | ◐ | Test number active; production needs Business Verification (Plan 4.5) |
| Inbound webhook endpoint | ■ | Plan 4 |
| Forwarded-message event creation | ■ | Plan 4 (confirm flow → ingest_and_extract with source_type='whatsapp_forward_shape_x') |
| Client matching on inbound events | ■ | Plan 4 ClientMatcher |
| Dashboard review queue surfaces low-confidence matches | ■ | Plan 4 pending-forwards tray |
| No outbound replies by default | ■ | Plan 4 inbound-only by design |

### Phase 2 — Relationship Memory System  ⊘ (post-MVP per PRD)

Items partially shipped early (Plans 2-3 included them because they were near-free to add given the architecture):

- ■ Fact memory with provenance / receipts (Plan 2 — source_spans mandatory)
- ■ Event timeline view (partial — Overview tab shows recent events)
- □ Open loops surfacing
- □ Follow-up task intelligence (auto-suggested due dates, stale detection)
- □ Room update diffing
- □ Search across clients (full-text + semantic)
- □ Better client matching (pgvector)

### Phase 3 — Vertical Templates  ⊘

Templates: real estate buyer, seller, commercial property, insurance, wealth advisory, renovation, B2B sales.

Decision: defer until we have real users in the real estate vertical generating signal about what to template. Plan 7+.

### Phase 4 — Collaboration & Team  ⊘

Multi-user accounts, shared branding, manager view, team templates, permissioning, audit logs. Maps to design doc Phase 3 (Hivemind tier). Plan 10+.

### Phase 5 — Integrations  ⊘

Google Drive, Calendar, Zoom, Otter, HubSpot, Salesforce, Zapier/Make, Email. Plan 9+.

### Phase 6 — Optional Conversational Bot Layer  ⊘ (only if user demand proves strong)

WhatsApp confirmation replies, command flow, reminders, proactive templates. Explicitly out of MVP per PRD.

---

## Versioning & Release Strategy

- Major.Minor.Patch. Pre-MVP work tagged `v0.0.x` → `v0.x.0` for each shipped plan.
- Every shipped build tagged. `CHANGELOG.md` updated with each tag (plain-language for the builder).
- Release notes never duplicate commit messages; they describe what an operator can now do.
- v1.0.0 = the first version we'd let an external paying agent use day-to-day (currently estimated: after Plan 6, with at least one PRD Phase 1.5 production deployment).

---

## Frozen Constraints

These are non-negotiable through PRD Phase 1.5. Any proposal that violates one must be raised explicitly and entered into the decision ledger before implementation.

1. **WhatsApp endpoint is silent.** No outbound replies. No MCQ. No slash commands. *(Plan 4.5 adds an outbound notification but only as a "you have N pending" nudge — never client-facing.)*
2. **No auto-publish to client-facing surfaces.** Operator approval gates everything visible to clients.
3. **Internal vs client-facing memory are separate stores with separate visibility.** Tactful rewrite happens at publish, not at ingestion. *(Plan 2 enforces this structurally via two profile columns + the SENSITIVE_FACT_TYPES filter.)*
4. **Sensitive inferences (family dynamics, emotional state) never auto-publish.** Even with operator approval, the rewrite layer must strip these before they reach the client room.
5. **Source events are append-only.** Re-extraction creates new derived rows; never mutates raw. *(Enforced by triggers on `events.raw_text` and storage object immutability on `room_attachments`.)*

---

## How this roadmap stays accurate

- Updated on every plan completion (single line item flips `□` → `■`, status block at the top refreshed)
- Plan 4.5 items list is the canonical "stuff we owe ourselves" — every "follow up later" the decision ledger references should be in there
- New plans get added to the table when they're written; doc path filled in once committed
- PRD phase mapping refreshed when a substantial new item lands or a deferred decision shifts category
