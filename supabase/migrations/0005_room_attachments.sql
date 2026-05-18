-- Migration: 0005 — room_attachments table (file drop channel)
-- Purpose: Files dropped by operator into client's room (PDFs, images, docs, links)
-- Rollback: DROP TABLE room_attachments; DROP FUNCTION enforce_attachment_file_immutability;

CREATE TABLE room_attachments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
  operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,

  -- File identity (IMMUTABLE after creation)
  storage_path TEXT NOT NULL,
  original_filename TEXT NOT NULL,
  mime_type TEXT NOT NULL,
  size_bytes BIGINT NOT NULL CHECK (size_bytes > 0),
  content_hash TEXT,

  -- Operator context
  source_event_id UUID REFERENCES events(id),
  related_fact_ids UUID[] DEFAULT '{}',
  operator_note TEXT,

  -- Pending action mechanic
  pending_action_type TEXT CHECK (pending_action_type IN (
    'for_review','for_signature','for_consideration','for_payment','informational'
  )),
  pending_action_due TIMESTAMPTZ,
  pending_action_label TEXT,

  -- Visibility tiers
  visibility TEXT NOT NULL DEFAULT 'operator_only'
    CHECK (visibility IN ('operator_only','client_facing_safe','agency_visible')),
  visibility_promoted_at TIMESTAMPTZ,
  visibility_promoted_by TEXT,

  -- Client interaction tracking
  client_viewed_at TIMESTAMPTZ,
  client_viewed_count INTEGER NOT NULL DEFAULT 0,
  client_downloaded_at TIMESTAMPTZ,
  client_acted_at TIMESTAMPTZ,
  client_action_taken TEXT,

  -- Versioning
  superseded_by UUID REFERENCES room_attachments(id),
  supersedes UUID REFERENCES room_attachments(id),
  version_number INTEGER NOT NULL DEFAULT 1,

  -- Lifecycle
  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,

  -- Provenance / extraction
  extraction_metadata JSONB DEFAULT '{}',
  extracted_text TEXT,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_attachments_client_visible ON room_attachments(client_id, visibility, created_at DESC)
  WHERE NOT is_deleted;
CREATE INDEX idx_attachments_pending ON room_attachments(client_id, pending_action_type, pending_action_due)
  WHERE pending_action_type IS NOT NULL AND client_acted_at IS NULL AND NOT is_deleted;
CREATE INDEX idx_attachments_type ON room_attachments(client_id, mime_type) WHERE NOT is_deleted;
CREATE INDEX idx_attachments_extracted_text ON room_attachments
  USING gin(to_tsvector('english', COALESCE(extracted_text, '')))
  WHERE NOT is_deleted;

-- Append-only enforcement on file identity (Pattern 21 extended)
CREATE OR REPLACE FUNCTION public.enforce_attachment_file_immutability()
RETURNS TRIGGER AS $$
BEGIN
  IF OLD.storage_path != NEW.storage_path
     OR OLD.content_hash IS DISTINCT FROM NEW.content_hash
     OR OLD.original_filename != NEW.original_filename
     OR OLD.size_bytes != NEW.size_bytes THEN
    RAISE EXCEPTION 'attachment file identity is immutable; create a new version via superseded_by';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS attachments_file_immutability ON room_attachments;
CREATE TRIGGER attachments_file_immutability
BEFORE UPDATE ON room_attachments
FOR EACH ROW EXECUTE FUNCTION public.enforce_attachment_file_immutability();

DROP TRIGGER IF EXISTS attachments_set_updated_at ON room_attachments;
CREATE TRIGGER attachments_set_updated_at
BEFORE UPDATE ON room_attachments
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
