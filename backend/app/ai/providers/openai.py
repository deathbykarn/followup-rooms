from typing import Any


class OpenAIProvider:
    """OpenAI adapter. Phase 1 stub; Plan 2 wires real SDK."""

    def call(self, model: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "provider": "openai",
            "model": model,
            "prompt_preview": prompt[:200],
            "stub": True,
        }
