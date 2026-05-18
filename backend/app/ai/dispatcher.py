from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.ai.providers.anthropic import AnthropicProvider
from app.ai.providers.base import Provider
from app.ai.providers.openai import OpenAIProvider


class LogicalRole(str, Enum):
    """
    Logical roles separate business logic from vendor coupling
    (Pattern 20 — Vendor Agnostic; design doc §8.5).
    Role → (provider, model) resolved via config below.
    """
    CLASSIFIER = "classifier"
    SUMMARIZER = "summarizer"
    EXTRACTOR = "extractor"
    GENERATOR = "generator"
    JUDGE = "judge"
    VALIDATOR = "validator"
    TRANSCRIBER = "transcriber"


@dataclass(frozen=True)
class RoleConfig:
    provider_name: str
    model: str


# Default role-to-provider/model mapping for Phase 1.
# Future: load from a YAML config file or env so swaps don't require redeploy.
_DEFAULT_ROLE_MAP: dict[LogicalRole, RoleConfig] = {
    LogicalRole.CLASSIFIER: RoleConfig("anthropic", "claude-haiku-4-5"),
    LogicalRole.SUMMARIZER: RoleConfig("anthropic", "claude-haiku-4-5"),
    LogicalRole.EXTRACTOR: RoleConfig("anthropic", "claude-sonnet-4-6"),
    LogicalRole.GENERATOR: RoleConfig("anthropic", "claude-sonnet-4-6"),
    LogicalRole.JUDGE: RoleConfig("anthropic", "claude-haiku-4-5"),
    LogicalRole.VALIDATOR: RoleConfig("anthropic", "claude-haiku-4-5"),
    LogicalRole.TRANSCRIBER: RoleConfig("openai", "whisper-1"),
}


class AgentDispatcher:
    """
    Resolves a LogicalRole to a (provider, model) pair and dispatches.
    Phase 1: returns provider + model; actual `call()` returns stub
    response. Plan 2 wires real SDK calls + instructor + caching.
    """

    def __init__(self, role_map: dict[LogicalRole, RoleConfig] | None = None) -> None:
        self._role_map = role_map or _DEFAULT_ROLE_MAP
        self._providers: dict[str, Provider] = {
            "anthropic": AnthropicProvider(),
            "openai": OpenAIProvider(),
        }

    def resolve(self, role: LogicalRole) -> tuple[Provider, str]:
        config = self._role_map[role]
        provider = self._providers[config.provider_name]
        return provider, config.model

    def dispatch(self, role: LogicalRole, prompt: str, **kwargs: Any) -> dict[str, Any]:
        provider, model = self.resolve(role)
        return provider.call(model, prompt, **kwargs)

    def structured_dispatch(
        self,
        role: LogicalRole,
        system: str,
        user_prompt: str,
        response_model: type,
        **kwargs: Any,
    ) -> Any:
        """
        Structured-output dispatch: calls provider's structured_call.

        Returns an instance of response_model. The provider must implement
        structured_call (currently AnthropicProvider). Future providers
        adding this method are picked up automatically by the role map.
        """
        provider, model = self.resolve(role)
        if not hasattr(provider, "structured_call"):
            raise NotImplementedError(
                f"Provider for role {role} does not implement structured_call"
            )
        return provider.structured_call(
            model=model,
            system=system,
            user_prompt=user_prompt,
            response_model=response_model,
            **kwargs,
        )
