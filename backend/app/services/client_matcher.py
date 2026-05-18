"""
ClientMatcher — given an operator's caption text on a forward, suggest
the most likely client.

Two-pass design:
1. Fuzzy pass: lowercase substring match against client_name and aliases[].
   - Single hit → 0.95 confidence
   - No hit → fall through to LLM
   - Multiple hits → fall through to LLM (ambiguity resolution)
2. LLM pass (Haiku 4.5 via AgentDispatcher.structured_dispatch): asked to
   pick from the operator's client list, returns {client_id, confidence}.

The operator always sees the suggestion + can Change/Discard — this is
attribution assistance, never auto-confirm. Tier 3 risk (wrong-client
attribution) is mitigated by structural confirm step.
"""
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field
from supabase import Client

from app.ai.dispatcher import AgentDispatcher, LogicalRole

FUZZY_CONFIDENCE = 0.95
LLM_DEFAULT_CONFIDENCE = 0.6


@dataclass
class MatchSuggestion:
    client_id: str | None
    confidence: float


class _LLMPickResponse(BaseModel):
    """Structured output schema for the disambiguation prompt."""

    client_id: str | None = Field(
        default=None,
        description="UUID of the chosen client, or null if no good match.",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="0-1 confidence in the pick.",
    )
    reasoning: str | None = Field(
        default=None,
        description="One short sentence on why this client (or none).",
    )


_LLM_SYSTEM = (
    "You disambiguate which client an operator meant when they typed a short "
    "identifier as a WhatsApp forward caption. You pick from the provided "
    "client list, or return null if none fit. You never invent client IDs."
)


def _build_llm_prompt(
    caption_text: str,
    forwarded_text: str,
    clients: list[dict[str, Any]],
) -> str:
    client_lines = "\n".join(
        f"- id={c['id']} name={c['client_name']!r}"
        + (f" aliases={c.get('aliases') or []}" if c.get("aliases") else "")
        + (
            f" short_context={c.get('short_context', '')[:120]!r}"
            if c.get("short_context")
            else ""
        )
        for c in clients
    )
    return f"""The operator's clients:
{client_lines}

The operator's caption on the forward:
\"\"\"{caption_text}\"\"\"

The forwarded message (for additional context only):
\"\"\"{forwarded_text}\"\"\"

Pick the client_id this forward is most likely about. Return null if no client fits well."""


class ClientMatcher:
    """Suggests a client_id from caption_text for an operator's pending forward."""

    def __init__(
        self,
        supabase: Client,
        dispatcher: AgentDispatcher | None = None,
    ) -> None:
        self._db = supabase
        self._dispatcher = dispatcher or AgentDispatcher()

    def suggest(
        self,
        operator_id: str,
        caption_text: str,
        forwarded_text: str = "",
    ) -> MatchSuggestion:
        clients = self._fetch_active_clients(operator_id)
        if not clients:
            return MatchSuggestion(client_id=None, confidence=0.0)

        # Strip empty caption — fall straight to LLM with empty hint
        caption = (caption_text or "").strip()

        # Fuzzy pass
        if caption:
            hits = self._fuzzy_match(caption, clients)
            if len(hits) == 1:
                return MatchSuggestion(client_id=hits[0], confidence=FUZZY_CONFIDENCE)

        # LLM pass — disambiguation or no-fuzzy-hit
        try:
            pick = self._llm_pick(caption, forwarded_text, clients)
        except Exception:
            return MatchSuggestion(client_id=None, confidence=0.0)

        # Validate the LLM's pick is actually one of the operator's clients
        valid_ids = {c["id"] for c in clients}
        if pick.client_id and pick.client_id in valid_ids:
            return MatchSuggestion(
                client_id=pick.client_id,
                confidence=pick.confidence or LLM_DEFAULT_CONFIDENCE,
            )
        return MatchSuggestion(client_id=None, confidence=0.0)

    # --- helpers ---

    def _fetch_active_clients(self, operator_id: str) -> list[dict[str, Any]]:
        resp = (
            self._db.table("clients")
            .select("id, client_name, aliases, short_context")
            .eq("operator_id", operator_id)
            .eq("is_deleted", False)
            .execute()
        )
        return resp.data or []

    def _fuzzy_match(
        self,
        caption_lower: str,
        clients: list[dict[str, Any]],
    ) -> list[str]:
        caption_lower = caption_lower.lower()
        hits: list[str] = []
        for c in clients:
            name = (c.get("client_name") or "").lower()
            if name and (caption_lower in name or name in caption_lower):
                hits.append(c["id"])
                continue
            for alias in c.get("aliases") or []:
                alias_lower = (alias or "").lower()
                if alias_lower and (caption_lower in alias_lower or alias_lower in caption_lower):
                    hits.append(c["id"])
                    break
        return hits

    def _llm_pick(
        self,
        caption: str,
        forwarded_text: str,
        clients: list[dict[str, Any]],
    ) -> _LLMPickResponse:
        prompt = _build_llm_prompt(caption, forwarded_text, clients)
        return self._dispatcher.structured_dispatch(
            role=LogicalRole.CLASSIFIER,
            system=_LLM_SYSTEM,
            user_prompt=prompt,
            response_model=_LLMPickResponse,
        )
