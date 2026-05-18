"""
TranscriptionService — thin wrapper that swaps providers per config.

Phase 3 ships with AssemblyAI. Pattern 20 (Vendor Agnostic): adding a
Whisper / Deepgram path is a constructor swap, not a refactor.
"""
from typing import Protocol

from app.ai.providers.assemblyai import AssemblyAIProvider, TranscriptionResult


class TranscriptionProvider(Protocol):
    def transcribe(self, audio_url: str, diarize: bool = True) -> TranscriptionResult: ...


class TranscriptionService:
    def __init__(self, provider: TranscriptionProvider | None = None) -> None:
        self._provider = provider or AssemblyAIProvider()

    def transcribe(self, audio_url: str, diarize: bool) -> TranscriptionResult:
        return self._provider.transcribe(audio_url, diarize=diarize)
