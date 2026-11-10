"""Testes unitários para comandos de localização, temporizadores e notícias."""

from __future__ import annotations

from jarvis.commands import Outcome, build_registry
from jarvis.commands.timer_commands import _parse_duration
from tests.fakes import make_context


def test_timer_duration_parsing() -> None:
    secs, label = _parse_duration("temporizador de 5 minutos")
    assert secs == 300
    assert label == "5 minutos"

    secs_sec, label_sec = _parse_duration("timer de 45 segundos")
    assert secs_sec == 45
    assert label_sec == "45 segundos"

    secs_h, label_h = _parse_duration("alarme de 2 horas")
    assert secs_h == 7200
    assert label_h == "2 horas"


def test_timer_commands_dispatch() -> None:
    ctx = make_context()
    registry = build_registry()

    outcome = registry.dispatch(ctx, "definir temporizador de 1 minuto")
    assert outcome is Outcome.CONTINUE
    assert "temporizador" in ctx.speaker.spoken[-1].lower()  # type: ignore[attr-defined]

    outcome_cancel = registry.dispatch(ctx, "cancelar temporizador")
    assert outcome_cancel is Outcome.CONTINUE
    assert "cancelado" in ctx.speaker.spoken[-1].lower()  # type: ignore[attr-defined]


def test_location_commands_dispatch() -> None:
    ctx = make_context()
    registry = build_registry()

    outcome = registry.dispatch(ctx, "onde estamos")
    assert outcome is Outcome.CONTINUE
    assert len(ctx.speaker.spoken) >= 1  # type: ignore[attr-defined]

    outcome_ip = registry.dispatch(ctx, "qual meu ip")
    assert outcome_ip is Outcome.CONTINUE
    assert len(ctx.speaker.spoken) >= 2  # type: ignore[attr-defined]


def test_news_commands_dispatch() -> None:
    ctx = make_context()
    registry = build_registry()

    outcome = registry.dispatch(ctx, "quais as noticias de hoje")
    assert outcome is Outcome.CONTINUE
    assert len(ctx.speaker.spoken) >= 1  # type: ignore[attr-defined]
