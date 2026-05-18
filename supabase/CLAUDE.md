# CLAUDE.md — Supabase (FollowRoom)

**Read `SCHEMA_REFERENCE.md` before writing ANY migration.**

---

## Migration Discipline

**Non-destructive only:**
- Never `DROP TABLE`, `DROP COLUMN`, or `ALTER COLUMN ... TYPE` on tables with user data without an explicit rollback plan
- Follow expand → backfill → cutover → contract
- Every migration file includes a `-- Rollback:` comment describing the reverse operation
- Idempotent where possible: `IF NOT EXISTS`, `CREATE OR REPLACE`
- Sequential numbering with no gaps

**Next migration number:** check the highest existing file in `migrations/`.

---

## RLS Checklist (Every New Table)

- [ ] RLS enabled
- [ ] SELECT policy for authenticated users on own data
- [ ] INSERT policy for authenticated users on own data
- [ ] UPDATE policy for authenticated users on own data
- [ ] DELETE policy (prefer soft-delete via `is_deleted` flag; no DELETE policy if soft-delete is in use)

**Cross-user access prevention:** every user-facing table must scope by `user_id = auth.uid()`. Never trust path parameters for authorization.

---

## FollowRoom-Specific Sacred Bits

- **Internal vs client-facing separation.** `events`, `extracted_facts`, `internal_summary` are operator-private. `room_update_drafts` flow through approval before any `client_visible_*` field is written.
- **Source immutability.** `events.raw_text` is append-only. Re-extraction creates new `extracted_facts` rows; never mutate raw input.
- **Soft-delete defaults.** Client/Room deletion sets `is_deleted = TRUE, deleted_at = NOW()`. Hard delete requires explicit endpoint with grace period and audit trail.
- **Public room access.** `rooms.public_slug` and optional `passcode_hash` enable unauthenticated access via specific RLS policies. The published surface is a strict subset of internal memory — published columns are explicit, not derived from a JOIN.

---

## Status

No migrations yet. Schema lives only in PRD §9. Once stack is locked, the first migrations will mirror PRD §9 (User → Client → Room → Event → ExtractedFact → Task → SuggestedReply → RoomUpdateDraft → ReviewQueueItem).
