# docs/design — Client-Facing Room Visual Design

**Plan 4.2 deliverable.** Visual design for the client-facing room surface that ships with Plan 6.

## What's in here

- **`DESIGN_SPEC.md`** — the design decisions made visible in the mockups. Color tokens, typography, component patterns, state patterns, anti-patterns avoided. This is the surface we work backwards from when building Plan 6's React components.
- **`mockups/`** — standalone HTML files demonstrating the visual language across both surfaces:
  - Client-facing rooms (Plan 6 target):
    - `01-sarah-tan-discovery.html` — first-meeting room. Empty-state grace.
    - `02-wendy-lim-negotiation.html` — active negotiation room. Calm restraint at high stakes.
    - `03-david-chen-feature-showcase.html` — long-term client with full feature utilization.
  - Operator dashboard (Plans 5/7/8 target):
    - `04-operator-dashboard.html` — daily working surface. Density, ⌘K-ready, Linear/Superhuman pattern. Includes a `PREVIEW`-flagged Hivemind panel that anchors the Stage 2 visual ahead of implementation.

## How to view

Open each `.html` file directly in your browser — they're self-contained, no server needed. Tailwind + Google Fonts load from CDN; first load may take 1-2 seconds.

For the intended experience: open on a phone, since clients open these from WhatsApp on mobile. Desktop works too (max-width 640px centered).

## The four design emphases (read DESIGN_SPEC.md for detail)

1. **Receipts woven into prose**, not bulleted as data
2. **Empty-state grace** — sparse rooms feel intentional, not impoverished
3. **Calm restraint at high stakes** — no badges, no urgency theater
4. **Operator voice ≠ extracted memory** — visible distinction between what the operator wrote and what the system synthesized

## How this becomes code

DESIGN_SPEC.md §"Translating to Plan 6 React components" sketches the component decomposition. Each section in a mockup maps cleanly to a React component that renders `null` when its data is empty — the room layout is a composition of optional sections, not a fixed template.

## Iteration loop

Mockup HTML changes here are the canonical design source. When you want to change how a room looks:
1. Edit the relevant `.html` file directly (no build step needed)
2. Update `DESIGN_SPEC.md` if a new pattern emerges
3. After approval, Plan 6's React components get updated to match
