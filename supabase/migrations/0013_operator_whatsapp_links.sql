-- Migration: 0013 — operator_whatsapp_links for /link CODE onboarding (Plan 4)
-- Dashboard generates a 6-digit code; operator sends /link CODE from their
-- WhatsApp to the FollowRoom test number; webhook matches the code and ties
-- wa_id ↔ operator_id. Subsequent forwards routed by sender wa_id lookup.

CREATE TABLE IF NOT EXISTS operator_whatsapp_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,

    -- E.164 digits-only (no '+'), matches Meta's `from` field exactly.
    -- UNIQUE — one wa_id maps to at most one active operator.
    wa_id TEXT UNIQUE,

    -- /link CODE handshake fields. Code is nulled after successful link.
    link_code TEXT,
    link_code_expires_at TIMESTAMPTZ,
    linked_at TIMESTAMPTZ,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- One active row per operator
CREATE UNIQUE INDEX IF NOT EXISTS idx_operator_whatsapp_links_one_per_operator
    ON operator_whatsapp_links(operator_id)
    WHERE is_active;

-- Webhook uses link_code lookup during /link handshake
CREATE INDEX IF NOT EXISTS idx_operator_whatsapp_links_pending_codes
    ON operator_whatsapp_links(link_code)
    WHERE link_code IS NOT NULL AND linked_at IS NULL;

DROP TRIGGER IF EXISTS operator_whatsapp_links_set_updated_at ON operator_whatsapp_links;
CREATE TRIGGER operator_whatsapp_links_set_updated_at
BEFORE UPDATE ON operator_whatsapp_links
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE operator_whatsapp_links ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS operator_whatsapp_links_select ON operator_whatsapp_links;
CREATE POLICY operator_whatsapp_links_select ON operator_whatsapp_links
    FOR SELECT USING (operator_id = auth.uid());

DROP POLICY IF EXISTS operator_whatsapp_links_insert ON operator_whatsapp_links;
CREATE POLICY operator_whatsapp_links_insert ON operator_whatsapp_links
    FOR INSERT WITH CHECK (operator_id = auth.uid());

DROP POLICY IF EXISTS operator_whatsapp_links_update ON operator_whatsapp_links;
CREATE POLICY operator_whatsapp_links_update ON operator_whatsapp_links
    FOR UPDATE USING (operator_id = auth.uid());

-- No DELETE policy — links are deactivated via is_active flag, not deleted,
-- so audit trail of historical wa_id ↔ operator_id mappings is preserved.

-- Rollback:
-- DROP POLICY IF EXISTS operator_whatsapp_links_update ON operator_whatsapp_links;
-- DROP POLICY IF EXISTS operator_whatsapp_links_insert ON operator_whatsapp_links;
-- DROP POLICY IF EXISTS operator_whatsapp_links_select ON operator_whatsapp_links;
-- DROP TRIGGER IF EXISTS operator_whatsapp_links_set_updated_at ON operator_whatsapp_links;
-- DROP INDEX IF EXISTS idx_operator_whatsapp_links_pending_codes;
-- DROP INDEX IF EXISTS idx_operator_whatsapp_links_one_per_operator;
-- DROP TABLE IF EXISTS operator_whatsapp_links;
