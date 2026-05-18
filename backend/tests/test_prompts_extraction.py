from app.ai.prompts.extraction import build_extraction_prompt


def test_extraction_prompt_includes_event_id_and_raw_text():
    p = build_extraction_prompt(
        event_id="evt-abc",
        raw_text="Sarah said she wants Marine Parade for parents nearby.",
        client_context="Sarah Tan — HDB upgrade, East Coast, $1.8M",
    )
    assert "evt-abc" in p
    assert "Sarah said she wants Marine Parade" in p
    assert "Sarah Tan — HDB upgrade" in p


def test_extraction_prompt_lists_fact_types():
    p = build_extraction_prompt(event_id="x", raw_text="x", client_context="x")
    for t in ["goal", "budget_constraint", "objection", "property_preference"]:
        assert t in p


def test_extraction_prompt_emphasizes_source_spans():
    p = build_extraction_prompt(event_id="x", raw_text="x", client_context="x")
    assert "verbatim" in p.lower() or "exact" in p.lower()
    assert "snippet" in p.lower() or "quote" in p.lower()
