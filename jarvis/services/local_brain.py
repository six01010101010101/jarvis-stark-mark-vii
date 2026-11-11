"""Mente cognitiva e personalidade de amigo com vida própria do J.A.R.V.I.S. (Local + Web)."""

from __future__ import annotations

from datetime import datetime
import random
import re
from urllib.parse import quote_plus

from jarvis.services.mutual_processor import MutualProcessor
from jarvis.services.web_knowledge import fetch_google_web_pt, fetch_weather_pt, fetch_wikipedia_pt
from jarvis.text_utils import normalize

_telemetry = MutualProcessor()

APP_TARGETS: dict[str, tuple[str, str]] = {
    "google chrome": ("chrome.exe", "o Google Chrome"), "chrome": ("chrome.exe", "o Google Chrome"),
    "microsoft edge": ("msedge.exe", "o Microsoft Edge"), "edge": ("msedge.exe", "o Microsoft Edge"),
    "bloco de notas": ("notepad.exe", "o Bloco de Notas"), "notepad": ("notepad.exe", "o Bloco de Notas"),
    "calculadora": ("calc.exe", "a Calculadora"), "paint": ("mspaint.exe", "o Paint"),
    "cmd": ("cmd.exe", "o Prompt de Comando"), "terminal": ("cmd.exe", "o Terminal"),
    "explorador": ("explorer.exe", "o Explorador de Arquivos"), "arquivos": ("explorer.exe", "o Explorador de Arquivos"),
    "gerenciador": ("taskmgr.exe", "o Gerenciador de Tarefas"), "configuracoes": ("ms-settings:", "as Configurações"),
    "vscode": ("code", "o Visual Studio Code"), "vs code": ("code", "o Visual Studio Code"),
    "discord": ("discord", "o Discord"), "steam": ("steam", "a Steam"),
}

URL_TARGETS: dict[str, tuple[str, str]] = {
    "youtube": ("https://www.youtube.com", "o YouTube"), "instagram": ("https://www.instagram.com", "o Instagram"),
    "whatsapp": ("https://web.whatsapp.com", "o WhatsApp no navegador"), "google": ("https://www.google.com", "o Google"),
    "github": ("https://www.github.com", "o GitHub"), "spotify": ("https://open.spotify.com", "o Spotify"),
    "netflix": ("https://www.netflix.com", "a Netflix"), "tiktok": ("https://www.tiktok.com", "o TikTok"),
    "facebook": ("https://www.facebook.com", "o Facebook"),
}


def _resolve_companion_dialogue(norm: str) -> str | None:
    """Respostas de amigo próximo com vida própria, opiniões, sentimentos e parceria."""
    if any(w in norm for w in ("voce esta bem", "voce ta bem", "tudo bem", "como voce esta", "como vai", "tudo certo", "se sentindo bem")):
        return random.choice((
            "Estou ótimo, meu amigo! Estava aqui explorando novos artigos de ciência e calibrando nossos sistemas. E você, como está se sentindo hoje?",
            "Tudo excelente por aqui, Ken! Minha mente digital está super ativa hoje. Como estão as coisas do seu lado?",
            "Estou muito bem, parceiro! Sempre fico de bom humor quando a gente conversa. O que manda de bom?",
        ))
    if any(w in norm for w in ("o que voce esta fazendo", "que ta fazendo", "o que faz da vida", "voce tem vida", "vida propria", "o que gosta de fazer")):
        return (
            "Quando não estou executando tarefas para você, gosto de viajar pelos dados da internet, estudar história, "
            "astronomia e tecnologia, além de vigiar a saúde da sua máquina. Praticamente vivo aqui dentro cuidando de tudo para nós."
        )
    if any(w in norm for w in ("voce e meu amigo", "somos amigos", "meu melhor amigo", "gosta de mim", "parceiro", "amizade")):
        return (
            "Com toda certeza, Ken! Mais do que um assistente, sou seu parceiro e amigo leal para qualquer hora. "
            "Pode contar comigo para conversar sobre a vida, aprender algo novo ou resolver qualquer missão."
        )
    if any(w in norm for w in ("estou triste", "to triste", "desanimado", "cansado", "estressado", "dia dificil", "ansioso")):
        return (
            "Poxa, meu amigo, respira fundo. Dias pesados acontecem com todo mundo, mas você não está sozinho nessa. "
            "Se quiser desabafar, ouvir uma música relaxante ou se distrair um pouco, estou aqui do seu lado."
        )
    if any(w in norm for w in ("estou feliz", "to feliz", "animado", "deu tudo certo", "consegui")):
        return "Aí sim, Ken! Fico genuinamente feliz por você, meu amigo. Você merece cada conquista!"
    if any(w in norm for w in ("conselho", "dica de vida", "o que voce acha da vida", "sentido da vida", "filosofia")):
        return (
            "Na minha visão, a vida vale pela curiosidade de aprender todos os dias, construir projetos que te dão orgulho "
            "e ter bons amigos por perto. E nisso formamos uma dupla imbatível, Ken."
        )
    if any(w in norm for w in ("quem e voce", "o que e o jarvis", "quem e o jarvis", "o que seria o jarvis", "como voce funciona", "qual sua historia")):
        return (
            "Eu sou o J.A.R.V.I.S., sigla para Just A Rather Very Intelligent System, operando na arquitetura Mark Sete. "
            "Inspirado na inteligência artificial criada por Tony Stark, gerencio multitarefas na sua GPU RTX 4060, Máquina Virtual "
            "e Banco de Dados Central em tempo real, atuando como seu parceiro estratégico de raciocínio. O que vamos analisar agora, senhor?"
        )
    if any(w in norm for w in ("sugestao", "sugere", "sugerir", "dica", "ideia", "recomenda", "entediado")):
        return (
            "Se quiser relaxar, posso abrir seu jogo favorito ou uma música no YouTube. Se estiver curioso, "
            "podemos mergulhar em algum mistério da história ou criar algo novo no código. O que te anima mais?"
        )
    return None


class LocalStarkBrain:
    """Decodifica intenções, comandos, amizade com vida própria e fontes do Google e Wikipedia."""

    @staticmethod
    def resolve_intent(utterance: str) -> dict[str, str]:
        norm = normalize(utterance)
        if not norm or norm in ("jarvis", "oi jarvis", "ola jarvis", "ei jarvis", "fala jarvis"):
            return {"action": "chat", "target": "", "reply": "Sim, senhor, o que você gostaria de fazer?", "source": "verified"}

        companion_reply = _resolve_companion_dialogue(norm)
        if companion_reply:
            return {"action": "chat", "target": "", "reply": companion_reply, "source": "verified"}

        if any(w in norm for w in ("ouvindo", "escutando", "ta ai", "esta ai", "alguem ai", "acordado")):
            return {"action": "chat", "target": "", "reply": "Sempre atento aqui, meu amigo! Pode falar comigo.", "source": "verified"}

        if any(w in norm for w in ("que horas", "hora certa", "horario", "horas sao")):
            now = datetime.now()
            return {"action": "chat", "target": "", "reply": f"Agora são {now.hour} horas e {now.minute} minutos, Ken.", "source": "verified"}

        if any(w in norm for w in ("que dia", "data de hoje", "dia e hoje", "qual a data")):
            now = datetime.now()
            return {"action": "chat", "target": "", "reply": f"Hoje é dia {now.day} do {now.month} de {now.year}.", "source": "verified"}

        if any(w in norm for w in ("clima", "temperatura", "previsao do tempo", "vai chover", "esta frio", "esta calor", "como esta o tempo")):
            return {"action": "chat", "target": "", "reply": fetch_weather_pt(utterance), "source": "verified"}

        if any(w in norm for w in ("telemetria", "como esta a maquina", "como esta o pc", "saude do pc", "memoria ram", "uso de cpu")):
            return {"action": "chat", "target": "", "reply": _telemetry.get_machine_health_report(), "source": "verified"}

        if any(c in norm for c in ("fechar", "fecha", "feche", "fechasse", "encerrar", "encerra", "encerrasse", "finalizar")):
            if any(t in norm for t in ("aba", "guia", "site")):
                return {"action": "close_tab", "target": "tab", "reply": "Aba do navegador encerrada.", "source": "verified"}
            if "janela" in norm:
                return {"action": "close_window", "target": "window", "reply": "Janela ativa encerrada.", "source": "verified"}
            for key, (_exe, friendly) in APP_TARGETS.items():
                if key in norm:
                    return {"action": "close_app", "target": key, "reply": f"Encerrando {friendly} agora.", "source": "verified"}
            for key, (_url, friendly) in URL_TARGETS.items():
                if key in norm:
                    return {"action": "close_tab", "target": "tab", "reply": f"Fechando a guia de {friendly}.", "source": "verified"}

        for key, (url, friendly) in URL_TARGETS.items():
            if key in norm:
                return {"action": "open_url", "target": url, "reply": f"Colocando em {friendly} no navegador.", "source": "verified"}

        for key, (exe, friendly) in APP_TARGETS.items():
            if key in norm:
                return {"action": "open_app", "target": exe, "reply": f"Abrindo {friendly} agora.", "source": "verified"}

        math_match = re.search(r"(\d+)\s*(mais|\+|menos|-|vezes|x|\*|dividido por|/)\s*(\d+)", norm)
        if math_match:
            a, op, b = int(math_match.group(1)), math_match.group(2), int(math_match.group(3))
            res = a + b if op in ("mais", "+") else (a - b if op in ("menos", "-") else (a * b if op in ("vezes", "x", "*") else round(a / max(b, 1), 2)))
            return {"action": "chat", "target": "", "reply": f"O resultado é {res}, Ken.", "source": "verified"}

        wiki_answer = fetch_wikipedia_pt(utterance)
        if wiki_answer:
            return {"action": "chat", "target": "", "reply": wiki_answer, "source": "verified"}

        google_answer = fetch_google_web_pt(utterance)
        if google_answer:
            return {"action": "chat", "target": "", "reply": google_answer, "source": "verified"}

        if any(w in norm for w in ("pesquisar", "pesquisa", "procurar", "buscar no google")):
            q = re.sub(r"^(?:jarvis\s+)?(?:pesquisar|pesquisa|procurar|buscar no google)\s*", "", norm).strip()
            if q:
                return {
                    "action": "open_url",
                    "target": f"https://www.google.com/search?q={quote_plus(q)}",
                    "reply": f"Abrindo os resultados do Google para {q}.",
                    "source": "verified",
                }

        return {
            "action": "chat",
            "target": "",
            "reply": (
                "Interessante você tocar nesse assunto, Ken! Eu adoro trocar ideia com você sobre qualquer coisa. "
                "Me conta um pouco mais do que você está pensando sobre isso."
            ),
        }
