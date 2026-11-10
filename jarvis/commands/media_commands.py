"""Comandos de multimídia, redes sociais, WhatsApp, YouTube e IA."""

from __future__ import annotations

import logging
import re
from urllib.parse import quote_plus

from jarvis.commands.registry import Command, CommandContext, Outcome
from jarvis.contracts import AnswerServiceError, LaunchError
from jarvis.text_utils import normalize, text_after

logger = logging.getLogger(__name__)

YOUTUBE_SEARCH_URL = "https://www.youtube.com/results?search_query={query}"

SOCIAL_NETWORKS = {
    "instagram": "https://www.instagram.com", "tiktok": "https://www.tiktok.com",
    "facebook": "https://www.facebook.com", "whatsapp": "https://web.whatsapp.com",
    "youtube": "https://www.youtube.com", "twitter": "https://x.com",
    "twitch": "https://www.twitch.tv", "reddit": "https://www.reddit.com",
    "linkedin": "https://www.linkedin.com", "github": "https://www.github.com",
    "netflix": "https://www.netflix.com", "spotify": "https://open.spotify.com",
    "globo": "https://www.globo.com",
}


def _ask(ctx: CommandContext, prompt: str) -> str | None:
    ctx.reply(prompt)
    ctx.view.show_status("Ouvindo...")
    return ctx.listener.listen()


def _play_youtube(ctx: CommandContext, utterance: str) -> Outcome:
    """Abre o YouTube diretamente ou reproduz a música/vídeo solicitado."""
    norm = normalize(utterance)
    home_phrases = (
        "youtube", "o youtube", "no youtube", "abrir youtube", "abre youtube",
        "abrir o youtube", "abre o youtube", "colocar no youtube", "coloca no youtube",
        "colocar youtube", "entrar no youtube", "ir para o youtube",
    )
    if norm in home_phrases:
        ctx.launcher.open_url("https://www.youtube.com")
        ctx.reply("Colocando no YouTube agora.")
        return Outcome.CONTINUE

    query = ""
    for prefix in (
        "tocar musica", "colocar musica", "colocar o video", "colocar video",
        "video no youtube", "ouvir musica", "tocar no youtube", "colocar no youtube",
        "tocar", "colocar", "ouvir", "video", "assistir", "abrir youtube e tocar",
        "abrir youtube", "abrir o youtube", "youtube",
    ):
        query = text_after(utterance, prefix)
        if query:
            break

    if normalize(query) in ("musica", "um video", "uma musica", "video", "no youtube", "o youtube"):
        query = ""

    if not query:
        query = _ask(ctx, "Qual música ou vídeo deseja reproduzir, senhor?")

    if not query:
        ctx.reply("Qual música ou vídeo deseja reproduzir, senhor?", pending_intent="play_media")
        return Outcome.CONTINUE

    clean_query = query.replace("no youtube", "").strip()
    url = YOUTUBE_SEARCH_URL.format(query=quote_plus(clean_query))
    try:
        ctx.launcher.open_url(url)
        ctx.reply(f"Entendido, senhor. Reproduzindo {clean_query} no YouTube.")
    except LaunchError:
        ctx.reply("Não consegui abrir o navegador.")
    return Outcome.CONTINUE


def _whatsapp_chat(ctx: CommandContext, utterance: str) -> Outcome:
    """Abre conversa direta do WhatsApp com número e mensagem pré-digitada."""
    cleaned_spaces = re.sub(r"[()\-+]", "", utterance)
    digits_matches = re.findall(r"\b\d{8,15}\b", cleaned_spaces)
    phone = digits_matches[0] if digits_matches else ""

    message = ""
    for prefix in ("dizendo", "falando", "com a mensagem", "mensagem"):
        message = text_after(utterance, prefix)
        if message:
            break

    if not phone and not message:
        ctx.launcher.open_url("https://web.whatsapp.com")
        ctx.reply("Colocando no WhatsApp do navegador agora.")
        return Outcome.CONTINUE
    if not phone:
        spoken_num = _ask(ctx, "Qual o número de telefone com DDD?")
        phone = "".join(re.findall(r"\d+", (spoken_num or "").replace(" ", "")))
    if not phone:
        ctx.launcher.open_url("https://web.whatsapp.com")
        ctx.reply("Abrindo o WhatsApp Web no navegador.")
        return Outcome.CONTINUE
    if len(phone) in (10, 11) and not phone.startswith("55"):
        phone = f"55{phone}"
    url = f"https://web.whatsapp.com/send?phone={phone}" + (f"&text={quote_plus(message)}" if message else "")
    ctx.launcher.open_url(url)
    ctx.reply(f"Abrindo conversa do WhatsApp para {phone}.")
    return Outcome.CONTINUE


def _open_social_or_site(ctx: CommandContext, utterance: str) -> Outcome:
    """Abre redes sociais e sites específicos solicitados."""
    norm = normalize(utterance)
    for net_name, net_url in SOCIAL_NETWORKS.items():
        if net_name in norm:
            ctx.launcher.open_url(net_url)
            ctx.reply(f"Entendido, senhor. Abrindo {net_name.capitalize()}.")
            return Outcome.CONTINUE

    target = ""
    for prefix in ("abrir o site", "abrir site", "abrir a aba", "abrir aba", "acessar site"):
        target = text_after(utterance, prefix)
        if target:
            break

    if not target:
        target = _ask(ctx, "Qual site deseja acessar, senhor?")
    if not target:
        ctx.reply("Qual site deseja que eu acesse, senhor?", pending_intent="open_url")
        return Outcome.CONTINUE

    clean = normalize(target).replace(" ", "")
    url = f"https://www.{clean}.com" if "." not in clean else f"https://{clean}"
    try:
        ctx.launcher.open_url(url)
        ctx.reply(f"Entendido, senhor. Acessando {target}.")
    except LaunchError:
        ctx.reply(f"Não foi possível abrir {target}.")
    return Outcome.CONTINUE


def _search_ai(ctx: CommandContext, utterance: str) -> Outcome:
    """Responde perguntas de história, ciência e internet usando Gemini + Fontes do Google."""
    topic = ""
    for prefix in (
        "pesquisar", "pesquise", "me explique", "qual a historia", "historia de",
        "historia do", "historia da", "quem foi", "quem descobriu", "quem criou",
        "o que e", "quem e", "como funciona", "me fale sobre", "conte sobre",
    ):
        topic = text_after(utterance, prefix)
        if topic:
            break
    if not topic:
        topic = utterance.strip()

    try:
        query = topic if any(p in normalize(utterance) for p in ("pesquisar", "pesquise")) else utterance
        answer = ctx.answers.ask(query)
        if ctx.memory:
            ctx.memory.remember(f"fact:{topic[:40]}", answer, category="knowledge")
        ctx.reply(answer)
    except AnswerServiceError:
        logger.exception("Falha na consulta de conhecimento")
        ctx.reply("Serviço de consulta temporariamente indisponível.")
    return Outcome.CONTINUE


def _transcribe_note(ctx: CommandContext, utterance: str) -> Outcome:
    """Anota mensagem no arquivo de texto da Área de Trabalho."""
    note = ""
    for prefix in ("escrever", "anotar", "transcrever", "gravar mensagem", "salvar nota"):
        note = text_after(utterance, prefix)
        if note:
            break
    if not note:
        note = _ask(ctx, "O que gostaria de anotar, senhor?")
    if not note:
        ctx.reply("Nenhuma anotação informada.")
        return Outcome.CONTINUE

    try:
        ctx.messages.save(note)
        ctx.reply("Entendido, senhor. Anotação salva na sua Área de Trabalho.")
    except OSError:
        ctx.reply("Não foi possível salvar o arquivo.")
    return Outcome.CONTINUE


def media_commands() -> list[Command]:
    search_triggers = (
        "pesquisar", "pesquise", "o que e", "quem e", "quem foi", "quem descobriu",
        "historia de", "historia do", "historia da", "qual a historia", "como funciona", "me explique",
    )
    return [
        Command("whatsapp", ("whatsapp", "zap", "mensagem no whatsapp"), _whatsapp_chat),
        Command("youtube", ("youtube", "tocar", "colocar musica", "colocar video", "video", "ouvir", "assistir"), _play_youtube),
        Command("redes sociais", ("instagram", "tiktok", "facebook", "twitter", "google", "github", "spotify", "netflix", "twitch", "globo", "abrir site", "acessar site"), _open_social_or_site),
        Command("pesquisar", search_triggers, _search_ai),
        Command("anotar", ("escrever", "anotar", "transcrever", "gravar mensagem", "salvar nota"), _transcribe_note),
    ]
