-- Migration: 0007 — visibility_promotions table
-- Purpose: Audit log for every tier promotion (operator_only → client_facing_safe etc.)
-- Rollback: DROP TABLE visibility_promotions;

CREATE TABLE visibility_promotions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,

  artifact_id UUID NOT NULL,
  artifact_type TEXT NOT NULL CHECK (artifact_type IN (
    'fact','room_attachment','room_update_draft'
  )),

  from_tier TEXT NOT NULL CHECK (from_tier IN ('operator_only','client_facing_safe','agency_visible')),
  to_tier TEXT NOT NULL CHECK (to_tier IN ('operator_only','client_facing_safe','agency_visible')),
  approved_by TEXT NOT NULL,
  approved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  reason TEXT,
  reversible BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_promotions_operator ON visibility_promotions(operator_id, approved_at DESC);
CREATE INDEX idx_promotions_artifact ON visibility_promotions(artifact_type, artifact_id);
