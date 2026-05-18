# Decision Ledger

**Purpose:** Authoritative record of architectural and product decisions for FollowRoom.
**Max items:** 20-30 active. Archive older decisions to `decision-ledger-archive.md` when this exceeds 30.
**Format:** Most recent first.

Categories: `ARCH` (architecture), `PROD` (product), `DATA` (database), `UX` (user experience), `OPS` (operations), `AI` (AI/prompts), `PRIV` (privacy).

---

## Active Decisions

### [2026-05-18] AI: Phase 2 extraction synchronous in POST /events (deferred queue to Phase 3)

**Context:** Plan 2 needed to choose between synchronous extraction (the POST /events handler calls Anthropic before returning) vs an async job queue. Synchronous keeps the architecture flat; async insulates the user from latency spikes and Anthropic outages.

**Decision:** Phase 2 ships synchronous. POST /events runs ExtractionPipeline (extract + match + persist + profile regen) inline; the response carries facts_added/updated/noop/deleted counters and profile_regenerated bool so the UI shows an immediate receipt. Phase 3 introduces a queue when volume (multiple WhatsApp events / transcripts per minute) or reliability concerns (Anthropic outages blocking the form) justify it.

**Rationale:** Phase 1 volume is per-operator manual notes — latency budget (~3-8s extraction + 5-15s profile regen) is acceptable in exchange for the simpler debug path. The receipt UX also reinforces operator trust: they see exactly what the model did. Queueing now would force premature design of retry / dead-letter / poll-status patterns with no real workload to validate against.

**Link:** `docs/superpowers/plans/2026-05-18-core-kb-layer.md` §ExtractionPipeline; `backend/app/services/extraction_pipeline.py`

### [2026-05-18] DATA: Internal vs client_facing profiles as 2 TEXT columns on clients (not separate table)

**Context:** Plan 2 needed to decide where to store the two profile markdown views (internal: operator-only, includes spouse/emotional/blocker facts; client_facing: filtered, shareable). Options: separate `client_profiles` table with a row per view; two TEXT columns on `clients`.

**Decision:** Two TEXT columns on `clients` — `internal_profile_md`, `client_facing_profile_md`, plus `profile_regenerated_at`. Migration 0010. ProfileService writes both on every regenerate; SENSITIVE_FACT_TYPES filter at the service layer guarantees the client_facing view never contains spouse_family_factor / emotional_hesitation / decision_blocker.

**Rationale:** profiles are 1:1 with clients and always regenerated together — a separate table adds JOIN cost with no flexibility win. The structural guard against leakage lives in code (SENSITIVE_FACT_TYPES) backed by tests, not schema. Phase 3 (agency tier) may add a third `agency_visible_profile_md` column or move to a separate table if profile fan-out grows.

**Link:** `supabase/migrations/0010_clients_profile_columns.sql`; `backend/app/ai/profile.py`

### [2026-05-18] OPS: Python 3.14 (not 3.12) for backend runtime

**Context:** Foundation plan originally pinned Python 3.12.7. During execution, implementer subagent reported BLOCKED — local machine only has Python 3.14.4 (no 3.12 installed). Pragmatic options: install 3.12 locally vs update plan to 3.14.

**Decision:** Pin Python 3.14.4 across local + Render + CI. Updated Foundation plan §Task 2, §Task 5 (Render config), §Task 6 (CI workflow) accordingly.

**Rationale:** May 2026 compat research (dispatched agent) confirmed:
- Full stack supports 3.14: FastAPI 0.136+, Uvicorn 0.47+ (with cp314 uvloop/httptools wheels), Pydantic 2.13+, supabase-py 2.30, anthropic 0.102, openai 2.37, instructor 1.15, pytest 9, ruff 0.15, mypy 2.1, psycopg 3.3.4 — all officially or runtime-compatible
- Render defaults to Python 3.14.3 for services created after Feb 11, 2026
- One soft caveat: httpx stable (0.28.1) lacks 3.14 PyPI classifier but runtime works; httpx 1.0 (dev) has 3.14 work in flight. Pinning `httpx>=0.28.1` and monitoring is sufficient.
- Avoiding a second Python install locally; matching dev + prod runtime exactly.

**Link:** `docs/superpowers/plans/2026-05-18-foundation.md` §Task 2 + §Task 5 + §Task 6

### [2026-05-18] UX: Client-facing room URL confidentiality — minimal 3-mechanism stack

**Context:** Operators share room links via WhatsApp; clients may forward to others. Sensitive details (financial discussion, family dynamics interpreted at internal-only tier) could leak. Initial design proposed 5 mechanisms (slug + accountability watermark + PIN + revoke + per-attachment view-only); review surfaced over-engineering and security theater concerns.

**Decision:** Adopt 3-mechanism stack: word-phrase slug (`forest-river-amber` pattern; cryptographically secure + premium-feeling) + optional 6-digit PIN with rate limiting + revoke/regenerate with 24h grace screen + WhatsApp send helper. Drop accountability watermark (room's natural client-name header provides implicit framing) and per-attachment view-only (security theater; doesn't prevent screenshots). Onboarding honestly states FollowRoom is for relationship continuity, not secure execution; direct operators to DocuSign for legally sensitive items.

**Rationale:** simplicity proportional to actual protection; honest framing builds operator trust; avoids overpromising.

**Link:** `docs/superpowers/specs/2026-05-18-followroom-architecture-design.md` §11.15

### [2026-05-18] UX: View tracking ethics — default aggregate + explicit audit drill

**Context:** Granular view tracking (minute-level timestamps, time-on-page, scroll depth) is technically easy but feels surveillance-y to clients and uncomfortable for operators to see. Erodes the Quiet Witness posture (Axiom 9).

**Decision:** Default operator UX shows aggregate signals (viewed yes/no; last-seen relative dates; acted yes/no + action type; pending-overdue boolean). Specific timestamps and sequences available only via explicit *"Show timeline"* drill. Architecturally never tracked: IP, fingerprint, location, time-on-page, scroll depth, third-party analytics. Client-facing transparency footer with plain-English "Learn what's tracked" link.

**Rationale:** the tracking surfaces what enables follow-up; everything more granular is in an audit view that operators must click for. Respects client dignity; preserves operator trust position.

**Link:** `docs/superpowers/specs/2026-05-18-followroom-architecture-design.md` §11.16

### [2026-05-18] DESIGN: Impeccable adoption deferred to Phase 1.5

**Context:** Impeccable is an open-source design discipline layer for AI-coding workflows (slop detection, design vocabulary, PRODUCT.md/DESIGN.md memory). 28k stars; credible builder background (Paul Bakaus). Strong fit for FollowRoom's client-facing room visual stakes.

**Decision:** Defer Impeccable tooling adoption to Phase 1.5. In Phase 1, author FollowRoom's own `DESIGN.md` and `PRODUCT.md` at the repo root (analogous to `PROJECT_DEV_SOUL.md` for engineering doctrine), capturing brand, audience, voice, anti-references from founder's lived-persona perspective. Reference Impeccable's anti-pattern catalog as a checklist during UI reviews (no tooling dependency). Adopt Impeccable's CLI (`detect` in CI, `audit` + `critique` for PR reviews) at Phase 1.5 when meaningful UI exists.

**Rationale:** at Phase 1 there's no UI to discipline; tooling overhead exceeds value. Authoring design memory first protects FollowRoom's specific soul from being anchored on Impeccable's templates. Impeccable still moving fast (frequent releases); Phase 1.5 entry will be more stable.

**Link:** `docs/superpowers/specs/2026-05-18-followroom-architecture-design.md` §9.8

### [2026-05-18] ARCH: FollowRoom architecture design doc committed as founding artifact

**Context:** Three-day architecture brainstorm (2026-05-16 → 2026-05-18) converged on a comprehensive design. Founding artifact needed to anchor Phase 1 implementation with explicit forward-compatibility hooks for Phases 2-3.

**Decision:** Design doc at `docs/superpowers/specs/2026-05-18-followroom-architecture-design.md` is the canonical architectural reference. Covers: product framing (FollowRoom as LineOS application, commercial spear to LineOS), 10 constitutional axioms, three-phase layering (Karpathy → Zettel → Hivemind = Solo MVP → Solo Pro → Agency Enterprise), pattern language inheritance (14 verbatim + 9 adapted from Decades), six ingestion channels with deterministic attribution, knowledge base architecture with attachment layer (room as active delivery surface), TG-lite governance, forward-compatibility hooks Phase 1 must bake in, tech stack with design discipline layer, felt-experience per phase, 16 risks with mitigations, 13 open implementation questions.

**Rationale:** the design doc is the contract between Phase 1 build and future phases. Subsequent implementation plans extend it; deviations require constitutional amendment via this ledger.

**Link:** `docs/superpowers/specs/2026-05-18-followroom-architecture-design.md`

### [2026-05-16] OPS: Repo doctrine bootstrapped from Decades

**Context:** New project. Builder already has 37 days of doctrine accumulated in the Decades repo (PROJECT_DEV_SOUL.md, multi-CLAUDE.md model, schema reference, husky guards, findings/postmortems/dailyimpact rituals). Reinventing this for FollowRoom would discard hard-won learnings; importing verbatim would carry Decades-specific scar tissue.

**Decision:** Adapt PROJECT_DEV_SOUL.md to FollowRoom while preserving its principles, architecture rules, and process. Mirror Decades' folder structure (`backend/` `web/` `supabase/` `docs/` plus per-domain CLAUDE.md, SCHEMA_REFERENCE.md, decision ledger, findings, dailyimpact). Replace `mobile/` (Expo) with `web/` (TBD stack) — FollowRoom is a web product.

**Rationale:**
- Doctrine compounds. Re-deriving it from scratch wastes the Decades investment.
- The seven core principles (evidence over assertion, source immutability, user authority over truth, etc.) translate directly: relationship events are sacred raw input; extracted facts are derived; client-facing publishes require explicit operator approval.
- File structure familiarity reduces cognitive overhead when context-switching between repos.

**Link:** `PROJECT_DEV_SOUL.md`, `CLAUDE.md`
