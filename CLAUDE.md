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
├── web/                            TBD — stack not yet locked
├── .claude/                        phase-plans, session-state, hooks, skills
├── .husky/pre-commit               Branch + symlink guards
├── .github/workflows/              CI / daily-impact email (future)
├── agents/                         Adapted reviewer roster
├── scripts/
└── drafts/                         WIP scratch
```

---

## Status

**Phase: pre-Phase 0.** Doctrine and folder structure scaffolded. Stack not yet locked. No code yet. See `.claude/session-state.md` for what's next.
