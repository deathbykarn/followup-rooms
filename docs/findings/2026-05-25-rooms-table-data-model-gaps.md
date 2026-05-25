# Finding — `rooms` table & data-model gaps (Plan 6 input)

**Date:** 2026-05-25
**Source:** Adversarial review (technical/data-model lens) of the redesigned room + dashboard mockups (`docs/design/mockups/01–04`) against `supabase/SCHEMA_REFERENCE.md`.
**Status:** Open — drives Plan 6 (`rooms`) backend design. No code change yet.

---

## The load-bearing realization

The redesign promoted **"room" to a first-class entity** with a title, transaction type, stage, deal value, offers, comparables, and a room-level view count. The current schema models everything **1:1 with `clients`** — there is **no `rooms` table** (`rooms_public` is a placeholder view returning 0 rows). Most of what the mockups display has no home yet, and a multi-deal client (mockup 03: David Chen, three concurrent fronts) **cannot be represented** without `1:N` rooms per client.

**Headline recommendation:** land a `rooms` table before backing these mockups with real data, and make it `1:N` per client.

---

## Gaps (what the design assumes → what the schema has → fix)

| # | Sev | Design assumes | Schema today | Fix |
|---|-----|----------------|--------------|-----|
| 1 | High | A `room` entity with its own title/stage/etc., 1:N per client | `clients` 1:1; no `rooms` table | New `rooms` table, `1:N` to `clients` |
| 2 | High | Auto-extracted, operator-editable **room title** ("Purchase of a 4-bedroom HDB") | No title field; no `deal_headline` fact type | `rooms.title TEXT` (operator-editable) + a derivation step in `ExtractionService` |
| 3 | High | Per-deal **transaction type** (purchase/sale) — drives anchor framing + title verb | `clients.relationship_type` is per-*client*, not per-deal; a client can buy AND sell | `rooms.transaction_type` enum |
| 4 | High | **Stage** vocabulary: Discovery / Negotiation / Standing / Awaiting | `clients.status` enum has different values (`new_lead`, `proposal_sent`, `dormant`, …) — no "Negotiation"/"Discovery"/"Standing" | Per-room stage field + a display-mapping (or extend/rename the enum via expand→backfill→cutover) |
| 5 | Med | (Was) a numeric **deal value** for ranking | Price/budget only as free-text inside `facts.value` (`budget_constraint`) | *Mooted for sorting* by the value→neglect decision (sort by recency/stage/attention, all derivable). If a numeric `deal_value_sgd` is ever wanted, add it to `rooms` (nullable, extraction + operator override) |
| 6 | Med | Side-by-side **offers** (buyer, amount, conditions, status) | No offers model | `offers` table (room_id, buyer_label, amount, conditions, status, source_event_id) |
| 7 | Med | **Comparable transactions** table (unit, PSF, sold date) | No comps model; no market-data ingestion; comps would lack `source_event_ids` (collides with Receipts-Are-Mandatory) | Decide: manual operator entry (new table) vs external market-data integration; exempt comps from the fact-receipt rule or model them as a distinct, sourced entity |
| 8 | Med | Sensitive financial intel (liquidity, yield) correctly **kept off** the client surface | No fact type for financial position; no enforced visibility tier for it | Add a financial-position fact type defaulting to `visibility='operator_only'` + a publish-time rewrite/redaction gate |
| 9 | Med | **Room-level** view tracking ("3 viewings this room last week") + a "What's tracked" disclosure | Tracking is **per-attachment** (`room_attachments.client_viewed_*`); no room entity; relative-language + disclosure mandated by design doc §11.16 | Room-level view stream on the new `rooms` table; render relative/aggregate only; ship the disclosure link |
| 10 | Med | **Link-type** attachments (saved links: yield calculator, comps) + a client→operator WhatsApp send-helper | `room_attachments` requires `storage_path`, `content_hash`, `size_bytes > 0` — geared to uploaded files | Allow link-type attachments (nullable storage fields or a `kind` discriminator). Confirm the client→operator `wa.me` direction is intended vs the "no outbound WhatsApp" rule |
| 11 | Low | Dashboard metrics: active rooms / facts / events / "time saved" | Facts + events counts are derivable; "active rooms" presumes `rooms`; "time saved vs manual" has no input | Derive what's countable; define a formula + baseline for "time saved" or drop it |
| 12 | Low | "Across your book" cross-room insights | Stage-2 Hivemind; correctly flagged `PREVIEW` | No action — keep hand-curated behind the PREVIEW pill until Stage 2 |

---

## Suggested `rooms` schema sketch (for Plan 6 design, not final)

```
rooms
  id              UUID PK
  client_id       UUID NOT NULL REFERENCES clients(id)      -- 1:N (a client may have several rooms)
  operator_id     UUID NOT NULL REFERENCES operators(id)
  title           TEXT NOT NULL                              -- extracted deal headline, operator-editable
  transaction_type TEXT NOT NULL CHECK (transaction_type IN ('purchase','sale','rental','other'))
  stage           TEXT NOT NULL                              -- spine stage; reconcile with clients.status vocabulary
  public_slug     TEXT UNIQUE                                -- opaque token; NOT derived from title
  passcode_hash   TEXT
  -- optional, nullable:
  deal_value_sgd  NUMERIC                                     -- only if a numeric value is later needed
  is_deleted      BOOLEAN NOT NULL DEFAULT FALSE
  created_at / updated_at TIMESTAMPTZ
-- plus: offers (room_id …), room_views (room_id, viewed_at …), and a link-type allowance on room_attachments
```

Per migration discipline (`supabase/CLAUDE.md`): non-destructive, `-- Rollback:` comment, RLS scoped by operator, opaque slug for the public surface.

---

## Sequencing

1. `rooms` table (gaps 1–4, 9) — unblocks the most mockup surface.
2. `offers` + link-type attachments (6, 10) — needed for the negotiation/mature rooms.
3. Financial-position fact type + visibility gating (8).
4. Comps source decision (7) — manual vs integration.
5. Defer: numeric `deal_value` (5), "time saved" metric (11), Hivemind (12).

Until `rooms` lands, treat mockups 01–04 as design targets, not data-backed renders.
