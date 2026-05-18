import pytest
from pydantic import ValidationError

from app.models.fact import ExtractedFact, FactStanceUpdate, SourceSpan


def test_source_span_requires_event_id_and_snippet():
    s = SourceSpan(event_id="evt-1", snippet="wants Marine Parade")
    assert s.event_id == "evt-1"
    assert s.snippet == "wants Marine Parade"


def test_extracted_fact_requires_at_least_one_source_span():
    with pytest.raises(ValidationError):
        ExtractedFact(
            type="property_preference",
            value="Marine Parade",
            confidence_score=0.85,
            visibility="operator_only",
            source_spans=[],
        )


def test_extracted_fact_rejects_invalid_type():
    with pytest.raises(ValidationError):
        ExtractedFact(
            type="not_a_real_type",
            value="x",
            confidence_score=0.5,
            visibility="operator_only",
            source_spans=[SourceSpan(event_id="evt-1", snippet="x")],
        )


def test_extracted_fact_confidence_must_be_0_to_1():
    with pytest.raises(ValidationError):
        ExtractedFact(
            type="goal",
            value="x",
            confidence_score=1.5,
            visibility="operator_only",
            source_spans=[SourceSpan(event_id="evt-1", snippet="x")],
        )


def test_fact_stance_update_validates_stance_enum():
    with pytest.raises(ValidationError):
        FactStanceUpdate(stance="invalid")
    valid = FactStanceUpdate(stance="accepted")
    assert valid.stance == "accepted"


def test_fact_stance_update_optional_value_override():
    u = FactStanceUpdate(stance="reframed", value="Wife prefers Marine Parade only")
    assert u.value == "Wife prefers Marine Parade only"
