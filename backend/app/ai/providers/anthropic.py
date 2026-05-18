from typing import Any


class AnthropicProvider:
    """
    Anthropic adapter. Phase 1: stub that returns echo-like responses.
    Plan 2 wires real Anthropic SDK + instructor calls.
    """

    def call(self, model: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "provider": "anthropic",
            "model": model,
            "prompt_preview": prompt[:200],
            "stub": True,
        }
