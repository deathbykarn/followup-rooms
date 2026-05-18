from unittest.mock import MagicMock

from app.ai.extraction import ExtractionResult, ExtractionService
from app.models.fact import ExtractedFact, SourceSpan


def test_extraction_service_calls_dispatcher_with_extractor_role():
    fake_dispatcher = MagicMock()
    fake_dispatcher.structured_dispatch.return_value = ExtractionResult(
        facts=[
            ExtractedFact(
                type="property_preference",
                value="Marine Parade preference for parent proximity",
                confidence_score=0.9,
                visibility="operator_only",
                source_spans=[
                    SourceSpan(event_id="evt-1", snippet="wants Marine Parade because parents nearby"),
                ],
            ),
        ]
    )

    svc = ExtractionService(dispatcher=fake_dispatcher)
    result = svc.extract(
        event_id="evt-1",
        raw_text="Sarah wants Marine Parade because parents nearby.",
        client_context="Sarah Tan — HDB upgrade",
    )

    assert isinstance(result, ExtractionResult)
    assert len(result.facts) == 1
    assert result.facts[0].type == "property_preference"
    args, kwargs = fake_dispatcher.structured_dispatch.call_args
    assert kwargs["role"].value == "extractor"
    assert kwargs["response_model"] is ExtractionResult


def test_extraction_service_returns_empty_when_no_facts_found():
    fake_dispatcher = MagicMock()
    fake_dispatcher.structured_dispatch.return_value = ExtractionResult(facts=[])

    svc = ExtractionService(dispatcher=fake_dispatcher)
    result = svc.extract(event_id="evt-1", raw_text="ok thanks", client_context="x")

    assert result.facts == []
