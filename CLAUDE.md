# CLAUDE.md — FollowRoom

**Dynamic client follow-up rooms. Silent WhatsApp ingestion + transcript upload → AI extraction → operator dashboard → approved client-facing rooms.**

---

## Resume Ritual (Start Here)

**After compaction or starting a new session:**

1. Read `.claude/session-state.md` for continuity
2. Check `git status` for uncommitted work
3. Read `docs/decisions/decision-ledger.md` for recent constraints
4. For database work: read `supabase/SCHEMA_REFERENCE.md` FIRST
5. For product principles: read `PROJECT_DEV_SOUL.md`
6. For phase context: read `ROADMAP.md`
7. PRD canonical: `docs/prd/followroom_prd_v0_2_silent_whatsapp_ingestion.md`

---

## Compaction Survival Protocol

**If unsure about:**
- Column names → `supabase/SCHEMA_REFERENCE.md`
- Product principles → `PROJECT_DEV_SOUL.md`
- Current phase → `ROADMAP.md`
- Previous work → `.claude/session-state.md`
- Why a thing was decided → `docs/decisions/decision-ledger.md`

**Before creating:**
- Migration → read latest in `supabase/migrations/` AND `SCHEMA_REFERENCE.md`
- New table → run RLS checklist in `supabase/CLAUDE.md`
- API endpoint → check patterns in `backend/app/api/` *(when backend lands)*
- UI surface → check patterns in `web/app/` *(when web lands)*

**After any decision:** record it in `docs/decisions/decision-ledger.md`.

---

## Hard Rules

### Git Discipline
- **Never commit directly to main.** All changes via feature branch + squash-merge PR. Enforced by `.husky/pre-commit`.
- Branch naming: `feat/*`, `fix/*`, `chore/*`, `docs/*`, `exp/*` off main.
- Conventional commits required: `feat()`, `fix()`, `chore()`, `docs()`.

### Documentation Doctrine
- **All FollowRoom documentation lives in this repo.** No cross-repo symlinks under `docs/` or `.claude/` — enforced by `.husky/pre-commit`. (See Decades' 2026-05-07 daily-impact symlink-rot postmortem for why.)
- Internal relative symlinks (build artifacts, regenerated venvs) are fine — only `docs/` and `.claude/` are symlink-free.

### Migration Safety (Non-Destructive)
- **Never** `DROP TABLE`, `DROP COLUMN`, or `ALTER COLUMN ... TYPE` on tables with user data without an explicit rollback plan.
- All schema changes follow expand → backfill → cutover → contract.
- Every migration file must include a `-- Rollback:` comment.
- Next migration number: check `supabase/migrations/` for the highest existing number.

### Sacred Data
- **Events are append-only.** `events.raw_text` (raw WhatsApp forwards, raw transcripts) is never mutated. Re-extraction creates new `extracted_facts` rows.
- **Soft-delete by default.** Clients/Rooms set `is_deleted = TRUE, deleted_at = NOW()`. Hard delete = explicit endpoint, grace period, audit trail.
- **No auto-publish to client-facing surfaces.** Internal memory updates may happen on high-confidence ingestion. Anything that becomes visible to the client requires operator approval through the dashboard.
- **No outbound WhatsApp by default.** The forwarding endpoint receives only. Outbound replies are not in MVP.

### Release Discipline
- SemVer tags on every shipped build.
- `CHANGELOG.md` updated with every tagged release (plain language for the builder, not commit messages).
- Tag the commit before release work begins (rollback point).
- Never force-push main.

---

## System Map

```
followup-rooms/
├── README.md                       Entry point, status
├── CLAUDE.md                       This file
├── PROJECT_DEV_SOUL.md             Constitution
├── ROADMAP.md                      Phase plan
├── CHANGELOG.md                    Release log
├── docs/
│   ├── prd/                        PRD versions (canonical: v0.2)
│   ├── decisions/decision-ledger.md   Architectural decisions
│   ├── findings/                   Multi-agent investigation memos (YYYY-MM-DD)
│   ├── postmortems/                Crisis writeups
│   ├── plans/                      Phase plans
│   ├── proposals/                  RFCs
│   ├── patterns/                   Pattern Language entries
│   ├── architecture/               Architecture docs
│   ├── systems/                    Per-system specs
│   └── dailyimpact/                Daily impact reports (DD-MM-YY)
├── supabase/
│   ├── CLAUDE.md
│   ├── SCHEMA_REFERENCE.md         Column source of truth
│   ├── migrations/                 Numbered, with -- Rollback: comments
│   ├── functions/                  Edge functions
│   ├── schema.sql
│   ├── scripts/
│   └── verify/                     RLS / schema drift checks
├── backend/                        TBD — stack not yet locked
├── web/                            Next.js 16 + Tailwind 4 + shadcn/ui + @supabase/ssr
├── .claude/                        phase-plans, session-state, hooks, skills
├── .husky/pre-commit               Branch + symlink guards
├── .github/workflows/              CI / daily-impact email (future)
├── agents/                         Adapted reviewer roster
├── scripts/
└── drafts/                         WIP scratch
```

---

## Status

**Phase: Phase 3 — Ingestion (transcript + voice) complete (2026-05-19).**

What's standing (Plans 1 + 2 + 3):
- Deployable backend (FastAPI on Render) + frontend (Next.js 16 on Vercel) shells
- Supabase schema: 8 tables + 1 view + clients profile columns + ingestion_jobs (12 migrations applied; `_migrations` tracking table)
- Storage bucket `ingestion-uploads` with per-operator RLS (100MB cap, text + audio mimes)
- Forward-compatibility hooks per design doc §8 (append-only triggers, soft-delete + bi-temporal, per-principal attribution, `store()` write path, `AgentDispatcher`, visibility tiers)
- Auth: Supabase Auth + `@supabase/ssr` with cross-user session leak prevention (request-scoped factories)
- **Extraction pipeline (Plan 2):** POST /events → ExtractionService (Anthropic + instructor) → MatchingService (ADD/UPDATE/NOOP/DELETE) → fact persistence → ProfileService regenerates both `internal_profile_md` + `client_facing_profile_md`
- **Ingestion pipeline (Plan 3):** POST /uploads (multipart) → Supabase Storage → BackgroundTask worker walks queued → transcribing (AssemblyAI Universal-2 + diarization) → extracting (reuses Plan 2 pipeline via new `extract_for_event` entry) → done. Text transcripts skip transcription; voice memos disable diarization
- **Operator dashboard:** client list → client detail with tabs (Overview / Add note / Upload / Facts / Profile); FactCard with Accept/Reject; ProfileViewer toggles internal vs client_facing + Regenerate; UploadForm with react-dropzone + IngestionStatusCard polling state
- DESIGN.md + PRODUCT.md authored (Impeccable deferred to Phase 1.5)
- Tests: 88 backend (pytest), 10 frontend unit (Vitest), 3 E2E specs (Playwright; skip in CI, run locally with backend + real ANTHROPIC_API_KEY)
- CI: backend + web GitHub Actions workflows

Plan 3 decisions in `docs/decisions/decision-ledger.md`:
- AssemblyAI Universal-2 for transcription (best diarization + code-switching for SG market); PDPA mitigation via onboarding disclosure (Plan 3.5)
- FastAPI BackgroundTasks for async; ingestion_jobs table IS the durability layer (Arq+Redis deferred to scale signal)

Plan 2 decisions (still active):
- Sync extraction in POST /events; profile columns on clients (not separate table); NEXT_PUBLIC_BACKEND_API_URL for frontend→FastAPI calls

Plan 1 deviations (still active):
- Python 3.14.4 (not 3.12.7); Next.js 16 (proxy.ts not middleware.ts); Tremor skipped (React 18); dashboard at `/dashboard`

Next:
- Plan 4 — WhatsApp ingestion (Shape X forwarding with operator commit; Meta Cloud API + webhook + push notifications)

References:
- Design doc: `docs/superpowers/specs/2026-05-18-followroom-architecture-design.md`
- Plans: foundation, core-kb-layer, ingestion-transcript-voice in `docs/superpowers/plans/`
- Findings: `docs/findings/2026-05-18-assemblyai-validation.md`
- Schema: `supabase/SCHEMA_REFERENCE.md`
