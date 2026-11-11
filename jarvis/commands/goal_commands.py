"""Comandos de voz para gerenciamento de metas e tarefas integrado ao Hivemind Goals."""

from __future__ import annotations

import re

from jarvis.commands.registry import Command, CommandContext, Outcome
from jarvis.services.goal_tracker import GoalTracker

_ADD_PATTERNS = (
    r"^(?:adicionar\s+meta|adiciona\s+meta|nova\s+meta|criar\s+meta|cria\s+meta|salvar\s+meta|salve\s+a\s+meta|anote\s+a\s+meta|anotar\s+meta)(?:\s+de|\s+para)?\s*",
    r"^(?:lembre-se\s+de|lembre\s+de|guarde\s+a\s+tarefa|anote\s+a\s+tarefa)(?:\s+de)?\s*",
)

_COMPLETE_PATTERNS = (
    r"^(?:concluir\s+meta|conclua\s+a\s+meta|finalizar\s+meta|finaliza\s+a\s+meta|meta\s+concluida|tarefa\s+concluida|concluir\s+tarefa)(?:\s+de)?\s*",
)


def _get_tracker(ctx: CommandContext) -> GoalTracker | None:
    if ctx.memory:
        return GoalTracker(ctx.memory)
    return None


def _extract_text(utterance: str, patterns: tuple[str, ...]) -> str:
    cleaned = utterance.strip()
    for pat in patterns:
        replaced = re.sub(pat, "", cleaned, flags=re.IGNORECASE).strip()
        if replaced != cleaned:
            return replaced
    return ""


def _list_goals_handler(ctx: CommandContext, _utterance: str) -> Outcome:
    tracker = _get_tracker(ctx)
    if not tracker:
        ctx.reply("Módulo de memória indisponível no momento, senhor.")
        return Outcome.CONTINUE
    summary = tracker.format_summary_spoken()
    ctx.reply(summary)
    return Outcome.CONTINUE


def _add_goal_handler(ctx: CommandContext, utterance: str) -> Outcome:
    tracker = _get_tracker(ctx)
    if not tracker:
        ctx.reply("Módulo de memória indisponível no momento, senhor.")
        return Outcome.CONTINUE
    title = _extract_text(utterance, _ADD_PATTERNS)
    if not title:
        ctx.reply("Qual objetivo ou meta o senhor deseja que eu registre?", pending_intent="add_goal")
        return Outcome.CONTINUE
    goal = tracker.add_goal(title=title)
    ctx.reply(f"Meta registrada com sucesso, senhor: '{goal.title}'. Já está gravada em nossa central de objetivos.")
    return Outcome.CONTINUE


def _complete_goal_handler(ctx: CommandContext, utterance: str) -> Outcome:
    tracker = _get_tracker(ctx)
    if not tracker:
        ctx.reply("Módulo de memória indisponível no momento, senhor.")
        return Outcome.CONTINUE
    target = _extract_text(utterance, _COMPLETE_PATTERNS)
    if not target:
        ctx.reply("Qual meta o senhor gostaria de marcar como concluída?", pending_intent="complete_goal")
        return Outcome.CONTINUE
    success = tracker.complete_goal(target)
    if success:
        ctx.reply(f"Excelente progresso, senhor. Meta '{target}' marcada como concluída com sucesso.")
    else:
        ctx.reply(f"Não localizei nenhuma meta ativa compatível com '{target}', senhor.")
    return Outcome.CONTINUE


def goal_commands() -> tuple[Command, ...]:
    """Retorna os comandos de voz associados ao gerenciamento de metas."""
    return (
        Command(
            name="list_goals",
            triggers=("minhas metas", "quais sao minhas metas", "listar metas", "ver metas", "minhas tarefas", "ver tarefas"),
            handler=_list_goals_handler,
        ),
        Command(
            name="add_goal",
            triggers=("adicionar meta", "adiciona meta", "nova meta", "criar meta", "lembre de", "lembre-se de", "salve a meta", "anote a meta"),
            handler=_add_goal_handler,
        ),
        Command(
            name="complete_goal",
            triggers=("concluir meta", "conclua a meta", "finalizar meta", "meta concluida", "tarefa concluida", "concluir tarefa"),
            handler=_complete_goal_handler,
        ),
    )
