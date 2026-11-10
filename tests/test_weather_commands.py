"""Testes unitários para comandos meteorológicos e extração de cidades."""

from __future__ import annotations

from jarvis.commands import Outcome, build_registry
from jarvis.commands.weather_commands import _extract_city
from tests.fakes import make_context


def test_extract_city_from_phrases() -> None:
    assert _extract_city("como esta o tempo em Sao Paulo") == "Sao Paulo"
    assert _extract_city("temperatura no Rio de Janeiro") == "Rio De Janeiro"
    assert _extract_city("qual o clima em Curitiba") == "Curitiba"
    assert _extract_city("como ta o tempo hoje") is None


def test_weather_commands_match_and_dispatch() -> None:
    ctx = make_context()
    registry = build_registry()

    # Previsão do tempo
    outcome_forecast = registry.dispatch(ctx, "previsao do tempo para amanha")
    assert outcome_forecast is Outcome.CONTINUE
    assert len(ctx.speaker.spoken) >= 1  # type: ignore[attr-defined]

    # Clima atual
    outcome_current = registry.dispatch(ctx, "qual a temperatura agora")
    assert outcome_current is Outcome.CONTINUE
    assert len(ctx.speaker.spoken) >= 2  # type: ignore[attr-defined]
