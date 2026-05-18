# Supabase Schema Reference — FollowRoom

**IMPORTANT:** Read this file before writing ANY SQL migration.

Last updated: 2026-05-16 (placeholder — no tables yet)

---

## Status

Schema not yet implemented. The intended entity set lives in `docs/prd/followroom_prd_v0_2_silent_whatsapp_ingestion.md` §9:

- `users` — operator profile
- `clients` — relationship records owned by a user
- `rooms` — one per client; holds public slug, passcode, published sections
- `events` — polymorphic ingestion (whatsapp_forward, whatsapp_paste, meeting_transcript, manual_note, document_upload, future_api_ingestion); raw text is append-only
- `extracted_facts` — derived from events; regenerable; carries confidence and visibility
- `tasks` — follow-up actions, optionally tied to a source event
- `suggested_replies` — AI-drafted WhatsApp-ready replies, dashboard only
- `room_update_drafts` — pending client-facing updates; require operator approval
- `review_queue_items` — uncertain matches, unassigned events, sensitive notes, pending updates

When the first migration lands, replace this section with the per-table column reference (column name, type, notes — call out non-obvious bits like split columns vs JSONB, hash vs raw, etc.).
