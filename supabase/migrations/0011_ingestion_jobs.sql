-- Migration: 0011 — ingestion_jobs table for async transcript/voice upload pipeline (Plan 3)
-- Tracks the state machine: queued → transcribing → extracting → done | failed
-- Backend FastAPI worker advances state; frontend polls GET /uploads/{id} for status.

CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,

    -- What was uploaded
    upload_type TEXT NOT NULL CHECK (upload_type IN ('transcript', 'voice_memo')),
    storage_path TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes BIGINT NOT NULL CHECK (size_bytes > 0),

    -- State machine
    state TEXT NOT NULL DEFAULT 'queued' CHECK (state IN (
        'queued', 'transcribing', 'extracting', 'done', 'failed'
    )),
    error_message TEXT,
    error_code TEXT CHECK (error_code IN (
        'transcription_failed', 'extraction_failed', 'storage_failed', 'unknown'
    )),

    -- Outputs (populated as the worker advances)
    transcript_text TEXT,
    event_id UUID REFERENCES events(id),
    transcription_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Lifecycle
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_operator_recent
    ON ingestion_jobs(operator_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_client_recent
    ON ingestion_jobs(client_id, created_at DESC);

-- Partial index for in-flight jobs (worker scans / dashboard "currently processing" badge)
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_active
    ON ingestion_jobs(state, created_at)
    WHERE state IN ('queued', 'transcribing', 'extracting');

-- updated_at trigger (uses the shared set_updated_at() function from migration 0002)
DROP TRIGGER IF EXISTS ingestion_jobs_set_updated_at ON ingestion_jobs;
CREATE TRIGGER ingestion_jobs_set_updated_at
BEFORE UPDATE ON ingestion_jobs
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- RLS — operator-scoped, no DELETE policy (jobs are kept as audit trail; failed
-- jobs surface in the UI but aren't deleted automatically)
ALTER TABLE ingestion_jobs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS ingestion_jobs_select ON ingestion_jobs;
CREATE POLICY ingestion_jobs_select ON ingestion_jobs
    FOR SELECT USING (operator_id = auth.uid());

DROP POLICY IF EXISTS ingestion_jobs_insert ON ingestion_jobs;
CREATE POLICY ingestion_jobs_insert ON ingestion_jobs
    FOR INSERT WITH CHECK (operator_id = auth.uid());

DROP POLICY IF EXISTS ingestion_jobs_update ON ingestion_jobs;
CREATE POLICY ingestion_jobs_update ON ingestion_jobs
    FOR UPDATE USING (operator_id = auth.uid());

-- Rollback:
-- DROP POLICY IF EXISTS ingestion_jobs_update ON ingestion_jobs;
-- DROP POLICY IF EXISTS ingestion_jobs_insert ON ingestion_jobs;
-- DROP POLICY IF EXISTS ingestion_jobs_select ON ingestion_jobs;
-- DROP TRIGGER IF EXISTS ingestion_jobs_set_updated_at ON ingestion_jobs;
-- DROP INDEX IF EXISTS idx_ingestion_jobs_active;
-- DROP INDEX IF EXISTS idx_ingestion_jobs_client_recent;
-- DROP INDEX IF EXISTS idx_ingestion_jobs_operator_recent;
-- DROP TABLE IF EXISTS ingestion_jobs;
