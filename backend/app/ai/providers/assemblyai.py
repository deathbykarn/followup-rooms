"""
AssemblyAI provider for the transcription role.

Universal-2 speech model + native speaker diarization. We hand AssemblyAI
a signed URL to the Supabase-stored audio rather than streaming bytes
through our backend — keeps memory low on Render and matches AssemblyAI's
recommended pre-recorded ingestion pattern.

Pattern 20 (Vendor Agnostic): this provider is thin; the rest of the
codebase talks to TranscriptionService which can swap providers via config.
"""
from dataclasses import dataclass, field

import assemblyai as aai

from app.core.config import get_settings


@dataclass
class SpeakerTurn:
    """One contiguous utterance by a single speaker."""

    speaker: str          # 'A', 'B', 'C', ...
    text: str
    start_ms: int
    end_ms: int


@dataclass
class TranscriptionResult:
    text: str
    language: str | None
    duration_seconds: int | None
    speaker_turns: list[SpeakerTurn] = field(default_factory=list)
    provider: str = "assemblyai"
    model: str = "universal-2"


class AssemblyAIProvider:
    """Real AssemblyAI transcription. Construct lazily so import doesn't require env."""

    def __init__(self) -> None:
        aai.settings.api_key = get_settings().assemblyai_api_key
        self._transcriber = aai.Transcriber()

    def transcribe(self, audio_url: str, diarize: bool = True) -> TranscriptionResult:
        """
        Transcribe an audio file at `audio_url` (typically a signed Supabase URL).
        When `diarize=True`, returns speaker_turns; otherwise turns is empty.
        Raises RuntimeError on AssemblyAI-side failure.
        """
        config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.universal,
            speaker_labels=diarize,
            language_detection=True,
        )
        transcript = self._transcriber.transcribe(audio_url, config=config)

        if transcript.status == aai.TranscriptStatus.error:
            raise RuntimeError(f"AssemblyAI transcription failed: {transcript.error}")

        turns: list[SpeakerTurn] = []
        if diarize and transcript.utterances:
            turns = [
                SpeakerTurn(
                    speaker=u.speaker,
                    text=u.text,
                    start_ms=u.start,
                    end_ms=u.end,
                )
                for u in transcript.utterances
            ]

        # AssemblyAI returns detected language inside json_response when
        # language_detection is on. Fall back to None if absent.
        language = None
        if transcript.json_response:
            language = transcript.json_response.get("language_code")

        duration = int(transcript.audio_duration) if transcript.audio_duration else None

        return TranscriptionResult(
            text=transcript.text or "",
            language=language,
            duration_seconds=duration,
            speaker_turns=turns,
        )
