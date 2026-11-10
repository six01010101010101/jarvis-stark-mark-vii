"""Comandos informativos: hora, data, matemática e controle do assistente."""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from jarvis.commands.registry import Command, CommandContext, Outcome
from jarvis.services.world_intelligence import WorldIntelligence

Clock = Callable[[], datetime]


def info_commands(clock: Clock = datetime.now) -> list[Command]:
    """Retorna comandos informativos, cálculos aritméticos e desligamento."""

    def tell_time(ctx: CommandContext, _utterance: str) -> Outcome:
        intel = WorldIntelligence(ctx.answers, clock)
        ctx.reply(intel.get_time_report())
        return Outcome.CONTINUE

    def tell_date(ctx: CommandContext, _utterance: str) -> Outcome:
        intel = WorldIntelligence(ctx.answers, clock)
        ctx.reply(intel.get_date_report())
        return Outcome.CONTINUE

    def calculate(ctx: CommandContext, utterance: str) -> Outcome:
        intel = WorldIntelligence(ctx.answers, clock)
        res = intel.evaluate_math(utterance)
        if res:
            ctx.reply(res)
        else:
            ans = intel.answer_direct(utterance)
            ctx.reply(ans)
        return Outcome.CONTINUE

    def shutdown(ctx: CommandContext, _utterance: str) -> Outcome:
        ctx.speaker.say("Finalizando todos os sistemas, senhor. Até logo.")
        ctx.view.show_status("Assistente Desligado.")
        return Outcome.SHUTDOWN

    return [
        Command("hora", ("que horas", "horario", "horas sao"), tell_time),
        Command("data", ("que dia e hoje", "qual e a data", "dia de hoje"), tell_date),
        Command("matematica", ("quanto e", "calcule", "qual o resultado", "vezes", "dividido por"), calculate),
        Command("desligar", ("desligar sistema", "encerrar jarvis"), shutdown),
    ]
