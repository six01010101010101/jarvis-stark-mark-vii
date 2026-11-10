"""Testes unitários do motor de escuta, fluxo com VU meter e transcrição."""

from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pytest
import speech_recognition as sr

from jarvis.speech.listener import GoogleSpeechListener, MeteredAudioStream


def test_metered_audio_stream_updates_volume() -> None:
    volumes: list[float] = []

    class DummyRawStream:
        def read(self, size: int) -> bytes:
            return b"\x50\x00" * (size // 2)

    dummy = DummyRawStream()
    metered = MeteredAudioStream(dummy, on_volume=volumes.append)

    data = metered.read(512)
    assert len(data) == 512
    assert len(volumes) == 1
    assert volumes[0] > 0.0


def test_listener_initialization_and_thresholds() -> None:
    listener = GoogleSpeechListener(language="pt-BR")
    assert listener._recognizer.energy_threshold >= 45
    assert listener._recognizer.dynamic_energy_threshold is True
    assert listener._language == "pt-BR"
    listener.close()


def test_transcribe_successful_google_stt() -> None:
    listener = GoogleSpeechListener(language="pt-BR")
    audio = sr.AudioData(b"\x00" * 3200, 16000, 2)

    with patch.object(listener._recognizer, "recognize_google", return_value="  jarvis que horas sao  "):
        result = listener._transcribe(audio)
        assert result == "jarvis que horas sao"
    listener.close()


def test_transcribe_unknown_value_error_returns_none() -> None:
    listener = GoogleSpeechListener(language="pt-BR")
    audio = sr.AudioData(b"\x00" * 3200, 16000, 2)

    with patch.object(listener._recognizer, "recognize_google", side_effect=sr.UnknownValueError()):
        result = listener._transcribe(audio)
        assert result is None
    listener.close()


def test_transcribe_request_error_returns_none() -> None:
    listener = GoogleSpeechListener(language="pt-BR")
    audio = sr.AudioData(b"\x00" * 3200, 16000, 2)

    with patch.object(listener._recognizer, "recognize_google", side_effect=sr.RequestError("Network error")):
        result = listener._transcribe(audio)
        assert result is None
    listener.close()


def test_set_device_updates_index() -> None:
    listener = GoogleSpeechListener(language="pt-BR")
    with patch.object(listener, "_init_microphone"):
        listener.set_device(3)
        assert listener._device_index == 3
    listener.close()
