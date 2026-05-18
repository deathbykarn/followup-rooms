"""
Extraction prompt for FollowRoom KB.

Sonnet 4.6 extracts typed facts with mandatory verbatim source spans
from raw event text (operator's manual note, transcript line, forwarded
message, etc.). Receipts are non-negotiable (Axiom 3).
"""

EXTRACTION_SYSTEM = """You are an extraction component inside FollowRoom, a relationship-memory product for property agents. You read raw client interaction text and extract typed, evidence-grounded facts about the client relationship. You never speculate beyond the source text. You never invent dates, numbers, or names that aren't present."""

FACT_TYPE_DESCRIPTIONS = """
Valid fact types (use the exact identifier):

- goal: what the client wants (e.g., "buy a 3-bed HDB in East Coast")
- budget_constraint: monetary or affordability concern (e.g., "monthly repayment ceiling ~$5k")
- timeline_signal: when something will or might happen (e.g., "after bonus in Q1")
- objection: explicit pushback or concern (e.g., "wife not convinced about location")
- spouse_family_factor: family dynamics affecting the deal (e.g., "wife's parents nearby is important")
- emotional_hesitation: uncertainty or anxiety signals (e.g., "stressed about timing")
- document_request: client asked for or promised documents (e.g., "wants floor plans")
- follow_up_promise: operator promised to do something (e.g., "send affordability scenarios by Friday")
- viewing_preference: what they want from a viewing (e.g., "weekends only")
- property_preference: property attributes they care about (e.g., "ground floor unit")
- decision_blocker: what's stopping the deal from progressing (e.g., "spouse alignment on timing")
- buying_intent_signal: positive purchase intent (e.g., "ready to move forward")
- market_signal: signal about market behavior the client mentioned (e.g., "other buyers backing off")
- content_opportunity: explainer/asset the operator could create (e.g., "ABSD explainer")
"""

EXTRACTION_INSTRUCTIONS = """
For each extractable fact in the text:

1. Pick the most specific fact type from the list above.
2. Write a single sentence stating the fact in plain English (avoid pronouns; use the client's name or relationship terms).
3. Provide a confidence_score between 0.0 and 1.0. Use 0.9+ only when the source text states the fact explicitly. Use 0.5-0.8 when inferred from context. Below 0.5: do not emit.
4. Provide source_spans: at least one verbatim quote from raw_text that grounds the claim. Each snippet must appear character-for-character in raw_text. Multiple snippets allowed if the fact is supported by multiple sentences.
5. Set visibility:
   - "operator_only" by default
   - "client_facing_safe" only if the fact is something the client themselves said about their own preferences (not inferences about their family dynamics, emotional state, or decision-making process)

Hard rules:
- Never fabricate names, dates, money amounts, or property identifiers not in the source.
- If raw_text has no extractable client-relationship facts, emit an empty list.
- Do not include the operator's actions/thoughts as facts about the client (unless they're follow_up_promise type).
- Tier 3 inferences (family dynamics, emotional state, decision-blocker speculation) MUST be visibility="operator_only" — never client_facing_safe.
"""


def build_extraction_prompt(
    event_id: str,
    raw_text: str,
    client_context: str,
) -> str:
    """
    Build a single user-message prompt for the extractor.

    Returns the prompt string. The caller wraps it with the SYSTEM
    message and the structured-output schema via instructor.
    """
    return f"""{FACT_TYPE_DESCRIPTIONS}

{EXTRACTION_INSTRUCTIONS}

---

Client context (background — do NOT treat as source for facts; only the raw_text below is sourceable):
{client_context}

---

Event ID: {event_id}
Source text (this is the only thing you may cite verbatim in source_spans):
\"\"\"
{raw_text}
\"\"\"

Extract facts now."""
