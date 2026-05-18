-- Migration: 0006 — attributions table
-- Purpose: Per-principal audit log for every write to durable memory
-- Rollback: DROP TABLE attributions;

CREATE TABLE attributions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,

  -- The artifact this attribution is about
  artifact_id UUID NOT NULL,
  artifact_type TEXT NOT NULL CHECK (artifact_type IN (
    'event','fact','room_attachment','room_update_draft','client','operator'
  )),

  -- Per-principal (Hivemind prep)
  agent_id TEXT NOT NULL DEFAULT 'operator',
  surface TEXT NOT NULL CHECK (surface IN (
    'web_dashboard','whatsapp_webhook','voice_upload','file_drop','manual_note','system_cron'
  )),
  session_id TEXT,
  turn_index INTEGER,
  confidence REAL NOT NULL DEFAULT 1.0 CHECK (confidence >= 0 AND confidence <= 1),
  reason TEXT,

  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_attributions_artifact ON attributions(artifact_type, artifact_id);
CREATE INDEX idx_attributions_operator ON attributions(operator_id, timestamp DESC);
