"""Comandos de diagnóstico mútuo, janela em tela, saúde da máquina e autocura."""

from __future__ import annotations

from jarvis.commands.registry import Command, CommandContext, Outcome
from jarvis.services.mutual_processor import MutualProcessor

_processor = MutualProcessor()


def _machine_status(ctx: CommandContext, _utterance: str) -> Outcome:
    report = _processor.get_machine_health_report()
    ctx.reply(report)
    return Outcome.CONTINUE


def _what_i_need(ctx: CommandContext, _utterance: str) -> Outcome:
    report = _processor.diagnose_current_needs()
    ctx.reply(report)
    return Outcome.CONTINUE


def _current_screen(ctx: CommandContext, _utterance: str) -> Outcome:
    report = _processor.report_current_screen()
    ctx.reply(report)
    return Outcome.CONTINUE


def _optimize_machine(ctx: CommandContext, _utterance: str) -> Outcome:
    report = _processor.execute_mutual_optimization()
    ctx.reply(report)
    return Outcome.CONTINUE


def machine_commands() -> list[Command]:
    """Retorna comandos de correlação e diagnóstico situacional mútuo."""
    return [
        Command(
            "status_maquina_mutua",
            (
                "como esta a maquina", "como ta a maquina", "saude do pc",
                "saude do computador", "diagnostico completo", "estado do computador",
                "status da maquina", "raio x da maquina", "como estao as coisas na maquina",
            ),
            _machine_status,
        ),
        Command(
            "o_que_preciso",
            (
                "o que eu preciso", "o que a maquina precisa", "o que preciso agora",
                "qual a situacao da maquina", "preciso de algo", "o que precisamos",
            ),
            _what_i_need,
        ),
        Command(
            "janela_em_tela",
            (
                "o que estou usando", "qual janela esta aberta", "o que esta na tela",
                "qual programa esta aberto", "janela ativa", "o que esta aberto agora",
            ),
            _current_screen,
        ),
        Command(
            "otimizar_maquina",
            (
                "otimizar maquina", "otimizar computador", "otimizar pc",
                "liberar memoria", "limpar memoria", "acelerar computador",
                "acelerar maquina", "autocura",
            ),
            _optimize_machine,
        ),
    ]
