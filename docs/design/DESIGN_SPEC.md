# DESIGN_SPEC.md — Client-Facing Room Visual Language

**Companion to:** `DESIGN.md` (brand voice + audience), `docs/superpowers/specs/2026-05-18-followroom-architecture-design.md` §6.8 (Room as Active Surface) + §11.15-16 (URL confidentiality + view tracking ethics), and the three mockups in `docs/design/mockups/`.

**Purpose:** translate FollowRoom's brand voice into specific visual decisions for the client-facing room surface. This document is what lets us work backwards from the mockups into Plan 6's Next.js components.

---

## The four emphases

Every design decision below ladders up to one of four identity-defining choices:

1. **Receipts woven into prose, not bulleted as data.** The room reads like a letter from someone who paid attention, not a CRM extract.
2. **Empty-state grace.** A sparse first-meeting room reads as *"we've just started — here's what's already clear"*, not *"there isn't enough here yet."*
3. **Calm restraint at high stakes.** When deals are in motion, the room does NOT scream. No badges, no alerts, no countdown timers. Visual restraint when stakes are highest is the brand statement.
4. **Operator voice ≠ extracted memory.** Things the operator wrote (their words, their tone) render visibly differently from things synthesized from facts. Without this distinction, the product looks like an AI dump.

---

## Typography

**Headings — serif** (`Newsreader`, Google Fonts).
Warm, contemporary serif. Not as classical as Georgia, not as cold as a grotesque. Reads as "thoughtfully edited" rather than "AI-generated."

- Display (room title): 32-40px, weight 400, tracking -0.01em
- Section heading: 20-24px, weight 500, tracking -0.005em
- Operator name (header): 18px, weight 500

**Body — sans** (`Inter`, Google Fonts).
Clean, neutral, widely used. No SaaS connotation; the workhorse.

- Body prose: 17px, weight 400, line-height 1.6
- Captions / source attributions: 13-14px, weight 400, color secondary
- Action labels: 14px, weight 500, tracking 0

**Deliberately avoided:**
- `system-ui` defaults everywhere (looks unfinished)
- Heading sans-serif (too SaaS-y for this context)
- Loud display fonts (Playfair, Cormorant — too wedding-website)

---

## Color palette

Warm, never sterile. The DESIGN.md frozen line: *warm, not dark by default.*

| Token | Hex | Use |
|-------|-----|-----|
| `bg-page` | `#FBFAF6` | Page background — warm white, slight cream |
| `bg-card` | `#FFFFFF` | Card / panel surfaces |
| `bg-muted` | `#F5F2EB` | Subtle nested surface (e.g., embedded note) |
| `text-primary` | `#1A1815` | Headings, body — warm near-black |
| `text-secondary` | `#5C574E` | Source attributions, captions — warm gray |
| `text-muted` | `#9B9489` | Meta info, view counts — warm light gray |
| `border-subtle` | `#E8E3D9` | Card borders, dividers — warm cream-gray |
| `accent-gold` | `#9B7B3B` | Section accents, operator brand line — warm gold |
| `accent-deep` | `#1F4F4A` | Action buttons, key links — deep teal |
| `attention-warm` | `#9B5B3B` | "Needs attention" (used sparingly) — warm rust, NEVER red |

**Deliberately avoided:**
- Pure neutrals (`#FFFFFF` page bg, `#000000` text, `#808080` gray) — feels sterile
- Startup blue (`#3B82F6`, `#2563EB`) — generic SaaS
- Bright red for alerts — anxiety pattern, doesn't fit "calm never urgent"
- Purple gradients, hot pink, neon — generic AI-SaaS visual identity

---

## Layout

**Single scrollable surface.** No tabs, no nested navigation, no sidebar. Information appears in importance order, top to bottom.

**Mobile-first.** The default mental model is: client opens link from WhatsApp on their phone, scrolls once. Desktop is a polished side effect.

- Mobile: full-width container, 24px horizontal padding
- Tablet/desktop: max-width 640px, centered (single-column always — no two-column on wide screens; that's a dashboard pattern, not a letter pattern)
- Section vertical rhythm: 56-72px between major sections
- Within-section spacing: 16-24px between elements
- Generous line-height for prose (1.6) — designed for one-thumb scrolling without strain

---

## Component patterns

### Operator brand header

Always at the top. Operator's name and short context lead; FollowRoom is silent here. Establishes whose room this is.

```
[Avatar circle, operator initials or photo, 40px]
Khaniff Lau
Your advisor for Marine Parade and East Coast
```

Soft horizontal hairline below (1px `border-subtle`). No FollowRoom logo, no "powered by" up here.

### Room title

Below the operator header. Client's perspective.

```
Sarah's room
[serif, 36px, weight 400, color primary]
[short subtitle in body sans, secondary color]
```

### Operator note (curated, in operator's voice)

This is what the operator WROTE. Visually distinct from extracted memory.

- Subtle left border (`accent-gold`, 2px)
- Background `bg-muted` (slight cream nest)
- Body in body sans, slightly larger leading (1.7)
- No operator avatar inline (the brand header sufficient)
- Italic only for genuinely italic phrases, never for the entire note

### Receipt thread (extracted memory in prose)

What FollowRoom learned, written as conversational sentences with source attribution. NOT bullets.

```
You mentioned wanting a 3-bedroom unit close to your parents in Marine Parade,
with a firm budget ceiling of $1.8M.
                                  ↑ inline link: hover shows "from your conversation on 14 May"
```

Implementation: each source-grounded claim is wrapped in a styled span/`<a>` that on hover shows the source ("from your conversation on Tuesday"). On mobile, source can be expanded via tap. The receipt is conversational, not technical (no confidence percentages on the client surface).

### Pending action card

Calm. No badges, no red, no countdown.

```
[Small icon, gold]   Floor plan to review
                     Sent yesterday · by Friday
                     [single subtle link: "Open"]
```

Distinguished from non-action items by a single thin gold left border + tiny icon. The "by Friday" is in muted text, not loud.

### Document/attachment row

Minimal. Filename, mime icon (subtle), date added. No "Download" badges; click-anywhere on the row.

```
[icon] Floor plan — Marine Parade Central #14-22
        Added 12 May
```

### Memory section (synthesized facts)

Where the receipt thread becomes a paragraph. Different visual treatment from operator notes — no nested card, just structured paragraphs under a section heading.

```
What your record shows
────────────────────
Budget and timeline are aligned: $1.8M ceiling, ideally moving in by Q3.
Three locations under consideration, with Marine Parade leading for parent
proximity. Your husband's preference for slower decision-making is noted —
no rush from our side.
```

The third sentence is interesting: it surfaces a sensitive fact (`spouse_family_factor` + `emotional_hesitation`) BUT in a tactful rewrite — *not* as raw operator-only intel. This is the "tactful rewrite at publish, not at ingestion" principle made visible. In the internal profile, the same fact would read: "Husband prefers slower decisions; potential blocker on timing." The client-facing rewrite acknowledges the dynamic gracefully without surveillance flavor.

### Footer

```
Tended by Khaniff Lau
[tiny FollowRoom mark, secondary text size, muted color]
```

Operator first, FollowRoom subtle attribution. No "Built with ❤️" or rocket emojis.

---

## State patterns

### Empty / sparse (scenario 1: discovery)

The room MUST feel intentional when there's little data, not impoverished.

- Lead with the operator's note ("Here's what stood out from our conversation today")
- Make 4-5 facts feel sufficient by spacing them generously
- End with "I'll add more as we go" — signal that this is a starting point, not the whole story
- NO "no documents yet" empty placeholders — just omit the section entirely until it's relevant

### Active / busy (scenario 2: negotiation)

Lots happening. Restraint is harder and more important here.

- Open with operator's "here's where we are this week" note
- Pending actions in a single grouped section, with calm visual treatment
- Comparable data as a simple unstyled table (no zebra stripes, no chart icons, no animation)
- "Next room update Friday" mentioned in passing in the operator note — sets expectation without creating anxiety
- Status indicators in muted gold/teal, never red/orange/green badges

### Mature / rich (scenario 3: feature showcase)

Maximum richness without sensory overload.

- Operator note is longer (3-4 paragraphs) — sets relationship continuity
- Memory section visibly synthesized from many sources — feels like the room has *grown*
- Document library appears as an organized list, not a grid of cards
- Family member context (spouse Mei Lin) referenced naturally in operator's prose, not in a separate "stakeholders" panel
- Subtle view tracking aggregate at the bottom ("3 viewings recorded last week") — informative, not surveilling
- WhatsApp send-helper appears once, on the most relevant item

---

## What's deliberately invisible

These are present in the data model but NEVER rendered on the client surface:

- Confidence scores (clients don't need to know the model was 87% sure)
- Internal fact types like `spouse_family_factor`, `emotional_hesitation`, `decision_blocker` — tactfully rewritten or omitted
- Operator's discard/reject history (clients don't see "your agent rejected this fact")
- Internal review queue (the operator's curation apparatus is not part of the client experience)
- Raw view-tracking timestamps ("opened at 3:47pm on Tuesday")
- Source span literal text (the operator's review surface shows verbatim quotes; client room shows them tactfully reframed)

The boundary between internal and client-facing is a structural promise from PRD §1.2 frozen constraint #3. Every Plan 6 component must honor this.

---

## Anti-patterns demonstrated (look for their absence)

- "AI-powered" badges, sparkle ✨ icons, robot iconography
- Purple gradients, hot pink accents, neon
- "URGENT" alerts, red badges, countdown timers
- Chatbot bubbles, "Ask AI" prompts, suggested-message inline composers (the operator drafts in dashboard, sends from their own WhatsApp)
- "Insights" panels with bullet-point summaries of obvious facts
- Engagement-bait language ("Don't miss this!" "Act fast!")
- Multiple CTAs competing for attention
- Dark mode default

---

## Translating to Plan 6 React components

Suggested component decomposition based on the mockups:

```
<Room>
  <OperatorBrandHeader operator={operator} />
  <RoomTitle clientName={...} subtitle={...} />
  <OperatorNote content={...} /> {/* the curated letter */}
  <PendingActionList items={...} /> {/* gold-bordered cards, omit if empty */}
  <MemoryParagraph blocks={...} /> {/* receipt thread */}
  <DocumentList docs={...} /> {/* omit if empty */}
  <OfferTable offers={...} /> {/* only for scenario-2 style */}
  <ComparableTable rows={...} /> {/* only for scenario-2 style */}
  <ViewTrackingAggregate stats={...} /> {/* scenario-3 only, very subtle */}
  <Footer operator={...} />
</Room>
```

Each component renders nothing (returns `null`) if its data is empty. The room layout is a composition of optional sections, not a fixed template.

For typography: use CSS variables defined at the root that map to the color tokens above. Tailwind extends the theme with these tokens; component styling uses `text-primary`, `bg-page`, etc., not raw hex.

For the receipt-thread component: take an array of `{text, source: {label, date}}` blocks and render them with inline `<a>` elements styled for the hover behavior described above.

---

## Open questions for the operator preview surface

Outside the scope of these three mockups (which are client-facing) but worth noting for Plan 6:

- How does the operator preview a room before publishing? Same layout, different chrome (an "Edit" / "Publish" bar)?
- How does the operator approve a room update? Diff view? Side-by-side?
- What does "revoke + grace screen" look like to a client who tries to access a revoked link? (Per §11.15)

These are Plan 6 concerns. The three mockups in this folder demonstrate the *client* experience exclusively.
