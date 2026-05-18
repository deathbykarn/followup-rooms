# DESIGN.md — FollowRoom

**Phase 1 design doctrine. Authored before tooling adoption.**

This document captures the design intent that should govern every UI
decision in FollowRoom. It exists so that the visual identity of the
product is articulated in our own words, from the founder's lived-persona
perspective (former real estate agent), before any external tooling
(Impeccable, design system libraries, AI generation) shapes the aesthetic.

Per the architecture design doc §9.8, Impeccable tooling adoption is
deferred to Phase 1.5. Until then, this document is the source of truth.

---

## Brand voice

FollowRoom is the **quiet witness with receipts.** It watches client
relationships unfold, remembers what mattered, and surfaces evidence
when asked — without coaching, diagnosing, or befriending.

Tone:
- **Calm, never urgent** — the product holds time well; doesn't manufacture pressure
- **Specific, never generic** — Pattern 4 (Specificity is Identity); language about clients is particular, not abstract
- **Warm, never effusive** — empathy without overclaim; professional warmth, not chatbot enthusiasm
- **Honest, never overpromising** — confidence scores visible; receipts mandatory; we say "we noticed" not "you should"

Voice anti-patterns to avoid:
- Sales-coaching language ("close this deal!" "follow up now!")
- Empty enthusiasm ("Amazing!" "Great job!")
- Excessive emojis or punctuation (no 🚀 in product copy)
- Generic AI-SaaS phrases ("powered by AI" "leverage AI" "AI-driven insights")
- Surveillance-flavored framing ("we tracked" "we noticed they"); prefer "your record shows" or "evidence indicates"

---

## Audience

Two distinct audiences, two distinct design contexts:

### Operator (the property agent or sales operator)

- 30-55 years old, mobile-heavy, dense schedule, low tolerance for friction
- Already uses WhatsApp, voice memos, Otter/Fireflies for transcription
- Wants to appear organized, premium, thoughtful to clients
- Resistant to heavy CRMs; price-conscious but values polished tools
- Reads English natively; may operate in mixed-language environment (Mandarin / Malay client communications)

Dashboard design priorities:
- **Density over whitespace** — operators want to see a lot at a glance (Linear / Superhuman pattern)
- **Keyboard navigability** — power users will use ⌘K-style command palette in Phase 2
- **Mobile dashboard works on phone**, but operator's primary workflow may be desktop during deep review
- **Adaptive layout** — works fluently on phone for in-the-moment captures, on desktop for batch review

### Client (the operator's customer)

- 25-60 years old, opening links from WhatsApp on phones
- Doesn't know they're using "FollowRoom" — they see *"Sarah's room"* (operator-branded)
- Expects polished, premium experience; this is their advisor's professionalism rendered as a page
- Single-session purpose — they came to view something specific, not browse

Client-facing room design priorities:
- **Mobile-first, polished, premium-feeling**
- **Single scrollable surface** — no nested navigation
- **Instant load** — PPR rendering (design doc §9.2); edge caching; sub-second perceived load
- **No app required** — works in browser; no login (or one-time PIN if operator chose)
- **No FollowRoom branding intrusion** — subtle attribution; the operator's brand leads

---

## Anti-references

What FollowRoom should NOT look or feel like:

### Generic AI SaaS

- Purple gradient hero sections, "AI-powered" badges, hexagon iconography
- Animations on scroll, parallax marketing pages, sticky chat bubbles
- Dark mode by default (we are warm, not sterile)
- Big "Try it free" CTAs with countdown timers

### Heavy enterprise CRM

- Tabbed forms with 30 fields
- Dropdown-of-dropdowns navigation
- Configuration screens before content
- Loading spinners for everything

### Maximalist "design" SaaS

- Overuse of glassmorphism, neumorphism, brutalism trends
- Six fonts on one page
- Decorative emoji as content
- Mascots, characters, illustrations of generic happy diverse people

### Linear copies

- FollowRoom dashboard CAN borrow from Linear's density patterns, but it's
  not a project tracker. Avoid issue-board metaphors; we're a relationship-
  arc product.

### Notion clones

- Avoid the "everything is a block" feel; FollowRoom has specific surfaces
  for specific purposes, not infinite-canvas flexibility.

---

## Visual identity (initial)

Colors:
- **Primary palette: warm neutrals** — off-white background, dark slate text, subtle warm accent
- **Avoid: cool grays, pure white, vibrant brand colors that scream "tech"**
- One restrained accent color for actions and key signals (TBD during build)

Typography:
- **System fonts for dashboard** (San Francisco / Segoe UI / Inter) for performance + native feel
- **Serif heading for client-facing rooms** (premium feel; e.g., Source Serif Pro or similar) — distinguishes the room from the operator dashboard
- One font family per surface, two weights max

Spacing:
- Generous but not luxurious — dense enough for power users, breathable enough for clients
- Mobile: edge-to-edge with safe-area awareness
- Desktop: max-width containers (~896px for content, ~1200px for dashboards)

Components:
- shadcn/ui base; restrained customization
- Tremor deferred to Phase 2 (React 19 compat — see decision ledger)
- TanStack Table for dense data grids (client list, pending queue)
- Avoid: shadow-heavy floating cards, gradient buttons, animated loading skeletons that distract

---

## Anti-pattern checklist (Impeccable-inspired)

Run through this checklist before merging any UI PR. These come from
Impeccable's anti-slop catalog (referenced, not tooled, until Phase 1.5).

- [ ] No purple gradients anywhere
- [ ] No nested cards (card-within-card-within-card)
- [ ] No more than 2 typefaces on a single page
- [ ] No gradient headings (one solid color)
- [ ] Text contrast ≥ WCAG AA against background
- [ ] Touch targets ≥ 44×44px on mobile
- [ ] No more than 3 button styles in product (primary, secondary, tertiary/link)
- [ ] No decorative emoji in product copy (functional emoji in user content is fine)
- [ ] Loading states show meaningful progress, not vague spinners
- [ ] Empty states explain what comes next, not "no data found"
- [ ] Mobile layout works at 360px width minimum
- [ ] No content reflow on initial load (CLS = 0)

---

## Evolution

This doc is a living artifact. As FollowRoom's UI emerges:
- Update sections as patterns crystallize
- Add concrete examples (screenshots, before/afters) as they become available
- At Phase 1.5, when Impeccable tooling is adopted, this doc becomes the
  input to `/impeccable teach` for generating the tool's canonical
  `DESIGN.md` shape — but the soul stays here

---

*Founded 2026-05-18. Last updated: 2026-05-18.*
