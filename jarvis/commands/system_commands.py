"""Comandos de controle do sistema: abertura de jogos/programas e encerramento profundo de tarefas."""

from __future__ import annotations

import ctypes
from datetime import datetime
import logging
import os
from pathlib import Path
import random

from jarvis.commands.registry import Command, CommandContext, Handler, Outcome
from jarvis.contracts import LaunchError
from jarvis.text_utils import normalize

logger = logging.getLogger(__name__)

DOWNLOADS_DIR = str(Path.home() / "Downloads")
NETWORK_TROUBLESHOOTER_URI = "ms-settings:troubleshoot"

VK_CONTROL = 0x11
VK_MENU = 0x12
VK_F4 = 0x73
KEYEVENTF_KEYUP = 0x0002


def _send_shortcut(key1: int, key2: int) -> None:
    user32 = ctypes.windll.user32
    user32.keybd_event(key1, 0, 0, 0)
    user32.keybd_event(key2, 0, 0, 0)
    user32.keybd_event(key2, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(key1, 0, KEYEVENTF_KEYUP, 0)


def _open_app(target: str, friendly_name: str) -> Handler:
    def handler(ctx: CommandContext, _utterance: str) -> Outcome:
        try:
            ctx.launcher.launch(target)
            ctx.reply(f"Entendido, senhor. Abrindo {friendly_name}.")
        except LaunchError:
            logger.exception("Falha ao abrir: %s", target)
            ctx.reply(f"Não foi possível abrir {friendly_name}, senhor.")
        return Outcome.CONTINUE

    return handler


def _open_url(url: str, friendly_name: str) -> Handler:
    def handler(ctx: CommandContext, _utterance: str) -> Outcome:
        try:
            ctx.launcher.open_url(url)
            ctx.reply(f"Entendido, senhor. Abrindo {friendly_name}.")
        except LaunchError:
            ctx.reply(f"Não foi possível acessar {friendly_name}, senhor.")
        return Outcome.CONTINUE

    return handler


def _close_app(ctx: CommandContext, utterance: str) -> Outcome:
    """Encerra profundamente um processo/jogo nas tarefas do sistema, ou fecha janela/aba."""
    norm = normalize(utterance)
    ignore = (
        "eu", "gostaria", "quero", "que", "voce", "fechasse", "encerrasse", "feche",
        "fechar", "fecha", "encerrar", "encerra", "finalizar", "finaliza", "finalizasse",
        "matar", "mata", "terminar", "termina", "tarefa", "tarefas", "processo", "processos",
        "sistema", "maquina", "fundo", "la", "bem", "no", "na", "do", "da", "dos", "das",
        "o", "a", "os", "as", "um", "uma", "aplicativo", "programa", "app", "jogo",
        "por", "favor", "agora", "ai", "para", "pra", "mim", "senhor", "jarvis",
    )

    if any(t in norm.split() for t in ("aba", "guia", "site")) or any(
        s in norm for s in ("youtube", "instagram")
    ):
        _send_shortcut(VK_CONTROL, 0x57)  # Ctrl + W
        ctx.reply("Aba do navegador encerrada, senhor.")
        return Outcome.CONTINUE

    words = [w for w in norm.split() if w not in ignore and w != "janela"]
    target = " ".join(words).strip()

    if "janela" in norm and not target:
        _send_shortcut(VK_MENU, VK_F4)  # Alt + F4
        ctx.reply("Janela encerrada, senhor.")
        return Outcome.CONTINUE

    if not target:
        ctx.reply("Ok, senhor, o que você gostaria que eu fechasse ou encerrasse?", pending_intent="close_app")
        return Outcome.CONTINUE

    if ctx.processes.close_app(target):
        ctx.reply(f"Certo, fechando {target.capitalize()}.")
    else:
        ctx.reply(f"Não encontrei {target.capitalize()} aberto no momento.")
    return Outcome.CONTINUE


def _open_generic_app(ctx: CommandContext, utterance: str) -> Outcome:
    words = normalize(utterance).split()
    ignore = (
        "eu", "gostaria", "quero", "que", "voce", "abrisse", "executasse", "abra",
        "abrir", "abre", "iniciar", "inicia", "executar", "executa", "rodar", "roda",
        "colocar", "coloca", "o", "a", "os", "as", "no", "na", "um", "uma", "aplicativo",
        "programa", "app", "jogo", "janela", "do", "da", "por", "favor", "agora",
        "ai", "para", "pra", "mim", "senhor", "jarvis",
    )
    target = " ".join([w for w in words if w not in ignore]).strip()
    if not target:
        ctx.reply("Ok, senhor, mas o que você gostaria de abrir ou executar?", pending_intent="open_app")
        return Outcome.CONTINUE
    try:
        ctx.launcher.launch(target)
        ctx.reply(f"Abrindo {target} agora.")
    except LaunchError:
        ctx.reply(f"Não encontrei o programa {target} no sistema.")
    return Outcome.CONTINUE


def _take_screenshot(ctx: CommandContext, _utterance: str) -> Outcome:
    """Captura a tela atual e salva na pasta Imagens."""
    pics_dir = Path.home() / "Pictures"
    pics_dir.mkdir(parents=True, exist_ok=True)
    out_file = pics_dir / f"jarvis_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    try:
        from PIL import ImageGrab
        ImageGrab.grab().save(str(out_file))
        ctx.reply("Captura de tela realizada e salva na sua pasta de Imagens, senhor Ken.")
    except Exception:
        VK_SNAPSHOT = 0x2C
        ctypes.windll.user32.keybd_event(VK_SNAPSHOT, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_SNAPSHOT, 0, KEYEVENTF_KEYUP, 0)
        ctx.reply("Captura de tela copiada para a área de transferência, senhor Ken.")
    return Outcome.CONTINUE


def _play_local_music(ctx: CommandContext, _utterance: str) -> Outcome:
    """Toca música da biblioteca local ou abre o player musical."""
    music_dir = Path.home() / "Music"
    if music_dir.exists():
        songs = [f for f in music_dir.iterdir() if f.is_file() and f.suffix.lower() in (".mp3", ".wav", ".flac", ".m4a")]
        if songs:
            song = random.choice(songs)
            os.startfile(str(song))
            ctx.reply(f"Reproduzindo {song.stem} da sua biblioteca musical, senhor Ken.")
            return Outcome.CONTINUE
    ctx.launcher.open_url("https://music.youtube.com")
    ctx.reply("Abrindo o YouTube Music para o senhor, senhor Ken.")
    return Outcome.CONTINUE


def _adjust_mic_sensitivity(ctx: CommandContext, utterance: str) -> Outcome:
    """Ajusta a sensibilidade do microfone por comando de voz."""
    norm = normalize(utterance)
    target_val = 4.5 if any(w in norm for w in ("maxima", "aumentar", "alta", "mais")) else 2.0
    if hasattr(ctx.listener, "set_sensitivity"):
        ctx.listener.set_sensitivity(target_val)
    ctx.reply(f"Sensibilidade do sensor acústico calibrada para {target_val:.1f} vezes, senhor Ken.")
    return Outcome.CONTINUE


def close_commands() -> list[Command]:
    """Comandos de fechamento e finalização de tarefas prioritários."""
    return [
        Command(
            "fechar app",
            (
                "fechar", "fecha", "feche", "fechasse", "encerrar", "encerra", "encerrasse",
                "finalizar", "finaliza", "finalizasse", "matar", "terminar", "termina",
            ),
            _close_app,
        ),
    ]


def system_commands() -> list[Command]:
    """Retorna comandos de sistema, processos, jogos e aplicativos do Windows."""
    return [
        *close_commands(),
        Command("captura de tela", ("captura de tela", "tirar print", "screenshot", "print da tela"), _take_screenshot),
        Command("tocar musica", ("tocar musica", "reproduzir musica", "ouvir musica"), _play_local_music),
        Command("sensibilidade mic", ("aumentar sensibilidade", "sensibilidade maxima", "diminuir sensibilidade", "calibrar microfone"), _adjust_mic_sensitivity),
        Command("bloco de notas", ("bloco de notas", "blocos de notas", "notepad"), _open_app("notepad.exe", "Bloco de Notas")),
        Command("calculadora", ("calculadora", "calc"), _open_app("calc.exe", "Calculadora")),
        Command("paint", ("paint", "mspaint"), _open_app("mspaint.exe", "Paint")),
        Command("chrome", ("chrome", "google chrome", "navegador"), _open_url("https://www.google.com", "Google Chrome")),
        Command("edge", ("edge", "microsoft edge"), _open_app("msedge.exe", "Microsoft Edge")),
        Command("vs code", ("vs code", "vscode", "visual studio code"), _open_app("code", "Visual Studio Code")),
        Command("cmd", ("prompt", "cmd", "terminal", "powershell"), _open_app("cmd.exe", "Prompt de Comando")),
        Command("excel", ("excel", "planilha"), _open_app("excel.exe", "Excel")),
        Command("word", ("word", "documento"), _open_app("winword.exe", "Word")),
        Command("gerenciador", ("gerenciador de tarefas", "task manager"), _open_app("taskmgr.exe", "Gerenciador de Tarefas")),
        Command("explorador", ("explorador de arquivos", "meus arquivos", "abrir arquivos"), _open_app("explorer.exe", "Explorador de Arquivos")),
        Command("downloads", ("downloads", "pasta downloads"), _open_app(DOWNLOADS_DIR, "Downloads")),
        Command("configuracoes", ("configuracoes", "painel de controle"), _open_app("ms-settings:", "Configurações do Windows")),
        Command("internet", ("consertar internet", "concertar internet", "solucionar rede"), _open_app(NETWORK_TROUBLESHOOTER_URI, "Solução de Problemas")),
        Command("abrir app generico", ("abra", "abrir", "abre", "abrisse", "iniciar", "inicia", "executar", "executa", "rodar", "roda"), _open_generic_app),
    ]
