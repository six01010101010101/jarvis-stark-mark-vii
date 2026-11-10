"""Testes unitários dos sintetizadores de voz (NeuralSpeaker e NativeWindowsSpeaker)."""

from __future__ import annotations

from unittest.mock import MagicMock

from jarvis.services.neural_speaker import NeuralSpeaker
from jarvis.speech.tts import NativeWindowsSpeaker, build_speaker


def test_build_speaker_returns_neural_speaker() -> None:
    on_start = MagicMock()
    on_end = MagicMock()
    speaker = build_speaker(on_start, on_end)
    assert isinstance(speaker, NeuralSpeaker)


def test_native_speaker_profile_switching() -> None:
    speaker = NativeWindowsSpeaker(MagicMock(), MagicMock())
    speaker.set_voice("female")
    assert speaker.get_voice() == "Maria (Feminina)"

    speaker.set_voice("male")
    assert speaker.get_voice() == "Daniel (Masculina)"


def test_neural_speaker_profile_switching() -> None:
    native = NativeWindowsSpeaker(MagicMock(), MagicMock())
    speaker = NeuralSpeaker(native, MagicMock(), MagicMock())
    speaker.set_voice("female")
    assert "Francisca" in speaker.get_voice()

    speaker.set_voice("male")
    assert "Antonio" in speaker.get_voice()


def test_native_speaker_empty_string_no_crash() -> None:
    on_start = MagicMock()
    on_end = MagicMock()
    speaker = NativeWindowsSpeaker(on_start, on_end)
    speaker.say("   ")
    on_start.assert_not_called()
    on_end.assert_not_called()


def test_neural_speaker_empty_string_no_crash() -> None:
    native = MagicMock()
    on_start = MagicMock()
    on_end = MagicMock()
    speaker = NeuralSpeaker(native, on_start, on_end)
    speaker.say("   ")
    on_start.assert_not_called()
    on_end.assert_not_called()
    native.say.assert_not_called()


def test_native_speaker_triggers_start_and_end_callbacks() -> None:
    on_start = MagicMock()
    on_end = MagicMock()
    speaker = NativeWindowsSpeaker(on_start, on_end)
    speaker._voice = MagicMock()
    speaker.say("Olá senhor Ken")

    on_start.assert_called_once()
    on_end.assert_called_once()
    speaker._voice.Speak.assert_called_once_with("Olá senhor Ken", 0)
