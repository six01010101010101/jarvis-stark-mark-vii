"""Comandos de voz para Alt+Tab, Área de Trabalho, Gerenciador de Tarefas e troca de telas."""

from __future__ import annotations

import re
from jarvis.commands.registry import Command, CommandContext, Outcome
from jarvis.services.window_switcher import WindowSwitcher


def _alt_tab_handler(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply("Alternando para a próxima janela ativa, senhor.")
    WindowSwitcher.trigger_alt_tab()
    if ctx.session and hasattr(ctx.session, "close_dialogue"):
        ctx.session.close_dialogue()
    return Outcome.CONTINUE


def _desktop_handler(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply("Transição para a Área de Trabalho concluída, senhor.")
    WindowSwitcher.show_desktop()
    if ctx.session and hasattr(ctx.session, "close_dialogue"):
        ctx.session.close_dialogue()
    return Outcome.CONTINUE


def _taskmgr_handler(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply("Abrindo o Gerenciador de Tarefas do Windows agora, senhor.")
    WindowSwitcher.open_task_manager()
    if ctx.session and hasattr(ctx.session, "close_dialogue"):
        ctx.session.close_dialogue()
    return Outcome.CONTINUE


def _switch_app_handler(ctx: CommandContext, utterance: str) -> Outcome:
    clean = re.sub(r"^(?:mudar\s+para\s+o|mudar\s+para\s+a|mudar\s+pro|mudar\s+pra|alternar\s+para\s+o|alternar\s+para\s+a|trocar\s+para\s+o|trocar\s+para\s+a)\s*", "", utterance, flags=re.I).strip()
    if not clean:
        ctx.reply("Para qual aplicativo ou tela o senhor deseja mudar?")
        return Outcome.CONTINUE

    ctx.reply(f"Mudando o foco para {clean}, senhor.")
    switched = WindowSwitcher.switch_to_app(clean)
    if not switched:
        ctx.launcher.launch(clean)

    if ctx.session and hasattr(ctx.session, "close_dialogue"):
        ctx.session.close_dialogue()
    return Outcome.CONTINUE


def window_navigation_commands() -> tuple[Command, ...]:
    """Retorna os comandos de alternância de janelas do SO."""
    return (
        Command(
            name="alt_tab_switch",
            triggers=("alt tab", "mudar de tela", "alternar tela", "trocar tela", "muda de tela", "proxima janela", "alterna tela"),
            handler=_alt_tab_handler,
        ),
        Command(
            name="show_desktop_screen",
            triggers=("area de trabalho", "área de trabalho", "mostrar area de trabalho", "ir para area de trabalho", "ir para a area de trabalho", "vai para a area de trabalho"),
            handler=_desktop_handler,
        ),
        Command(
            name="open_task_manager_screen",
            triggers=("gerenciador de tarefas", "ir para o gerenciador de tarefas", "abrir gerenciador de tarefas", "abre o gerenciador de tarefas", "gerenciador de processos"),
            handler=_taskmgr_handler,
        ),
        Command(
            name="switch_to_application",
            triggers=("mudar para o", "mudar para a", "alternar para o", "alternar para a", "trocar para o", "trocar para a", "muda pro", "muda pra"),
            handler=_switch_app_handler,
        ),
    )
