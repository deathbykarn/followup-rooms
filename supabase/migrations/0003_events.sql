-- Migration: 0003 — events table (immutable, append-only source layer)
-- Purpose: The substrate layer of the KB; raw_text is append-only per Pattern 21
-- Rollback: DROP TABLE events; DROP FUNCTION enforce_raw_text_append_only;

CREATE TABLE events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
  operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,

  -- Source content (IMMUTABLE after first write)
  source_type TEXT NOT NULL CHECK (source_type IN (
    'meeting_transcript','voice_memo','whatsapp_forward_shapeX',
    'whatsapp_coexistence','manual_note','file_drop'
  )),
  raw_text TEXT NOT NULL,

  -- Bi-temporal columns (TG Memory primitive)
  transaction_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- when recorded
  valid_time TIMESTAMPTZ,                               -- when claimed true (event time)

  -- Attribution (per-principal data model from Day 1)
  attributed_to TEXT NOT NULL DEFAULT 'operator',
  attributed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Lifecycle
  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_events_client_time ON events(client_id, transaction_time DESC) WHERE NOT is_deleted;
CREATE INDEX idx_events_operator ON events(operator_id) WHERE NOT is_deleted;

-- CRITICAL: append-only enforcement on raw_text + source_type
-- This is Decades migration 069 pattern (Pattern 21 — Source Evidence Immutability)
CREATE OR REPLACE FUNCTION public.enforce_raw_text_append_only()
RETURNS TRIGGER AS $$
BEGIN
  IF OLD.raw_text IS NOT NULL AND NEW.raw_text != OLD.raw_text THEN
    RAISE EXCEPTION 'events.raw_text is append-only; mutation forbidden';
  END IF;
  IF OLD.source_type != NEW.source_type THEN
    RAISE EXCEPTION 'events.source_type is immutable after creation';
  END IF;
  IF OLD.client_id != NEW.client_id THEN
    RAISE EXCEPTION 'events.client_id is immutable; reassign via attribution record';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS events_raw_text_append_only ON events;
CREATE TRIGGER events_raw_text_append_only
BEFORE UPDATE ON events
FOR EACH ROW EXECUTE FUNCTION public.enforce_raw_text_append_only();
