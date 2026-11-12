"""Comandos de voz para automação do Windows Explorer, seleção de arquivos e YouTube."""

from __future__ import annotations

import re

from jarvis.commands.registry import Command, CommandContext, Outcome
from jarvis.security.security_guard import SecurityGuard
from jarvis.services.browser_controller import BrowserAndMediaController
from jarvis.services.semantic_intent_adapter import SemanticIntentAdapter
from jarvis.services.windows_automation import WindowsExplorerAutomation

_explorer = WindowsExplorerAutomation()
_media = BrowserAndMediaController()


def _open_folder_handler(ctx: CommandContext, utterance: str) -> Outcome:
    target = re.sub(r"^(?:abrir\s+pasta|abre\s+a\s+pasta|abrir\s+explorer\s+em|vai\s+na\s+pasta)\s*", "", utterance, flags=re.IGNORECASE).strip()
    if not SecurityGuard.is_safe_shell_input(target):
        ctx.reply("Comando de pasta cancelado pelo protocolo de segurança Stark.")
        return Outcome.CONTINUE
    safe_target = SecurityGuard.sanitize_command_argument(target)
    # 1. Fala primeiro a confirmação (protocolo sequencial estrito)
    ctx.reply(f"Abrindo o Windows Explorer {'em ' + safe_target if safe_target else 'agora'}, senhor.")
    # 2. Executa a abertura física somente após terminar de falar
    _explorer.open_folder(safe_target)
    return Outcome.CONTINUE


def _select_file_handler(ctx: CommandContext, utterance: str) -> Outcome:
    clean = re.sub(r"^(?:selecionar\s+arquivo|destacar\s+arquivo|seleciona\s+o\s+arquivo|destaca\s+o\s+arquivo|achar\s+arquivo)\s*", "", utterance, flags=re.IGNORECASE).strip()
    if not clean:
        ctx.reply("Qual arquivo o senhor deseja selecionar no Windows Explorer?")
        return Outcome.CONTINUE
    if not SecurityGuard.is_safe_shell_input(clean):
        ctx.reply("Nome de arquivo cancelado por protocolo de cibersegurança.")
        return Outcome.CONTINUE
    safe_clean = SecurityGuard.sanitize_command_argument(clean)
    # 1. Fala primeiro
    ctx.reply(f"Localizando e destacando o arquivo '{safe_clean}' no Windows Explorer, senhor.")
    # 2. Executa a seleção após a fala
    _explorer.select_file_in_explorer(safe_clean)
    return Outcome.CONTINUE


def _youtube_play_handler(ctx: CommandContext, utterance: str) -> Outcome:
    query = re.sub(r"^(?:tocar\s+no\s+youtube|pesquisar\s+no\s+youtube|poe\s+no\s+yt|põe\s+no\s+yt|bota\s+no\s+yt)\s*", "", utterance, flags=re.IGNORECASE).strip()
    if not query:
        parsed = SemanticIntentAdapter.parse_colloquial_action(utterance)
        if parsed and parsed["action"] == "play_youtube":
            query = str(parsed["target"])

    if not query:
        ctx.reply("O que o senhor gostaria de ouvir ou assistir no YouTube?")
        return Outcome.CONTINUE

    # 1. Fala primeiro a confirmação
    ctx.reply(f"Reproduzindo '{query}' no YouTube agora mesmo, senhor.")
    # 2. Abre o navegador somente após concluir a fala
    _media.play_youtube_search(query)
    return Outcome.CONTINUE


def _toggle_pause_handler(ctx: CommandContext, _utterance: str) -> Outcome:
    ctx.reply("Comando de reprodução enviado ao vídeo, senhor.")
    _media.toggle_play_pause()
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
