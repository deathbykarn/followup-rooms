"""
IngestionWorker — async pipeline orchestrator for transcript/voice uploads.

State machine walked by run(job_id):

    queued
       └─► transcribing (audio only)
              └─► extracting
                     └─► done
       └─► extracting (text transcript path — skip transcription)
              └─► done

    Any step that throws → state=failed with error_message + error_code.

The job row is the durability boundary — if the BackgroundTask itself
dies mid-flight (Render restart, OOM), the row stays at its last set
state. A future watchdog (Plan 3.5) surfaces stuck jobs for retry.

Service-role supabase client is required (writes bypass RLS; operator_id
is enforced via the job row's operator_id field).
"""
from collections import Counter
from datetime import UTC, datetime
from typing import Any

from supabase import Client

from app.ai.providers.assemblyai import SpeakerTurn, TranscriptionResult
from app.services.extraction_pipeline import ExtractionPipeline
from app.services.storage import StorageService
from app.services.transcription import TranscriptionService

AUDIO_MIME_PREFIX = "audio/"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _format_speaker_summary(turns: list[SpeakerTurn]) -> str | None:
    """Word counts per speaker — used by the extraction prompt to identify
    the operator (most-words heuristic). Returns None for empty input."""
    if not turns:
        return None
    counts: Counter[str] = Counter()
    for turn in turns:
        counts[turn.speaker] += len(turn.text.split())
    parts = [f"Speaker {speaker}: {n} words" for speaker, n in counts.most_common()]
    return " / ".join(parts)


def _format_speaker_transcript(turns: list[SpeakerTurn], fallback_text: str) -> str:
    """Render diarized utterances as `Speaker X: text` lines. Falls back
    to the flat transcript text if no turns are available."""
    if not turns:
        return fallback_text
    return "\n".join(f"Speaker {t.speaker}: {t.text}" for t in turns)


class IngestionFailure(Exception):
    """Internal exception with a machine-readable error_code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class IngestionWorker:
    """Walks one ingestion_jobs row through transcribe → extract → done."""

    def __init__(
        self,
        supabase: Client,
        storage: StorageService | None = None,
        transcription: TranscriptionService | None = None,
        pipeline: ExtractionPipeline | None = None,
    ) -> None:
        self._db = supabase
        self._storage = storage or StorageService(supabase)
        self._transcription = transcription or TranscriptionService()
        self._pipeline = pipeline or ExtractionPipeline(supabase)

    def run(self, job_id: str) -> None:
        job = self._fetch_job(job_id)
        try:
            transcript_text, speaker_labels, meta = self._produce_transcript(job, job_id)

            self._update_job(
                job_id,
                transcript_text=transcript_text,
                transcription_metadata=meta,
            )

            event_id = self._insert_event(job, transcript_text)
            self._update_job(job_id, event_id=event_id)

            self._set_state(job_id, "extracting")
            self._pipeline.extract_for_event(
                operator_id=job["operator_id"],
                client_id=job["client_id"],
                event_id=event_id,
                raw_text=transcript_text,
                speaker_labels=speaker_labels,
            )

            self._set_state(job_id, "done", completed_at=_now_iso())
        except IngestionFailure as exc:
            self._set_state(
                job_id, "failed",
                error_message=exc.message[:500],
                error_code=exc.code,
                completed_at=_now_iso(),
            )
            raise
        except Exception as exc:
            self._set_state(
                job_id, "failed",
                error_message=str(exc)[:500],
                error_code="unknown",
                completed_at=_now_iso(),
            )
            raise

    # --- transcript production ---

    def _produce_transcript(
        self,
        job: dict[str, Any],
        job_id: str,
    ) -> tuple[str, str | None, dict[str, Any]]:
        if (job["mime_type"] or "").startswith(AUDIO_MIME_PREFIX):
            self._set_state(job_id, "transcribing", started_at=_now_iso())
            try:
                signed = self._storage.signed_url(job["storage_path"])
            except Exception as exc:
                raise IngestionFailure("storage_failed", str(exc)) from exc

            try:
                # Multi-party transcripts benefit from diarization; solo
                # voice memos don't (one speaker).
                diarize = job["upload_type"] == "transcript"
                result: TranscriptionResult = self._transcription.transcribe(
                    signed, diarize=diarize,
                )
            except Exception as exc:
                raise IngestionFailure("transcription_failed", str(exc)) from exc

            speaker_labels = _format_speaker_summary(result.speaker_turns)
            transcript_text = _format_speaker_transcript(
                result.speaker_turns, fallback_text=result.text,
            )
            meta = {
                "provider": result.provider,
                "model": result.model,
                "duration_seconds": result.duration_seconds,
                "language": result.language,
                "speaker_count": len({t.speaker for t in result.speaker_turns}),
            }
            return transcript_text, speaker_labels, meta

        # Text upload path — download bytes, decode, done.
        if (job["upload_type"] or "") != "transcript":
            raise IngestionFailure(
                "unknown",
                f"voice_memo upload had non-audio mime: {job['mime_type']}",
            )
        try:
            raw = self._storage.download(job["storage_path"])
        except Exception as exc:
            raise IngestionFailure("storage_failed", str(exc)) from exc

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise IngestionFailure(
                "unknown",
                f"transcript file is not UTF-8 text: {exc}",
            ) from exc

        return text, None, {"provider": "text_upload"}

    # --- DB helpers ---

    def _fetch_job(self, job_id: str) -> dict[str, Any]:
        resp = (
            self._db.table("ingestion_jobs")
            .select("*")
            .eq("id", job_id)
            .maybe_single()
            .execute()
        )
        if not resp or not resp.data:
            raise IngestionFailure("unknown", f"ingestion_job {job_id} not found")
        return resp.data

    def _set_state(
        self,
        job_id: str,
        state: str,
        *,
        started_at: str | None = None,
        completed_at: str | None = None,
        error_message: str | None = None,
        error_code: str | None = None,
    ) -> None:
        payload: dict[str, Any] = {"state": state}
        if started_at is not None:
            payload["started_at"] = started_at
        if completed_at is not None:
            payload["completed_at"] = completed_at
        if error_message is not None:
            payload["error_message"] = error_message
        if error_code is not None:
            payload["error_code"] = error_code
        self._db.table("ingestion_jobs").update(payload).eq("id", job_id).execute()

    def _update_job(self, job_id: str, **fields: Any) -> None:
        self._db.table("ingestion_jobs").update(fields).eq("id", job_id).execute()

    def _insert_event(self, job: dict[str, Any], raw_text: str) -> str:
        source_type = (
            "meeting_transcript" if job["upload_type"] == "transcript" else "voice_memo"
        )
        resp = (
            self._db.table("events")
            .insert({
                "operator_id": job["operator_id"],
                "client_id": job["client_id"],
                "source_type": source_type,
                "raw_text": raw_text,
            })
            .execute()
        )
        return resp.data[0]["id"]
