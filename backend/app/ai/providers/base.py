from typing import Any, Protocol


class Provider(Protocol):
    """AI provider Protocol — adapters must implement this interface."""

    def call(self, model: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """
        Make a structured call to the provider. Returns parsed response.
        Phase 1: stub implementations; real calls land in Plan 2.
        """
        ...
