"""Comandos de voz para leitura das principais notícias em tempo real."""

from __future__ import annotations

from jarvis.commands.registry import Command, CommandContext, Outcome
from jarvis.services.news_service import NewsService

_news = NewsService()


def _tell_news(ctx: CommandContext, _utterance: str) -> Outcome:
    report = _news.get_headlines()
    ctx.reply(report)
    return Outcome.CONTINUE


def news_commands() -> list[Command]:
    """Retorna comandos de notícias e acontecimentos do mundo."""
    return [
        Command(
            "noticias",
            (
                "quais as noticias", "principais noticias", "noticias do dia",
                "noticias de hoje", "manchetes", "o que esta acontecendo no mundo",
                "me conte as noticias", "ultimas noticias", "noticias",
            ),
            _tell_news,
        ),
    ]
