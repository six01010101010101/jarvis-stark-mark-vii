"""Testes unitários para o motor de voz neural do Jarvis (Edge-TTS)."""

from __future__ import annotations

import pytest

from jarvis.services.neural_speaker import NeuralSpeaker
from tests.fakes import FakeSpeaker


def test_neural_speaker_profile_switching() -> None:
    fallback = FakeSpeaker()
    speaker = NeuralSpeaker(
        fallback=fallback,
        on_start=lambda: None,
        on_end=lambda: None,
    )

    # Padrão é a voz sofisticada do Jarvis (Antonio)
    assert "Antonio" in speaker.get_voice() or "Jarvis" in speaker.get_voice()

    # Alterna para a voz britânica de cinema (Paul Bettany / Ryan)
    speaker.set_voice("cinema")
    assert "Ryan" in speaker.get_voice() or "Inglês" in speaker.get_voice()

    # Alterna para voz feminina
    speaker.set_voice("female")
    assert "Feminina" in speaker.get_voice()

    # Retorna para português do Jarvis
    speaker.set_voice("male")
    assert "Antonio" in speaker.get_voice() or "Jarvis" in speaker.get_voice()
