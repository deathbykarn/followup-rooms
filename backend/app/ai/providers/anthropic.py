"""
Anthropic provider — real SDK + instructor integration.

Two interfaces:
- structured_call(): typed extraction via instructor; returns Pydantic model
- call(): legacy stub interface from Foundation; kept for backward-compat
"""
from typing import Any, TypeVar

import anthropic
import instructor
from pydantic import BaseModel

from app.core.config import get_settings

T = TypeVar("T", bound=BaseModel)


def _build_instructor_client() -> Any:
    """
    Build an instructor-wrapped Anthropic client.

    Request-scoped pattern matches the Supabase client convention (Foundation
    §Task 3): never module-scope a client that carries auth-bearing config.
    """
    settings = get_settings()
    raw_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return instructor.from_anthropic(raw_client)


class AnthropicProvider:
    """Anthropic adapter with structured output via instructor."""

    def structured_call(
        self,
        model: str,
        system: str,
        user_prompt: str,
        response_model: type[T],
        max_tokens: int = 4096,
        max_retries: int = 2,
        **kwargs: Any,
    ) -> T:
        """
        Make a structured call. Returns an instance of response_model.

        instructor handles JSON-schema-strict mode + retry-on-validation-error.
        """
        client = _build_instructor_client()
        return client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_prompt}],
            response_model=response_model,
            max_retries=max_retries,
            **kwargs,
        )

    def call(self, model: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Legacy interface kept for backward-compat with Foundation tests."""
        return {
            "provider": "anthropic",
            "model": model,
            "prompt_preview": prompt[:200],
            "stub": True,
        }
