# Supabase Schema Reference — FollowRoom

**IMPORTANT:** Read this file before writing ANY SQL migration.

Last updated: 2026-05-19 (Ingestion plan complete — Plan 3)

---

## operators

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK, FK to auth.users(id), ON DELETE CASCADE |
| email | TEXT | UNIQUE NOT NULL |
| name | TEXT | nullable |
| company_name | TEXT | nullable |
| role_title | TEXT | nullable |
| industry | TEXT | DEFAULT 'real_estate' |
| profile_photo_url | TEXT | nullable |
| default_language | TEXT | DEFAULT 'en' |
| default_tone | TEXT | nullable |
| timezone | TEXT | DEFAULT 'Asia/Singapore' |
| is_deleted | BOOLEAN | DEFAULT FALSE |
| deleted_at | TIMESTAMPTZ | nullable |
| transaction_time | TIMESTAMPTZ | bi-temporal; DEFAULT NOW() |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() |

Indexes:
- `idx_operators_active` on `(id)` WHERE NOT is_deleted

Triggers:
- `on_auth_user_created` on `auth.users` AFTER INSERT — auto-creates operators row via `handle_new_auth_user()`

RLS: ENABLED. Operator sees only their own row. No DELETE policy.

---

## clients

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| operator_id | UUID | NOT NULL, FK to operators(id), ON DELETE CASCADE |
| client_name | TEXT | NOT NULL |
| phone_number | TEXT | nullable |
| aliases | TEXT[] | DEFAULT '{}' |
| relationship_type | TEXT | CHECK (buyer/seller/landlord/tenant/investor/...) |
| status | TEXT | CHECK (new_lead/active_discussion/...) |
| tags | TEXT[] | DEFAULT '{}' |
| short_context | TEXT | NOT NULL, CHECK (length >= 20) — cold-start mitigation (design doc §5.7) |
| internal_profile_md | TEXT | nullable — operator-only synthesized profile (migration 0010, Plan 2) |
| client_facing_profile_md | TEXT | nullable — shareable profile, sensitive sections filtered out (Plan 2) |
| profile_regenerated_at | TIMESTAMPTZ | nullable — last successful ProfileService run |
| is_deleted | BOOLEAN | DEFAULT FALSE |
| deleted_at | TIMESTAMPTZ | nullable |
| transaction_time | TIMESTAMPTZ | bi-temporal |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | auto-updated via trigger |

Indexes:
- `idx_clients_operator_active` on `(operator_id)` WHERE NOT is_deleted
- `idx_clients_operator_status` on `(operator_id, status)` WHERE NOT is_deleted

RLS: per-operator. No DELETE policy.

---

## events

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| client_id | UUID | NOT NULL, FK clients(id), ON DELETE RESTRICT |
| operator_id | UUID | NOT NULL, FK operators(id), ON DELETE CASCADE |
| source_type | TEXT | CHECK (meeting_transcript/voice_memo/whatsapp_forward_shapeX/whatsapp_coexistence/manual_note/file_drop) — IMMUTABLE |
| raw_text | TEXT | NOT NULL — **APPEND-ONLY** (Pattern 21; trigger enforced) |
| transaction_time | TIMESTAMPTZ | when recorded |
| valid_time | TIMESTAMPTZ | when claimed true (event time) |
| attributed_to | TEXT | DEFAULT 'operator' |
| attributed_at | TIMESTAMPTZ | |
| is_deleted | BOOLEAN | DEFAULT FALSE |
| deleted_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |

Indexes:
- `idx_events_client_time` on `(client_id, transaction_time DESC)` WHERE NOT is_deleted
- `idx_events_operator` on `(operator_id)` WHERE NOT is_deleted

Triggers:
- `events_raw_text_append_only` BEFORE UPDATE — RAISES on raw_text/source_type/client_id mutation

RLS: per-operator.

---

## facts

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| client_id | UUID | NOT NULL, FK clients(id) |
| operator_id | UUID | NOT NULL, FK operators(id) |
| type | TEXT | CHECK (goal/budget_constraint/objection/...) |
| value | TEXT | NOT NULL |
| source_event_ids | UUID[] | NOT NULL, CHECK (length >= 1) — Receipts mandatory |
| source_spans | JSONB | DEFAULT '[]' — verbatim citation snippets |
| confidence_score | REAL | CHECK (0-1) |
| visibility | TEXT | CHECK (operator_only/client_facing_safe/agency_visible) |
| provenance | TEXT | CHECK (llm_generated/operator_curated/operator_edited/regenerable/canonical) |
| user_stance | TEXT | CHECK (unreviewed/accepted/rejected/reframed/operator_curated) |
| user_stance_set_at | TIMESTAMPTZ | |
| superseded_by | UUID | FK facts(id) — UPDATE in ADD/UPDATE/DELETE/NOOP pipeline |
| generation_metadata | JSONB | model_id, prompt_hash, schema_version, etc. |
| is_deleted | BOOLEAN | DEFAULT FALSE |
| deleted_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | auto-updated via trigger |

Indexes:
- `idx_facts_client_active` on `(client_id)` WHERE NOT is_deleted AND superseded_by IS NULL
- `idx_facts_client_type` on `(client_id, type)` WHERE NOT is_deleted AND superseded_by IS NULL
- `idx_facts_client_visibility` on `(client_id, visibility)` WHERE NOT is_deleted AND superseded_by IS NULL

RLS: per-operator.

---

## room_attachments

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| client_id | UUID | NOT NULL, FK clients(id) |
| operator_id | UUID | NOT NULL, FK operators(id) |
| storage_path | TEXT | NOT NULL — IMMUTABLE |
| original_filename | TEXT | NOT NULL — IMMUTABLE |
| mime_type | TEXT | NOT NULL |
| size_bytes | BIGINT | CHECK (> 0) — IMMUTABLE |
| content_hash | TEXT | SHA256 — IMMUTABLE |
| source_event_id | UUID | nullable, FK events(id) |
| related_fact_ids | UUID[] | DEFAULT '{}' |
| operator_note | TEXT | nullable |
| pending_action_type | TEXT | CHECK (for_review/for_signature/for_consideration/for_payment/informational) |
| pending_action_due | TIMESTAMPTZ | nullable |
| pending_action_label | TEXT | |
| visibility | TEXT | CHECK (operator_only/client_facing_safe/agency_visible) |
| visibility_promoted_at | TIMESTAMPTZ | |
| visibility_promoted_by | TEXT | |
| client_viewed_at | TIMESTAMPTZ | |
| client_viewed_count | INTEGER | DEFAULT 0 |
| client_downloaded_at | TIMESTAMPTZ | |
| client_acted_at | TIMESTAMPTZ | |
| client_action_taken | TEXT | acknowledged/signed/declined/paid/archived |
| superseded_by | UUID | FK self |
| supersedes | UUID | FK self |
| version_number | INTEGER | DEFAULT 1 |
| is_deleted | BOOLEAN | DEFAULT FALSE |
| deleted_at | TIMESTAMPTZ | |
| extraction_metadata | JSONB | DEFAULT '{}' |
| extracted_text | TEXT | for in-room search |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | auto |

Indexes:
- `idx_attachments_client_visible` on `(client_id, visibility, created_at DESC)` WHERE NOT is_deleted
- `idx_attachments_pending` on `(client_id, pending_action_type, pending_action_due)` WHERE pending_action_type IS NOT NULL AND client_acted_at IS NULL AND NOT is_deleted
- `idx_attachments_type` on `(client_id, mime_type)` WHERE NOT is_deleted
- `idx_attachments_extracted_text` GIN on `to_tsvector('english', extracted_text)` WHERE NOT is_deleted

Triggers:
- `attachments_file_immutability` BEFORE UPDATE — RAISES on storage_path/content_hash/filename/size_bytes mutation

RLS: per-operator (base table). Plan 6 adds a view for anonymous public-room reads.

---

## attributions

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| operator_id | UUID | NOT NULL, FK operators(id) |
| artifact_id | UUID | NOT NULL |
| artifact_type | TEXT | CHECK (event/fact/room_attachment/room_update_draft/client/operator) |
| agent_id | TEXT | DEFAULT 'operator' — Phase 3 expands |
| surface | TEXT | CHECK (web_dashboard/whatsapp_webhook/voice_upload/file_drop/manual_note/system_cron) |
| session_id | TEXT | |
| turn_index | INTEGER | |
| confidence | REAL | CHECK (0-1) DEFAULT 1.0 |
| reason | TEXT | |
| timestamp | TIMESTAMPTZ | DEFAULT NOW() |

Indexes:
- `idx_attributions_artifact` on `(artifact_type, artifact_id)`
- `idx_attributions_operator` on `(operator_id, timestamp DESC)`

RLS: per-operator (SELECT + INSERT only).

---

## visibility_promotions

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| operator_id | UUID | NOT NULL, FK operators(id) |
| artifact_id | UUID | NOT NULL |
| artifact_type | TEXT | CHECK (fact/room_attachment/room_update_draft) |
| from_tier | TEXT | CHECK (operator_only/client_facing_safe/agency_visible) |
| to_tier | TEXT | CHECK (same) |
| approved_by | TEXT | NOT NULL — 'operator:<id>' |
| approved_at | TIMESTAMPTZ | DEFAULT NOW() |
| reason | TEXT | |
| reversible | BOOLEAN | DEFAULT TRUE |

Indexes:
- `idx_promotions_operator` on `(operator_id, approved_at DESC)`
- `idx_promotions_artifact` on `(artifact_type, artifact_id)`

RLS: per-operator (SELECT + INSERT only).

---

## rooms_public (view)

Placeholder view. Returns 0 rows in Phase 1 (WHERE FALSE). Plan 6 populates with a `rooms` table holding `public_slug` + `passcode_hash` + room metadata.

---

## ingestion_jobs

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| operator_id | UUID | NOT NULL, FK operators(id), ON DELETE CASCADE |
| client_id | UUID | NOT NULL, FK clients(id), ON DELETE RESTRICT |
| upload_type | TEXT | CHECK (transcript/voice_memo) |
| storage_path | TEXT | NOT NULL — `<operator_id>/<job_id>/<filename>` |
| original_filename | TEXT | NOT NULL |
| mime_type | TEXT | NOT NULL |
| size_bytes | BIGINT | CHECK (> 0) |
| state | TEXT | CHECK (queued/transcribing/extracting/done/failed) — DEFAULT 'queued' |
| error_message | TEXT | populated when state='failed' |
| error_code | TEXT | CHECK (transcription_failed/extraction_failed/storage_failed/unknown) |
| transcript_text | TEXT | populated after transcription (or download for text uploads) |
| event_id | UUID | FK events(id) — populated after event creation |
| transcription_metadata | JSONB | DEFAULT '{}' — provider/model/duration/language/speaker_count |
| started_at | TIMESTAMPTZ | when worker began processing |
| completed_at | TIMESTAMPTZ | when state transitioned to done or failed |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | auto-updated via trigger |

Indexes:
- `idx_ingestion_jobs_operator_recent` on `(operator_id, created_at DESC)`
- `idx_ingestion_jobs_client_recent` on `(client_id, created_at DESC)`
- `idx_ingestion_jobs_active` partial on `(state, created_at)` WHERE state IN ('queued', 'transcribing', 'extracting')

RLS: per-operator (SELECT + INSERT + UPDATE). No DELETE policy — jobs persist as audit trail. State machine is walked by `IngestionWorker.run()` in a FastAPI BackgroundTask.

---

## Storage buckets

### ingestion-uploads (migration 0012)

- Private (`public = false`); 100MB file size limit
- Allowed mime types: text/plain, text/vtt, application/x-subrip, audio/mpeg, audio/mp4, audio/x-m4a, audio/wav, audio/x-wav, audio/ogg, audio/webm, audio/aac
- Path convention: `<operator_id>/<ingestion_job_id>/<original_filename>`
- RLS on `storage.objects` (2 policies): SELECT + INSERT both check `(storage.foldername(name))[1] = auth.uid()::text`
- No UPDATE/DELETE — uploads are append-only (Pattern 21). Hard delete via service-role cleanup tooling only (Phase 4+).

---

## Useful patterns when writing migrations

- Number files sequentially: `0001_*.sql`, `0002_*.sql`, ...
- Every migration starts with `-- Migration: NNNN — <name>` and includes a `-- Rollback:` comment
- Use `CREATE OR REPLACE FUNCTION` and `IF NOT EXISTS` where possible for idempotency
- Add CHECK constraints generously for enum-style columns; CHECK is cheap and catches typos
- Add `is_deleted` + `deleted_at` to every user-data table (Pattern 18)
- Add `transaction_time` to tables that need bi-temporal querying
- Wrap append-only fields in BEFORE UPDATE triggers (Pattern 21)
- Apply RLS in a single dedicated migration after table creation (current pattern: migration 0008)

---

## Migration tracking

`apply_migrations.py` records every applied filename in `public._migrations` (filename PK + applied_at). Re-runs are idempotent — only un-applied files execute. To force a re-run, delete the relevant row from `_migrations` first.
