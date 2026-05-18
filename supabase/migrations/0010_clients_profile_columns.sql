-- Migration: 0010 — add profile columns to clients
-- Purpose: Store the regenerated internal + client-facing markdown profiles
--          per design doc §6.2 (two physical views, capped ~400 lines)
-- Rollback: ALTER TABLE clients DROP COLUMN internal_profile_md, DROP COLUMN client_facing_profile_md, DROP COLUMN profile_regenerated_at;

ALTER TABLE clients
  ADD COLUMN IF NOT EXISTS internal_profile_md TEXT,
  ADD COLUMN IF NOT EXISTS client_facing_profile_md TEXT,
  ADD COLUMN IF NOT EXISTS profile_regenerated_at TIMESTAMPTZ;
