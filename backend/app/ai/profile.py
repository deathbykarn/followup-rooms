"""
ProfileService — regenerate a client's markdown profile (internal OR
client_facing view) from current facts.

CRITICAL: client_facing view receives a FILTERED facts list — sensitive
types (spouse_family_factor, emotional_hesitation, decision_blocker) are
removed before the prompt is built. The model never sees them.
This is the structural Tier 3 guard per design doc §6.4.
"""
from typing import Any

from pydantic import BaseModel

from app.ai.dispatcher import AgentDispatcher, LogicalRole
from app.ai.prompts.profile import PROFILE_SYSTEM, ProfileView, build_profile_prompt

# Fact types that are NEVER visible in the client_facing profile
SENSITIVE_FACT_TYPES = {
    "spouse_family_factor",
    "emotional_hesitation",
    "decision_blocker",
}


class ProfileResult(BaseModel):
    markdown: str


class ProfileService:
    """Regenerate the markdown profile for a client."""

    def __init__(self, dispatcher: AgentDispatcher | None = None) -> None:
        self._dispatcher = dispatcher or AgentDispatcher()

    def regenerate(
        self,
        client_name: str,
        short_context: str,
        facts: list[dict[str, Any]],
        view: ProfileView,
    ) -> ProfileResult:
        filtered_facts = self._filter_facts_for_view(facts, view)
        user_prompt = build_profile_prompt(
            client_name=client_name,
            short_context=short_context,
            facts=filtered_facts,
            view=view,
        )
        return self._dispatcher.structured_dispatch(
            role=LogicalRole.GENERATOR,
            system=PROFILE_SYSTEM,
            user_prompt=user_prompt,
            response_model=ProfileResult,
        )

    @staticmethod
    def _filter_facts_for_view(
        facts: list[dict[str, Any]],
        view: ProfileView,
    ) -> list[dict[str, Any]]:
        if view == "internal":
            return facts
        # client_facing: remove sensitive types AND require visibility=client_facing_safe
        return [
            f for f in facts
            if f["type"] not in SENSITIVE_FACT_TYPES
            and f.get("visibility") == "client_facing_safe"
        ]
