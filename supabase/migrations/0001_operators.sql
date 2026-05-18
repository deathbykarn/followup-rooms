-- Migration: 0001 — operators table
-- Purpose: Per-account operator profile, FK to Supabase auth.users
-- Rollback: DROP TABLE operators;

CREATE TABLE operators (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL UNIQUE,
  name TEXT,
  company_name TEXT,
  role_title TEXT,
  industry TEXT DEFAULT 'real_estate',
  profile_photo_url TEXT,
  default_language TEXT DEFAULT 'en',
  default_tone TEXT,
  timezone TEXT DEFAULT 'Asia/Singapore',

  -- Soft-delete (Pattern 18)
  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,

  -- Bi-temporal columns (TG Memory primitive prep)
  transaction_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for soft-delete-aware queries
CREATE INDEX idx_operators_active ON operators(id) WHERE NOT is_deleted;

-- Auto-create operator row when an auth user signs up
CREATE OR REPLACE FUNCTION public.handle_new_auth_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.operators (id, email)
  VALUES (NEW.id, NEW.email)
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW EXECUTE FUNCTION public.handle_new_auth_user();
