"""Pipeline seguro para integração de captura de voz com desempacotamento de áudio."""

from __future__ import annotations

from typing import TYPE_CHECKING
from jarvis.commands import Outcome
from jarvis.speech.transcriber import unpack_transcription

if TYPE_CHECKING:
    from jarvis.assistant import Assistant


class RobustVoicePipeline:
    """Encaminha o resultado da transcrição para o processador de frases do assistente."""

    def __init__(self, assistant: Assistant) -> None:
        self.assistant = assistant

    def on_audio_captured(self, raw_result: object) -> Outcome:
        text, _ = unpack_transcription(raw_result)
        return self.assistant.handle_phrase(text) if text else Outcome.CONTINUE
