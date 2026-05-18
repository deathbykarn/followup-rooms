from unittest.mock import MagicMock

from app.ai.profile import ProfileResult, ProfileService


def test_profile_service_filters_sensitive_facts_for_client_facing_view():
    fake_dispatcher = MagicMock()
    fake_dispatcher.structured_dispatch.return_value = ProfileResult(markdown="## Goals\n- buy HDB")

    svc = ProfileService(dispatcher=fake_dispatcher)
    facts = [
        {"type": "goal", "value": "buy HDB", "visibility": "client_facing_safe", "source_event_ids": ["e1"]},
        {"type": "spouse_family_factor", "value": "wife is blocker", "visibility": "operator_only", "source_event_ids": ["e2"]},
        {"type": "emotional_hesitation", "value": "stressed about timing", "visibility": "operator_only", "source_event_ids": ["e3"]},
    ]
    svc.regenerate(
        client_name="Sarah",
        short_context="HDB upgrade",
        facts=facts,
        view="client_facing",
    )

    args, kwargs = fake_dispatcher.structured_dispatch.call_args
    prompt = kwargs["user_prompt"]
    assert "buy HDB" in prompt
    assert "wife is blocker" not in prompt
    assert "stressed about timing" not in prompt


def test_profile_service_internal_view_includes_all_visible_facts():
    fake_dispatcher = MagicMock()
    fake_dispatcher.structured_dispatch.return_value = ProfileResult(markdown="## Identity\nx")

    svc = ProfileService(dispatcher=fake_dispatcher)
    facts = [
        {"type": "goal", "value": "buy HDB", "visibility": "client_facing_safe", "source_event_ids": ["e1"]},
        {"type": "spouse_family_factor", "value": "wife is blocker", "visibility": "operator_only", "source_event_ids": ["e2"]},
    ]
    svc.regenerate(client_name="Sarah", short_context="x", facts=facts, view="internal")

    args, kwargs = fake_dispatcher.structured_dispatch.call_args
    prompt = kwargs["user_prompt"]
    assert "buy HDB" in prompt
    assert "wife is blocker" in prompt


def test_profile_service_returns_markdown_string():
    fake_dispatcher = MagicMock()
    fake_dispatcher.structured_dispatch.return_value = ProfileResult(markdown="## Goals\n- buy")
    svc = ProfileService(dispatcher=fake_dispatcher)
    out = svc.regenerate(client_name="x", short_context="x", facts=[], view="internal")
    assert out.markdown.startswith("## Goals")
