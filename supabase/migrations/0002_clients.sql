-- Migration: 0002 — clients table
-- Purpose: Per-operator client records, with required short_context for KB seed
-- Rollback: DROP TABLE clients;

CREATE TABLE clients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,

  -- Identity
  client_name TEXT NOT NULL,
  phone_number TEXT,
  aliases TEXT[] DEFAULT '{}',
  relationship_type TEXT NOT NULL DEFAULT 'buyer'
    CHECK (relationship_type IN (
      'buyer','seller','landlord','tenant','investor',
      'commercial_landlord','commercial_tenant','referral_partner','other'
    )),
  status TEXT NOT NULL DEFAULT 'new_lead'
    CHECK (status IN (
      'new_lead','active_discussion','awaiting_client_decision',
      'follow_up_needed','proposal_sent','viewing_scheduled',
      'closed_won','closed_lost','dormant','archived'
    )),
  tags TEXT[] DEFAULT '{}',

  -- Required seed context (design doc §5.7 cold-start mitigation)
  short_context TEXT NOT NULL CHECK (length(short_context) >= 20),

  -- Soft-delete
  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,

  -- Bi-temporal
  transaction_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_clients_operator_active ON clients(operator_id) WHERE NOT is_deleted;
CREATE INDEX idx_clients_operator_status ON clients(operator_id, status) WHERE NOT is_deleted;

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS clients_set_updated_at ON clients;
CREATE TRIGGER clients_set_updated_at
BEFORE UPDATE ON clients
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
