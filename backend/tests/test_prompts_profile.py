from app.ai.prompts.profile import build_profile_prompt


def test_profile_prompt_includes_client_name_and_facts():
    facts = [
        {"type": "goal", "value": "buy 3-bed HDB East Coast", "source_event_ids": ["e1"]},
        {"type": "budget_constraint", "value": "ceiling $1.8M", "source_event_ids": ["e2"]},
    ]
    p = build_profile_prompt(
        client_name="Sarah Tan",
        short_context="HDB upgrade, East Coast",
        facts=facts,
        view="internal",
    )
    assert "Sarah Tan" in p
    assert "HDB upgrade" in p
    assert "buy 3-bed HDB East Coast" in p
    assert "ceiling $1.8M" in p


def test_profile_prompt_internal_view_allows_sensitive_sections():
    p = build_profile_prompt(
        client_name="Sarah",
        short_context="x",
        facts=[],
        view="internal",
    )
    assert "Decision dynamics" in p or "decision" in p.lower()


def test_profile_prompt_client_facing_view_strips_sensitive_sections():
    p = build_profile_prompt(
        client_name="Sarah",
        short_context="x",
        facts=[],
        view="client_facing",
    )
    assert "decision_blocker" not in p
    assert "spouse_family_factor" not in p
    assert "emotional_hesitation" not in p


def test_profile_prompt_includes_line_cap_directive():
    p = build_profile_prompt(client_name="x", short_context="x", facts=[], view="internal")
    assert "400" in p
