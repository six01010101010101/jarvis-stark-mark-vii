"""Comandos de IA cognitiva, mapas mentais Mermaid, aprendizagem e memória de longo prazo."""

from __future__ import annotations

import re

from jarvis.commands.registry import Command, CommandContext, Outcome


def _extract_topic(utterance: str, default: str = "o assunto solicitado") -> str:
    match = re.search(r"(?:sobre|de|do|da|para)\s+(.+)$", utterance, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    words = utterance.split()
    return " ".join(words[-3:]) if len(words) >= 3 else default


def _mind_map(ctx: CommandContext, utterance: str) -> Outcome:
    topic = _extract_topic(utterance, "inteligência artificial")
    ctx.reply(f"Estruturando mapa mental sobre {topic}, senhor...")
    if ctx.cognitive:
        result = ctx.cognitive.generate_mind_map(topic)
        ctx.reply(result)
    else:
        ctx.reply("Módulo cognitivo indisponível no momento, senhor.")
    return Outcome.CONTINUE


def _sticky_notes(ctx: CommandContext, utterance: str) -> Outcome:
    topic = _extract_topic(utterance, "estudos")
    ctx.reply(f"Organizando notas adesivas sobre {topic}, senhor...")
    if ctx.cognitive:
        result = ctx.cognitive.generate_sticky_notes(topic)
        ctx.reply(result)
    else:
        ctx.reply("Módulo cognitivo indisponível no momento, senhor.")
    return Outcome.CONTINUE


def _visual_learning(ctx: CommandContext, utterance: str) -> Outcome:
    topic = _extract_topic(utterance, "ciência")
    ctx.reply(f"Preparando infográfico educacional sobre {topic}, senhor...")
    if ctx.cognitive:
        result = ctx.cognitive.generate_visual_learning(topic)
        ctx.reply(result)
    else:
        ctx.reply("Módulo cognitivo indisponível no momento, senhor.")
    return Outcome.CONTINUE


def _three_levels(ctx: CommandContext, utterance: str) -> Outcome:
    topic = _extract_topic(utterance, "tecnologia")
    ctx.reply(f"Elaborando explicação em três níveis sobre {topic}, senhor...")
    if ctx.cognitive:
        result = ctx.cognitive.explain_three_levels(topic)
        ctx.reply(result)
    else:
        ctx.reply("Módulo cognitivo indisponível no momento, senhor.")
    return Outcome.CONTINUE


def _flashcards(ctx: CommandContext, utterance: str) -> Outcome:
    topic = _extract_topic(utterance, "revisão")
    ctx.reply(f"Gerando flashcards de estudo sobre {topic}, senhor...")
    if ctx.cognitive:
        result = ctx.cognitive.generate_flashcards(topic)
        ctx.reply(result)
    else:
        ctx.reply("Módulo cognitivo indisponível no momento, senhor.")
    return Outcome.CONTINUE


def _quiz(ctx: CommandContext, utterance: str) -> Outcome:
    topic = _extract_topic(utterance, "conhecimentos gerais")
    ctx.reply(f"Montando quiz interativo sobre {topic}, senhor...")
    if ctx.cognitive:
        result = ctx.cognitive.generate_quiz(topic)
        ctx.reply(result)
    else:
        ctx.reply("Módulo cognitivo indisponível no momento, senhor.")
    return Outcome.CONTINUE


def _study_roadmap(ctx: CommandContext, utterance: str) -> Outcome:
    topic = _extract_topic(utterance, "programação")
    ctx.reply(f"Planejando roteiro de estudos sobre {topic}, senhor...")
    if ctx.cognitive:
        result = ctx.cognitive.generate_study_roadmap(topic)
        ctx.reply(result)
    else:
        ctx.reply("Módulo cognitivo indisponível no momento, senhor.")
    return Outcome.CONTINUE


def _remember(ctx: CommandContext, utterance: str) -> Outcome:
    match = re.search(r"(?:lembre-?se\s+que|lembre\s+que|guarde\s+que|anote\s+que)\s+(.+)$", utterance, re.I)
    fact = match.group(1).strip() if match else utterance
    if " e " in fact or " é " in fact:
        parts = re.split(r"\s+[eé]\s+", fact, maxsplit=1)
        key, val = parts[0].strip(), parts[1].strip()
    else:
        key, val = fact, "verdadeiro"

    if ctx.memory:
        ctx.memory.set_memory(key, val)
        ctx.reply(f"Compreendido, memorizei que {key} é {val}, senhor.")
    else:
        ctx.reply("Memória permanente indisponível no momento, senhor.")
    return Outcome.CONTINUE


def _recall_memory(ctx: CommandContext, _utterance: str) -> Outcome:
    if not ctx.memory:
        ctx.reply("Banco de memórias inacessível, senhor.")
        return Outcome.CONTINUE

    mems = ctx.memory.get_all_memories()
    if not mems:
        ctx.reply("Ainda não tenho registros salvos na minha memória permanente, senhor.")
        return Outcome.CONTINUE

    items = [f"{m['key']}: {m['value']}" for m in mems[:5]]
    ctx.reply("Aqui está o que recordo, senhor: " + "; ".join(items))
    return Outcome.CONTINUE


def cognitive_commands() -> tuple[Command, ...]:
    """Retorna os comandos cognitivos e de aprendizagem."""
    return (
        Command("mind_map", ("mapa mental", "mapa conceitual", "mind map", "mindmap"), _mind_map),
        Command("sticky_notes", ("notas adesivas", "nota adesiva", "post it", "post-it"), _sticky_notes),
        Command("visual_learning", ("explicacao visual", "explicação visual", "infografico"), _visual_learning),
        Command("three_levels", ("tres niveis", "três níveis", "explicar em niveis"), _three_levels),
        Command("flashcards", ("flashcards", "flash cards", "cartoes de estudo"), _flashcards),
        Command("quiz", ("quiz", "questionario", "questionário"), _quiz),
        Command("study_roadmap", ("plano de estudo", "roteiro de estudo", "cronograma de estudo"), _study_roadmap),
        Command("remember", ("lembre se que", "lembre-se que", "guarde que", "anote que"), _remember),
        Command("recall_memory", ("o que voce sabe", "minhas memorias", "minhas preferencias"), _recall_memory),
    )
