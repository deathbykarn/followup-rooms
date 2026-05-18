-- Migration: 0004 — facts table (derived from events; regenerable)
-- Purpose: Typed, deduped relationship facts with source citations
-- Rollback: DROP TABLE facts;

CREATE TABLE facts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
  operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,

  -- The fact itself
  type TEXT NOT NULL CHECK (type IN (
    'goal','budget_constraint','timeline_signal','objection',
    'spouse_family_factor','emotional_hesitation','document_request',
    'follow_up_promise','viewing_preference','property_preference',
    'decision_blocker','buying_intent_signal','market_signal','content_opportunity'
  )),
  value TEXT NOT NULL,

  -- Source citations (Axiom 3 — Receipts Are Mandatory)
  source_event_ids UUID[] NOT NULL CHECK (array_length(source_event_ids, 1) >= 1),
  source_spans JSONB DEFAULT '[]',  -- [{ event_id, snippet, char_range }]

  -- Confidence + visibility tiers
  confidence_score REAL NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
  visibility TEXT NOT NULL DEFAULT 'operator_only'
    CHECK (visibility IN ('operator_only','client_facing_safe','agency_visible')),

  -- Provenance (Axiom 4 — Operator's Edit Is Canon)
  provenance TEXT NOT NULL DEFAULT 'llm_generated'
    CHECK (provenance IN (
      'llm_generated','operator_curated','operator_edited','regenerable','canonical'
    )),
  user_stance TEXT NOT NULL DEFAULT 'unreviewed'
    CHECK (user_stance IN ('unreviewed','accepted','rejected','reframed','operator_curated')),
  user_stance_set_at TIMESTAMPTZ,

  -- Supersession (UPDATE/DELETE in ADD/UPDATE/DELETE/NOOP pipeline)
  superseded_by UUID REFERENCES facts(id),

  -- Generation metadata (Axiom 2 — Truth ≠ Tone, regenerability)
  generation_metadata JSONB NOT NULL DEFAULT '{}',
    -- { model_id, prompt_version, prompt_hash, schema_version, evidence_snapshot, regenerated_from, generated_at }

  -- Lifecycle
  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_facts_client_active ON facts(client_id) WHERE NOT is_deleted AND superseded_by IS NULL;
CREATE INDEX idx_facts_client_type ON facts(client_id, type) WHERE NOT is_deleted AND superseded_by IS NULL;
CREATE INDEX idx_facts_client_visibility ON facts(client_id, visibility) WHERE NOT is_deleted AND superseded_by IS NULL;

DROP TRIGGER IF EXISTS facts_set_updated_at ON facts;
CREATE TRIGGER facts_set_updated_at
BEFORE UPDATE ON facts
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
