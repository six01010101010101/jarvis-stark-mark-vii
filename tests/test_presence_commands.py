"""Testes unitários dos comandos de presença, prontidão e saudações em tempo real."""

from __future__ import annotations

from jarvis.commands import Outcome, build_registry
from tests.fakes import make_context


def test_presence_check_answers_immediately() -> None:
    ctx = make_context()
    registry = build_registry()

    outcome = registry.dispatch(ctx, "jarvis voce ta ai")
    assert outcome is Outcome.CONTINUE
    spoken = ctx.speaker.spoken[-1]  # type: ignore[attr-defined]
    assert "senhor Ken" in spoken
    assert "online" in spoken


def test_hearing_check_answers_immediately() -> None:
    ctx = make_context()
    registry = build_registry()

    outcome = registry.dispatch(ctx, "esta me ouvindo")
    assert outcome is Outcome.CONTINUE
    spoken = ctx.speaker.spoken[-1]  # type: ignore[attr-defined]
    assert "senhor Ken" in spoken


def test_night_greeting_acknowledges_time() -> None:
    ctx = make_context()
    registry = build_registry()

    outcome = registry.dispatch(ctx, "boa noite jarvis")
    assert outcome is Outcome.CONTINUE
    spoken = ctx.speaker.spoken[-1]  # type: ignore[attr-defined]
    assert "Boa noite, senhor Ken" in spoken
    assert "madrugada" in spoken


def test_day_greeting_acknowledges_time() -> None:
    ctx = make_context()
    registry = build_registry()

    outcome = registry.dispatch(ctx, "bom dia jarvis")
    assert outcome is Outcome.CONTINUE
    spoken = ctx.speaker.spoken[-1]  # type: ignore[attr-defined]
    assert "Bom dia, senhor Ken" in spoken


def test_status_inquiry_answers_with_stark_personality() -> None:
    ctx = make_context()
    registry = build_registry()

    outcome = registry.dispatch(ctx, "como vai voce")
    assert outcome is Outcome.CONTINUE
    spoken = ctx.speaker.spoken[-1]  # type: ignore[attr-defined]
    assert "senhor Ken" in spoken
    assert "potência máxima" in spoken
