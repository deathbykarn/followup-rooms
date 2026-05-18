from unittest.mock import MagicMock

from app.ai.extraction import ExtractionResult
from app.ai.matching import MatchAction, MatchDecision
from app.ai.profile import ProfileResult
from app.models.fact import ExtractedFact, SourceSpan
from app.services.extraction_pipeline import ExtractionPipeline


def _make_extracted() -> ExtractedFact:
    return ExtractedFact(
        type="property_preference",
        value="Marine Parade preferred",
        confidence_score=0.9,
        visibility="operator_only",
        source_spans=[SourceSpan(event_id="evt-1", snippet="wants Marine Parade")],
    )


def test_pipeline_extract_and_persist_inserts_event_then_facts_then_regenerates_profile():
    fake_supabase = MagicMock()
    fake_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "evt-1"}],
    )
    fake_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[]
    )
    fake_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data={"client_name": "Sarah", "short_context": "HDB upgrade"}
    )

    fake_extraction = MagicMock()
    fake_extraction.extract.return_value = ExtractionResult(facts=[_make_extracted()])

    fake_matching = MagicMock()
    fake_matching.decide.return_value = MatchDecision(action=MatchAction.ADD)

    fake_profile = MagicMock()
    fake_profile.regenerate.return_value = ProfileResult(markdown="## Identity\nSarah")

    pipeline = ExtractionPipeline(
        supabase=fake_supabase,
        extraction=fake_extraction,
        matching=fake_matching,
        profile=fake_profile,
    )

    result = pipeline.ingest_and_extract(
        operator_id="op-1",
        client_id="cli-1",
        source_type="manual_note",
        raw_text="Sarah wants Marine Parade because parents nearby.",
    )

    assert result.event_id == "evt-1"
    assert result.facts_added == 1
    assert result.facts_updated == 0
    assert result.facts_noop == 0
    assert fake_profile.regenerate.call_count == 2


def test_pipeline_noop_extraction_still_records_event_but_skips_profile():
    fake_supabase = MagicMock()
    fake_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "evt-1"}],
    )

    fake_extraction = MagicMock()
    fake_extraction.extract.return_value = ExtractionResult(facts=[])

    fake_matching = MagicMock()
    fake_profile = MagicMock()

    pipeline = ExtractionPipeline(
        supabase=fake_supabase,
        extraction=fake_extraction,
        matching=fake_matching,
        profile=fake_profile,
    )

    result = pipeline.ingest_and_extract(
        operator_id="op-1",
        client_id="cli-1",
        source_type="manual_note",
        raw_text="ok thanks",
    )

    assert result.event_id == "evt-1"
    assert result.facts_added == 0
    assert fake_profile.regenerate.call_count == 0
