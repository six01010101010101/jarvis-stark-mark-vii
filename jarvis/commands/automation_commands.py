"""Comandos de voz para automação do Windows Explorer, seleção de arquivos e YouTube."""

from __future__ import annotations

import re

from jarvis.commands.registry import Command, CommandContext, Outcome
from jarvis.services.browser_controller import BrowserAndMediaController
from jarvis.services.semantic_intent_adapter import SemanticIntentAdapter
from jarvis.services.windows_automation import WindowsExplorerAutomation

_explorer = WindowsExplorerAutomation()
_media = BrowserAndMediaController()


def _open_folder_handler(ctx: CommandContext, utterance: str) -> Outcome:
    target = re.sub(r"^(?:abrir\s+pasta|abre\s+a\s+pasta|abrir\s+explorer\s+em|vai\s+na\s+pasta)\s*", "", utterance, flags=re.IGNORECASE).strip()
    success = _explorer.open_folder(target)
    if success:
        ctx.reply(f"Windows Explorer aberto {'em ' + target if target else 'com sucesso'}, senhor.")
    else:
        ctx.reply("Não consegui abrir o Windows Explorer neste diretório, senhor.")
    return Outcome.CONTINUE


def _select_file_handler(ctx: CommandContext, utterance: str) -> Outcome:
    clean = re.sub(r"^(?:selecionar\s+arquivo|destacar\s+arquivo|seleciona\s+o\s+arquivo|destaca\s+o\s+arquivo|achar\s+arquivo)\s*", "", utterance, flags=re.IGNORECASE).strip()
    if not clean:
        ctx.reply("Qual arquivo o senhor deseja selecionar no Windows Explorer?")
        return Outcome.CONTINUE
    success = _explorer.select_file_in_explorer(clean)
    if success:
        ctx.reply(f"Localizei e destaquei o arquivo '{clean}' no Windows Explorer, senhor.")
    else:
        ctx.reply(f"Não encontrei o arquivo '{clean}' nas pastas do sistema, senhor.")
    return Outcome.CONTINUE


def _youtube_play_handler(ctx: CommandContext, utterance: str) -> Outcome:
    query = re.sub(r"^(?:tocar\s+no\s+youtube|pesquisar\s+no\s+youtube|poe\s+no\s+yt|põe\s+no\s+yt|tocar\s+musica|tocar\s+música|bota\s+no\s+yt)\s*", "", utterance, flags=re.IGNORECASE).strip()
    if not query:
        parsed = SemanticIntentAdapter.parse_colloquial_action(utterance)
        if parsed and parsed["action"] == "play_youtube":
            query = str(parsed["target"])

    if not query:
        ctx.reply("O que o senhor gostaria de ouvir ou assistir no YouTube?")
        return Outcome.CONTINUE

    _media.play_youtube_search(query)
    ctx.reply(f"Reproduzindo '{query}' no YouTube agora mesmo, senhor.")
    return Outcome.CONTINUE


def _toggle_pause_handler(ctx: CommandContext, _utterance: str) -> Outcome:
    _media.toggle_play_pause()
    ctx.reply("Comando de reprodução enviado ao vídeo, senhor.")
    return Outcome.CONTINUE


def automation_commands() -> tuple[Command, ...]:
    """Retorna os comandos de controle de SO, Explorer e YouTube."""
    return (
        Command(
            name="open_explorer_folder",
            triggers=("abrir pasta", "abre a pasta", "abrir explorer", "abrir windows explorer", "vai nos downloads", "vai na pasta"),
            handler=_open_folder_handler,
        ),
        Command(
            name="select_system_file",
            triggers=("selecionar arquivo", "destacar arquivo", "seleciona o arquivo", "destaca o arquivo", "acha o arquivo"),
            handler=_select_file_handler,
        ),
        Command(
            name="youtube_play",
            triggers=("tocar no youtube", "pesquisar no youtube", "poe no yt", "põe no yt", "bota no yt", "tocar no yt"),
            handler=_youtube_play_handler,
        ),
        Command(
            name="toggle_video_pause",
            triggers=("pausar video", "pausar vídeo", "pausar musica", "pausar música", "despausar video", "despausar vídeo", "pausa ai", "pausa o video"),
            handler=_toggle_pause_handler,
        ),
    )
