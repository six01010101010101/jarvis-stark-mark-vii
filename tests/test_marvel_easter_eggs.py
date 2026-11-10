"""Testes unitários das falas e protocolos de Tony Stark e J.A.R.V.I.S."""

from __future__ import annotations

from jarvis.commands import Outcome, build_registry
from tests.fakes import make_context


def test_marvel_flight_mode_command() -> None:
    ctx = make_context()
    registry = build_registry()

    outcome = registry.dispatch(ctx, "jarvis protocolo de voo")
    assert outcome is Outcome.CONTINUE
    spoken = ctx.speaker.spoken[-1]  # type: ignore[attr-defined]
    assert "Propulsores" in spoken
    assert "senhor Ken" in spoken


def test_marvel_arc_reactor_command() -> None:
    ctx = make_context()
    registry = build_registry()

    outcome = registry.dispatch(ctx, "status do reator")
    assert outcome is Outcome.CONTINUE
    spoken = ctx.speaker.spoken[-1]  # type: ignore[attr-defined]
    assert "Reator Arc" in spoken
    assert "senhor Ken" in spoken


def test_marvel_run_before_walk_command() -> None:
    ctx = make_context()
    registry = build_registry()

    outcome = registry.dispatch(ctx, "as vezes voce tem que correr")
    assert outcome is Outcome.CONTINUE
    spoken = ctx.speaker.spoken[-1]  # type: ignore[attr-defined]
    assert "correr antes de aprender a andar" in spoken
    assert "senhor Ken" in spoken


def test_marvel_virtual_tour_command() -> None:
    ctx = make_context()
    registry = build_registry()

    outcome = registry.dispatch(ctx, "iniciar passeio virtual")
    assert outcome is Outcome.CONTINUE
    spoken = ctx.speaker.spoken[-1]  # type: ignore[attr-defined]
    assert "ambiente virtual" in spoken
    assert "senhor Ken" in spoken
