# Session State — 2026-05-16

**Saved:** 2026-05-16 (initial scaffold)
**Active branch:** `main` (no commits yet)
**Open PRs:** 0

## Where we are

**Pre-Phase 0.** Repo just initialized. GitHub remote `deathbykarn/followup-rooms` exists but is empty. Today's session set up doctrine and folder structure mirroring Decades.

## What shipped today

- Folder tree: `backend/` and `web/` deferred until stack lock; `docs/`, `supabase/`, `.claude/`, `.husky/`, `.github/`, `agents/`, `scripts/`, `drafts/` scaffolded
- PRD v0.2 moved to `docs/prd/`
- `PROJECT_DEV_SOUL.md` adapted from Decades
- `CLAUDE.md` (root) — golden rules + resume ritual
- `ROADMAP.md` — phases mirrored from PRD §23
- `CHANGELOG.md`, `README.md`, `docs/decisions/decision-ledger.md` initialized
- `.gitignore`, `.husky/pre-commit` (block direct main + symlinks under docs/.claude)
- `supabase/CLAUDE.md`, `supabase/SCHEMA_REFERENCE.md` placeholders

## Pending / parked

- **Stack lock.** PRD recommends Next.js + FastAPI + Supabase. Final call deferred until next message. Once locked: scaffold `backend/` and `web/`.
- **First commit.** Repo has zero commits. Create `feat/scaffold` branch, commit doctrine, push, PR to main.
- **Husky install.** `.husky/pre-commit` exists but `husky install` will only run once a `package.json` lands in `web/` (or wherever we put it). Until then, hook works only if developer runs `git config core.hooksPath .husky` manually.

## Next session: start here

1. Read this file
2. Read `CLAUDE.md`
3. Lock stack (see PRD §24.1; awaiting builder confirmation on Next.js single-app vs split, FastAPI vs Next.js API routes)
4. Scaffold `backend/` and `web/` per chosen stack
5. First commit on `feat/scaffold` branch
