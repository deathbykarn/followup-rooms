# FollowRoom — Architecture Design

**Date:** 2026-05-18
**Status:** DRAFT (founding architectural artifact for Phase 1, with Phases 2-3 forward-compatibility baked in)
**Author:** Khaniff Lau (with Claude Code synthesis)
**Source:** Architecture brainstorming session 2026-05-16 → 2026-05-18
**Position in LineOS:** FollowRoom is a LineOS application — the substrate for tending client Lines, sibling to Decades (which tends the operator's own Line)

**Related:**
- PRD: `docs/prd/followroom_prd_v0_2_silent_whatsapp_ingestion.md`
- SOUL: `PROJECT_DEV_SOUL.md` (adapted from Decades)
- LineOS genesis: `Decades/docs/narrative/2026-05-04-lineos-genesis.md`
- LineOS pattern language: `Decades/docs/patterns/decades-pattern-language.md`
- Hivemind canonical proposal: `Decades/docs/proposals/2026-04-08-hivemind-meta-layer-proposal.md`
- Zettelkasten fourth-pillar proposal: `Decades/docs/proposals/2026-05-02-zettelkasten-fourth-pillar.md`

---

## TL;DR

FollowRoom is a CRM-adjacent product for relationship-driven sales operators (initially Singapore property agents). Its headline promise is **"meeting transcripts become meeting rooms"**; its marketing pitch is **"living relationship rooms"**; its engine is a **compounding per-client knowledgebase**.

It is built as a **LineOS application** — applying the four-thread architecture (capture / memory / synthesis / governance) developed for Decades, with the subject shifted from operator-self to operator's-clients. This inheritance gives FollowRoom a head start on architecture, governance, and pattern discipline that competing products would have to invent from scratch.

The product is **phased across three substrate layers** that double as commercial tiers:

| Phase | Substrate | ICP | Pricing tier |
|---|---|---|---|
| **1** | Karpathy LLM Wiki per client, single corpus with client tags | Solo property agent | $29-39/mo (PRD's Pro tier) |
| **2** | Zettel upgrade: link-graph, bookkeeper agent, Serendipity Engine | Solo Pro power user | $59-99/mo (PRD's Premium tier) |
| **3** | Hivemind upgrade: federation, governance arbitration, multi-agent, multi-surface | Real estate agency | Per-seat enterprise |

The architecture commits to **additive upgrades, never migrations**. Phase 1 bakes in the forward-compatibility hooks (schema, attribution, write path, file structure, tooling abstractions, visibility tiers) that Phases 2 and 3 extend without rewriting.

The non-negotiable architectural invariant is **zero misattribution** of ingested events to clients. Misattribution is treated as a Tier 3 risk (identity-shaping; wrong-client publishing is a trust breach). Attribution is **structurally deterministic** via four channels — never LLM-judged at first-touch. The system may use LLM to *suggest* in the review queue (faster operator tap), but the operator's explicit commit event is always the canonical attribution authority.

---

## 1. Product Framing

### 1.1 The Pitch (External)

> **FollowRoom — living relationship rooms for the operator who refuses to let clients fall through the cracks.**

This is the marketing surface. Property agents, insurance advisors, wealth managers, B2B consultants — anyone whose work is mediated by long, asymmetric, high-trust client relationships — gets a dynamic HTML "room" per client that organizes the relationship over time. The room is theirs to share with the client (private link, optional passcode) or keep purely internal.

### 1.2 The Promise (Headline)

> **Meeting transcripts become meeting rooms.**

This is the concrete, demonstrable-in-60-seconds version of the pitch. Upload a 30-minute meeting transcript; FollowRoom turns it into a polished client-facing page (room), drafts a tactful WhatsApp follow-up the operator can copy and send, and adds the relationship signals to that client's private memory layer. Voice memos and forwarded WhatsApp messages enrich the room over time.

**The room is active, not static.** As the relationship unfolds, the operator drops artifacts into it from mobile or desktop — floor plans, market reports, affordability calculators, contracts, photos from viewings, property links — each with a quick note. These cohere with the timeline. The client opens the private room link and finds a sorted, organized library: by type, by recency, by what's pending their action. They view inline where possible; download when not. The operator sees what was opened, when, and what's still waiting. The room becomes the **delivery surface, reference library, and relationship audit trail** in one.

### 1.3 The Engine (Internal Framing)

> **A compounding per-client knowledgebase, structured for retrieval, generation, and synthesis.**

Each client has a growing knowledgebase that captures relationship texture — goals, constraints, preferences, decision-maker dynamics, open threads, recent events. The KB is the substrate that powers everything visible: room generation, suggested replies, cross-relationship insights. **The KB is the product's spine.**

### 1.4 The Commercial Spear Thesis

FollowRoom is positioned as the commercial entry point to LineOS — the architecture that also powers Decades (capture-self) and Temporal Governance and (eventually) Zettel and Hivemind. Operators who adopt FollowRoom discover they're already using a LineOS-shaped substrate. Cross-sell into Decades becomes a natural extension: *"you already tend your clients' Lines — tend your own."* Agencies eventually adopt the full stack with FollowRoom as the client-relationship layer.

This frames FollowRoom not as "another AI CRM" but as **the relationship-domain instantiation of an operating system for the self that scales from individual to enterprise**. The architectural ambition is visible to investors and sophisticated buyers; the headline pitch ("living relationship rooms") is what sells to operators.

### 1.5 LineOS Application Positioning

The four LineOS threads map to FollowRoom components:

| LineOS thread | FollowRoom equivalent | Adaptation |
|---|---|---|
| **Decades thread** (Capture) | Transcripts + voice memos + WhatsApp ingestion → per-client events | Subject shift: per-client, not per-self |
| **Hivemind thread** (Institutional memory, PMM-shaped) | Compounding client knowledgebase | Subject shift: per-client KB; federated only at Phase 3 (agency multi-operator) |
| **Zettel thread** (Synthesis + SE) | Client-facing room + cross-relationship meta intelligence | Synthesis surface is the room; SE surfaces emergent cross-client patterns |
| **TG thread** (Governance) | TG-lite: operator approval gate + visibility tiers + publishing controls | Full TG primitives only emerge at Phase 3 multi-operator |

Plus a **WhatsApp adapter** that doesn't exist in LineOS — FollowRoom's specific addition for relationship-domain ingestion.

**The framing that makes everything click:**

- *Decades is the LineOS surface for tending YOUR Line across decades.*
- *FollowRoom is the LineOS surface for tending each CLIENT'S Line across the lifespan of the relationship.*

Same architecture; different subject. Same patterns; different signal. Same doctrine; different audience.

---

## 2. Constitutional Axioms

These ten axioms govern every architectural decision. Adopted from Decades' product doctrine, LineOS conceptual foundations, Hivemind axioms, and Zettelkasten axioms; refit for FollowRoom's relationship-domain subject.

1. **Source Evidence Immutability.** Raw voice notes, raw transcriptions, raw forwarded messages, raw manual notes are append-only at the database level. Every interpretation downstream is regenerable. The receipt chain is meaningless if receipts can be altered.

2. **Truth ≠ Tone.** Memory selection (what is true about this client) is separate from language generation (how to phrase the WhatsApp follow-up, the room update, the suggested reply). Changing the model changes the voice, not the facts. Vendor swaps must not rewrite history.

3. **Receipts Are Mandatory.** Every AI claim about a client, deal, or follow-up links back to verbatim source material — the specific transcript line, the forwarded message, the date. *"Your history shows X"* — never *"AI says X."* If no receipt can be produced, the claim is not surfaced.

4. **The Operator's Edit Is Canon.** When the operator edits an extracted fact, a drafted reply, or a room update, that edit is canonical. The system does not overwrite it on regeneration. Provenance distinguishes `llm_generated` / `operator_curated` / `operator_edited`. Operator-as-canon is structurally enforced; bookkeeper agents (Phase 2+) never overwrite operator-canonical rows.

5. **Forgetting by Promotion, Not Deletion.** Stale entries are archived (`is_deleted = TRUE, deleted_at = NOW()`) or demoted, never hard-deleted by default. Hard deletion requires explicit operator action + grace period + audit trail. Pages can be regenerated; the evidence chain cannot.

6. **Tiered Epistemic Risk.** Tier 1 (capture/display/retrieve) ships freely. Tier 2 (interpretive but regenerable: extracted facts, suggested replies, room update drafts) ships with operator approval gates. Tier 3 (identity-shaping, client-judgment, decision-blocker speculation, family-dynamic inferences) is FROZEN from auto-publishing to client-facing surfaces. Tier 3 inferences may appear in internal memory with caveats; they never reach the room.

7. **Save Is Sacred.** Nothing gates the save operation between "operator stopped recording / hit send" and "raw event persisted to durable storage." Upload queues, transcription runs, AI extraction, attribution checks all happen AFTER save. The data loss incident that earned this rule in Decades (Feb 9, 2025) is FollowRoom's pre-emptive scar.

8. **Vendors Are Adapters.** No business logic depends on a specific AI vendor or transcription provider. `AgentDispatcher` + logical roles (`classifier`, `summarizer`, `generator`, `validator`, `transcriber`) in code; model → provider in config. Vendor changes are config changes.

9. **The Quiet Witness Posture.** The system watches, remembers, shows evidence when asked. It does not advise, diagnose, befriend, or coach the operator. *"You noticed this client went silent"* — not *"You should call them now."* The product's trust position depends on epistemic humility: it surfaces patterns; the operator decides what they mean.

10. **Zero Misattribution.** Every event in a client's knowledgebase has a deterministic operator-commit event behind its attribution. LLM judgment may suggest in the review queue (faster operator tap), but the operator's explicit commit is always the canonical authority. Misattribution is treated as a Tier 3 trust breach; the architecture is designed to make it structurally impossible.

These ten axioms are non-negotiable. Every PR must demonstrate compatibility with them. Violations require constitutional amendment (a documented decision in `docs/decisions/decision-ledger.md` with explicit rationale).

---

## 3. Three-Phase Layering

> **Refinement (2026-05-19):** the Phase 2 / Phase 3 ordering below has been refined. The active sequencing is Karpathy → **Hivemind** (Stage 2) → **Zettel** (Stage 3), not Karpathy → Zettel → Hivemind as originally written here. Rationale: Hivemind delivers cross-vector insights at solo-operator scale (not just agency scale), which is higher leverage earlier. See `docs/architecture/lineos-evolution.md` for the narrative + trigger conditions. The §3.2 / §3.3 sub-sections below remain useful as conceptual reference for what each layer DOES; the ORDERING in the canonical sequence is now defined by the narrative doc.

FollowRoom evolves through three substrate phases that double as commercial tiers. Each phase **adds** layers without **rewriting** earlier ones.

### 3.1 Phase 1 — Karpathy (Solo Real Estate Agent MVP)

**Substrate:** Per-client knowledgebase shaped as a Karpathy-style LLM Wiki. Plain markdown profile + typed facts JSON + immutable events log + cross-client index, all stored in Supabase Postgres (markdown as TEXT columns, JSON as JSONB).

**Single-corpus framing with client tags:** All events live in one `events` table tagged by `client_id`. Cross-relationship queries are simple grouped queries with LLM synthesis layered on top — no federation infrastructure needed at this scale.

**Operations:**
- **Ingest** — transcripts (audio/text), voice memos, WhatsApp forwards (Shape X), manual notes
- **Maintain** — ADD/UPDATE/DELETE/NOOP pipeline per event arrival; updates the affected client's profile + facts
- **Query** — operator opens a client's workspace → load that client's KB; operator triggers cross-relationship insights → batch scan all clients
- **Publish** — operator approves room updates → write to `room_published_view`

**No bookkeeper agent. No link-graph. No formal manifest. No tiered loading discipline.** Everything is direct DB operations with cron-driven batch jobs.

**Pricing:** $29-39/month. PRD's Pro tier.

**Target ICP:** Solo property agents (Singapore primarily for MVP), eventually any solo relationship-driven sales operator.

**MVP success criteria:**
- 10-20 paying solo operators within 6 months of launch
- ≥70% weekly active rate among paying operators
- ≥50% of paying operators publish at least one room update per week
- ≥1 NPS-worthy testimonial per operator cohort

### 3.2 Phase 2 — Zettel (Solo Pro Power User)

**Trigger to build:** Phase 1 has 50+ paying operators, AND operator demand for cross-relationship insights and serendipitous pattern surfacing is documented.

**Substrate additions:**
- **SQLite link-graph (or Postgres equivalent)** with `zettel_units`, `zettel_links`, `zettel_drift` tables (adapted from the Decades Zettel proposal substrate amendment)
- **Unit-level addressing via sidecar** — pillar-prefixed compound addresses for events, facts, profile sections
- **Bookkeeper agent (Demosthenes-equivalent for FollowRoom)** with formal mandate / scope / soul contract / tools. Maintains the link-graph and unit-level addressing autonomously on cadence (incremental + weekly maintain + on-demand reflection)
- **Serendipity Engine** reads link-graph + Hivemind-shaped per-client KBs (now structured as PMM-light); surfaces emergent cross-client patterns as invitations
- **Topic emergence** — auto-categorization per client from co-occurrence (Pattern 11 extended to per-client ontology)

**Migration shape:** purely additive. Phase 1 markdown profiles and facts JSON are unchanged. Unit-IDs are assigned via sidecar; the underlying data isn't modified. Bookkeeper agent starts maintaining the link-graph; the existing direct write path continues to work alongside.

**Pricing:** $59-99/month. PRD's Premium tier.

**Target ICP:** Solo Pro operators — agents who've outgrown Phase 1's simpler tools and value cross-relationship intelligence, premium room aesthetics, and the "second brain" feel.

**Phase 2 success criteria:**
- ≥30% of Phase 1 operators upgrade to Pro within 6 months of Phase 2 launch
- Cross-relationship insight features generate measurable engagement (≥1 insight-triggered action per operator per week)
- Bookkeeper agent's autonomous maintenance reduces operator's perceived friction (NPS lift)

### 3.3 Phase 3 — Hivemind (Real Estate Agency Enterprise)

**Trigger to build:** Phase 2 has 100+ paying Pro operators AND multiple inbound agency inquiries documented.

**Substrate additions:**
- **YAML manifest** (`hivemind.yaml` per agency tenant) cataloging all client domains, source files, tier assignments, governance rules
- **Formal `store()` write path** with multi-agent attribution, scoping enforcement, redaction notices injected into response content
- **Tier 0/1/2/3/Aug loading discipline** — always-loaded budget (~800 tokens) vs on-demand recall vs cross-domain vs forensic vs augmentation index
- **Gravity model for access** — `(action, source_domain, target_domain, tool_sensitivity)` → Routine / Medium / High routing
- **Temporal knowledge graph** (sqlite-vec or pgvector equivalent) — `"what was true about Sarah at time T?"` queries
- **Cross-operator federation** within an agency — managers see aggregate client portfolios; assistants tend specific clients; access control is per-principal + per-domain
- **Multi-surface coherence** — same memory accessible from web dashboard, Telegram, mobile app, possibly Slack
- **Multi-agent fleet** — bookkeeper agents per operator, assistant agents per agency role, governor agent for agency-level operations
- **Permission decay** — standing permissions expire after 30 days of non-use (Hivemind discipline)

**Migration shape:** additive. Phase 1 + Phase 2 data structures remain valid. Hivemind layer wraps them with manifest + governance + federation primitives. Per-client KBs become Hivemind domains.

**Pricing:** Per-seat enterprise. $50-100/seat/month for typical agency configurations (5-50 seats), with annual contracts, custom onboarding, dedicated success management.

**Target ICP:** Real estate agencies (brokerages with 5-50+ agents), eventually any relationship-driven sales organization that wants multi-operator memory coordination.

**Phase 3 success criteria:**
- 5+ paying agency contracts within 12 months of Phase 3 launch
- Average agency contract ≥$30k ARR
- Agency NRR ≥110% (expansion through seat additions)

### 3.4 Additive Upgrades — Never Migrations

The phases are upgrades because the architecture commits to forward-compatibility hooks in Phase 1 (Section 8). Specifically:

- Phase 1 data structures (events, facts, operator_overrides, profile, tone_profile) remain valid in Phase 2 and Phase 3 — never rewritten.
- Phase 2 (Zettel) adds layers (link-graph, unit-IDs via sidecar, bookkeeper) WITHOUT modifying Phase 1 data.
- Phase 3 (Hivemind) wraps Phase 1+2 with federation, governance, tiered loading WITHOUT modifying the underlying data.

This is the **"enterprise-grade for a 1-citizen civilization, scales to enterprise"** promise from LineOS instantiated. The same architecture serves a solo agent at $29/mo and an agency at enterprise pricing — just with more machinery exposed at each tier.

### 3.5 Felt Experience Per Phase

What the operator FEELS at each layer (synthesized from Hivemind experiential outcome doc):

**Phase 1 Karpathy — *"the institution remembers what I forgot."***
> The agent walks out of a viewing, records 90 seconds of voice notes, and tomorrow morning sees a card: *"You told Mrs Chen you'd send the floor plan for unit #14-22 by Wednesday. Here's the snippet."* No CRM data-entry ceremony. The conversation was the documentation. Friction near zero.

**Phase 2 Zettel — *"patterns surface from my own words."***
> Cross-client emergent ontology arrives as invitation, not assertion: *"You've shown 6 clients orchard-area properties in the last 30 days. 4 of them mentioned 'school catchment' unprompted. Possible positioning angle?"* The agent's own data, surfaced as a quiet provocation. The agent feels seen by their own work.

**Phase 3 Hivemind — *"the institution traces threads no single conversation could see."***
> The agency manager opens the dashboard: *"Three deals in the team are at the same stage with the same objection pattern. Sarah Chen (Wong Tan's deal) handled it well last quarter — share the playbook?"* The institution holds the topology. Operators hold relationships. Coordination cost drops near zero.

The felt quality across all phases: **calm, evidentiary, trustworthy, non-judgmental.** The Quiet Witness posture (Axiom 9) is the experiential signature.

---

## 4. Pattern Language Inheritance

FollowRoom inherits the LineOS Pattern Language (the 23 patterns codified in Decades). 14 patterns transfer verbatim; 9 adapt to FollowRoom's per-client subject; 0 don't apply.

### 4.1 Inheritance Map

| # | Pattern | Verdict | Adaptation note (where applicable) |
|---|---|---|---|
| 1 | Temporal Coherence | ADAPT | Subject shifts: client relationship arc surfaced over time, not operator's own arc |
| 2 | The Quiet Witness | VERBATIM | Load-bearing posture; non-negotiable |
| 3 | Aggregation Cascade | ADAPT | Per-client cascade: Interaction → Day-with-client → Deal-stage → Client-arc → Portfolio-arc |
| 4 | Trinity Realms | ADAPT | Replaced with per-client triad — Need / Constraint / Signal (engagement temperature) |
| 5 | Epistemic Risk Tiers | VERBATIM | Tier 3 for FollowRoom = inferring client intent, scoring lead likelihood, family-dynamic speculation |
| 6 | The Minimum Living Loop | VERBATIM | Capture → Store → Resurface → Reflect → Integrate. Every PR must preserve the loop |
| 7 | Voice Within Two Taps | VERBATIM | Property agents are mobile-first; capture friction kills data |
| 8 | Gentle Recall | VERBATIM | One provocation per day, not ten. The follow-up card replaces the dashboard dump |
| 9 | Truth With Receipts | VERBATIM | Every AI claim links to verbatim source — non-negotiable |
| 10 | Ask, Not Chat | ADAPT | Same posture; scopes shift to per-client, per-deal, per-portfolio |
| 11 | Emergent Ontology | ADAPT | Per-client emergent topics (school catchments, ROI, family-proximity); also portfolio-level emergent |
| 12 | Celebration Over Correction | ADAPT | Same posture but harder to hold — agents want sales coaching. Resist becoming a sales coach |
| 13 | The Careful Diplomat | ADAPT | If voice personas ship (post-viewing debrief): same warm-investigator posture |
| 14 | Serendipity as Reward | ADAPT | Cross-client bridges as invitations — *"two clients looking at the same school catchment — possible introduction?"* |
| 15 | Ledger-Backed Growth | ADAPT or skip Phase 1 | If FollowRoom gamifies (follow-up streaks, response time), inherit ledger discipline. Skip if not |
| 16 | Save Is Sacred | VERBATIM | Voice notes from viewings are irreplaceable. No gates between "stopped recording" and "on disk" |
| 17 | Frozen Phases | VERBATIM | "Predict whether this client will close" is Tier 3. Freeze until governance exists |
| 18 | Never-Delete Doctrine | VERBATIM | Agent-client interactions are evidentiary. Real estate retention rules apply |
| 19 | Truth ≠ Tone | VERBATIM | Memory selection separate from language generation — non-negotiable |
| 20 | Vendor Agnostic | VERBATIM | `AgentDispatcher` + logical roles + provider config |
| 21 | Source Evidence Immutability | VERBATIM | Migration 069 pattern — PostgreSQL BEFORE UPDATE trigger blocking overwrite |
| 22 | Recovery On Every Open | VERBATIM | Same 5-step sweep, same ordering, on every app open |
| 23 | Every Safety System Breeds the Next Failure | VERBATIM | Meta-pattern; adopt as PR review culture from Day 1 |

**Net:** 14 verbatim, 9 adapt, 0 not-applicable. Every load-bearing pattern carries.

### 4.2 Pattern Adoption Rules

- **VERBATIM patterns are constitutional from Day 1.** Every new feature, every PR, every migration must demonstrate compatibility. Violations require constitutional amendment.
- **ADAPT patterns must have explicit adaptation rationale** captured in either this design doc or `docs/patterns/followroom-pattern-language.md` (when created in Phase 1).
- **The 23 patterns are versioned together with LineOS upstream.** When Decades introduces Pattern 24+ (or amends an existing pattern), FollowRoom evaluates inheritance.

---

## 5. Ingestion Architecture

FollowRoom has five ingestion channels in priority order, each with a deterministic attribution mechanism. The non-negotiable rule: **every event entering a client's KB has a deterministic operator-commit event behind its attribution.**

### 5.1 Channel 1 — Meeting Transcripts (Headline)

**Inputs supported (Phase 1):**
- Audio file upload (m4a, mp3, wav, ogg, opus) → transcribed via Whisper API → text
- Text upload (`.txt`, paste from clipboard) → parsed directly
- PDF upload (if parseable) → text extraction → parsed
- Future: native integrations with Otter / Fireflies / Granola transcript exports (Phase 2+)

**Attribution at upload time:**
- Operator selects the client at upload (dropdown with fuzzy search of existing clients + "create new client" option)
- Attribution is explicit, deterministic, recorded with timestamp + operator_id

**Pipeline:**
1. Operator uploads → file persisted to Supabase Storage (Save Is Sacred — before any extraction)
2. Background worker triggers Whisper transcription (if audio) or text parse (if text)
3. Transcript stored as `events.raw_text` with `source_type = 'meeting_transcript'`
4. AI extraction (Sonnet 4.6) runs — extracts facts with source-span citations, draft room update, draft suggested follow-up
5. Operator notified (dashboard activity feed); reviews + approves in dashboard
6. Approved facts → `facts` table; approved room update → `room_published_view`

**Volume estimate:** 20-40 transcripts/month per heavy operator. Headline channel.

### 5.2 Channel 2 — Operator Voice Memos

Two sub-channels with shared backend pipeline.

**Sub-channel 2a — Phone upload (Phase 1):**
- Operator records voice memo in phone's native voice memo app (iOS Voice Memos, Android Recorder)
- Opens FollowRoom mobile web in browser → "+ Add" → "Upload audio" → selects file → picks client (deterministic attribution)
- Backend transcribes via Whisper, extracts, adds to client's KB

**Sub-channel 2b — Via WhatsApp forward (Phase 1.5 or 2):**
- Operator records voice memo in WhatsApp directly (hold-to-record button)
- Forwards to FollowRoom WhatsApp number (Flavor 2 Shape X — see 5.4)
- OR auto-syncs via Coexistence (Flavor 1 — see 5.5)
- Backend transcribes via Whisper, attribution per the WhatsApp channel's rules

**Pipeline (both sub-channels share):**
1. Audio file persisted to Supabase Storage
2. Whisper transcription
3. AI extraction (Haiku 4.5 for light voice memos; Sonnet 4.6 if richer)
4. Operator notified; review + approve in dashboard

**Volume estimate:** 20-60 voice memos/month per heavy operator.

### 5.3 Channel 3 — WhatsApp Forwards (Flavor 2: Shape X)

**Setup:** Operator saves FollowRoom WhatsApp Business number in their phone. Adds clients in FollowRoom dashboard (name + short_context).

**Ingestion flow:**
1. Operator forwards a customer's message to FollowRoom number
2. Operator types a quick identifier as the forward caption (e.g., "Sarah Tan" or "Sarah, East Coast one")
3. Backend webhook receives both messages (forwarded text + caption) — pairs them by proximity
4. Backend creates a **PENDING event** with the forwarded text + identifier; pre-resolves likely client via LLM matching against the operator's client KB
5. **Push notification sent to operator's phone** (FCM / APNs): *"1 pending forward → Sarah Tan? [Confirm] [Change] [Discard]"*
6. Operator taps "Confirm" (or "Change" to pick a different client, or "Discard") — this is the canonical commit event
7. Committed event is attributed deterministically based on operator's tap, written to client's KB

**Why this is structurally zero-misattribution:**
- The forwarded WhatsApp message itself carries no original-sender metadata (Meta protocol-level limit; cannot be worked around). Confirmed by deep research 2026-05-17.
- The operator's typed identifier provides intent signal but is not the commit event.
- The operator's push notification tap IS the commit event — explicit, deterministic, operator-attributed.
- LLM is used only to pre-rank candidates for faster operator tap; LLM never decides attribution.

**Session-lock variant (operator convenience):** If operator forwards multiple messages from one thread quickly, push notification offers "Lock to Sarah Tan for next 5 min — auto-attach future forwards?" Operator confirms once; subsequent forwards in the window auto-attribute without per-forward notifications. The session-lock is itself a single explicit commit event.

**Fallback (operator doesn't tap):** Event sits in dashboard "Pending" queue until operator opens dashboard and processes. Operator can clear queue in batch (one screen, multiple confirmations).

**Volume estimate:** 60-100 forwards/month per heavy operator.

### 5.4 Channel 4 — WhatsApp Business Coexistence (Flavor 1, Phase 2/3)

**Setup:** Operator already uses WhatsApp Business app for client communications. Links their WhatsApp Business account to FollowRoom via Meta's Coexistence feature.

**Ingestion flow:**
1. Operator chats normally with clients in WhatsApp Business app
2. Every direct message in synced 1:1 chats arrives at FollowRoom Cloud API webhook with **full sender attribution** (`from_wa_id` = the customer's actual wa_id)
3. No forwarding needed; no operator action at message-time
4. Backend stores all messages in `events` with `source_type = 'whatsapp_coexistence'` and deterministic client attribution (via phone-number-to-client lookup)
5. AI extraction runs per-message or in batch
6. **Curation happens post-hoc in dashboard:** operator marks (stars / tags) which messages should be added to the formal KB vs which to skip; or AI auto-classifies importance and operator approves

**Why this is structurally zero-misattribution:**
- Direct messages (not forwards) preserve sender attribution at the Meta protocol level.
- Customer's wa_id is unambiguous; phone-number-to-client lookup is deterministic.

**Pricing tier:** Flavor 1 may be gated to Pro tier ($59-99) given the deeper integration + privacy surface.

**Important constraint:** Coexistence does NOT preserve forwarded-message attribution (same Meta limit applies). Direct messages: structurally attributed. Forwarded messages within synced chats: still need Shape X-style operator commit.

**Why this is Phase 2/3, not Phase 1:**
- Coexistence requires WhatsApp Business app (separate from personal WhatsApp) — many target operators won't have it
- Coexistence GA is recent (May 2026); operational risk profile unknown
- Curation UX is its own product question (star vs auto-classify vs chat-level tracking) — better solved with real Phase 1 users to inform the design

### 5.5 Channel 5 — Operator File Drop (Critical for the active room)

This is a peer ingestion channel to transcripts and voice memos, not a footnote under manual notes. Property agents drop documents constantly — floor plans, comparables, contracts, MyAnchor links, calculators, viewing photos. The room is where those artifacts live; file drop is how they get there.

**Sources supported (Phase 1):**
- Mobile camera capture (take photo of property doc, immediate upload)
- Mobile file picker (select from phone library)
- Desktop drag-and-drop
- iOS / Android Share Sheet ("Share to FollowRoom" from any app)
- Paste link from clipboard (property listing URLs, MyAnchor, Google Drive shares)
- In-flow drop alongside voice memo ("here's the floor plan, let me explain") — voice memo is captured into events; file is captured into attachments; both linked

**Attribution at drop time:**
- Operator picks the client at drop (explicit, deterministic)
- Operator adds a contextual note ("here's the floor plan for unit #14-22 we discussed")
- Operator marks a **pending-action type** if the client needs to act:
  - `for_review` — client should review
  - `for_signature` — client needs to sign
  - `for_consideration` — client should think about
  - `for_payment` — payment-related
  - `informational` — no action required
- Optional: link to a specific event / fact / decision in the client's KB

**Pipeline:**
1. Operator initiates drop → file persisted to Supabase Storage (Save Is Sacred — BEFORE any extraction)
2. Metadata captured (filename, mime type, size, operator note, pending-action)
3. Stored as `room_attachments` row + parallel `events` row (with `source_type = 'file_drop'`)
4. AI extraction on text content if applicable (PDF text extraction; image OCR for property docs; semantic content for KB)
5. Visibility defaults to `operator_only` until operator promotes to `client_facing_safe` (puts in client room)
6. Operator notified of the drop (toast / confirmation)
7. Client notified (if `client_facing_safe`) — push or email per operator's setting

**Volume estimate:** 10-40 file drops/month per heavy operator (varies by deal stage; closing deals generate more documents).

**Schema and surface design covered in §6.8 (The Room as Active Surface) and §8.1 (Forward-Compatibility Hooks).**

### 5.6 Channel 6 — Manual Notes

Operator types directly in dashboard. Attribution explicit at write time (operator picks client). Useful for:
- Post-meeting reflections operator wants to capture without recording
- Phone call summaries
- In-person interaction summaries
- Operator's own commentary on a client situation

Pipeline: text → AI extraction (Haiku 4.5) → facts with source = "manual_note"

**Volume estimate:** 20-30 manual notes/month per heavy operator.

### 5.7 Attribution Summary

| Channel | Attribution mechanism | Determinism source |
|---|---|---|
| 1 — Meeting transcripts | Operator picks client at upload | Operator click |
| 2 — Voice memos (phone upload) | Operator picks client at upload | Operator click |
| 2b — Voice memos (WhatsApp) | Shape X or Coexistence (per the WhatsApp channel rules) | Operator tap (Shape X) or protocol-deterministic (Coexistence) |
| 3 — WhatsApp Shape X | Push notification tap-to-confirm | Operator tap |
| 4 — WhatsApp Coexistence | Sender wa_id preserved at protocol level | Meta protocol guarantee |
| 5 — Operator File Drop | Operator picks client at drop | Operator click |
| 6 — Manual notes | Operator picks client at write | Operator click |

**Never used for first-touch attribution:** LLM judgment alone. The LLM may suggest in the review queue (faster operator tap), but the suggestion is never auto-attached.

### 5.8 Cold Start Behavior

**Concern raised in brainstorm:** the first 2-3 events for a brand-new client have minimal KB context for AI extraction/synthesis to work well.

**Mitigations (all in Phase 1):**

1. **Required `short_context` at client creation** — operator writes 2-3 sentences when creating a client (PRD §8.3 field; enforced at form level). Example: *"Sarah Tan — HDB upgrade, East Coast, ~$1.8M, husband in finance."* This seeds the initial profile and gives AI extraction immediate context.

2. **Optional guided onboarding** — dashboard prompts: *"Tell us 3 things you'd want to remember about Sarah."* Operator's typed answers enrich the seed profile.

3. **Most operators create clients AFTER first meeting** — first meeting transcript usually arrives within days of client creation. The KB starts rich, not empty.

4. **For truly cold cases** (forward arrives before any client info exists) → review queue. Operator one-taps to create new client + attach. The correction becomes the seed.

**Net:** the cold-start cliff is bounded to ~1-3 events per new client, occurs at moments when the operator is already paying attention, and is handled gracefully by the review queue.

---

## 6. Knowledge Base Architecture

### 6.1 Phase 1 KB Shape: Karpathy LLM Wiki per Client + Single Corpus with Client Tags

The KB is structured as a Karpathy-style LLM Wiki adapted for FollowRoom's relationship-domain subject. All data lives in Supabase Postgres; markdown is stored in TEXT columns; structured facts in JSONB.

**Per-client conceptual structure:**

```
client_<slug>/
├── events/           # Immutable append-only event log
├── profile.md        # LLM-maintained markdown, ~400 line cap, two views
│                     (internal_profile + client_facing_profile)
├── facts.json        # Typed key facts, deduped, with provenance
├── tone_profile.md   # Operator's voice for this client (Phase 2+)
├── log.md            # Append-only ingest history (audit trail)
└── index.md          # Catalog of all events + facts + sections
```

In Postgres, this maps to columns + tables (Section 8.1 has the schema).

**Single-corpus framing:** all events live in a single `events` table tagged by `client_id`. Cross-relationship queries (PRD §15 cross-relationship meta intelligence) are simple grouped SQL queries with LLM synthesis layered on top. **No federation infrastructure at Phase 1** — that's Phase 3 Hivemind territory.

### 6.2 The Four Layers

Per client, the KB has four logical layers:

**1. EVENTS (immutable, append-only)**
- `raw_text` — the source content (transcript line, forwarded message body, voice memo transcript, manual note)
- `source_type` — `meeting_transcript | voice_memo | whatsapp_forward_shapeX | whatsapp_coexistence | manual_note`
- `timestamp` — when recorded (event time, not ingestion time)
- `ingestion_time` — when arrived at FollowRoom
- `embedding` — vector representation for retrieval
- `attachments` — file references for media
- **Database-level append-only enforcement** via PostgreSQL BEFORE UPDATE trigger (Decades migration 069 pattern; Section 8.1)

**2. FACTS (typed, deduped, regenerable, with provenance)**
- `type` — `goal | budget_constraint | objection | family_factor | timeline_signal | etc.` (extensible enum)
- `value` — the fact content
- `source_event_ids[]` — pointers back to the immutable events that grounded this fact
- `confidence_score` — LLM-reported confidence
- `visibility` — `internal | client_facing_safe`
- `superseded_by` — pointer to a newer fact that replaced this one (UPDATE in ADD/UPDATE/DELETE/NOOP)
- `model_id + prompt_hash + schema_version + generated_at` — regeneration metadata
- Operator can mark facts as `user_stance = unreviewed | accepted | rejected | reframed`

**3. OPERATOR OVERRIDES (editable, permanent, win over derived)**
- On any fact or any profile section
- Marked `provenance = 'operator_edited'` or `'operator_curated'`
- Never overwritten by re-extraction (Axiom 4)
- Operator can edit, delete, mark sensitive
- Feed back into future generation prompts as "operator canon"

**4. PROFILE (markdown, capped, regenerated on conflict / event arrival)**

Two physical views stored:

**Internal profile** — full visibility, for dashboard + attribution suggestions + reply generation
```markdown
## Identity
- Sarah Tan, HDB upgrader, East Coast [ev_001, ev_023]
- Spouse: works in finance, key decision-maker [ev_001, ev_045]

## Goals
- Buy a 3-bedroom HDB in East Coast within 6 months [ev_001]
- Maintain monthly repayment comfort (max ~$5k/mo) [ev_023, ev_045]

## Constraints
- Budget ceiling ~$1.8M total; flexible to $2.2M if right unit [ev_001, ev_045]
- Wife wants proximity to parents (Marine Parade preference) [ev_023]
- Timeline shifted post-bonus (Q1 2027 likely) [ev_045]

## Decision dynamics
- Spouse alignment is the blocker on timing [ev_023, ev_045]
- Wife's parents involved in informal advisory role [ev_023]

## Preferences
- Pet-friendly; en-suite bathroom for kids [ev_001]
- Quiet streets; avoid main road frontage [ev_023]

## Open threads
- Promised floor plans for unit #14-22 by Wednesday [ev_067]
- Awaiting wife's confirmation on Marine Parade alternatives [ev_045]

## Recent events
- 2026-04-15: meeting transcript — discussed alternatives [ev_023]
- 2026-05-10: WhatsApp — confirmed Saturday viewing [ev_067]
```

**Client-facing profile** — tactfully rewritten subset, for room publishing. Tier 3 inferences (family-blocker speculation, emotional state) are physically not present in this view. The rewrite pipeline literally cannot leak them because the prompt is given a different SQL view that doesn't include those rows.

```markdown
## Goals
- Buying a 3-bedroom HDB in East Coast within the next 6 months
- Looking for monthly repayment comfort (~$5k/mo range)

## Key Considerations
- Budget around $1.8M, flexible if the right unit appears
- Family proximity (Marine Parade area) is important
- Timeline may move to after Q1 2027

## What's Pending
- Floor plans for unit #14-22 (sending Wednesday)
- Alternative options near Marine Parade
```

**Cap: ~400 lines for the internal profile.** Empirically (per 2026 research) profiles longer than this degrade LLM performance. Phase 2 introduces explicit summarization-and-archive at the 400-line threshold.

### 6.3 ADD/UPDATE/DELETE/NOOP Pipeline

When a new event arrives, the ingestion pipeline runs the following per extracted candidate fact:

1. **Extract candidates** from the new event (Sonnet 4.6 for rich extraction, Haiku 4.5 for cheap classification)
2. **For each candidate, semantic-match against existing facts in this client's KB**
3. **Determine action:**
   - **ADD** — no match found → append new fact with source pointer
   - **UPDATE** — semantic match but value differs (`budget: $1.8M` → `$2.2M`) → supersede old, add new, link via `superseded_by`
   - **DELETE** — new event explicitly negates a prior fact (`"actually no longer East Coast"`) → mark old as superseded with `deletion_reason`
   - **NOOP** — same fact, same value → append source_event_id to existing (more evidence, no new fact)
4. **Conflict detection:** if UPDATE/DELETE confidence is low (<0.7) or the new value contradicts strong existing evidence → flag for operator review rather than auto-apply
5. **Profile regeneration:** if any fact changed, regenerate the affected profile section(s) for both views; operator-canonical facts always survive regeneration

This pipeline is itself an instance of Pattern 21 (Source Evidence Immutability) — facts mutate via supersession, never via overwrite. The full history is preserved.

### 6.4 Visibility Tiers (FollowRoom-Specific)

Beyond LineOS's `internal | client_facing` distinction, FollowRoom adds **agency-visible** to support Phase 3 multi-operator agency contexts:

```
visibility = operator_only        # default; internal memory
           | agency_visible       # Phase 3; visible to operators in same agency tenant
           | client_facing_safe   # appears in client-facing room
           | public               # not used in Phase 1; reserved
```

**Schema-level enforcement:**
- Every fact, every profile section, every room update carries a `visibility` column
- Tier-promotion is an explicit operator action that creates an audit trail event in `visibility_promotions` table
- Client-facing room view is generated from a SQL view that filters `WHERE visibility = 'client_facing_safe'` — the rewrite prompt cannot see `operator_only` rows

**Why this is load-bearing:**
- Tier 3 safety guarantee (Axiom 6): structural, not promptly. The rewrite prompt physically doesn't receive private inferences.
- Phase 3 agency adoption: `agency_visible` is the proto-mandate primitive that becomes Hivemind's full governance arbitration.

### 6.5 Source Citations + Provenance

Every fact carries `source_event_ids[]` pointing to the immutable events that grounded it. Every claim in the room or in a suggested reply must be traceable to a source span.

**UI manifestation:**
- In dashboard: hover any fact / profile bullet → see the source events with verbatim quotes
- In suggested reply drafts: each substantive claim has a small footnote linking to source events
- In client-facing room: facts shown without footnotes (operators decide when to expose receipts to clients)

**Why citations are non-negotiable** (Axiom 3):
- Trust architecture for AI claims — operator can verify
- Defense against hallucinated dates, mis-attributed quotes (the dominant LLM failure modes per 2026 research)
- Enables Phase 2 Zettel link-graph (units link via shared source events)
- Enables Phase 3 Hivemind audit + arbitration

### 6.6 Phase 2 Upgrade Path (Zettel)

When Phase 1 has 50+ paying operators AND demand for cross-relationship synthesis is documented, the Zettel upgrade adds:

- **SQLite link-graph (or pgvector + Postgres equivalent)** with `zettel_units`, `zettel_links`, `zettel_drift` tables
- **Unit-level addressing via sidecar** — each `facts` row, each profile bullet, each event gets a unit-ID; bidirectional links resolve at unit level not row level
- **Bookkeeper agent** — adapted from Demosthenes spec in LineOS. Maintains link-graph + unit-IDs + drift detection autonomously. Cadence: incremental (per event) + weekly maintain + on-demand reflection
- **Serendipity Engine** — reads the link-graph; surfaces emergent cross-client patterns as invitations ("3 clients mentioned X in 30 days"); Pattern 14 (Serendipity as Reward) made operational
- **Topic emergence per client** — Pattern 11 extended; AI clusters per-client topics over time
- **Anti-Goodhart safeguards** — Pattern 23 applied to synthesis; drift detection when emergent ontology diverges from source evidence

**Migration shape:** purely additive. Existing data structures unchanged. Unit-IDs added via sidecar tables; existing rows unmodified. Bookkeeper agent runs alongside the existing direct write path.

### 6.7 Phase 3 Upgrade Path (Hivemind)

When Phase 2 has 100+ Pro operators AND multiple agency inquiries, the Hivemind upgrade adds:

- **YAML manifest per agency tenant** (`hivemind.yaml`) — catalogs all client domains, source files, tier assignments, governance rules. Schema documented in `Decades/docs/proposals/2026-04-08-hivemind-meta-layer-proposal.md` lines 251-314
- **Formal `store()` write path** with multi-agent attribution + scoping enforcement
- **Tier 0/1/2/3/Aug loading discipline** — always-loaded budget (~800 tokens) + on-demand recall + cross-domain + forensic + augmentation index
- **Gravity model for access** — Routine / Medium / High routing per `(action, source_domain, target_domain, tool_sensitivity)` tuple
- **Temporal knowledge graph** — `"what was true about Sarah at time T?"` queries via sqlite-vec or pgvector with bi-temporal columns
- **Cross-operator federation within agency** — managers, assistants, sub-agents; per-principal data model (`(principal_id, rule)`)
- **Multi-surface coherence** — same memory accessible from web + Telegram + mobile + Slack
- **Multi-agent fleet** — bookkeeper agents per operator, governor agents for agency-level operations, assistant agents per role
- **Permission decay** — standing permissions expire after 30 days non-use

**Migration shape:** additive. Phase 1 + Phase 2 data unchanged. Hivemind layer wraps existing structures with manifest + governance + tiered loading + federation primitives.

### 6.8 The Room as Active Delivery + Organization Surface

The client-facing room is **not a static recap.** It's an active surface where the operator delivers artifacts tied to the relationship timeline, and the client views, sorts, and acts on them. This is load-bearing for the product's promise — the room is where tangible value accumulates between the operator and the client, week after week.

#### Three views of the same underlying data

The same `room_attachments` rows serve three purposes simultaneously:

1. **Operator's working delivery channel** — what they push to the client during the relationship (floor plans, market reports, calculators, contracts, comparisons, photos from viewings, MyAnchor links)
2. **Client's reference library** — what the client accesses later, organized and sortable, accessible from any device via the private room link
3. **Relationship evidence chain** — what was sent, received, viewed, acted on; the audit trail of artifacts that grounds Pattern 9 (Truth With Receipts) for tangible outputs

#### Operator side — quick drop with contextual note

**Drop interactions (Phase 1):**

| Interaction | Where | Use case |
|---|---|---|
| Camera capture → upload | Mobile (PWA) | Snap a property doc, listing flyer, or whiteboard on the spot |
| File picker | Mobile or desktop | Drop existing PDFs, images, docs |
| Drag-and-drop | Desktop | Multi-file drop from desktop into a client's room |
| Share Sheet (iOS / Android) | Mobile | "Share to FollowRoom" from any app — Photos, Files, Safari/Chrome, Drive |
| Paste link | Mobile or desktop | MyAnchor listings, Google Drive shares, news articles |
| In-flow drop alongside voice memo | Mobile | "Here's the floor plan, let me explain" — voice memo + file captured together, linked in KB |

**Drop UX target: 2-3 taps from intent to confirmed drop on mobile.** Pattern 7 (Voice Within Two Taps) extended to file capture — friction kills the data.

**Each drop attaches contextual metadata:**

- **Operator note** (free text, 1-3 sentences) — *"Here's the floor plan for unit #14-22 we discussed"*
- **Pending action type** (optional but encouraged) — `for_review` / `for_signature` / `for_consideration` / `for_payment` / `informational`
- **Due date** (optional) — when the action is needed by
- **Link to event / fact / decision** in the client's KB (optional, AI-suggested) — connects the artifact to its triggering context

**Visibility default: `operator_only`.** Operator explicitly promotes to `client_facing_safe` to put in the client room. Promotion is a one-tap action; it can happen at drop-time (default for most artifacts) or later (if operator wants to hold a draft).

#### Client side — view, sort, organize, act

The room presents attachments in multiple complementary views, with the **Pending Action** surface most prominent:

**Default view: "What's pending for you"** — at the top of the room, before the timeline.
- Each item shows the file + action type + due date + operator's note + how-to (e.g., "Sign and reply via WhatsApp")
- Tap to view inline (PDF preview, image lightbox); long-press to download
- Client marks "viewed" or "acted on" (or app infers from open + download events)

**Timeline view** — chronological, embedded in the relationship narrative.
- Each meeting / event / file appears in time order
- Files appear inline with their note and pending status

**Filter views** (toggles at top):
- **By type** — Documents / Images / PDFs / Links / Spreadsheets
- **By recency** — most recent first
- **By status** — Pending action / Viewed / Acted on / Archived

**Inline preview** for common types (PDFs, images); **download** for others (xlsx, docx, etc., with operator-controlled "render in browser" option for premium feel).

**View tracking** — operator sees on their dashboard:
- Client opened the room (timestamp)
- Client opened each specific attachment (timestamp)
- Client downloaded (timestamp)
- Client marked acted (timestamp + action type)
- Client hasn't opened in N days (stale signal)

This is Pattern 9 (Truth With Receipts) extended — every artifact's lifecycle has provenance.

#### Pending action mechanic

When operator marks an attachment with a pending-action type, several things happen:

**Client room:**
- Pending item appears prominently at top, with clear "what to do" text
- Visual cue (badge, color) indicates urgency
- Marking acted (or system inferring from download + return-to-room behavior) clears it from the surface
- Acted items move to "Recently acted" with timestamp

**Operator dashboard:**
- Per-client view shows pending actions and their client status (sent / viewed / acted / overdue)
- Cross-client "Pending Actions Across All Clients" view — operator's prioritization surface
- Notifications when status changes (especially "client opened but didn't act after N days" — soft nudge to follow up)

**AI integration:**
- Suggested follow-up replies surface when a pending action stalls: *"Sarah hasn't acted on the floor plan you sent 5 days ago. Draft a soft check-in?"*
- Cross-relationship insights surface stuck patterns: *"3 clients haven't actioned similar pending items — consider revising the artifact?"*

This converts the room from passive recap to active workflow surface. The client doesn't have to remember what's pending; the operator doesn't have to remember what to chase.

#### Timeline coherence

The room is a relationship timeline with artifacts embedded at their correct moments — not a flat folder:

```
─────────────────────────────────────────────────────────────
April 10  Initial viewing meeting
          Recap: Discussed 3-bed HDB options, East Coast
          Promised: floor plans for unit #14-22

April 12  Voice memo from operator
          Summary: Spoke with Sarah about Marine Parade alternatives

April 13  📄 Floor plan #14-22  [PDF · for review]
          Operator's note: "The floor plan for the East Coast unit
                            we discussed — let me know what stands out."
          Status: Viewed Apr 14 · not yet actioned

April 15  WhatsApp from Sarah
          Recap: Confirmed Saturday viewing, asked about repayment

April 16  📊 Affordability scenarios  [PDF · for consideration]
          Operator's note: "Three monthly-repayment scenarios so you
                            and your husband can think through what
                            feels comfortable."
          Status: Viewed Apr 16 · acted on Apr 17

April 17  📝 Counter-proposal v1  [PDF · for signature, due Apr 24]
          Operator's note: "Revised proposal with adjusted price +
                            financing options. Pages 3-4 need your sign."
          Status: Not yet viewed
─────────────────────────────────────────────────────────────
```

This timeline is the heart of the room — the unfolding relationship narrative with artifacts at the right moments, in the right context.

#### Mobile-first, adaptive UX

The room is opened by clients **on mobile** (private link from WhatsApp on a phone). Operators interact **on both** (mobile for in-the-moment captures; desktop for considered review). UX adapts:

**Mobile (operator):**
- Bottom-anchored quick-action toolbar (camera, file, voice, note)
- Swipe-to-attach gestures
- Native share sheet integration
- 2-3 tap target for drop intent → confirmed drop
- Inline voice memo recording while attaching

**Mobile (client):**
- Single scrollable surface; no nested navigation
- Tap to preview, long-press for actions (download, mark acted)
- "What's pending" sticky to top until cleared
- Edge-rendered PPR (per Section 9.2) for fast initial load
- Works fluently on 3G — graceful degradation for large file previews

**Desktop (both):**
- Multi-pane layouts (timeline + filters + preview)
- Drag-drop zones
- Keyboard shortcuts for power-user operators
- Multi-file batch operations

**Adaptive by content:**
- Image-heavy clients (lots of property photos) → grid view available
- Document-heavy (contracts, proposals) → list view default
- Mixed → timeline by default
- Single-pending-action client → focused mode on the pending item

#### Phase progression for room-as-surface

| Phase | Room capability |
|---|---|
| **Phase 1** | Per-client `room_attachments` table; operator drop from all sources; client view with timeline + type + recency + pending-action surface; view tracking; promote-to-client visibility tier |
| **Phase 2** | AI-enhanced organization (auto-categorization of attachments by content); semantic search across all of a client's files; cross-client artifact reuse (*"reuse the affordability calculator you sent to Tan Family"*); Pending Action AI nudges (*"Sarah's been sitting on the floor plan 5 days"*) |
| **Phase 3** | Agency-level shared artifact library (brokerage-approved templates, compliance-vetted forms); per-agent attribution within agency tenant; agency-wide search; multi-agent collaboration on artifacts; client room can show "from your assigned agent" + "from the brokerage" sections |

#### Pattern inheritance for attachments

| Pattern | How it applies to attachments |
|---|---|
| **Pattern 7 — Voice Within Two Taps** | Extended: file drop within 2-3 taps from operator intent |
| **Pattern 9 — Truth With Receipts** | Every attachment carries provenance (added by, when, why-note); client-side view tracking grounds "sent" claims |
| **Pattern 16 — Save Is Sacred** | File persisted to Supabase Storage BEFORE any extraction, OCR, or AI processing |
| **Pattern 18 — Never-Delete Doctrine** | Soft-delete by default; explicit hard-delete requires grace period + audit trail |
| **Pattern 21 — Source Evidence Immutability** | Original file is immutable; new versions create new rows with `superseded_by` link |
| **Pattern 22 — Recovery On Every Open** | Recovery sweep on session start checks for failed uploads, orphaned storage objects, stuck OCR jobs |
| **Pattern 2 — Quiet Witness** | System surfaces "you have 3 unviewed files" or "Sarah opened but didn't act 5 days ago" without nagging; invitations not prescriptions |
| **Visibility Tiers (FollowRoom-specific)** | Default `operator_only`; explicit promotion to `client_facing_safe`; Phase 3 adds `agency_visible` for shared brokerage libraries |

---

## 7. TG-Lite Governance (Phase 1)

FollowRoom adopts Temporal Governance primitives, but in lite form for Phase 1 — only what a single-operator product needs. The full eight TG primitives become relevant at Phase 3 agency adoption.

### 7.1 Six Primitives Applied at Phase 1

| TG Primitive | Phase 1 application |
|---|---|
| **Intent** | Operator's intent (book of business compounds) + per-client intent (this client wants school-catchment home by Q3). Captured at client creation; refined via meeting transcripts. |
| **State** | Per-client state — warm/cold, last-touched-N-days-ago, promise-outstanding, deal-stage. Observable, not interpretive. Surfaced in dashboard. |
| **Signals** | Tiered signal ecology: outcome (closed/lost), behavioral (response time), weak ("they keep mentioning their kids' school"), contradiction ("said urgent but ignored 3 messages"). Tier per Axiom 6. |
| **Guards** | Tier 3 freeze; never-delete doctrine; save-is-sacred; visibility tier rules. These are the constitutional red lines. Cannot be overridden without explicit operator action + audit trail. |
| **Loops** | Daily resurface card (Pattern 8); weekly "what fell through" review; monthly per-client arc review. Cron-driven. |
| **Memory** | The KB itself (Section 6). Bi-temporal columns enable "what did we believe about X at time T?" |

### 7.2 Skipped at Phase 1 (Phase 3 additions)

- **Posture** — multi-operator governance needs posture for agency-level coordination. Single-operator Phase 1 doesn't need it (operator IS the posture).
- **Mandates** — full authority gradient (Observer → Advisor → Collaborator → Executor → Governor) only relevant when multiple agents act. Phase 1's only "agent" is the operator + cron extraction.

### 7.3 Visibility Tier Approval Gate

The Phase 1 governance core is the **operator approval gate for client-facing publishing.** Every promotion from `operator_only` to `client_facing_safe` is:

1. Explicit operator action (button tap in dashboard)
2. Logged to `visibility_promotions` table with `{from_tier, to_tier, approved_by, approved_at, artifact_id, reason}`
3. Reversible (operator can demote back to `operator_only`)

This proto-mandate primitive evolves into Phase 3 Hivemind's full governance arbitration.

### 7.4 Operator-Approval Discipline

Three things require explicit operator approval before going live:

1. **Client-facing room updates** — drafted by AI, approved by operator, published to room
2. **Suggested replies** — drafted by AI, copied by operator, sent through operator's own WhatsApp (we never send outbound)
3. **Attribution commits** — every event ingestion's attribution requires deterministic operator commit (Section 5)

Defaults:
- New room update drafts default to `pending_approval`, not auto-published
- Suggested replies are shown for copying, never auto-sent
- Attribution defaults to "pending in queue" if no commit event arrived

---

## 8. Forward-Compatibility Hooks (Phase 1 Must Bake In)

For Phase 2 (Zettel) and Phase 3 (Hivemind) to be ADDITIVE layers — not migrations — Phase 1 must include the following from Day 1. These are non-negotiable Phase 1 architecture decisions.

### 8.1 Schema-Level

**Append-only enforcement on raw-source columns:**
```sql
CREATE OR REPLACE FUNCTION enforce_raw_text_append_only()
RETURNS TRIGGER AS $$
BEGIN
  IF OLD.raw_text IS NOT NULL AND NEW.raw_text != OLD.raw_text THEN
    RAISE EXCEPTION 'raw_text is append-only; mutations are forbidden';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER events_raw_text_append_only
BEFORE UPDATE ON events
FOR EACH ROW EXECUTE FUNCTION enforce_raw_text_append_only();
```

Following Decades migration 069. Cannot be retrofitted later without data audit.

**Soft-delete columns on every user-data table:**
```sql
is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
deleted_at TIMESTAMPTZ NULL,
```

Pattern 18. All `SELECT` queries must `WHERE NOT is_deleted` by default. Retrofit cost is high.

**Bi-temporal columns** on the events ledger:
```sql
transaction_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- when recorded
valid_time TIMESTAMPTZ NULL,                          -- when claimed true (event time)
```

TG Memory primitive. Phase 3 temporal queries require this.

**Generation metadata JSONB on every AI-derived artifact:**
```sql
generation_metadata JSONB NOT NULL DEFAULT '{}',  -- { model_id, prompt_version, prompt_hash, schema_version, evidence_snapshot, regenerated_from, generated_at }
```

Axiom 2 (Truth ≠ Tone) regenerability requirement.

**User stance column** on interpretive artifacts:
```sql
user_stance TEXT CHECK (user_stance IN ('unreviewed','accepted','rejected','reframed','operator_curated')) DEFAULT 'unreviewed',
user_stance_set_at TIMESTAMPTZ NULL,
```

Axiom 4 (operator-edit-is-canon) enforcement.

**Provenance enum** on artifacts:
```sql
provenance TEXT CHECK (provenance IN ('llm_generated','operator_curated','operator_edited','regenerable','canonical')) DEFAULT 'llm_generated',
```

Zettel Axiom 2 prep.

**Room attachments table** (file drop channel, §5.5; surface design §6.8):

```sql
CREATE TABLE room_attachments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID NOT NULL REFERENCES clients(id),
  operator_id UUID NOT NULL REFERENCES operators(id),

  -- File metadata
  storage_path TEXT NOT NULL,            -- Supabase Storage path
  original_filename TEXT NOT NULL,
  mime_type TEXT NOT NULL,
  size_bytes BIGINT NOT NULL,
  content_hash TEXT,                     -- SHA256 for dedup + integrity

  -- Operator context
  source_event_id UUID REFERENCES events(id),   -- if drop linked to an event (e.g., dropped alongside a voice memo)
  related_fact_ids UUID[],                       -- optional links to facts in the KB
  operator_note TEXT,

  -- Pending action mechanic
  pending_action_type TEXT CHECK (pending_action_type IN
    ('for_review','for_signature','for_consideration','for_payment','informational')),
  pending_action_due TIMESTAMPTZ,
  pending_action_label TEXT,             -- human-readable, e.g. "Sign pages 3-4"

  -- Visibility (FollowRoom-specific tiers)
  visibility TEXT NOT NULL DEFAULT 'operator_only'
    CHECK (visibility IN ('operator_only','client_facing_safe','agency_visible')),
  visibility_promoted_at TIMESTAMPTZ,
  visibility_promoted_by TEXT,            -- 'operator:<id>'

  -- Client interaction tracking
  client_viewed_at TIMESTAMPTZ,
  client_viewed_count INTEGER NOT NULL DEFAULT 0,
  client_downloaded_at TIMESTAMPTZ,
  client_acted_at TIMESTAMPTZ,
  client_action_taken TEXT,              -- 'acknowledged','signed','declined','paid','archived'

  -- Versioning (Pattern 21 — Source Evidence Immutability)
  superseded_by UUID REFERENCES room_attachments(id),
  supersedes UUID REFERENCES room_attachments(id),
  version_number INTEGER NOT NULL DEFAULT 1,

  -- Lifecycle
  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,

  -- Provenance + regeneration metadata (extraction/OCR)
  extraction_metadata JSONB DEFAULT '{}',  -- { model_id, prompt_hash, schema_version, ocr_engine, extracted_text_hash }
  extracted_text TEXT,                      -- searchable text content (PDF text, OCR'd image text)

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for room-surface queries
CREATE INDEX idx_attachments_client_visible ON room_attachments(client_id, visibility, created_at DESC)
  WHERE NOT is_deleted;
CREATE INDEX idx_attachments_pending ON room_attachments(client_id, pending_action_type, pending_action_due)
  WHERE pending_action_type IS NOT NULL AND client_acted_at IS NULL AND NOT is_deleted;
CREATE INDEX idx_attachments_type ON room_attachments(client_id, mime_type)
  WHERE NOT is_deleted;
CREATE INDEX idx_attachments_extracted_text ON room_attachments USING gin(to_tsvector('english', extracted_text))
  WHERE NOT is_deleted;

-- Append-only enforcement on the file itself (storage_path, content_hash, original_filename immutable)
CREATE OR REPLACE FUNCTION enforce_attachment_file_immutability()
RETURNS TRIGGER AS $$
BEGIN
  IF OLD.storage_path != NEW.storage_path
     OR OLD.content_hash IS DISTINCT FROM NEW.content_hash
     OR OLD.original_filename != NEW.original_filename
     OR OLD.size_bytes != NEW.size_bytes THEN
    RAISE EXCEPTION 'attachment file identity is immutable; create a new version via superseded_by';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER attachments_file_immutability
BEFORE UPDATE ON room_attachments
FOR EACH ROW EXECUTE FUNCTION enforce_attachment_file_immutability();
```

**Client-facing room view** (Phase 1):

```sql
CREATE VIEW room_attachments_client_facing AS
SELECT
  id, client_id, original_filename, mime_type, size_bytes,
  operator_note, pending_action_type, pending_action_due, pending_action_label,
  client_viewed_at, client_acted_at, client_action_taken,
  version_number, created_at
FROM room_attachments
WHERE visibility = 'client_facing_safe'
  AND NOT is_deleted
  AND superseded_by IS NULL;  -- only show current version
```

The client room rendering pipeline reads from this view; the base table is operator-only. The rewrite prompt for room generation receives data filtered through this view.

### 8.2 Attribution Metadata (Everywhere)

Every write to durable memory carries inline attribution. Per-principal data model from Day 1:

```sql
CREATE TABLE attributions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  artifact_id UUID NOT NULL,  -- which event / fact / profile_section / etc.
  artifact_type TEXT NOT NULL,
  agent_id TEXT NOT NULL,     -- 'operator' at Phase 1; 'bookkeeper:demosthenes' at Phase 2+
  surface TEXT NOT NULL,      -- 'web_dashboard' | 'whatsapp_webhook' | 'voice_upload' | etc.
  session_id TEXT NULL,
  turn_index INTEGER NULL,
  confidence REAL NOT NULL DEFAULT 1.0,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  reason TEXT NULL            -- free-form explanation
);
```

Even at N=1 operator, this exists. Costs near-nothing; prevents multi-principal breakage in Phase 3.

### 8.3 Write Path Discipline

**Single governed write path** — even if it's a thin wrapper over a direct DB insert in Phase 1:

```python
# backend/app/services/store.py
def store(
    domain: str,        # 'client:<slug>' at Phase 1; Phase 3 expands
    artifact_type: str, # 'event' | 'fact' | 'profile_section' | 'room_update_draft'
    payload: dict,
    attribution: AttributionMetadata,
) -> StoredArtifact:
    """
    Phase 1: thin wrapper over direct insert + attribution record.
    Phase 3: same signature; implementation adds scoping, dedup, redaction.
    """
    # Phase 1: validate, insert, log attribution
    # Phase 3 (added later): scope check, dedup check, redaction notice injection
    ...
```

If Phase 1 has 12 ad-hoc write paths, Phase 3 becomes a migration, not an additive layer.

**Inline attribution on append** (not separate audit log alone):
- `events.raw_text` row carries `attributed_to` + `attributed_at` columns inline
- Plus a parallel `attributions` table entry for queryable audit
- Two-file split (canonical + pending) deferred to Phase 3

### 8.4 File / Directory Structure

The `memory/` directory exists per operator from Day 1, even if Phase 1 populates only a few files:

```
operators/{operator_id}/
├── memory/
│   ├── standinginstructions.md     # Phase 1: operator preferences. Phase 3: governance axioms + scoping rules
│   ├── decisions.md                # Phase 1: optional. Phase 3: append-only governance decisions
│   ├── last.md                     # Phase 1: dashboard "where did I leave off". Phase 3: agent session-start
│   └── .hivemind/                  # Empty in Phase 1. Reserved for Phase 3 (attributions, escalations, etc.)
└── clients/
    └── {client_slug}/
        ├── events/                  # Per-client events index (DB-backed)
        ├── profile.md               # Stored as Postgres TEXT column; UI exposes filesystem-shaped path
        ├── facts.json               # Stored as Postgres JSONB; UI exposes filesystem-shaped path
        ├── log.md                   # Append-only ingest log
        └── index.md                 # Auto-generated catalog
```

Note: at Phase 1 these are conceptual paths backed by Postgres rows. Phase 3 may add a literal filesystem export for portability + MCP exposure.

### 8.5 Tooling Abstractions

**`AgentDispatcher` + logical roles** from Day 1:

```python
# backend/app/ai/dispatcher.py
class AgentDispatcher:
    def dispatch(self, role: LogicalRole, prompt: str, **kwargs) -> StructuredResponse:
        provider, model = self.resolve(role)  # config-driven
        return provider.call(model, prompt, **kwargs)

# Roles (logical, not model-specific):
class LogicalRole(Enum):
    CLASSIFIER = "classifier"     # cheap classification; Haiku 4.5
    SUMMARIZER = "summarizer"     # text → summary; Haiku 4.5 or Sonnet 4.6
    EXTRACTOR = "extractor"       # facts extraction; Sonnet 4.6
    GENERATOR = "generator"       # tactful prose; Sonnet 4.6
    JUDGE = "judge"               # LLM-as-judge; Haiku 4.5
    VALIDATOR = "validator"       # schema validation; Haiku 4.5
    TRANSCRIBER = "transcriber"   # audio → text; Whisper
```

Even if Phase 1 uses Anthropic exclusively, the indirection prevents vendor coupling. Pattern 20 (Vendor Agnostic).

**`instructor` library wrapping Anthropic SDK** for structured output + auto-retry on validation failure. OpenAI SDK as the second adapter (already locked decision).

**Receipts data structure** on every interpretive artifact:
```python
@dataclass
class Receipt:
    snippet: str            # verbatim quote
    source_event_id: UUID
    source_date: datetime

@dataclass
class Fact:
    type: str
    value: str
    receipts: list[Receipt]  # mandatory; cannot be empty
    confidence: float
    visibility: Visibility
    # ... plus generation_metadata, provenance, user_stance, etc.
```

Phase 1 may not always display them; Phase 2 (Ask interface) and Phase 3 (Hivemind recall) require them as the trust substrate.

**Topic tags** on every artifact (free-form strings, denormalized). Phase 1 doesn't route on them; Phase 3 manifest routing requires the data.

### 8.6 Visibility Infrastructure

**`visibility` column** on every artifact that could potentially be shared (events, facts, profile sections, room update drafts). Default: `operator_only`. Promotion to `client_facing_safe` (or Phase 3's `agency_visible`) is an explicit audit-trail event.

**Approval-gate event log** (`visibility_promotions` table):
```sql
CREATE TABLE visibility_promotions (
  id UUID PRIMARY KEY,
  artifact_id UUID NOT NULL,
  artifact_type TEXT NOT NULL,
  from_tier TEXT NOT NULL,
  to_tier TEXT NOT NULL,
  approved_by TEXT NOT NULL,  -- 'operator:<id>'
  approved_at TIMESTAMPTZ NOT NULL,
  reason TEXT,
  reversible BOOLEAN NOT NULL DEFAULT TRUE
);
```

This becomes the proto-mandate for Phase 3 multi-operator governance.

**SQL views for visibility filtering:**

```sql
-- Phase 1 views
CREATE VIEW facts_internal AS
  SELECT * FROM facts WHERE NOT is_deleted;

CREATE VIEW facts_client_facing AS
  SELECT * FROM facts
  WHERE visibility = 'client_facing_safe' AND NOT is_deleted;
```

The room-rendering pipeline reads from `facts_client_facing`, never from the base table. The rewrite prompt receives data from the client-facing view; Tier 3 inferences are physically absent.

---

## 9. Tech Stack Mapping

Locked through brainstorm (see decision ledger entries from 2026-05-16 onward).

### 9.1 Backend

- **FastAPI + Python** — chosen for AI-pipeline alignment (instructor + Pydantic + structured_call pattern from Decades)
- **Hosted on Render** — Starter web service + Background Worker. Reliability ~3x better than Railway in 2026 research; 100-min HTTP cap (vs Railway's 15-min) matters for transcript processing

### 9.2 Frontend

- **Next.js 15 (App Router) + Tailwind + shadcn/ui + Tremor + TanStack Table** — canonical 2026 stack for dense operator dashboards
- **Hosted on Vercel** — natural Next.js home; PPR (Partial Prerendering) for `/room/[slug]` to achieve "instant on mobile" load
- **Single app with route groups** — `(dashboard)` auth-gated + `room/[slug]` public; middleware matcher excludes `/room/:slug*` from auth

### 9.3 Database / Auth / Storage

- **Supabase Postgres + Auth + Storage** — single security boundary; RLS for cross-operator isolation; `@supabase/ssr` package for Next.js integration
- **Critical footgun avoided:** instantiate Supabase client INSIDE each request handler, never module-scope (avoids cross-user session leak on Vercel Fluid Compute)
- **Public room reads via `rooms_public` view** with narrow RLS (`USING (is_public = TRUE)`) — not column-grant gymnastics on base table

### 9.4 AI

- **Anthropic primary** — Sonnet 4.6 for extraction + tactful rewrite + room generation + cross-rel insights; Haiku 4.5 for classification + LLM-as-judge + cheap extraction
- **`instructor` library** wrapping Anthropic SDK for structured output + auto-retry on validation failure
- **OpenAI as the second adapter** (text-embedding-3-small for embeddings; available as Sonnet alternative if needed)
- **1-hour prompt cache TTL** (pay 2× write premium; cache hit discount is 90% on Anthropic — biggest single cost lever)
- **Per-client prefix cached:** `[system + tools + tone_profile + last 20 messages + facts summary] | break | new event`

### 9.5 WhatsApp

- **Meta Cloud API directly** (no BSP) — free inbound; full payload control
- **Phone number rental** ~$0-1/month; Meta business verification 2-10 days

### 9.6 Transcription

- **Whisper API (OpenAI)** — $0.006/min; mature; multi-language
- **Alternative: Deepgram Nova-3** at ~$0.0043/min — flagged as cost-cutting opportunity at scale if Whisper budget becomes painful

### 9.7 Push Notifications

- **FCM (Android) + APNs (iOS)** — free at any realistic volume; web push as fallback

### 9.8 Design Discipline Layer

FollowRoom's UI surfaces (operator dashboard + client-facing room) are visual-stakes critical — generic AI-SaaS aesthetic undermines the "premium living relationship room" positioning. Two-phase design discipline approach:

**Phase 1 (founding):**
- **Author `DESIGN.md` and `PRODUCT.md` at FollowRoom root** — analogous to `PROJECT_DEV_SOUL.md` for engineering doctrine. These capture brand (warm-investigator, quiet witness, evidentiary), audience (relationship-driven sales operators + their clients), voice (calm, polished, never coaching), anti-references (generic AI SaaS, Linear-copy dashboards, dark-mode-by-default sterility, gradient hero sections).
- **Reference Impeccable's anti-pattern catalog as a checklist** — purple gradients, nested cards, overused fonts, gradient headings, low contrast, cramped spacing. Use as a human-in-the-loop reference during UI design reviews; no tooling dependency yet.
- **No CI lint or audit tools for design** — Phase 1 has too little UI to justify tooling overhead.

**Phase 1.5 (when meaningful UI exists):**
- **Adopt Impeccable's CLI** as a dev dependency
- **Add `impeccable detect` to CI for `web/` PRs** — catches deterministic anti-patterns
- **Use `/impeccable audit` and `/impeccable critique`** before merging room-renderer or dashboard PRs
- **Skip `/impeccable teach`** since `DESIGN.md` will already be mature
- **Skip Live Mode** (alpha as of mid-2026; revisit at Phase 2)

**Why defer:**
- At Phase 1 there's no UI to discipline — adding Impeccable to CI runs against an empty repo is symbolic, not useful
- Writing FollowRoom's own design memory FIRST protects its specific soul (former-agent intuition, lived persona perspective) from being anchored on Impeccable's templates
- Solo founder execution risk — every tool adds cognitive load; defer until value is concentrated
- Impeccable is still moving fast (28k stars, frequent releases); Phase 1.5 entry will be more stable

**Risk to monitor (Phase 1.5+):**
- "Anti-AI-slop monoculture" — products using Impeccable may converge on a similar tasteful aesthetic. FollowRoom's design soul must come from its own doctrine, not from Impeccable's defaults. Use it as lint, not as taste oracle.

### 9.9 Component Map (Patterns → Tech)

| Pattern | Tech component |
|---|---|
| Save Is Sacred | `app/api/upload/[type]/route.py` writes to Supabase Storage BEFORE any background job |
| Source Evidence Immutability | Postgres trigger on `events.raw_text` (per 8.1) |
| Never-Delete Doctrine | `is_deleted` / `deleted_at` on all user-data tables (per 8.1) |
| Vendor Agnostic | `backend/app/ai/dispatcher.py` + provider config |
| Truth With Receipts | `Fact.receipts: list[Receipt]` schema; mandatory non-empty |
| Truth ≠ Tone | Memory selection (DB query) separate from generation (Sonnet call); `instructor` structured output enforces schema |
| Recovery On Every Open | `backend/app/jobs/recovery_sweep.py` runs on every session-start trigger |
| The Quiet Witness | Dashboard UI copy + AI prompt templates enforce no-coaching language |
| Operator's Edit Is Canon | `user_stance` + `provenance` columns; bookkeeper agent (Phase 2+) never overwrites operator-canonical |

---

## 10. The Felt Experience (Per Phase, Operator's POV)

The product's trust position depends on how the operator FEELS using it. Each phase should produce a distinct, recognizable felt outcome.

### 10.1 Phase 1 — "The institution remembers what I forgot."

**Day-to-day scenario:**

> Tuesday morning. The agent finishes a viewing in East Coast with Sarah Tan and her husband. Walking back to the car, she records 90 seconds of voice notes about the conversation. By the time she's at the next viewing, FollowRoom has transcribed it, extracted that Sarah is leaning toward Marine Parade for parent proximity, that the husband is now open to $2.2M, and that they're hesitating until after bonus.
>
> Wednesday morning, the agent's phone shows a quiet card: *"You told Sarah you'd send floor plans for unit #14-22 by today. Here's the exact snippet."* She taps to share the floor plan PDF straight from her phone's Files app via the FollowRoom share sheet, picks Sarah's room, adds a one-line note (*"floor plan for the East Coast unit we discussed"*), marks it `for_review` — done in three taps. Sarah's phone gets a notification that a new artifact is in her room.
>
> Thursday, Sarah opens the room link from WhatsApp on her phone. The "What's pending for you" surface at the top shows the floor plan with the operator's note. She taps, scrolls the PDF inline, screenshots a detail for her husband. The agent's dashboard quietly updates: viewed.
>
> Saturday, before her meeting with the Lim family, the agent opens FollowRoom and reviews Lim's room: relationship summary, last three signals, what she promised, what's outstanding. 90 seconds of prep instead of scrolling through six weeks of WhatsApp.
>
> Monday afternoon, on the way to a viewing, the agent snaps a photo of a property's loft layout that wasn't in the original brochure, drops it into Lim's room from her camera with the note *"unexpected loft space — worth flagging for the storage question you raised."* The Lim family sees it within an hour.

**The felt quality:** calm, evidentiary, low-friction. The product is mostly invisible during the workday; it becomes visible at moments of natural reflection (start of day, before a meeting, end of week) and at moments of natural delivery (a document needs to land, the room is the channel). The room is *alive* — accumulating with the relationship.

### 10.2 Phase 2 — "Patterns surface from my own words."

**Day-to-day scenario:**

> Friday afternoon. The agent opens FollowRoom's weekly digest:
>
> > **This week, across your active clients:**
> > - Four clients mentioned affordability anxiety unprompted (Tan, Chen, Wong, Lim Couple). Possible positioning shift: lead with "what you can sustain" before "what you can afford."
> > - Two clients (Tan and Sarah Ong) are looking at the same Marine Parade area within a $200K range — possible mutual-interest introduction?
> > - Tan Family has been quiet for 11 days. Your pattern: quiet deals after price discussion re-engage at +14 days. Soft-touch on Monday?
>
> She marks one for follow-up, dismisses the others (with no friction), and feels seen by her own work.

**The felt quality:** invitational, gently provocative, never prescriptive. The product surfaces the agent's own patterns; the agent decides what they mean.

### 10.3 Phase 3 — "The institution traces threads no single conversation could see."

**Day-to-day scenario:**

> Monday morning. Agency principal opens FollowRoom's manager view:
>
> > **Team activity this week:**
> > - 12 deals at "viewing scheduled" stage across 4 agents. Common objection cluster: affordability + bonus timing (similar to Q4 last year).
> > - Sarah Chen's deal-close playbook from Q3 ("anchor on monthly comfort, not max affordability") shipped successfully on 3 deals last week. Want to share with Mei Lin and Raymond?
> > - 2 high-intent prospects (Tan Family, Lim Holdings) have stale follow-up across the team — neither has been touched in 7+ days. Suggest reassignment or escalation?
>
> The principal taps to share the playbook, taps to flag stale deals, gets a slack notification when Sarah Chen confirms the share.
>
> Meanwhile, each agent's individual experience (Phase 1 + 2 felt qualities) is unchanged. The Phase 3 institutional layer is purely additive — operators see only their own clients; the principal sees the aggregate.

**The felt quality:** the institution holds the topology. Operators hold relationships. Coordination cost drops near zero.

---

## 11. Risks and Traps (Pre-empted from LineOS Graveyard)

Each documented risk maps to a LineOS pattern that earned it through past failure.

### 11.1 Misattribution at scale — pre-empted by Axiom 10 (Zero Misattribution)

**Risk:** LLM-judged attribution at first-touch leads to wrong-client publishes; trust violated.
**Mitigation:** Architecture commits to four deterministic attribution channels (Section 5.6). LLM never decides attribution at commit time; only suggests in review queue.

### 11.2 Forwarded message metadata is structurally absent — pre-empted by deep WhatsApp research

**Risk:** PRD §13 mental model assumed forwarded messages carry sender attribution. They don't.
**Mitigation:** Shape X (typed identifier + push notification tap) is the operator's commit event. Documented in Section 5.3.

### 11.3 Audio loss (the foundational scar) — pre-empted by Patterns 16, 18, 22

**Risk:** Operator records a 30-min meeting; upload fails; audio is gone.
**Mitigation:** Save Is Sacred — file persisted to Supabase Storage BEFORE any background job runs. Never-Delete Doctrine — soft-delete defaults. Recovery On Every Open — startup sweep checks for stuck transcriptions, orphaned audio.

### 11.4 Silent degradation — pre-empted by Hivemind RT-2 finding

**Risk:** A bug or scoping rule silently filters facts from the rewrite prompt; operator never sees that something's hidden; the room is subtly wrong.
**Mitigation:** When facts are filtered (e.g., by visibility tier), the rewrite output explicitly notes *"3 facts were excluded for visibility (tap to review)."* Silent filtering is treated as a trust breach.

### 11.5 Tier 3 inferences leaking to client-facing — pre-empted by Axiom 6 + visibility view separation

**Risk:** AI extracts "wife is the blocker on timing"; this leaks into the client-facing room.
**Mitigation:** Two physical profile views (Section 6.2). Rewrite prompt receives `client_facing_profile` view that physically does not contain `internal-only` facts. Tier 3 cannot leak because the data isn't in the prompt.

### 11.6 Maintain bottleneck — pre-empted by Hivemind progressive capture pattern

**Risk:** Synchronous extraction on every event creates a write-path bottleneck; UX feels slow.
**Mitigation:** Three-tier write strategy — progressive (mid-event extraction on lightweight content), session-end batch (transcripts processed asynchronously), crash recovery (auto-retry on next session start).

### 11.7 Auto-memory becoming shadow canonical — pre-empted by Hivemind A4 finding

**Risk:** Browser's localStorage or Claude Code auto-memory grows unchecked; becomes the de-facto truth source; the Postgres KB withers.
**Mitigation:** Session-start protocol reconciles any local cache with Postgres canonical; local cache is treated as scratch pad, not source of truth.

### 11.8 Bridges-style false-positive insights — pre-empted by Pattern 14 + N-threshold rules

**Risk:** Cross-client insights surface too eagerly; operator feels surveilled.
**Mitigation:** Cross-client patterns require ≥3 client entries before surfacing. Phrased as invitations, never assertions. Operator can dismiss or mute pattern surfaces.

### 11.9 OpenClaw-style transport complexity — pre-empted by simple-transport choice

**Risk:** Trying to layer MCP-over-MCP for some clever federation gain; ends up with zombie processes and debugging nightmares.
**Mitigation:** Phase 1 uses direct HTTP REST between FastAPI backend and WhatsApp Cloud API + Anthropic + Supabase. Federation primitives (Phase 3 Hivemind) layer on top without nesting transports.

### 11.10 WhatsApp Business Account suspension — operational risk

**Risk:** Meta suspends the WABA number; all operators lose ingestion simultaneously.
**Mitigation strategies (Phase 1 → Phase 3):**
- Phase 1 (low scale): single WABA, strict ToS compliance discipline
- Phase 2 (50+ ops): multi-number strategy for redundancy
- Phase 3 (agencies): BSP-managed failover (e.g., 360dialog) for enterprise reliability

### 11.11 AI cost spikes — economic risk

**Risk:** Operators use 2-3× the median AI estimated; margins compress.
**Mitigations:**
- Aggressive prompt caching (locked: Anthropic 1-hour TTL)
- Haiku-first, escalate-to-Sonnet pattern (locked)
- Pricing tier mechanics — heavy users to higher tiers; usage-based overage as backstop
- Cheaper transcription provider option (Deepgram Nova-3) if Whisper budget hurts

### 11.12 Render reliability — infrastructure risk

**Risk:** Render had ~41 incidents in 90 days per 2026 research; an outage takes all operators down.
**Mitigations:**
- Robust retry / idempotency from Day 1
- Eventually migrate hot path (transcript processing) to Cloud Run or Modal at 1000+ scale
- Status page + transparent communication during incidents

### 11.13 File storage costs growing unchecked — economic risk

**Risk:** Operators drop high-resolution photos and large PDFs prolifically; Supabase Storage costs grow nonlinearly relative to AI cost.
**Mitigations:**
- Per-operator storage soft-cap with operator-visible meter (e.g., 10GB included; overage at $0.021/GB pass-through)
- Image compression at upload (target 1080p max; original retained only for premium tier)
- Lifecycle rule: archive (cold storage) files untouched for 12+ months unless operator pins
- Periodic dedup based on `content_hash` — if operator uploads same file to two clients, store once

### 11.14 Mobile file upload failure modes — UX risk

**Risk:** Large file upload over flaky 3G/4G timeouts; operator thinks file is uploaded, leaves the page, file isn't. Pattern 16 (Save Is Sacred) violation if not handled.
**Mitigations:**
- Resumable uploads (chunked, tus.io or Supabase Storage's native resumable protocol)
- Aggressive local cache before network (browser IndexedDB stash of file + metadata)
- Recovery sweep on session start (Pattern 22) detects unfinished uploads
- Clear UI feedback: "uploading…" → "uploaded" → "in client room" state transitions

### 11.15 Confidentiality of client-facing room URLs — privacy risk

**Risk:** Operator forwards a room link to a client via WhatsApp; client forwards to a friend; sensitive details leak.

**Locked mitigation: 3-mechanism stack, intentionally minimal.**

| Mechanism | Default | What it provides |
|---|---|---|
| **Word-phrase slug** (`followroom.app/r/forest-river-amber`) | Always | Cryptographically unguessable (~40 bits entropy from a 10k-word pool, 3 words = ~10^12 combinations); human-readable; premium-feeling. Room URLs are unlisted; robots.txt excludes; no link previews unless explicitly enabled. |
| **Optional 6-digit PIN** (per client) | Operator-opt-in | 6 digits (not 4) — still memorable, 100× more secure. Rate-limited at 5 failed attempts per 15 min per slug. Secure cookie persists 90 days for repeat visits. System suggests memorable PINs (pseudo-random, not 123456). One-tap "send PIN + link via WhatsApp" helper for the operator. |
| **Revoke + regenerate** | Always available | Operator kills current slug, generates new one. **24-hour grace screen on the old link**: instead of 404, shows *"This link has been replaced for security. Please ask <Operator> for the new link."* with one-tap "request new link" button. Operator gets a one-tap "send new link via WhatsApp" helper. |

**Honest framing surfaced in onboarding and in-app:**
> *"FollowRoom rooms protect against URL guessing and casual forwarding, and let you revoke compromised links instantly. For legally sensitive items (signed contracts, financial verification), use your brokerage's secure portal or DocuSign — FollowRoom is for relationship continuity, not secure document execution."*

**Deliberately NOT building** (over-engineering / security theater):
- IP rate-limiting / device fingerprinting
- SMS / magic-link auth
- Per-attachment view-only or watermarking (motivated leaks bypass via screenshot; promising more than we deliver erodes trust)
- One-time links (breaks the reference-library purpose)
- Anomaly detection

### 11.16 Client view tracking ethics — trust risk

**Risk:** Granular tracking ("client opened the PDF at 11:42pm Saturday for 2m14s on page 3") feels surveillance-y to client and creepy to operator. Erodes the Quiet Witness posture.

**Locked mitigation: default-aggregate + explicit-audit-drill model.**

**What operator sees by default (per attachment, per room):**
- *"Viewed"* (yes/no)
- *"Last seen — today / 3 days ago / 2 weeks ago"* (relative, not absolute timestamps)
- *"Acted"* (yes/no + action type — signed, paid, acknowledged, declined)
- *"Pending action overdue"* (boolean, surfaced as soft nudge)

**What operator can drill into** (must explicitly click *"Show timeline"*):
- Specific timestamps (date + time)
- Sequence of views and downloads
- Acted events with timestamps

**Architecturally never tracked:**
- IP address / device fingerprint / geographic location
- Time-on-page / scroll depth / interaction heatmaps
- Third-party analytics SDKs (already an SOUL principle)
- Cross-room behavioral aggregation
- Any cookies beyond the passcode session cookie

**Client-side transparency** (footer of every room):
> *"Your engagement with this room helps your advisor follow up at the right time. We track when you visit and when you act on items — nothing more. [Learn what's tracked]"*

The "Learn what's tracked" link goes to a plain-English page (no legalese) explaining exactly what's stored and how to request deletion (data export per operator-supplied request).

**Operator dashboard framing:**
- Surface: *"Sarah hasn't viewed the floor plan you sent 5 days ago"* (relative, actionable)
- Not surface: *"Sarah opened the floor plan at 11:42pm Saturday and spent 2 minutes 14 seconds on page 3"* (granular, surveillance-feeling)

The default respects the client's dignity; the audit view exists for rare compliance needs without polluting everyday operator UX.

---

## 12. Open Questions for Implementation Phase

These don't gate the Phase 1 build but will need answering as implementation proceeds.

### 12.1 Voice memo specifics

- **File formats supported:** target m4a, mp3, wav, ogg, opus (WhatsApp's default voice note format). Validate at upload.
- **Max length:** soft cap at 30 minutes; reject longer with friendly error suggesting transcript upload instead.
- **Transcription provider:** Phase 1 = Whisper API. Phase 2 evaluate Deepgram Nova-3 for cost.
- **Language detection:** Whisper auto-detects; FollowRoom UI surfaces detected language for operator to override if needed.

### 12.2 Pricing tier mechanics

- **Solo tier anchor:** $29/mo per PRD §22 baseline. Recommended consideration: $39/mo based on margin analysis (Section 3 of business-case discussion). Test both in early validation.
- **Pro tier price:** $59-99 range; specific anchor to be determined during Phase 2 build.
- **Agency tier:** per-seat $50-100; custom-quoted for first 5-10 agencies; standardized after.
- **Free trial:** 14 days, full Phase 1 features. Required to overcome the "compounding KB takes weeks to feel valuable" cold-start issue.
- **Annual discount:** 20% off for annual upfront; aligns with property agent income cycles (commission-heavy).

### 12.3 Cross-relationship insight UX details

- **Daily insight surfacing:** one card per day, dismissable, Pattern 8 (Gentle Recall).
- **Weekly digest:** Friday afternoon; richer, multi-pattern view.
- **Monthly per-client arc review:** triggered manually or quarterly; deeper look.
- **Anti-Goodhart drift detection:** Phase 2 Zettel adds this; Phase 1 manual operator-feedback loops.

### 12.4 Privacy / consent UX (Phase 2 Coexistence specifically)

- **Per-chat opt-in toggle** when enabling Coexistence — operator explicitly chooses which client chats sync to FollowRoom
- **Transparent UI** showing what's currently being ingested ("FollowRoom is syncing 12 of your 18 active client chats — manage")
- **Easy revoke** at chat level or globally
- **Customer-facing consent language** for operators to use with their clients: *"My follow-up tool helps me remember our conversations. Anything we discuss may be summarized for my reference. Let me know if you'd prefer not."*

### 12.5 Curation UX for Coexistence (Phase 2+)

- **Star-to-include model:** all messages enter events log; only starred ones promoted to formal KB
- **AI-auto-classify with operator approval:** AI suggests "important" / "skip"; operator approves in review queue
- **Per-chat tracking level:** operator sets "track all" / "track starred" / "don't track" per chat

Phase 2 design will pick the right model based on Phase 1 operator feedback.

### 12.6 Cold start onboarding flow specifics

- **Required `short_context` enforcement** at client creation — UI must prompt with examples and minimum 2-sentence requirement
- **Guided onboarding option:** *"Tell us 3 things you'd want to remember about Sarah"* — optional but encouraged
- **First-meeting transcript upload recommended in onboarding** — UI suggests "upload your most recent client meeting to seed the KB"
- **Empty-state handling:** dashboard's "no clients yet" view drives toward creating first client + uploading first transcript

### 12.7 Notification UX for Shape X

- **Push notification design:** *"1 pending forward → Sarah Tan? [Confirm] [Change] [Discard]"* with action buttons IN the notification (no app open required)
- **Notification fatigue mitigation:** session-lock pattern (one notification per forwarding burst, not per message)
- **Fallback when push fails:** event sits in dashboard "Pending" queue; dashboard prominently surfaces queue size

### 12.8 Backup / disaster recovery

- **Daily Supabase Postgres backups** (managed; included in Pro plan)
- **Storage redundancy:** Supabase Storage is S3-backed; sufficient
- **Cross-region replication:** Phase 3 consideration for agency tier reliability requirements
- **Export per operator:** operator can request full export of their data anytime (GDPR Article 20)

### 12.9 Mobile app trajectory

- **Phase 1:** mobile web (responsive Next.js); good enough for upload + dashboard touchpoints
- **Phase 2:** evaluate native iOS/Android shell wrapping mobile web (Capacitor, React Native)
- **Phase 3:** full native experience if agency demand justifies investment

### 12.10 Internationalization

- **Phase 1:** English only; Singapore-first launch market
- **Phase 2:** add Mandarin, Bahasa (large SEA property agent populations)
- **Phase 3:** additional languages based on agency demand

### 12.11 File handling specifics (Phase 1)

- **Supported file types Phase 1:** PDF, PNG/JPG/HEIC (auto-converted to JPG), MP4/MOV (transcoded for browser), DOCX/XLSX (preview only via Google Docs viewer; download primary), plain text. Link types: URL paste with OpenGraph preview fetch.
- **Max file size Phase 1:** 25 MB per upload. Larger gated to Pro tier (or chunked upload to S3 for Phase 2+).
- **Image compression policy:** automatic compression to 1080p max long edge on upload; original retained for first 30 days then archived to cold storage unless operator pins. Operator can override to keep original.
- **Versioning behavior:** uploading a file with the same `original_filename` to the same client prompts: "Replace as new version of [previous]?" Default = new version with `superseded_by` link. Old version retained per Pattern 18.
- **Inline preview support:** PDF (browser native), images (lightbox), text (rendered), DOCX/XLSX (Google Docs viewer iframe; falls back to download if blocked), MP4/MOV (browser video player).
- **OCR for images of documents:** automatic for image attachments; extracted text stored in `extracted_text` column for search; Pattern 9 receipts can cite OCR'd text.
- **Operator-controlled "view-only / watermark":** premium-tier flag on per-attachment basis; prevents download, adds operator/client identifier watermark.

### 12.12 Pending-action UX details

- **Default pending types** at Phase 1: `for_review`, `for_signature`, `for_consideration`, `for_payment`, `informational`. Operator can extend via free-text labels in Phase 2.
- **Acted-on inference:** by default, "viewed + downloaded" = inferred-acted; operator can require explicit confirmation toggle per attachment.
- **Notifications:** operator gets push when client acts; client gets push when new pending action lands (only if room push enabled — opt-in per client).
- **Stale pending nudges:** AI suggests follow-up replies after N days of un-acted (N defaults to 5 for `for_review`, 14 for `for_consideration`, 3 for `for_payment`); operator can tune per client.

### 12.13 Room rendering performance at scale per client

- **Pagination strategy:** rooms with 100+ attachments paginate by month (timeline view) or by 20 per page (list/grid views)
- **Edge caching:** room HTML cached at Vercel edge with `revalidateTag('room:'+slug)` invalidation on any new event / attachment / fact change
- **Search within room:** Phase 2 adds in-room search across attachments' `extracted_text` and operator notes

---

## 13. References

### LineOS source documents

- `Decades/PROJECT_DEV_SOUL.md` — LineOS constitution
- `Decades/docs/narrative/2026-05-04-lineos-genesis.md` — four-thread architecture genesis
- `Decades/docs/proposals/2026-05-04-lineos-naming.md` — naming amendment + 4Cs taxonomy
- `Decades/docs/patterns/decades-pattern-language.md` — the 23 patterns
- `Decades/docs/proposals/2026-04-08-hivemind-meta-layer-proposal.md` — Hivemind canonical
- `Decades/docs/proposals/2026-04-10-hivemind-experiential-outcome.md` — felt experience source
- `Decades/.claude/phase-plans/phase-memory-fleet-hivemind.md` — Hivemind phase plan
- `Decades/docs/proposals/2026-03-20-memory-upgrade-proposal.md` — PMM adoption
- `Decades/docs/proposals/2026-05-02-zettelkasten-fourth-pillar.md` — Zettel canonical
- `Decades/docs/proposals/2026-05-02-zettelkasten-substrate-amendment.md` — Zettel addressing model
- `Decades/docs/business/product-doctrine.md` — Decades thread doctrine
- `Decades/docs/proposals/2026-03-20-temporal-governance-methodology.md` — TG primitives

### FollowRoom internal

- `docs/prd/followroom_prd_v0_2_silent_whatsapp_ingestion.md` — PRD v0.2
- `PROJECT_DEV_SOUL.md` — FollowRoom constitution (adapted from Decades)
- `CLAUDE.md` — root golden rules
- `ROADMAP.md` — phase plan
- `docs/decisions/decision-ledger.md` — architectural decisions

### Brainstorm research (2026-05-16 → 2026-05-18)

- WhatsApp providers research (2026-05-16) — Meta Cloud API direct selected
- Next.js + Supabase patterns research (2026-05-16) — `@supabase/ssr` + PPR + middleware patterns
- AI extraction best practices research (2026-05-16) — Anthropic prompt caching as cost lever; instructor library; hybrid retrieval + LLM-as-judge
- FastAPI deployment research (2026-05-16) — Render over Railway on reliability
- WhatsApp forwarded message metadata research (2026-05-17) — definitive: no metadata at protocol level
- WhatsApp Business advanced metadata research (2026-05-17) — Coexistence + Groups API constraints
- Cloud API group chat verification (2026-05-17) — agencies-only at 100K/day tier; not viable for solo MVP
- LLM personal knowledgebase patterns research (2026-05-17) — Karpathy LLM Wiki + mem0 + Letta + Anthropic context engineering
- LineOS pillars + memory phase plans deep research (2026-05-18) — pattern inheritance map + forward-compatibility hooks

### External

- Andrej Karpathy, [LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- Anthropic, [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- mem0, [State of AI Agent Memory 2026](https://mem0.ai/blog/state-of-ai-agent-memory-2026)
- Letta, [Agent Memory](https://www.letta.com/blog/agent-memory)
- Meta, [WhatsApp Cloud API documentation](https://developers.facebook.com/docs/whatsapp/cloud-api/)

---

*This is the founding architectural artifact for FollowRoom. It anchors Phase 1 implementation, sets the forward-compatibility hooks for Phases 2-3, and positions FollowRoom as a LineOS application. Subsequent phase plans and implementation specs extend this design; deviations require constitutional amendment via the decision ledger.*

*Last updated: 2026-05-18 (initial draft)*
