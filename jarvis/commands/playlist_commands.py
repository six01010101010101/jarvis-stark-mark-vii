"""Comandos de reprodução de playlists temáticas (Foco, Treino e Estudo)."""

from __future__ import annotations

from jarvis.commands.registry import Command, CommandContext, Outcome

PLAYLIST_URLS = {
    "foco": "https://www.youtube.com/results?search_query=lofi+hip+hop+radio+beats+to+relax+study+to",
    "treino": "https://www.youtube.com/results?search_query=workout+motivation+music+gym",
    "estudo": "https://www.youtube.com/results?search_query=classical+music+for+studying+piano",
}


def _play_theme(theme: str) -> Command:
    def handler(ctx: CommandContext, _utterance: str) -> Outcome:
        url = PLAYLIST_URLS[theme]
        ctx.launcher.open_url(url)
        ctx.reply(f"Iniciando playlist de {theme} no YouTube, senhor.")
        return Outcome.CONTINUE

    triggers = {
        "foco": ("playlist de foco", "musica para foco", "musica de foco", "lofi"),
        "treino": ("playlist de treino", "musica de treino", "musica para malhar", "playlist de academia"),
        "estudo": ("playlist de estudo", "musica para estudar", "musica de estudo"),
    }[theme]

    return Command(f"playlist_{theme}", triggers, handler)


def playlist_commands() -> list[Command]:
    """Retorna comandos de playlists temáticas."""
    return [
        _play_theme("foco"),
        _play_theme("treino"),
        _play_theme("estudo"),
    ]
