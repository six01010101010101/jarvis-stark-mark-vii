"""Testes unitários do fluxo contínuo de áudio e medidor de RMS."""

from __future__ import annotations

import struct

from jarvis.speech.audio_stream import (
    AudioDeviceInfo,
    compute_rms,
    list_input_devices,
    pick_default_device_index,
)


def test_compute_rms_silence() -> None:
    silence = b"\x00" * 2048
    assert compute_rms(silence) == 0


def test_compute_rms_sine_wave() -> None:
    # Buffer com amplitude 500
    samples = [500 if i % 2 == 0 else -500 for i in range(1024)]
    data = struct.pack(f"<{len(samples)}h", *samples)
    rms = compute_rms(data)
    assert 490 <= rms <= 510


def test_pick_default_device_prioritizes_real_microphones() -> None:
    devices = [
        AudioDeviceInfo(index=0, name="Mapeador de som da Microsoft", sample_rate=16000, channels=2),
        AudioDeviceInfo(index=1, name="Mixagem estéreo (Realtek)", sample_rate=44100, channels=2),
        AudioDeviceInfo(index=2, name="Microfone (Realtek High Definition Audio)", sample_rate=48000, channels=1),
        AudioDeviceInfo(index=3, name="Steam Streaming Microphone", sample_rate=48000, channels=1),
    ]

    chosen = pick_default_device_index(devices)
    assert chosen == 2  # Deve escolher o microfone físico real!


def test_list_input_devices_returns_list() -> None:
    # Verifica que a enumeração de dispositivos funciona sem levantar exceções
    devs = list_input_devices()
    assert isinstance(devs, list)
