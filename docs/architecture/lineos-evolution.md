# LineOS Evolution Narrative — Three Stages of FollowRoom's Substrate Integration

**Purpose:** Narrative arc for how FollowRoom matures from a standalone per-operator product (Stage 1) into a federated cross-vector memory layer (Stage 2) into a full LineOS-substrate participant (Stage 3). Written experientially — what each stage looks and feels like to the operator — rather than purely architecturally.

**Companion to:** `PROJECT_DEV_SOUL.md` (constitution), `docs/superpowers/specs/2026-05-18-followroom-architecture-design.md` (architecture; supersedes that doc's §3 ordering — see footnote at the end), `ROADMAP.md` (when each stage lands).

---

## The framing: why Karpathy is the right compression for Stage 1

LineOS has three substrate layers we care about for FollowRoom's evolution:

- **Decades** — the operator's own Line tender (receipts, attribution, source-immutability discipline)
- **Hivemind** — cross-Line, cross-vector memory (patterns surfacing across the operator's whole book, eventually across agencies)
- **Zettel** — the link-graph layer (knowledge structured as addressable nodes with traversable edges)

A fully-substrate-integrated FollowRoom would be a thin client over all three: every fact is a Zettel node, every cross-client pattern comes from Hivemind, every receipt traces through Decades. But shipping that on day one would mean building (or depending on) three substrates in parallel before the product gets to its first operator.

**The Karpathy LLM Wiki pattern is the compression that lets us defer all three.** Each operator gets one wiki per client (the "room"). Within that wiki, we already have:

- **Zettel-flavored structure** — facts have types, events are typed, attribution is structured. The link-graph is implicit (facts reference events via `source_event_ids`; events reference clients; attachments reference both). It's a graph, just not a *queryable* graph yet.
- **Hivemind-flavored memory** — the wiki IS the operator's externalized memory for that relationship. It's not federated across clients yet, but the *primitive of remembering* is in place.
- **Decades-flavored receipts** — every fact has source_spans pointing to verbatim event text. The receipt chain is shorter (single-relationship) and we don't yet trace receipts through the operator's own Line, but the discipline is there.

This is the "condensed combo." One product, one operator, one client at a time. Zettel + Hivemind + Decades patterns compressed into a single per-client wiki that's easy to extract into, easy to render, easy to reason about. Quality of relationship memory now; substrate integration later, when scale or product surface demands it.

The three stages below are about progressively decompressing this — exchanging the compressed local form for richer, more capable substrate participation.

---

## Stage 1 — FollowRoom Alone (today)

**Operator experience:** *I open my dashboard. I see my clients listed. I click Sarah. I see her room — what we've discussed, what she wants, what's next. I add a note. The room updates. I forward a message from Wendy on WhatsApp. It appears in my pending tray. I confirm it. Wendy's room updates. Each client is a self-contained world I tend individually.*

**What's true at Stage 1:**

- One operator, their book of clients, their wikis
- The LLM wiki per client compresses Zettel structure + Hivemind memory + Decades receipts into a single per-relationship surface
- Cross-client visibility exists only as the client list — no automatic pattern-spotting across clients
- The operator does the synthesis across clients in their own head
- Substrates are conceptual — none are integrated; nothing depends on Decades, Hivemind, or Zettel running externally

**What this is good for:** validating that the per-client wiki is itself valuable. If the rooms aren't worth opening for one client at a time, no amount of substrate integration saves the product. Stage 1 is the *test of the relationship memory primitive*. If operators love it for the single-client experience, then federation and link-graph integration have something to amplify.

**What this is bad for:** anything that requires seeing patterns across clients. *"Three of my clients are weighing Marine Parade — what should I learn from that cluster?"* — operator has to notice it. *"My closing rate is higher when I send floor plans within 24 hours"* — operator has to track that. *"My energy was low last Tuesday; I should not commit to a viewing tomorrow"* — operator has no way to know FollowRoom should adjust.

**Where we are today (2026-05-19):** Stage 1 is largely shipped. Plans 1-4 deliver the per-client wiki with manual notes, transcript/voice upload, WhatsApp forwarding ingestion, fact extraction with provenance, profile regeneration in two views, operator-curated overrides. Plan 5 (file drop) and Plan 6 (client-facing rooms) complete Stage 1's surface area. Plans 4.5 and 4.2 are polish + design for what we have.

**What's NOT in Stage 1 by design:** no cross-client extraction, no agency tier, no autonomous agent writes, no Decades-Line integration, no shared dashboard with other LineOS apps. All deliberately deferred.

---

## Stage 2 — FollowRoom + Hivemind

**Operator experience:** *I sit down with my coffee. The dashboard greets me with three observations across my whole book: "Sarah, Wendy, and David are all waiting on your move this week — Sarah for her shortlist, Wendy for the OTP, David for the rental projections. Of those, Sarah's been quiet longest." Then: "Three buyer-side clients are weighing Marine Parade — David's been there too for the investment angle. There's a comparative read here you might use in any of those conversations." Below: "Your closing rate is higher when you send floor plans within 24 hours. Three clients are at day 2-3."*

*None of these are alarms. They're noticings. I can act on them, defer them, or dismiss them. The cross-vector layer is doing what I would do if I had the time to manually re-read all 32 client rooms every morning.*

**What changes at Stage 2:**

- FollowRoom's per-client wikis become *contributors* to a cross-vector memory layer (Hivemind)
- Vectors include: client preferences, relationship stage, deal patterns, behavioral signals, market signals, operator workflow patterns
- Cross-client pattern surfacing becomes automatic — the dashboard does the looking
- The `agency_visible` visibility tier (sitting unused in our schema since Plan 1) starts being meaningful
- First version of agency tier: a single operator's full book of business with cross-relationship insights
- Later: anonymized cross-operator patterns within an agency

**What stays the same:**

- The per-client room is unchanged. Sarah's room still feels like Sarah's room.
- All Stage 1 ingestion paths still work — manual notes, transcripts, voice memos, WhatsApp forwards
- Operator authority is unchanged — Hivemind surfaces patterns but never auto-publishes anything to client-facing rooms
- Receipts still trace to verbatim source — the Hivemind insights are themselves grounded in fact-level evidence

**What's new infrastructurally:**

- A read-side Hivemind query interface: FollowRoom can ASK Hivemind "show me patterns in my book"
- A write-side contribution: FollowRoom's fact extractions get tagged with vector metadata that Hivemind can index
- Cross-relationship insights surface in a new dashboard surface (probably a "Today" or "Across your book" panel)
- Agency tier requires multi-operator visibility scoping (we already have per-operator RLS; agency tier adds a layer above)

**What this is good for:** the operator stops being the bottleneck on cross-client synthesis. Insights they would have noticed *eventually* surface *now*, when they can act on them. The product starts feeling like a strategic layer, not just a memory store.

**What this is bad for:** privacy and noise. Cross-vector patterns at agency scale invite *"why does my colleague's KB inform my dashboard?"* questions; consent and visibility design becomes complex. False-positive pattern noise erodes trust faster than any other failure mode — Hivemind insights MUST be conservative.

**Trigger conditions for shipping Stage 2:**

- Solo operator approaching ~30 clients (where one-at-a-time browsing genuinely breaks down)
- OR first agency-tier customer asking for shared visibility
- OR Decades or other LineOS app stands up a Hivemind primitive we can consume

**Prerequisites we already have from Plan 1:**

- Three-tier visibility (`operator_only` / `client_facing_safe` / `agency_visible`) — third tier is the explicit Hivemind hook
- `attributions` table with `agent_id` field — per-principal write attribution, ready for Hivemind-initiated writes
- `visibility_promotions` log — every visibility transition is recorded, the seed of cross-tier accountability
- `AgentDispatcher` with `LogicalRole` abstraction — Hivemind's pattern-surfacing agent is just another logical role in our dispatcher

---

## Stage 3 — FollowRoom + Zettel

**Operator experience:** *I'm sketching a personal goal in Decades — "deepen my real-estate practice." On the same page, Decades surfaces: "Your FollowRoom shows Sarah, David, and three others are at decision points this month. They'd be a natural cohort for a one-evening 'where you are' touchpoint." It even drafts the WhatsApp message and tags it for my review.*

*Later, in FollowRoom, I open Wendy's room. At the bottom, FollowRoom says: "Your Decades-Line shows you have a long block tomorrow afternoon. Wendy's second viewer is asking for a callback before EOD tomorrow — fits well." It's not nagging. It's noticing. My systems work together because they share the same memory substrate.*

*The link-graph integration also means I can ASK questions that cross apps. "What happened around the time I bought the Tampines unit for David?" — Decades shows my own state at that time, FollowRoom shows what we discussed, the calendar shows what else I was doing. The answer surfaces from the graph, not from one app.*

**What changes at Stage 3:**

- FollowRoom's clients, facts, events, rooms, and attachments become first-class Zettel nodes with stable IDs
- Other LineOS apps can reference these nodes (Decades surfacing FollowRoom data on the operator's own Line; calendar tools linking events to client rooms; future apps composing in ways we can't predict)
- Conversely, FollowRoom can reference Zettel nodes from other apps (operator's own Line state from Decades, calendar slots, prior projects)
- Cross-app behaviors become possible without bilateral integration — both apps just speak Zettel
- Compositional surfaces emerge (the Decades + FollowRoom + Calendar suggestion in the experience above)

**What stays the same:**

- Per-client rooms are still per-client rooms. Sarah's room still feels like Sarah's room.
- Hivemind insights still surface as before (Stage 2 builds on, doesn't replace)
- All ingestion paths still work
- Operator authority still gates client-facing publishes
- Receipts still trace to verbatim source

**What's new infrastructurally:**

- Stable Zettel node IDs for our domain entities (we already have UUIDs; the question is whether to expose them in a substrate-compatible URN scheme)
- A Zettel-protocol read/write interface (probably HTTP + GraphQL or similar substrate-defined contract)
- Inbound queries from other LineOS apps need authentication + per-operator RLS at the substrate boundary
- Outbound queries to other LineOS apps need a discovery mechanism + capability declarations

**What this is good for:** compositional intelligence across the operator's whole working life. FollowRoom stops being a self-contained product and starts being a *participant* in a larger memory ecosystem. Apps that don't exist yet can reference our data; we can reference theirs. The product gets more capable over time without us building everything.

**What this is bad for:** dependency on substrate maturity. The substrate has to be stable, fast, and well-governed before Stage 3 is safe. A flaky Zettel layer would break apps in correlated ways. Temporal governance for cross-app writes becomes essential.

**Trigger conditions:**

- Decades (or another LineOS app) standing up a usable Zettel primitive with enough adoption that integration is high-leverage
- AND FollowRoom is mature enough internally that the substrate boundary is a stable seam
- AND temporal governance (`TG-lite`) for cross-app writes is designed (probably its own plan; see "Temporal Governance" below)

**Prerequisites we already have from Plan 1:**

- All domain entities have UUIDs (`clients.id`, `events.id`, `facts.id`, `room_attachments.id`, `pending_forwards.id`, `ingestion_jobs.id`)
- Single `store()` write path — substrate-bridging logic has exactly one place to live
- Source span structure on facts — every claim is grounded in a specific event, which translates cleanly into Zettel edges

---

## Temporal Governance — the cross-cutting requirement

When Stage 2 (Hivemind agents writing back to FollowRoom) and especially Stage 3 (cross-app writes) ship, *who* and *when* an agent is allowed to mutate state becomes a load-bearing question. Today, all writes are operator-initiated (manual notes, confirms, regenerate clicks). The Plan 1 schema records *who* wrote each row via `attributions.agent_id`, but there's no enforcement layer that decides whether a given agent SHOULD have written it.

**Temporal Governance ("TG-lite" per design doc §6.x)** is the layer that adds this. It would extend our existing `visibility_promotions` log to cover all agent-initiated writes — recording not just visibility transitions but every mutation attempted by a non-operator agent, plus the policy decision (allowed / blocked / queued for operator review).

When does TG need to ship? Whenever the first agent writes autonomously. Candidates:

- Plan 7 suggested-reply, if we let it auto-promote draft replies (probably not — operator-approval gates)
- Plan ~8-10 Hivemind, when cross-vector insights flow back as facts or annotations
- Plan ~11+ Zettel, when other LineOS apps write into FollowRoom via the substrate boundary

The plan for TG should probably ship just *before* the first autonomous-write feature, so the governance is in place by the time the policy questions become real.

---

## Mapping to the roadmap

The execution plans correspond to substrate stages roughly as follows:

| Stage | Plans | What it delivers |
|-------|-------|------------------|
| **Stage 1 — FollowRoom Alone** | Plans 1, 2, 3, 4, 4.2, 4.5, 5, 6 | Per-client LLM wikis with full ingestion + client-facing rooms |
| **Stage 2 — FollowRoom + Hivemind** | Plans ~7, 8, 9 | Cross-client insights, agency tier, multi-operator visibility |
| **Stage 3 — FollowRoom + Zettel** | Plans ~10+ | Substrate-level integration with LineOS link-graph |
| **Temporal Governance** | Cross-cuts — own plan probably between Stage 2 and Stage 3 | Enforcement layer for agent writes |

The ROADMAP `Execution plans (chronological)` table reflects this mapping. Specific plan numbering may shift as we sequence — what's stable is the stage progression and the trigger conditions for each.

---

## Open questions per stage

### Stage 1 (now → near-term)

- After Plan 6 (client-facing rooms ship), what's the test that tells us Stage 1's wiki primitive is genuinely valuable? Time-on-room? Number of attachments per client over 90 days? Operator retention?
- How much Stage 2 plumbing do we bake into Plan 6/7 to make Stage 2 trivially additive vs. waiting and doing it cleanly later?

### Stage 2 (when first triggered)

- How does Hivemind avoid surfacing false positives? Confidence threshold + operator-can-mute mechanics?
- Agency tier: explicit operator opt-in per cross-visibility relationship, or default-opt-in within an agency entity?
- What's the read/write contract with Hivemind — embedded library, separate service, or both?

### Stage 3 (when substrate matures)

- Zettel ID scheme: opaque UUIDs vs. URNs vs. content-addressed hashes?
- Cross-app read auth: operator-as-principal everywhere, or per-app capability tokens?
- Backward compatibility: when Decades or another app changes its node shape, what's the graceful-degradation story for FollowRoom?

### Temporal Governance (cross-stage)

- Block vs. queue-for-review vs. allow-with-receipt: which is the default policy for an unrecognized agent write?
- How does the operator audit / replay agent writes? Same UI as the existing facts review queue, or separate?

---

## Supersedes note on the design doc

`docs/superpowers/specs/2026-05-18-followroom-architecture-design.md` §3 ("Three-Phase Layering") ordered the phases as Karpathy (Phase 1) → Zettel (Phase 2) → Hivemind (Phase 3). This narrative document refines that ordering to Karpathy (Stage 1) → Hivemind (Stage 2) → Zettel (Stage 3).

**Rationale for the flip:**

- Hivemind delivers higher operator leverage earlier — cross-vector insights are valuable at solo-operator scale, not just at agency scale
- Zettel substrate integration depends on substrate maturity outside our control (other LineOS apps need to be standing); Hivemind can be built as a FollowRoom-native capability that LATER consumes external Zettel when it lands
- The design doc's ordering treated Hivemind primarily as "the agency tier"; this narrative recognizes it as also "the cross-vector layer for solo operators" — same capability, different scale

The design doc §3 should be updated to point at this narrative. (Tracked as a follow-up; not in this PR's scope.)
