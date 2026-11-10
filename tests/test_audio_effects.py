"""Testes unitários para geração e reprodução de efeitos sonoros Stark."""

from __future__ import annotations

from pathlib import Path
import pytest

from jarvis.services.audio_effects import StarkSoundPlayer, generate_sound_effects


@pytest.fixture
def sounds_dir(tmp_path: Path) -> Path:
    target = tmp_path / "sounds"
    generate_sound_effects(target)
    return target


def test_generate_sound_effects_creates_wav_files(sounds_dir: Path) -> None:
    boot_wav = sounds_dir / "stark_boot.wav"
    wake_wav = sounds_dir / "stark_wake.wav"
    ping_wav = sounds_dir / "stark_ping.wav"

    assert boot_wav.exists()
    assert boot_wav.stat().st_size > 100
    assert wake_wav.exists()
    assert wake_wav.stat().st_size > 100
    assert ping_wav.exists()
    assert ping_wav.stat().st_size > 100


def test_stark_sound_player_methods(sounds_dir: Path) -> None:
    player = StarkSoundPlayer(sounds_dir, enabled=False)  # enabled=False para não emitir som no teste
    # Verifica que chamadas não disparam exceções
    player.play_boot()
    player.play_wake()
    player.play_ping()
