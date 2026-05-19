from unittest.mock import MagicMock

from app.services.client_matcher import (
    FUZZY_CONFIDENCE,
    ClientMatcher,
    _LLMPickResponse,
)


def _mock_db_with_clients(clients: list[dict]):
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=clients
    )
    return db


def test_no_clients_returns_none():
    db = _mock_db_with_clients([])
    svc = ClientMatcher(supabase=db, dispatcher=MagicMock())
    result = svc.suggest(operator_id="op-1", caption_text="Sarah")
    assert result.client_id is None
    assert result.confidence == 0.0


def test_exact_name_match_returns_fuzzy_confidence():
    db = _mock_db_with_clients([
        {"id": "c1", "client_name": "Sarah Tan", "aliases": [], "short_context": ""},
        {"id": "c2", "client_name": "Michael Lee", "aliases": [], "short_context": ""},
    ])
    svc = ClientMatcher(supabase=db, dispatcher=MagicMock())
    result = svc.suggest(operator_id="op-1", caption_text="Sarah")
    assert result.client_id == "c1"
    assert result.confidence == FUZZY_CONFIDENCE


def test_alias_match_returns_fuzzy_confidence():
    db = _mock_db_with_clients([
        {"id": "c1", "client_name": "Sarah Tan", "aliases": ["Auntie Sarah"], "short_context": ""},
    ])
    svc = ClientMatcher(supabase=db, dispatcher=MagicMock())
    result = svc.suggest(operator_id="op-1", caption_text="auntie sarah")
    assert result.client_id == "c1"
    assert result.confidence == FUZZY_CONFIDENCE


def test_ambiguous_falls_through_to_llm():
    db = _mock_db_with_clients([
        {"id": "c1", "client_name": "Sarah Tan", "aliases": [], "short_context": "HDB upgrade"},
        {"id": "c2", "client_name": "Sarah Chen", "aliases": [], "short_context": "Condo investor"},
    ])
    dispatcher = MagicMock()
    dispatcher.structured_dispatch.return_value = _LLMPickResponse(
        client_id="c2", confidence=0.8, reasoning="caption mentions condo"
    )
    svc = ClientMatcher(supabase=db, dispatcher=dispatcher)
    result = svc.suggest(
        operator_id="op-1",
        caption_text="Sarah",
        forwarded_text="looking at the condo we discussed",
    )
    assert result.client_id == "c2"
    assert result.confidence == 0.8


def test_no_fuzzy_hit_falls_to_llm():
    db = _mock_db_with_clients([
        {"id": "c1", "client_name": "Michael Lee", "aliases": [], "short_context": ""},
    ])
    dispatcher = MagicMock()
    dispatcher.structured_dispatch.return_value = _LLMPickResponse(
        client_id="c1", confidence=0.7
    )
    svc = ClientMatcher(supabase=db, dispatcher=dispatcher)
    result = svc.suggest(operator_id="op-1", caption_text="the engineer guy")
    assert result.client_id == "c1"
    assert result.confidence == 0.7


def test_llm_returns_invalid_client_id_falls_back_to_none():
    db = _mock_db_with_clients([
        {"id": "c1", "client_name": "Michael Lee", "aliases": [], "short_context": ""},
    ])
    dispatcher = MagicMock()
    dispatcher.structured_dispatch.return_value = _LLMPickResponse(
        client_id="hallucinated-id", confidence=0.9
    )
    svc = ClientMatcher(supabase=db, dispatcher=dispatcher)
    result = svc.suggest(operator_id="op-1", caption_text="x")
    assert result.client_id is None
    assert result.confidence == 0.0


def test_llm_returns_null_when_no_client_fits():
    db = _mock_db_with_clients([
        {"id": "c1", "client_name": "Michael Lee", "aliases": [], "short_context": ""},
    ])
    dispatcher = MagicMock()
    dispatcher.structured_dispatch.return_value = _LLMPickResponse(
        client_id=None, confidence=0.0
    )
    svc = ClientMatcher(supabase=db, dispatcher=dispatcher)
    result = svc.suggest(operator_id="op-1", caption_text="unknown person")
    assert result.client_id is None


def test_llm_exception_returns_none_silently():
    db = _mock_db_with_clients([
        {"id": "c1", "client_name": "Michael Lee", "aliases": [], "short_context": ""},
    ])
    dispatcher = MagicMock()
    dispatcher.structured_dispatch.side_effect = RuntimeError("anthropic 500")
    svc = ClientMatcher(supabase=db, dispatcher=dispatcher)
    result = svc.suggest(operator_id="op-1", caption_text="x")
    assert result.client_id is None
    assert result.confidence == 0.0
