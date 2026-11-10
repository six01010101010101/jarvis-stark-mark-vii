"""Comandos de voz para criação e cancelamento de temporizadores e alarmes."""

from __future__ import annotations

import re

from jarvis.commands.registry import Command, CommandContext, Outcome
from jarvis.services.timer_service import TimerService
from jarvis.text_utils import normalize

_timers = TimerService()


def _parse_duration(utterance: str) -> tuple[int, str]:
    """Extrai segundos totais e descrição amigável da frase dita."""
    norm = normalize(utterance)

    # 1. Minutos
    match_min = re.search(r"(\d+)\s*(?:minuto|minutos|min)", norm)
    if match_min:
        val = int(match_min.group(1))
        return val * 60, f"{val} {'minuto' if val == 1 else 'minutos'}"

    # 2. Segundos
    match_sec = re.search(r"(\d+)\s*(?:segundo|segundos|seg)", norm)
    if match_sec:
        val = int(match_sec.group(1))
        return val, f"{val} {'segundo' if val == 1 else 'segundos'}"

    # 3. Horas
    match_hour = re.search(r"(\d+)\s*(?:hora|horas|h)", norm)
    if match_hour:
        val = int(match_hour.group(1))
        return val * 3600, f"{val} {'hora' if val == 1 else 'horas'}"

    # Padrão: 1 minuto caso não especificado
    return 60, "1 minuto"


def _set_timer(ctx: CommandContext, utterance: str) -> Outcome:
    seconds, label = _parse_duration(utterance)

    def _on_alarm(finished_label: str) -> None:
        ctx.speaker.say(f"Atenção, senhor Ken. O temporizador de {finished_label} acabou de terminar.")

    _timers.set_timer(seconds, label, _on_alarm)
    ctx.reply(f"Temporizador de {label} ativado, senhor. Avisarei assim que o tempo se esgotar.")
    return Outcome.CONTINUE


def _cancel_timers(ctx: CommandContext, _utterance: str) -> Outcome:
    count = _timers.cancel_all()
    if count > 0:
        ctx.reply(f"Todos os {count} temporizadores foram cancelados, senhor.")
    else:
        ctx.reply("Não há temporizadores ativos no momento, senhor.")
    return Outcome.CONTINUE


def timer_commands() -> list[Command]:
    """Retorna comandos de controle de temporizadores e alarmes."""
    return [
        Command(
            "cancelar_temporizador",
            (
                "cancelar temporizador", "cancelar timer", "parar temporizador",
                "parar timer", "cancelar alarme", "parar alarme",
            ),
            _cancel_timers,
        ),
        Command(
            "definir_temporizador",
            (
                "temporizador", "timer", "alarme", "cronometro",
                "me avise em", "me lembre em", "despertador",
            ),
            _set_timer,
        ),
    ]
