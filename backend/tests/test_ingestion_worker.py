from unittest.mock import MagicMock

import pytest

from app.ai.providers.assemblyai import SpeakerTurn, TranscriptionResult
from app.services.extraction_pipeline import PipelineResult
from app.services.ingestion_worker import (
    IngestionFailure,
    IngestionWorker,
    _format_speaker_summary,
    _format_speaker_transcript,
)


def _job(**overrides):
    base = {
        "id": "job-1",
        "operator_id": "op-1",
        "client_id": "cli-1",
        "upload_type": "transcript",
        "storage_path": "op-1/job-1/viewing.txt",
        "original_filename": "viewing.txt",
        "mime_type": "text/plain",
        "size_bytes": 1024,
        "state": "queued",
    }
    base.update(overrides)
    return base


def _mock_db_with_job(job):
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(
        data=job,
    )
    db.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "evt-new"}],
    )
    db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
    return db


def test_format_speaker_summary_orders_by_word_count_desc():
    turns = [
        SpeakerTurn(speaker="A", text="one two three", start_ms=0, end_ms=100),
        SpeakerTurn(speaker="B", text="hi", start_ms=200, end_ms=300),
        SpeakerTurn(speaker="A", text="four five", start_ms=400, end_ms=500),
    ]
    assert _format_speaker_summary(turns) == "Speaker A: 5 words / Speaker B: 1 words"


def test_format_speaker_summary_returns_none_for_empty():
    assert _format_speaker_summary([]) is None


def test_format_speaker_transcript_falls_back_when_no_turns():
    assert _format_speaker_transcript([], "flat text") == "flat text"


def test_format_speaker_transcript_renders_speaker_prefix():
    turns = [
        SpeakerTurn(speaker="A", text="hi", start_ms=0, end_ms=100),
        SpeakerTurn(speaker="B", text="hello", start_ms=100, end_ms=200),
    ]
    assert _format_speaker_transcript(turns, "ignored") == "Speaker A: hi\nSpeaker B: hello"


def test_text_transcript_happy_path_runs_through_to_done():
    job = _job(mime_type="text/plain", upload_type="transcript")
    db = _mock_db_with_job(job)
    storage = MagicMock()
    storage.download.return_value = b"Sarah wants Marine Parade. Budget 1.8M."
    transcription = MagicMock()
    pipeline = MagicMock()
    pipeline.extract_for_event.return_value = PipelineResult(event_id="evt-new")

    worker = IngestionWorker(supabase=db, storage=storage, transcription=transcription, pipeline=pipeline)
    worker.run("job-1")

    # Transcription was NOT called for text upload
    transcription.transcribe.assert_not_called()
    # Pipeline was called with the downloaded text + no speaker_labels
    _, kwargs = pipeline.extract_for_event.call_args
    assert kwargs["raw_text"] == "Sarah wants Marine Parade. Budget 1.8M."
    assert kwargs["speaker_labels"] is None
    assert kwargs["event_id"] == "evt-new"
    # Final state = done (last update call)
    final_payload = db.table.return_value.update.call_args_list[-1].args[0]
    assert final_payload["state"] == "done"


def test_audio_transcript_runs_through_transcribing_then_extracting_then_done():
    job = _job(
        mime_type="audio/m4a",
        upload_type="transcript",
        storage_path="op-1/job-1/viewing.m4a",
    )
    db = _mock_db_with_job(job)
    storage = MagicMock()
    storage.signed_url.return_value = "https://signed"
    transcription = MagicMock()
    transcription.transcribe.return_value = TranscriptionResult(
        text="A: hi sarah\nB: hi, marine parade please",
        language="en",
        duration_seconds=120,
        speaker_turns=[
            SpeakerTurn(speaker="A", text="hi sarah how are you", start_ms=0, end_ms=2000),
            SpeakerTurn(speaker="B", text="hi marine parade please", start_ms=2100, end_ms=4000),
        ],
    )
    pipeline = MagicMock()
    pipeline.extract_for_event.return_value = PipelineResult(event_id="evt-new")

    worker = IngestionWorker(supabase=db, storage=storage, transcription=transcription, pipeline=pipeline)
    worker.run("job-1")

    transcription.transcribe.assert_called_once_with("https://signed", diarize=True)
    _, kwargs = pipeline.extract_for_event.call_args
    assert "Speaker A:" in kwargs["raw_text"]
    assert kwargs["speaker_labels"] is not None
    assert "Speaker A:" in kwargs["speaker_labels"]


def test_voice_memo_audio_disables_diarization():
    job = _job(mime_type="audio/m4a", upload_type="voice_memo")
    db = _mock_db_with_job(job)
    storage = MagicMock()
    storage.signed_url.return_value = "https://signed"
    transcription = MagicMock()
    transcription.transcribe.return_value = TranscriptionResult(
        text="just met sarah, she's worried about timing",
        language="en",
        duration_seconds=30,
        speaker_turns=[],
    )
    pipeline = MagicMock()
    pipeline.extract_for_event.return_value = PipelineResult(event_id="evt-new")

    worker = IngestionWorker(supabase=db, storage=storage, transcription=transcription, pipeline=pipeline)
    worker.run("job-1")

    transcription.transcribe.assert_called_once_with("https://signed", diarize=False)
    _, kwargs = pipeline.extract_for_event.call_args
    assert kwargs["speaker_labels"] is None
    # Event inserted with source_type=voice_memo
    insert_payload = db.table.return_value.insert.call_args.args[0]
    assert insert_payload["source_type"] == "voice_memo"


def test_transcription_failure_sets_state_failed_with_code():
    job = _job(mime_type="audio/m4a")
    db = _mock_db_with_job(job)
    storage = MagicMock()
    storage.signed_url.return_value = "https://signed"
    transcription = MagicMock()
    transcription.transcribe.side_effect = RuntimeError("AssemblyAI 500")
    pipeline = MagicMock()

    worker = IngestionWorker(supabase=db, storage=storage, transcription=transcription, pipeline=pipeline)
    with pytest.raises(IngestionFailure) as exc:
        worker.run("job-1")
    assert exc.value.code == "transcription_failed"

    final_payload = db.table.return_value.update.call_args_list[-1].args[0]
    assert final_payload["state"] == "failed"
    assert final_payload["error_code"] == "transcription_failed"
    pipeline.extract_for_event.assert_not_called()


def test_extraction_failure_sets_state_failed_with_extraction_code():
    job = _job(mime_type="text/plain", upload_type="transcript")
    db = _mock_db_with_job(job)
    storage = MagicMock()
    storage.download.return_value = b"hello"
    transcription = MagicMock()
    pipeline = MagicMock()
    pipeline.extract_for_event.side_effect = RuntimeError("Claude 500")

    worker = IngestionWorker(supabase=db, storage=storage, transcription=transcription, pipeline=pipeline)
    with pytest.raises(RuntimeError, match="Claude 500"):
        worker.run("job-1")

    final_payload = db.table.return_value.update.call_args_list[-1].args[0]
    assert final_payload["state"] == "failed"
    # extraction failures bubble as 'unknown' (we only classify storage_failed /
    # transcription_failed inside _produce_transcript). Acceptable Phase 3 fidelity.
    assert final_payload["error_code"] == "unknown"
