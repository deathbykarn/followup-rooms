-- Migration: 0014 — pending_forwards table for Shape X attribution loop (Plan 4)
-- Inbound webhook inserts pending rows; operator confirms in dashboard tray;
-- confirm triggers Plan 2 extraction with source_type='whatsapp_forward_shape_x'.

CREATE TABLE IF NOT EXISTS pending_forwards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,

    -- Inbound message data (receipts from Meta — IMMUTABLE)
    wa_message_id TEXT NOT NULL UNIQUE,          -- Meta's message id; dedupe key
    sender_wa_id TEXT NOT NULL,                  -- the operator's wa_id (who forwarded)
    forwarded_text TEXT NOT NULL,                -- the content of the forwarded message
    caption_text TEXT,                           -- the operator's caption (paired with forward); nullable
    wa_timestamp TIMESTAMPTZ NOT NULL,           -- Meta's reported timestamp
    raw_payload JSONB NOT NULL,                  -- full webhook chunk for audit

    -- Suggested attribution (ClientMatcher fills in async after webhook returns)
    suggested_client_id UUID REFERENCES clients(id),
    suggested_confidence REAL CHECK (
        suggested_confidence IS NULL OR (suggested_confidence >= 0 AND suggested_confidence <= 1)
    ),

    -- State machine
    state TEXT NOT NULL DEFAULT 'pending' CHECK (state IN (
        'pending', 'confirmed', 'discarded', 'expired'
    )),

    -- Operator commit outputs
    committed_client_id UUID REFERENCES clients(id),
    committed_event_id UUID REFERENCES events(id),
    committed_at TIMESTAMPTZ,
    discarded_reason TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Pending tray query (most common): WHERE operator_id=... AND state='pending' ORDER BY created_at DESC
CREATE INDEX IF NOT EXISTS idx_pending_forwards_operator_pending
    ON pending_forwards(operator_id, created_at DESC)
    WHERE state = 'pending';

-- Recent history (operator's full activity feed)
CREATE INDEX IF NOT EXISTS idx_pending_forwards_operator_recent
    ON pending_forwards(operator_id, created_at DESC);

-- Caption-pairing lookup (within 60s window from sender)
CREATE INDEX IF NOT EXISTS idx_pending_forwards_caption_pairing
    ON pending_forwards(sender_wa_id, created_at DESC)
    WHERE caption_text IS NULL AND state = 'pending';

DROP TRIGGER IF EXISTS pending_forwards_set_updated_at ON pending_forwards;
CREATE TRIGGER pending_forwards_set_updated_at
BEFORE UPDATE ON pending_forwards
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE pending_forwards ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS pending_forwards_select ON pending_forwards;
CREATE POLICY pending_forwards_select ON pending_forwards
    FOR SELECT USING (operator_id = auth.uid());

DROP POLICY IF EXISTS pending_forwards_insert ON pending_forwards;
CREATE POLICY pending_forwards_insert ON pending_forwards
    FOR INSERT WITH CHECK (operator_id = auth.uid());

DROP POLICY IF EXISTS pending_forwards_update ON pending_forwards;
CREATE POLICY pending_forwards_update ON pending_forwards
    FOR UPDATE USING (operator_id = auth.uid());

-- Rollback:
-- DROP POLICY IF EXISTS pending_forwards_update ON pending_forwards;
-- DROP POLICY IF EXISTS pending_forwards_insert ON pending_forwards;
-- DROP POLICY IF EXISTS pending_forwards_select ON pending_forwards;
-- DROP TRIGGER IF EXISTS pending_forwards_set_updated_at ON pending_forwards;
-- DROP INDEX IF EXISTS idx_pending_forwards_caption_pairing;
-- DROP INDEX IF EXISTS idx_pending_forwards_operator_recent;
-- DROP INDEX IF EXISTS idx_pending_forwards_operator_pending;
-- DROP TABLE IF EXISTS pending_forwards;
