# PRODUCT.md — FollowRoom

**What we are, what we aren't, who we serve.**

---

## What FollowRoom is

FollowRoom is **living relationship rooms** for relationship-driven sales
operators — initially Singapore property agents, expanding to insurance
advisors, wealth managers, and B2B consultants over time.

Internally, FollowRoom is a **compounding per-client knowledgebase**
that takes meeting transcripts, voice memos, forwarded WhatsApp messages,
and operator-dropped artifacts (PDFs, photos, links) and synthesizes them
into:

1. A **private relationship memory** the operator can search and review
2. A **polished client-facing room** the operator can share with clients
3. **Cross-relationship insights** that surface patterns across the operator's book of business

Architecturally, FollowRoom is a **LineOS application** — the substrate
for tending client Lines, sibling to Decades (which tends the operator's
own Line). See `docs/superpowers/specs/2026-05-18-followroom-architecture-design.md`.

---

## What FollowRoom is NOT

- **Not a CRM replacement** — we sit above CRMs; we don't replace
  pipeline management
- **Not a meeting transcription tool** — we ingest transcripts (from
  Otter / Fireflies / Granola / direct audio); we don't compete with
  transcription tools
- **Not a WhatsApp client** — the operator keeps using WhatsApp; we are
  selective ingestion + organized memory
- **Not a chatbot** — we never message the operator's customers; the
  WhatsApp endpoint is silent (or minimally conversational, per design
  doc §5.3 Shape X)
- **Not DocuSign** — for legally sensitive document execution, operators
  use their brokerage's secure portal; FollowRoom is for relationship
  continuity
- **Not Notion** — we are opinionated about workflow; we don't offer
  infinite flexibility
- **Not a marketing automation tool** — we do not blast messages,
  schedule campaigns, or run nurture sequences

---

## Three audiences, three contracts

### Operator (the buyer)

The relationship-driven sales operator. They pay for FollowRoom.

What we promise:
- Their conversations become memory without manual filing
- Follow-up timing is surfaced before things go stale
- Client-facing rooms are polished enough to make clients feel properly remembered
- Cross-relationship patterns reveal what they couldn't see deal-by-deal
- Their data is theirs — exportable, deletable, never sold

### Client (the end-user of the room)

The operator's customer. They never pay; they may not even know "FollowRoom"
exists — they see "Sarah Tan's room."

What we promise:
- The room is private (URL is unguessable; optional PIN for sensitive deals)
- View tracking is minimal (aggregate signals only; no granular surveillance)
- The information shown is what the operator approved — no AI-generated
  speculation about them
- Documents shared are organized and accessible without an account
- The experience feels premium, not generic

### Future agency (Phase 3)

Real estate brokerages and similar agencies. They will pay enterprise
prices in Phase 3.

What we'll promise:
- Multi-operator coordination without silo'ing client knowledge
- Manager visibility into team activity without violating operator-client privacy
- Shared artifact library (brokerage-approved templates, compliance forms)
- Audit trails for regulatory compliance

---

## Foundational principles (Quiet Witness posture)

FollowRoom maintains a particular epistemic posture, summarized in three
inherited Decades patterns:

1. **The Quiet Witness** (Pattern 2) — Watches, remembers, shows what
   it saw with evidence. Does NOT advise, diagnose, befriend, or coach.
2. **Truth With Receipts** (Pattern 9) — Every AI claim links back to
   verbatim source material. If we can't produce a receipt, we don't
   make the claim.
3. **Celebration Over Correction** (Pattern 12) — We surface patterns
   ("3 clients mentioned affordability") as discovery, not diagnosis
   ("you should change your pitch").

These patterns shape every product decision:
- Suggested replies are drafts, never sent automatically
- Cross-relationship insights are invitations, never assertions
- Tier 3 inferences (family dynamics, emotional state, decision-blocker
  speculation) NEVER appear in client-facing rooms
- Confidence scores are visible alongside AI-extracted facts
- Operators can mark any AI extraction as rejected; the rejection is
  canonical and persists across regenerations

---

## What success looks like

Phase 1 (Solo MVP) success:
- 10-20 paying solo property agents within 6 months of launch
- ≥70% weekly active rate among paying operators
- ≥50% of paying operators publish at least one room update per week
- ≥1 NPS-worthy testimonial per cohort

Phase 2 (Solo Pro) success:
- ≥30% of Phase 1 operators upgrade to Pro within 6 months of Phase 2 launch
- Cross-relationship insight features generate ≥1 insight-triggered action per operator per week

Phase 3 (Agency Enterprise) success:
- 5+ paying agency contracts within 12 months of Phase 3 launch
- Average agency contract ≥$30k ARR
- Agency NRR ≥110% (expansion via seat additions)

---

## Voice samples (use as reference for product copy)

**Welcome email:**
> Welcome to FollowRoom. Add your first client, upload your most recent
> meeting with them, and your first room takes shape in about 60 seconds.
> No setup ceremony. Your conversations are the documentation.

**Empty state (no clients yet):**
> Add your first client to start building their relationship room.

**Empty state (no events yet for a client):**
> Sarah's room is waiting for its first signal. Upload a meeting
> transcript, drop a document, or forward a WhatsApp message.

**Cross-relationship insight (good):**
> Four clients mentioned affordability anxiety this week (Tan, Chen,
> Wong, Lim). Worth knowing.

**Cross-relationship insight (avoid):**
> ❌ "Your pitch isn't landing — 4 clients pushed back on price.
> Consider revising your approach."

**Pending action surface for client:**
> Sarah, your advisor shared the floor plan for unit #14-22 for your
> review. Tap to view.

**Revoke link grace screen:**
> This link has been replaced for security. Please ask Sarah Tan for
> the new link.

---

## Evolution

This doc evolves with the product. As we learn:
- What language operators use to describe FollowRoom unprompted (their
  framing beats ours)
- Which patterns from Decades / LineOS map cleanly vs need adaptation
- What competitor products emerge in the space and how we differentiate
- What we'd kill if we had to (constraint clarifies positioning)

Update this doc when those learnings crystallize.

---

*Founded 2026-05-18. Last updated: 2026-05-18.*
