"""
Profile prompt — generate a markdown profile (internal OR client-facing)
from a client's facts.

Two views are PHYSICALLY SEPARATED (design doc §6.4 — Tier 3 safety):
- "internal": full visibility; includes decision dynamics, family factors,
  emotional hesitation, decision blockers
- "client_facing": tactfully rewritten subset; sensitive types are
  FILTERED OUT before the prompt is built so the model never sees them
"""
from typing import Any, Literal


ProfileView = Literal["internal", "client_facing"]


PROFILE_SYSTEM = """You are a profile composer inside FollowRoom. You read a client's typed facts and write a concise, evidence-grounded markdown profile for the relationship-driven sales operator. You never speculate beyond the supplied facts. You never invent details."""


INTERNAL_SECTIONS = """
Sections (use these exact ## headings; omit a section if no facts for it):

## Identity
Name, relationship type, status, short context.

## Goals
What the client wants.

## Constraints
Budget, timeline, location, family logistics.

## Decision dynamics
Who needs to align; what they care about; who blocks.

## Preferences
Specific likes; communication style; viewing preferences.

## Open threads
What's pending; what was promised.

## Recent events
Last 30 days, summarized.

Each bullet ends with source event citations like [ev_001, ev_023].
"""

CLIENT_FACING_SECTIONS = """
Sections (use these exact ## headings; omit a section if no facts for it):

## Goals
What we're working toward, plainly stated.

## Key considerations
The things that matter most to you in this decision.

## Options being explored
What we've looked at; what's next.

## What's pending
Things we're waiting on or actively preparing.

Each bullet should read warmly and professionally; this is for the CLIENT to read.
Do not include inferences about family dynamics, emotional state, or
decision-making process. Use only the operator-approved facts provided.
"""


def build_profile_prompt(
    client_name: str,
    short_context: str,
    facts: list[dict[str, Any]],
    view: ProfileView,
) -> str:
    sections = INTERNAL_SECTIONS if view == "internal" else CLIENT_FACING_SECTIONS

    if facts:
        facts_block_lines = []
        for f in facts:
            src = f.get("source_event_ids", [])
            src_str = ", ".join(src) if src else ""
            facts_block_lines.append(f"- type={f['type']}: {f['value']} [{src_str}]")
        facts_block = "\n".join(facts_block_lines)
    else:
        facts_block = "(no facts yet — render a placeholder profile from short_context only)"

    return f"""Write a markdown profile for the client below.

CAP: 400 lines maximum. Be concise. If a section has no relevant facts, omit it (do not write empty sections).

{sections}

---

Client name: {client_name}
Short context (operator-supplied seed): {short_context}

Facts available (use these as your sources; cite their event IDs in brackets):
{facts_block}

---

Now write the profile."""
