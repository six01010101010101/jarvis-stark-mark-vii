"""Comandos de diagnóstico e telemetria de hardware da máquina no estilo Stark."""

from __future__ import annotations

from jarvis.commands.registry import Command, CommandContext, Outcome
from jarvis.services.telemetry import SystemTelemetry

_telemetry = SystemTelemetry()


def _full_status(ctx: CommandContext, _utterance: str) -> Outcome:
    report = _telemetry.get_full_report()
    ctx.reply(report)
    return Outcome.CONTINUE


def _ram_status(ctx: CommandContext, _utterance: str) -> Outcome:
    total, used, free = _telemetry.get_memory_status()
    ctx.reply(f"A memória física está com {used} gigabytes em uso e {free} gigabytes livres de {total} gigabytes no total, senhor.")
    return Outcome.CONTINUE


def _disk_status(ctx: CommandContext, _utterance: str) -> Outcome:
    total, _, free = _telemetry.get_disk_status()
    ctx.reply(f"A partição primária C dispõe de {free} gigabytes livres de uma capacidade total de {total} gigabytes, senhor.")
    return Outcome.CONTINUE


def _power_status(ctx: CommandContext, _utterance: str) -> Outcome:
    status = _telemetry.get_power_status()
    ctx.reply(f"Os circuitos de alimentação acusam estado de {status}, senhor.")
    return Outcome.CONTINUE


def _uptime_status(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply(f"O computador está em atividade ininterrupta há {_telemetry.get_uptime()}, senhor.")
    return Outcome.CONTINUE


def telemetry_commands() -> list[Command]:
    """Retorna comandos de diagnóstico de hardware e status da máquina."""
    return [
        Command("status_geral", ("status do sistema", "diagnostico do computador", "status da maquina", "saude do pc", "telemetria", "diagnostico"), _full_status),
        Command("uptime", ("tempo de atividade", "quanto tempo ligado", "tempo ligado", "uptime"), _uptime_status),
        Command("memoria_ram", ("memoria ram", "quanto de memoria", "uso de ram", "memoria livre"), _ram_status),
        Command("espaco_disco", ("espaco em disco", "espaco livre", "armazenamento", "disco c"), _disk_status),
        Command("bateria_energia", ("status da bateria", "nivel da bateria", "energia do computador"), _power_status),
    ]

