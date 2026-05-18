# ROADMAP — FollowRoom

**Source:** PRD v0.2, §23. This file mirrors the PRD's phase plan and tracks shipping status. PRD remains the canonical scope document.

Status legend: `□ pending` `◐ in progress` `■ shipped` `⊘ deferred`

---

## Phase 0 — Prototype  □

**Goal:** prove output quality.

- □ Manual transcript / chat paste
- □ AI extraction
- □ Static generated room
- □ Suggested reply
- □ Manual client selection

No WhatsApp bot. No persistence beyond the prototype's needs. Throwaway code is acceptable here; the goal is to confirm extraction and generation quality before investing in the system.

---

## Phase 1 — Web-First MVP  □

**Goal:** prove the core relationship-room workflow with persistent storage and the operator's full dashboard.

- □ Operator dashboard (home, client list, client detail tabs)
- □ Client creation (manual, from transcript, from forwarded snippet)
- □ Internal memory (relationship summary, facts, events, tasks)
- □ Client-facing dynamic HTML room (preview + editor)
- □ Transcript upload / paste
- □ WhatsApp snippet paste (manual, into dashboard)
- □ Generic event ingestion model (polymorphic)
- □ AI extraction with confidence scores
- □ Client matching (rules first; pgvector deferred to Phase 2)
- □ Review queue (uncertain matches, unassigned, sensitive notes, room update pending)
- □ Suggested reply generated in dashboard
- □ Room update approval flow
- □ Basic cross-relationship meta insights
- □ Supabase schema + RLS for all MVP entities
- □ Architecture ready for inbound WhatsApp webhook (Phase 1.5 plug-in)

---

## Phase 1.5 — Silent WhatsApp Forwarding Inbox  □

**Goal:** add WhatsApp as an inbound pipe. Not a bot.

- □ WhatsApp Business Platform number provisioned
- □ Inbound webhook endpoint (verified, receipt-only)
- □ Forwarded-message event creation (reuses Phase 1 ingestion pipeline)
- □ Client matching on inbound events
- □ Dashboard review queue surfaces low-confidence matches
- □ No outbound replies by default (operator copies and sends from their own WhatsApp)

**Cost principle:** charges accrue only on outbound. MVP stays inbound-only.

---

## Phase 2 — Relationship Memory System  ⊘ (post-MVP)

**Goal:** make rooms compound over time.

- ⊘ Event timeline view
- ⊘ Fact memory with provenance / receipts
- ⊘ Open loops surfacing
- ⊘ Follow-up task intelligence (auto-suggested due dates, stale detection)
- ⊘ Room update diffing
- ⊘ Search across clients (full-text + semantic)
- ⊘ Better client matching (pgvector)

---

## Phase 3 — Vertical Templates  ⊘

**Goal:** deepen value for target industries.

Templates for: real estate buyer, real estate seller, commercial property, insurance, wealth advisory, renovation, B2B sales.

---

## Phase 4 — Collaboration & Team  ⊘

Multi-user accounts, shared branding, manager view, team templates, permissioning, audit logs.

---

## Phase 5 — Integrations  ⊘

Google Drive, Calendar, Zoom, Otter, HubSpot, Salesforce, Zapier/Make, Email.

---

## Phase 6 — Optional Conversational Bot Layer  ⊘

WhatsApp confirmation replies, command flow, reminders, suggested-reply delivery, proactive templates. **Only if user demand proves strong.** Explicitly out of MVP.

---

## Versioning & Release Strategy

- Major.Minor.Patch. Pre-MVP work tagged `v0.0.x`.
- Every shipped build tagged. `CHANGELOG.md` updated with each tag.
- Release notes are plain-language for the builder, not commit messages.

---

## Frozen Constraints

These are non-negotiable through Phase 1.5. Any proposal that violates one must be raised explicitly and entered into the decision ledger before implementation.

1. **WhatsApp endpoint is silent.** No outbound replies. No MCQ. No slash commands.
2. **No auto-publish to client-facing surfaces.** Operator approval gates everything visible to clients.
3. **Internal vs client-facing memory are separate stores with separate visibility.** Tactful rewrite happens at publish, not at ingestion.
4. **Sensitive inferences (family dynamics, emotional state) never auto-publish.** Even with operator approval, the rewrite layer must strip these before they reach the client room.
5. **Source events are append-only.** Re-extraction creates new derived rows; never mutates raw.
