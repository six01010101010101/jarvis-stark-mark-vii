"""Comandos de localização geográfica e informações de rede."""

from __future__ import annotations

from jarvis.commands.registry import Command, CommandContext, Outcome
from jarvis.services.location_service import LocationService

_location = LocationService()


def _where_are_we(ctx: CommandContext, _utterance: str) -> Outcome:
    report = _location.get_location_report()
    ctx.reply(report)
    return Outcome.CONTINUE


def _ip_address(ctx: CommandContext, _utterance: str) -> Outcome:
    report = _location.get_ip_report()
    ctx.reply(report)
    return Outcome.CONTINUE


def location_commands() -> list[Command]:
    """Retorna comandos de localização e endereço IP."""
    return [
        Command(
            "onde_estamos",
            (
                "onde estamos", "onde voce esta", "onde eu estou", "qual nossa localizacao",
                "minha localizacao", "qual cidade", "em que cidade estamos",
            ),
            _where_are_we,
        ),
        Command("meu_ip", ("qual meu ip", "meu ip", "qual o ip", "qual e o ip", "endereco ip"), _ip_address),
    ]
