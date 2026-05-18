from unittest.mock import MagicMock, patch

from pydantic import BaseModel

from app.ai.providers.anthropic import AnthropicProvider


class _DummyOutput(BaseModel):
    message: str


def test_anthropic_provider_structured_call_returns_typed_model():
    fake_instructor_client = MagicMock()
    fake_instructor_client.messages.create.return_value = _DummyOutput(message="hello")

    with patch(
        "app.ai.providers.anthropic._build_instructor_client",
        return_value=fake_instructor_client,
    ):
        provider = AnthropicProvider()
        result = provider.structured_call(
            model="claude-haiku-4-5",
            system="you are a test",
            user_prompt="say hello",
            response_model=_DummyOutput,
        )

    assert isinstance(result, _DummyOutput)
    assert result.message == "hello"


def test_anthropic_provider_call_legacy_signature_still_returns_dict():
    provider = AnthropicProvider()
    result = provider.call(model="claude-haiku-4-5", prompt="x")
    assert result["provider"] == "anthropic"
    assert "model" in result
