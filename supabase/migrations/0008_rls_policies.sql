-- Migration: 0008 — RLS policies for all user-data tables
-- Purpose: Cross-operator isolation; defense layer beyond app code
-- Rollback: ALTER TABLE ... DISABLE ROW LEVEL SECURITY;

-- operators: each user sees only their own row
ALTER TABLE operators ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS operators_select_own ON operators;
CREATE POLICY operators_select_own ON operators FOR SELECT
  USING (id = auth.uid());

DROP POLICY IF EXISTS operators_update_own ON operators;
CREATE POLICY operators_update_own ON operators FOR UPDATE
  USING (id = auth.uid()) WITH CHECK (id = auth.uid());

-- clients: per-operator
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS clients_select_own ON clients;
CREATE POLICY clients_select_own ON clients FOR SELECT
  USING (operator_id = auth.uid() AND NOT is_deleted);

DROP POLICY IF EXISTS clients_insert_own ON clients;
CREATE POLICY clients_insert_own ON clients FOR INSERT
  WITH CHECK (operator_id = auth.uid());

DROP POLICY IF EXISTS clients_update_own ON clients;
CREATE POLICY clients_update_own ON clients FOR UPDATE
  USING (operator_id = auth.uid()) WITH CHECK (operator_id = auth.uid());

-- events: per-operator
ALTER TABLE events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS events_select_own ON events;
CREATE POLICY events_select_own ON events FOR SELECT
  USING (operator_id = auth.uid() AND NOT is_deleted);

DROP POLICY IF EXISTS events_insert_own ON events;
CREATE POLICY events_insert_own ON events FOR INSERT
  WITH CHECK (operator_id = auth.uid());

DROP POLICY IF EXISTS events_update_own ON events;
CREATE POLICY events_update_own ON events FOR UPDATE
  USING (operator_id = auth.uid()) WITH CHECK (operator_id = auth.uid());

-- facts: per-operator
ALTER TABLE facts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS facts_select_own ON facts;
CREATE POLICY facts_select_own ON facts FOR SELECT
  USING (operator_id = auth.uid() AND NOT is_deleted);

DROP POLICY IF EXISTS facts_insert_own ON facts;
CREATE POLICY facts_insert_own ON facts FOR INSERT
  WITH CHECK (operator_id = auth.uid());

DROP POLICY IF EXISTS facts_update_own ON facts;
CREATE POLICY facts_update_own ON facts FOR UPDATE
  USING (operator_id = auth.uid()) WITH CHECK (operator_id = auth.uid());

-- room_attachments: per-operator (client-facing view added in 0009)
ALTER TABLE room_attachments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS attachments_select_own ON room_attachments;
CREATE POLICY attachments_select_own ON room_attachments FOR SELECT
  USING (operator_id = auth.uid() AND NOT is_deleted);

DROP POLICY IF EXISTS attachments_insert_own ON room_attachments;
CREATE POLICY attachments_insert_own ON room_attachments FOR INSERT
  WITH CHECK (operator_id = auth.uid());

DROP POLICY IF EXISTS attachments_update_own ON room_attachments;
CREATE POLICY attachments_update_own ON room_attachments FOR UPDATE
  USING (operator_id = auth.uid()) WITH CHECK (operator_id = auth.uid());

-- attributions: per-operator
ALTER TABLE attributions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS attributions_select_own ON attributions;
CREATE POLICY attributions_select_own ON attributions FOR SELECT
  USING (operator_id = auth.uid());

DROP POLICY IF EXISTS attributions_insert_own ON attributions;
CREATE POLICY attributions_insert_own ON attributions FOR INSERT
  WITH CHECK (operator_id = auth.uid());

-- visibility_promotions: per-operator
ALTER TABLE visibility_promotions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS promotions_select_own ON visibility_promotions;
CREATE POLICY promotions_select_own ON visibility_promotions FOR SELECT
  USING (operator_id = auth.uid());

DROP POLICY IF EXISTS promotions_insert_own ON visibility_promotions;
CREATE POLICY promotions_insert_own ON visibility_promotions FOR INSERT
  WITH CHECK (operator_id = auth.uid());
