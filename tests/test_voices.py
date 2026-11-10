"""Testes unitários para troca dinâmica de vozes do J.A.R.V.I.S."""

from __future__ import annotations

from dataclasses import dataclass, field
import pytest

from jarvis.commands.voice_commands import voice_commands
from jarvis.commands.registry import Outcome
from tests.fakes import make_context


@dataclass
class FakeSwitchableSpeaker:
    spoken: list[str] = field(default_factory=list)
    current_voice: str = "male"

    def say(self, text: str) -> None:
        self.spoken.append(text)

    def set_voice(self, voice_name: str) -> bool:
        self.current_voice = voice_name
        return True

    def get_voice(self) -> str:
        return self.current_voice


def test_switch_to_female_voice() -> None:
    speaker = FakeSwitchableSpeaker()
    ctx = make_context(speaker=speaker)
    cmd = next(c for c in voice_commands() if c.name == "voice_female")
    assert cmd.matches("mudar voz para feminina")
    assert cmd.matches("usar voz da maria")
    assert cmd.handler(ctx, "mudar voz para feminina") is Outcome.CONTINUE
    assert speaker.current_voice == "female"


def test_switch_to_male_voice() -> None:
    speaker = FakeSwitchableSpeaker(current_voice="female")
    ctx = make_context(speaker=speaker)
    cmd = next(c for c in voice_commands() if c.name == "voice_male")
    assert cmd.matches("mudar voz para masculina")
    assert cmd.matches("usar voz do daniel")
    assert cmd.handler(ctx, "mudar voz para masculina") is Outcome.CONTINUE
    assert speaker.current_voice == "male"
