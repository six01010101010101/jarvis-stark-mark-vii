"""Montagem do registro de comandos suportados pelo J.A.R.V.I.S."""

from __future__ import annotations

from typing import TYPE_CHECKING

from jarvis.commands.cognitive_commands import cognitive_commands
from jarvis.commands.info_commands import info_commands
from jarvis.commands.location_commands import location_commands
from jarvis.commands.machine_commands import machine_commands
from jarvis.commands.marvel_easter_eggs import marvel_commands
from jarvis.commands.media_commands import media_commands
from jarvis.commands.multimedia_control_commands import multimedia_control_commands
from jarvis.commands.news_commands import news_commands
from jarvis.commands.note_commands import note_commands
from jarvis.commands.playlist_commands import playlist_commands
from jarvis.commands.presence_commands import presence_commands
from jarvis.commands.privacy_commands import privacy_commands
from jarvis.commands.registry import Command, CommandContext, CommandRegistry, Outcome
from jarvis.commands.screen_commands import screen_commands
from jarvis.commands.system_commands import close_commands, system_commands
from jarvis.commands.telemetry_commands import telemetry_commands
from jarvis.commands.timer_commands import timer_commands
from jarvis.commands.user_shortcuts import user_shortcuts
from jarvis.commands.voice_commands import voice_commands
from jarvis.commands.weather_commands import weather_commands

if TYPE_CHECKING:
    from jarvis.services.intent_cache import IntentCache

__all__ = ["Command", "CommandContext", "CommandRegistry", "Outcome", "build_registry"]


def build_registry(cache: IntentCache | None = None) -> CommandRegistry:
    """Cria o registro completo de comandos do J.A.R.V.I.S."""
    registry = CommandRegistry(cache=cache)
    registry.register(
        *user_shortcuts(),
        *presence_commands(),
        *machine_commands(),
        *weather_commands(),
        *news_commands(),
        *location_commands(),
        *timer_commands(),
        *privacy_commands(),
        *voice_commands(),
        *telemetry_commands(),
        *multimedia_control_commands(),
        *screen_commands(),
        *note_commands(),
        *marvel_commands(),
        *playlist_commands(),
        *cognitive_commands(),
        *close_commands(),
        *media_commands(),
        *system_commands(),
        *info_commands(),
    )
    return registry
