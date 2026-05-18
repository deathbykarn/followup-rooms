from app.ai.matching import MatchAction, MatchingService
from app.models.fact import ExtractedFact, SourceSpan


def _make_extracted(value: str, type_: str = "budget_constraint", confidence: float = 0.9) -> ExtractedFact:
    return ExtractedFact(
        type=type_,
        value=value,
        confidence_score=confidence,
        visibility="operator_only",
        source_spans=[SourceSpan(event_id="evt-x", snippet=value)],
    )


def test_match_returns_ADD_when_no_existing_facts():
    svc = MatchingService()
    extracted = _make_extracted("monthly repayment ceiling ~$5k")
    decision = svc.decide(extracted, existing_facts=[])
    assert decision.action is MatchAction.ADD
    assert decision.supersedes_id is None


def test_match_returns_NOOP_when_identical_value_already_exists():
    svc = MatchingService()
    extracted = _make_extracted("monthly repayment ceiling ~$5k")
    existing = [{
        "id": "fact-1",
        "type": "budget_constraint",
        "value": "monthly repayment ceiling ~$5k",
        "is_deleted": False,
        "superseded_by": None,
    }]
    decision = svc.decide(extracted, existing_facts=existing)
    assert decision.action is MatchAction.NOOP
    assert decision.matches_id == "fact-1"


def test_match_returns_UPDATE_when_same_type_different_value():
    svc = MatchingService()
    extracted = _make_extracted("monthly repayment ceiling ~$5.5k")
    existing = [{
        "id": "fact-1",
        "type": "budget_constraint",
        "value": "monthly repayment ceiling ~$5k",
        "is_deleted": False,
        "superseded_by": None,
    }]
    decision = svc.decide(extracted, existing_facts=existing)
    assert decision.action is MatchAction.UPDATE
    assert decision.supersedes_id == "fact-1"


def test_match_ignores_superseded_and_deleted_facts():
    svc = MatchingService()
    extracted = _make_extracted("budget $1.8M")
    existing = [
        {"id": "f1", "type": "budget_constraint", "value": "budget $1.8M", "is_deleted": True, "superseded_by": None},
        {"id": "f2", "type": "budget_constraint", "value": "budget $1.8M", "is_deleted": False, "superseded_by": "f9"},
    ]
    decision = svc.decide(extracted, existing_facts=existing)
    assert decision.action is MatchAction.ADD


def test_match_returns_UPDATE_only_among_same_type():
    svc = MatchingService()
    extracted = _make_extracted("budget $2M", type_="budget_constraint")
    existing = [
        {"id": "f1", "type": "goal", "value": "budget $1.8M", "is_deleted": False, "superseded_by": None},
        {"id": "f2", "type": "budget_constraint", "value": "budget $1.8M", "is_deleted": False, "superseded_by": None},
    ]
    decision = svc.decide(extracted, existing_facts=existing)
    assert decision.action is MatchAction.UPDATE
    assert decision.supersedes_id == "f2"
