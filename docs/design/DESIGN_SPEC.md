# DESIGN_SPEC.md — FollowRoom Visual Language

**Companion to:** `DESIGN.md` (brand voice + audience), `docs/superpowers/specs/2026-05-18-followroom-architecture-design.md` §6.8 (Room as Active Surface) + §11.15-16 (URL confidentiality + view tracking ethics), and the mockups in `docs/design/mockups/`.

**Purpose:** translate FollowRoom's brand voice into specific visual decisions for both surfaces — the client-facing room AND the operator dashboard. This document is what lets us work backwards from the mockups into Next.js components (Plan 6 for client rooms; Plans 5/7/8 for dashboard evolution).

**Two surfaces, shared tokens, different density:**

- **Client-facing room** (mockups 01-03) — letter-like, single-session, mobile-first, "calm never urgent." Generous spacing.
- **Operator dashboard** (mockup 04) — power-user workspace, density over whitespace, Linear/Superhuman pattern, command-palette ready. Compact spacing.

Both surfaces use the **same color tokens and typography** below. They diverge in *layout density* and *information architecture*, not in visual identity.

---

## The four emphases

Every design decision below ladders up to one of four identity-defining choices:

1. **A letter, not a CRM extract.** The client room reads like warm prose from someone who paid attention — never bulleted data fields. *(Verbatim source quotes — "receipts" — are an operator-side trust tool, not shown on the client surface; see Settled patterns → Receipts are operator-only.)*
2. **Empty-state grace.** A sparse first-meeting room reads as *"we've just started — here's what's already clear"*, not *"there isn't enough here yet."*
3. **Calm restraint at high stakes.** When deals are in motion, the room does NOT scream. No badges, no alerts, no countdown timers. Visual restraint when stakes are highest is the brand statement.
4. **Operator voice ≠ extracted memory.** Things the operator wrote (their words, their tone) render visibly differently from things synthesized from facts. Without this distinction, the product looks like an AI dump.

---

## Foundational principle — fully adaptive to device size

Both surfaces are **fluid, not fixed-with-breakpoints.** Every element — type, spacing, grids, panels — scales *continuously* across the full device range (≈320px phone → tablet → wide desktop), not in one or two snaps. A client opens the link from WhatsApp on a phone; an operator may batch-review on a laptop and capture on a phone an hour later. The layout must feel deliberately composed at *every* width — never "the desktop design, shrunk."

This is a hard rule, co-equal with the four emphases above: **if a new element doesn't adapt fluidly, it isn't done.** Concretely (techniques in Layout → Responsive adaptation):

- **Fluid type** via `clamp()` — sizes scale with viewport, no step-jumps.
- **Fluid spacing** — section rhythm and padding scale, not fixed px.
- **Fluid grids** — anchor cells, dashboard panels, stats, rooms index reflow continuously (`auto-fit` / `minmax`, or container queries), not at a single cutoff.
- **Max-width is a readability cap, not the layout** — 640px (room) / 960px (dashboard) bound line length; within them, everything is fluid.
- **Tested across the range** — 320 / 375 / tablet / wide, not just "phone vs. not-phone."

---

## Settled patterns (2026-05-25 — post-redesign + red-team)

This section is the **current source of truth** for room + dashboard structure. Where older descriptions further down conflict, **this wins** (they predate the redesign).

### The model — one transaction spine, two projections
The relationship is organized around a **transaction spine** — the deal it's about (a purchase or a sale). Five context layers, most-permanent first:

1. **Anchor** — the spine summary: deal type · property/criteria · budget · parties · key dates · stage. Emergent from facts, **display-as-captured** (only cells we actually have — never "N/A").
2. **Core** — stable preferences, constraints, motivations.
3. **Recency** — what's fresh / where things stand now.
4. **Timeline** — the immutable event log.
5. **Receipts** — cross-cutting source quotes; **operator-only** (see below).

Both surfaces project from the spine: the **client room** shows the *filled* cells (a clean letter); the **dashboard** shows the *same anchor as the operator's checklist, gaps included* (e.g. "Financing not captured"). **Anchor framing by deal type:** purchase → "Target purchase specifications" (what the buyer wants); sale → "Home for sale" (the listed property's specs).

### Room title = the deal, not the person
Default title is the extracted transaction topic — *"Purchase of a 4-bedroom HDB"*, *"Sale · Marina One"* — **operator-editable**, and it names the deal, not the client. **Confidentiality:** the `<title>` is generic (*"Your sale · FollowRoom"*), the URL is an opaque slug, and the exact unit/stack-floor never appears in the title or URL (it may appear only inside anchor cells). *(Supersedes the "Sarah's room" example below.)*

### Receipts are operator-only
Receipts (verbatim source quotes) are the **agent's** trust tool, shown on the operator surface — **not** on the client-facing room, which renders clean prose. This re-scopes emphasis #1 and the "Receipt thread" component below. The public pages were updated to match: `followroom-citations-page.html` is now operator-facing; `followroom-positioning.html`'s hero sub-line and the "Receipts, always" pillar scope the promise to the operator's confidence, not the client's view.

### Operator voice ≠ synthesized memory (held)
The operator note stays first-person in the gold-bordered card. The synthesized "what we noted" section renders in a **neutral record register** — never first-person "I" — so machine-synthesized memory never impersonates the operator. Extracted figures are **hedged** on the client surface ("around $1.8M", not "$1.8M (firm)"). Operator-only fact types (`spouse_family_factor`, financial position / liquidity, yield) are tactfully reframed or omitted client-side.

### Layout follows content (+ the no-reorder rule)
Don't manufacture a sidebar to fill width. A room is **single-column** when its genuinely-secondary content is light (discovery, most negotiation); a **two-zone** reading-column + rail appears only when there's enough secondary content to earn it (mature rooms: documents, history, view-stats). Main column = primary content (the anchor lives here, under the note); rail = secondary (timeline, reach, documents, view-tracking).

**A11y hard rule — no reorder:** DOM/source order MUST equal reading order. Never use `display:contents` + CSS `order` (or grid placement) to make the visual sequence diverge from source order on any breakpoint — it desyncs screen readers and keyboard focus (WCAG 1.3.2 / 2.4.3). Decide each element's priority once; lay it out with flex/grid in that order. **Re-flow, never re-order.**

### Structural breakpoints are allowed (amends the foundational principle)
"Fully fluid" governs type / spacing / grids — they scale continuously via `clamp()` / `auto-fit`, no snaps. But a change of *layout mode* (single-column ↔ two-zone; dashboard topbar collapse) is a legitimate **structural** breakpoint. The rule stands as: breakpoints for structure only, never for resizing type or spacing.

### Dashboard — attention, not commercial value
The rooms index sorts by **Recency (default) · Stage · Needs attention**. Do **NOT** rank clients by commercial worth (deal size / velocity) — a value leaderboard contradicts "witness, not coach" and "every client matters." Surface *neglect* instead: gentle "quiet for 3 weeks" freshness hints (muted, no alarm). The activity **pulse dot** stays the only color-as-status indicator. Capture-gaps render inline as calm warm-rust chips ("Financing not captured") — no "⚠" alarm glyphs, no "★" sparkle.

### Tokens (AA contrast)
`--text-muted` is **`#6E685D`** (~5:1 on page; the old `#9B9489` failed AA at caption sizes). `--accent-gold` (`#9B7B3B`) is for **borders/marks only**; use **`--accent-gold-text` (`#7E6224`)** for small gold text (eyebrows, numerals).

### Demo branding (external-safe)
Mockups use a **fictional** agency ("Meridian Realty") as a self-contained letter-tile, a generated agent ("Marcus Lim"), and an **initials avatar** — no real trademarks, no real faces, no external image hotlinks. In production, an operator's real logo/photo is operator-uploaded and served from our own storage — never a third-party favicon or stock hotlink (which also leaks the visitor's IP from a client-facing surface).

### Still owed to the backend (Plan 6)
The design promotes "room" to a first-class entity (title, transaction type, stage, deal value, offers, comparables, room-level view count) — none of which the current `clients`-centric schema can produce. Tracked in `docs/findings/2026-05-25-rooms-table-data-model-gaps.md`.

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
| `text-muted` | `#6E685D` | Meta info, captions, view counts — warm gray (AA ~5:1; was `#9B9489`, which failed AA at small sizes) |
| `border-subtle` | `#E8E3D9` | Card borders, dividers — warm cream-gray |
| `accent-gold` | `#9B7B3B` | Borders & marks only (fails AA as small text) |
| `accent-gold-text` | `#7E6224` | AA-passing gold for small text — eyebrows, numerals |
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

**Mobile-first, fully fluid.** The default mental model is: client opens the link from WhatsApp on their phone, scrolls once. But "mobile-first" here means *fluid from 320px up* — not a phone layout that snaps to a desktop one. Desktop is the same composition, breathing wider.

### Responsive adaptation

Per the foundational principle, type / spacing / grids scale continuously. Reference scales (tune per surface):

- **Container:** full-bleed with fluid padding `clamp(20px, 5vw, 24px)`; capped at `max-width: 640px` for line length; single-column at every width (two-column is a dashboard pattern, not a letter pattern).
- **Fluid type:** room title `clamp(28px, 7vw, 38px)`, section heading `clamp(19px, 4vw, 22px)`. Body holds at 17px — the prose readability floor — with line-height 1.6 for one-thumb scrolling.
- **Fluid rhythm:** between major sections `clamp(40px, 8vw, 56px)`; within a section `clamp(14px, 3vw, 20px)`.
- **Fluid grids:** multi-cell blocks (the anchor) use `repeat(auto-fit, minmax(220px, 1fr))` so they flow from 1 → N columns continuously — never a single 480px snap.
- **Breakpoints are for structure only** (e.g. the dashboard topbar collapse), never for resizing type or spacing — those are always fluid.

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

### Receipt thread (operator surface only)

**Re-scoped 2026-05-25 — receipts live on the operator surface, not the client room.** On the operator's view, each piece of extracted memory shows with its source quote one tap away. On the *client* room, the same memory renders as clean prose with NO source attribution (see Settled patterns → Receipts are operator-only). The pattern below describes the operator surface.

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

## Open questions for the operator room preview surface

Outside the scope of the three client-facing mockups (01-03) but worth noting for Plan 6:

- How does the operator preview a room before publishing? Same layout, different chrome (an "Edit" / "Publish" bar)?
- How does the operator approve a room update? Diff view? Side-by-side?
- What does "revoke + grace screen" look like to a client who tries to access a revoked link? (Per §11.15)

These are Plan 6 concerns. Mockups 01-03 demonstrate the *client* experience exclusively; mockup 04 is the *operator dashboard*.

---

## Operator Dashboard — distinct pattern (mockup 04)

The dashboard inherits all color tokens, typography choices, and brand identity from the client-room patterns above. What changes is **density** and **information architecture**. The dashboard is the operator's working surface — they live here, opening it dozens of times a day. The client room is a single-session letter. The two CANNOT be the same layout.

### Dashboard-specific design priorities (from `DESIGN.md` Operator section)

- **Density over whitespace** — Linear/Superhuman pattern. Multiple actionable items in a single viewport.
- **Keyboard-navigable** — ⌘K command palette hint visible from top bar; designed for power users who don't reach for mouse.
- **Adaptive (fluid)** — works on phone for in-the-moment captures, on desktop for batch review. Same components, fluidly scaled: type and spacing via `clamp()`; the stats row, rooms index, and panels reflow continuously (`auto-fit` / `minmax`); the topbar collapse (dropping ⌘K) is the *only* structural breakpoint — there is no separate mobile layout.
- **FollowRoom brand visible** — unlike client rooms where the operator's brand leads, the dashboard is operator-facing so the FollowRoom mark sits at top-left of the topbar (small, with a gold accent dot).

### Layout

- **Max-width 960px** (vs 640px for client rooms) — operator needs to see more at a glance
- **Sticky top bar** with backdrop blur — persistent context: brand, ⌘K hint, pending count, operator avatar
- **Single column** still, but denser vertical rhythm (40px between sections vs 56-72px in client rooms)
- **Fluid reflow** — stats row, rooms index, and insight cards use `auto-fit` / `minmax` (continuous reflow, not a 4→2 snap); the topbar dropping its ⌘K hint is the one structural collapse

### Dashboard-specific components

**Top bar** — operator-facing, FollowRoom mark visible. Layout: brand + (spacer) + ⌘K hint chip + pending-count chip (gold left-border, links to pending tray) + operator avatar+name.

**Day greeting** — serif headline that names the day's theme. Format: *"Good morning, Khaniff. [subtle gray] Three things would benefit from your eyes this week."* Subtle subhead in the same line, lighter color. Not generic ("Welcome back!"). Specific to what the system noticed.

**Panel** — the dashboard's repeating layout unit. Each panel has:
- Header row: serif panel title + uppercase meta on the right
- Subtle hairline below header
- Body: dense list of items (today actions, pending forwards, clients, activity)

**Today list** — 3 items max. Each item: `[when, gold serif] [title, weight 500] [meta, muted]` + right-aligned "Open" link. The "when" is human-relative ("By Fri 5pm", "By Sun", "End of May"), not absolute timestamps.

**Pending-forward strip** — single-card summary of unconfirmed forwards. Visual: large serif count + body text + right-aligned "Review" button with deep-teal border. Always present (even when 0); reads as ambient awareness rather than alarm.

**Cross-relationship insight card** ("Across your book") — Stage 2 Hivemind preview. Each insight is a card with:
- Eyebrow: `[uppercase muted label] [PREVIEW pill in gold]` — the pill makes the not-yet-shipped status explicit
- Body: serif sentence with inline `<strong>` for the most actionable phrase
- Meta: "based on..." source + deep-teal action link

The PREVIEW pill is critical. When Stage 2 actually ships, we drop the pill but keep the visual. The dashboard renders the same component; only the data source changes.

**Client list row** — dense, Linear-style. Grid: `[name with pulse dot] [stage label, uppercase muted] [last activity, tabular]`. Hover state expands subtle background to indicate clickability. Pulse dot color encodes activity state:
- Gold filled — active this week
- Deep teal — high-engagement client (multiple active threads)
- Muted gray — standing/quiet relationship

The pulse dot is the ONLY color-as-status indicator we use. Replaces red/green/yellow badges from generic CRMs.

**Stage label** — uppercase, muted, 11px. Examples: "Discovery", "Active discussion", "Decision · Friday", "Standing relationship", "Awaiting". The "·" prefix (e.g., "Decision · Friday") subtly conveys urgency without using color. When a stage truly needs attention, use `--attention-warm` for the label color (warm rust, never red).

**Activity feed** — compact list with `[when, tabular muted] [type pill, uppercase muted] [body with strong client name]`. Activity types: Forward, Room, Confirm, Upload, Room update. Reads as a journal, not a notifications panel.

**Stats row** — 4-column footer with serif numbers + uppercase labels. Examples: "Active clients · 32", "Facts in memory · 847", "Events this week · 14", "Time saved vs manual · 3.2hr". Calm, non-vanity metrics that affirm progress without sales-coaching ("You're crushing it! 🚀" anti-pattern).

### Density-vs-room comparison

| Aspect | Client room (01-03) | Dashboard (04) |
|--------|---------------------|----------------|
| Max-width | 640px | 960px |
| Section spacing | 56-72px | 40px |
| Heading scale | 22-38px serif | 17-32px serif |
| Items per viewport | 1-2 sections | 3-5 panels |
| Hover states | Receipts only | Client rows, action items, links |
| Sticky elements | None | Topbar with backdrop blur |
| Brand visibility | "FollowRoom" tiny footer | "● FollowRoom" topbar left |
| Color status indicators | None | Pulse dot (gold/deep/muted only) |
| Tone | Letter | Workshop |

### Dashboard anti-patterns (deliberately avoided in mockup 04)

- Red/green/yellow status badges (we use pulse dot color only — gold/deep/muted)
- "🎉 You're on fire!" engagement-bait copy
- Sparkle ✨ "AI Insights" panels (we have "Across your book" — same idea, no AI-SaaS vocabulary)
- Animated chart visualizations on load
- Floating action buttons (FABs) — keyboard-first means we don't add tap-target overhead
- Tabs / nested navigation — single scrollable surface still applies; the dashboard is just a denser version
- Avatar stacks ("4 viewers online") — surveillance-flavored, doesn't fit operator workspace either

### Translating dashboard to React (when Plan 7+ rebuilds the operator surface)

The current `web/app/dashboard/page.tsx` is a starter; the mockup 04 pattern is where it grows toward. Component sketch:

```
<Dashboard>
  <Topbar
    brand="FollowRoom"
    pendingCount={4}
    operator={{ name, avatar }}
  />
  <DayGreeting operator={...} theme={...} />
  <Panel title="This week" meta="3 items">
    <TodayList items={...} />
  </Panel>
  <Panel title="WhatsApp forwards" meta="awaiting attribution">
    <PendingForwardStrip count={4} suggestedClients={...} />
  </Panel>
  <Panel title="Across your book" meta="2 noticings this week">
    <InsightCard preview={true} ... />
    <InsightCard preview={true} ... />
  </Panel>
  <Panel title="Your clients" link="View all 32 →">
    <ClientList clients={...} />
  </Panel>
  <Panel title="Recent activity" link="See all →">
    <ActivityFeed items={...} />
  </Panel>
  <StatsRow stats={...} />
</Dashboard>
```

Each panel renders `null` when its data is empty, except Today + Clients (always present, with their own empty-state messages: "Nothing on your plate this week — quiet days have value." / "Add your first client →").

The `<InsightCard preview>` pattern lets us ship the Hivemind panel BEFORE the data source exists — the panel is on screen with hand-curated examples, the PREVIEW pill explains it. When Stage 2 lands, drop the pill, swap the data source. Component contract unchanged.
