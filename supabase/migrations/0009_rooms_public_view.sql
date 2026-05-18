-- Migration: 0009 — rooms_public placeholder view
-- Purpose: Reserve the public-room read surface; Plan 6 fleshes out
-- Rollback: DROP VIEW IF EXISTS rooms_public;

-- Placeholder: returns nothing in Phase 1 (no slug column on clients yet).
-- Plan 6 adds a 'rooms' table with public_slug + passcode_hash, and this
-- view becomes the canonical read surface for anonymous clients.

CREATE OR REPLACE VIEW rooms_public AS
SELECT
  c.id AS client_id,
  c.client_name,
  ''::text AS slug,
  NULL::text AS passcode_hash,
  c.created_at
FROM clients c
WHERE FALSE;

COMMENT ON VIEW rooms_public IS
  'Placeholder for Plan 6 client-facing room. Reserved here so RLS + auth layout can be designed against the final shape. Returns 0 rows in Phase 1 (WHERE FALSE).';
