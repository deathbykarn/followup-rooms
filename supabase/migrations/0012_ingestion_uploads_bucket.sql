-- Migration: 0012 — ingestion-uploads Supabase Storage bucket + RLS (Plan 3)
-- Stores raw uploaded transcripts and voice memos. Path convention:
--   <operator_id>/<ingestion_job_id>/<original_filename>
-- RLS scopes uploads/reads to the owning operator's folder.

INSERT INTO storage.buckets (
    id,
    name,
    public,
    file_size_limit,
    allowed_mime_types
)
VALUES (
    'ingestion-uploads',
    'ingestion-uploads',
    false,
    104857600,  -- 100 MB
    ARRAY[
        -- Text transcripts
        'text/plain',
        'text/vtt',
        'application/x-subrip',
        -- Audio formats commonly produced by iOS / Android / WhatsApp / desktop
        'audio/mpeg',      -- mp3
        'audio/mp4',       -- mp4 audio container
        'audio/x-m4a',     -- iOS Voice Memos
        'audio/wav',
        'audio/x-wav',
        'audio/ogg',       -- WhatsApp voice
        'audio/webm',      -- desktop browser recordings
        'audio/aac'
    ]
)
ON CONFLICT (id) DO NOTHING;

-- RLS on storage.objects scoped to this bucket. Folder convention puts
-- operator_id as the first path segment, so we can authorize via
-- storage.foldername(name)[1] = auth.uid()::text.
DROP POLICY IF EXISTS ingestion_uploads_owner_select ON storage.objects;
CREATE POLICY ingestion_uploads_owner_select ON storage.objects
    FOR SELECT USING (
        bucket_id = 'ingestion-uploads'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

DROP POLICY IF EXISTS ingestion_uploads_owner_insert ON storage.objects;
CREATE POLICY ingestion_uploads_owner_insert ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'ingestion-uploads'
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- No UPDATE / DELETE policies — uploads are append-only (Pattern 21).
-- Hard delete via service-role only (cleanup tooling, Phase 4+).

-- Rollback:
-- DROP POLICY IF EXISTS ingestion_uploads_owner_insert ON storage.objects;
-- DROP POLICY IF EXISTS ingestion_uploads_owner_select ON storage.objects;
-- DELETE FROM storage.buckets WHERE id = 'ingestion-uploads';
