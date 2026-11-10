"""Comandos de voz para consulta de clima, temperatura e previsão do tempo."""

from __future__ import annotations

import re

from jarvis.commands.registry import Command, CommandContext, Outcome
from jarvis.services.weather_service import WeatherService
from jarvis.text_utils import normalize

_weather = WeatherService()


def _extract_city(utterance: str) -> str | None:
    norm = normalize(utterance)
    match = re.search(r"(?:em|de|no|na|para)\s+([a-z\s]+)$", norm)
    if match:
        city = match.group(1).strip()
        ignore = ("amanha", "hoje", "agora", "tarde", "noite")
        if city not in ignore:
            return city.title()
    return None


def _weather_current(ctx: CommandContext, utterance: str) -> Outcome:
    city = _extract_city(utterance)
    report = _weather.get_current_weather(city)
    ctx.reply(report)
    return Outcome.CONTINUE


def _weather_forecast(ctx: CommandContext, utterance: str) -> Outcome:
    city = _extract_city(utterance)
    report = _weather.get_forecast(city)
    ctx.reply(report)
    return Outcome.CONTINUE


def weather_commands() -> list[Command]:
    """Retorna comandos de consulta meteorológica em tempo real."""
    return [
        Command(
            "previsao_tempo",
            (
                "previsao do tempo", "previsao para amanha", "vai chover",
                "previsao de chuva", "previsao meteorologica", "previsao",
            ),
            _weather_forecast,
        ),
        Command(
            "clima_atual",
            (
                "clima", "temperatura", "como esta o tempo", "como ta o tempo",
                "quantos graus", "sensacao termica", "esta calor", "esta frio",
            ),
            _weather_current,
        ),
    ]
