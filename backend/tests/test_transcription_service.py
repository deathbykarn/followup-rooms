from unittest.mock import MagicMock

from app.ai.providers.assemblyai import SpeakerTurn, TranscriptionResult
from app.services.transcription import TranscriptionService


def test_transcribe_passes_through_to_provider():
    fake_provider = MagicMock()
    fake_provider.transcribe.return_value = TranscriptionResult(
        text="hello sarah",
        language="en",
        duration_seconds=42,
    )
    svc = TranscriptionService(provider=fake_provider)

    result = svc.transcribe("https://signed-url", diarize=False)

    assert result.text == "hello sarah"
    assert result.language == "en"
    assert result.duration_seconds == 42
    fake_provider.transcribe.assert_called_once_with("https://signed-url", diarize=False)


def test_diarize_true_returns_speaker_turns():
    fake_provider = MagicMock()
    fake_provider.transcribe.return_value = TranscriptionResult(
        text="A: hi\nB: hello",
        language="en",
        duration_seconds=10,
        speaker_turns=[
            SpeakerTurn(speaker="A", text="hi", start_ms=0, end_ms=500),
            SpeakerTurn(speaker="B", text="hello", start_ms=600, end_ms=1100),
        ],
    )
    svc = TranscriptionService(provider=fake_provider)

    result = svc.transcribe("https://signed", diarize=True)
    assert len(result.speaker_turns) == 2
    assert result.speaker_turns[0].speaker == "A"
    assert result.speaker_turns[1].text == "hello"


def test_diarize_false_returns_empty_turns():
    fake_provider = MagicMock()
    fake_provider.transcribe.return_value = TranscriptionResult(
        text="solo memo",
        language="en",
        duration_seconds=30,
        speaker_turns=[],
    )
    svc = TranscriptionService(provider=fake_provider)

    result = svc.transcribe("https://signed", diarize=False)
    assert result.speaker_turns == []
