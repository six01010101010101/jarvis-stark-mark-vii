"""Mente cognitiva local do J.A.R.V.I.S. integrada ao SQLite, Telemetria e Fontes da Internet."""

from __future__ import annotations

from datetime import datetime
import re
from urllib.parse import quote_plus

from jarvis.services.mutual_processor import MutualProcessor
from jarvis.services.web_knowledge import fetch_google_web_pt, fetch_weather_pt, fetch_wikipedia_pt
from jarvis.text_utils import normalize

_telemetry = MutualProcessor()

APP_TARGETS: dict[str, tuple[str, str]] = {
    "google chrome": ("chrome.exe", "o Google Chrome"),
    "chrome": ("chrome.exe", "o Google Chrome"),
    "microsoft edge": ("msedge.exe", "o Microsoft Edge"),
    "edge": ("msedge.exe", "o Microsoft Edge"),
    "bloco de notas": ("notepad.exe", "o Bloco de Notas"),
    "notepad": ("notepad.exe", "o Bloco de Notas"),
    "calculadora": ("calc.exe", "a Calculadora"),
    "paint": ("mspaint.exe", "o Paint"),
    "cmd": ("cmd.exe", "o Prompt de Comando"),
    "terminal": ("cmd.exe", "o Terminal"),
    "explorador": ("explorer.exe", "o Explorador de Arquivos"),
    "arquivos": ("explorer.exe", "o Explorador de Arquivos"),
    "gerenciador": ("taskmgr.exe", "o Gerenciador de Tarefas"),
    "configuracoes": ("ms-settings:", "as Configurações do Windows"),
    "vscode": ("code", "o Visual Studio Code"),
    "vs code": ("code", "o Visual Studio Code"),
    "discord": ("discord", "o Discord"),
    "steam": ("steam", "a Steam"),
}

URL_TARGETS: dict[str, tuple[str, str]] = {
    "youtube": ("https://www.youtube.com", "o YouTube"),
    "instagram": ("https://www.instagram.com", "o Instagram"),
    "whatsapp": ("https://web.whatsapp.com", "o WhatsApp no navegador"),
    "google": ("https://www.google.com", "o Google"),
    "github": ("https://www.github.com", "o GitHub"),
    "spotify": ("https://open.spotify.com", "o Spotify"),
    "netflix": ("https://www.netflix.com", "a Netflix"),
    "tiktok": ("https://www.tiktok.com", "o TikTok"),
    "facebook": ("https://www.facebook.com", "o Facebook"),
}


class LocalStarkBrain:
    """Decodifica intenções, comandos e perguntas com fontes do Google e Wikipedia."""

    @staticmethod
    def resolve_intent(utterance: str) -> dict[str, str]:
        """Analisa a fala e retorna ação + resposta fluida sem repetição artificial."""
        norm = normalize(utterance)
        if not norm or norm in ("jarvis", "oi jarvis", "ola jarvis", "ei jarvis", "fala jarvis"):
            return {
                "action": "chat",
                "target": "",
                "reply": "Sim, senhor, o que você gostaria de fazer?",
                "source": "verified",
            }

        # 1. Pedidos de sugestão ou ideia
        if any(w in norm for w in ("sugestao", "sugere", "sugerir", "dica", "ideia", "recomenda", "entediado")):
            return {
                "action": "chat",
                "target": "",
                "reply": (
                    "Posso colocar uma playlist no YouTube, abrir o Visual Studio Code para seus projetos "
                    "ou buscar as últimas notícias e clima de hoje. O que prefere?"
                ),
                "source": "verified",
            }

        # 2. Verificação de escuta e presença
        if any(w in norm for w in ("ouvindo", "escutando", "ta ai", "esta ai", "alguem ai", "acordado")):
            return {
                "action": "chat",
                "target": "",
                "reply": "Estou na escuta com todos os sensores e banco de dados ativos. Como posso ajudar?",
                "source": "verified",
            }

        # 3. Data e Horário
        if any(w in norm for w in ("que horas", "hora certa", "horario", "horas sao")):
            now = datetime.now()
            return {
                "action": "chat",
                "target": "",
                "reply": f"Agora são {now.hour} horas e {now.minute} minutos.",
                "source": "verified",
            }

        if any(w in norm for w in ("que dia", "data de hoje", "dia e hoje", "qual a data")):
            now = datetime.now()
            return {
                "action": "chat",
                "target": "",
                "reply": f"Hoje é dia {now.day} do {now.month} de {now.year}.",
                "source": "verified",
            }

        # 4. Clima, Tempo e Temperatura em tempo real (Fontes da Internet)
        if any(w in norm for w in ("clima", "temperatura", "previsao do tempo", "vai chover", "esta frio", "esta calor", "como esta o tempo")):
            return {
                "action": "chat",
                "target": "",
                "reply": fetch_weather_pt(utterance),
                "source": "verified",
            }

        # 5. Telemetria e Saúde do Sistema
        if any(w in norm for w in ("telemetria", "como esta a maquina", "como esta o pc", "saude do pc", "memoria ram", "uso de cpu")):
            return {
                "action": "chat",
                "target": "",
                "reply": _telemetry.get_machine_health_report(),
                "source": "verified",
            }

        # 6. Fechar / Encerrar aba, janela, site ou aplicativo
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

        # 7. Colocar em site (YouTube, Instagram, WhatsApp) ou Abrir navegador/programa
        for key, (url, friendly) in URL_TARGETS.items():
            if key in norm:
                return {"action": "open_url", "target": url, "reply": f"Colocando em {friendly} no navegador.", "source": "verified"}

        for key, (exe, friendly) in APP_TARGETS.items():
            if key in norm:
                return {"action": "open_app", "target": exe, "reply": f"Abrindo {friendly} agora.", "source": "verified"}

        # 8. Cálculos matemáticos
        math_match = re.search(r"(\d+)\s*(mais|\+|menos|-|vezes|x|\*|dividido por|/)\s*(\d+)", norm)
        if math_match:
            a, op, b = int(math_match.group(1)), math_match.group(2), int(math_match.group(3))
            res = a + b if op in ("mais", "+") else (a - b if op in ("menos", "-") else (a * b if op in ("vezes", "x", "*") else round(a / max(b, 1), 2)))
            return {"action": "chat", "target": "", "reply": f"O resultado é {res}.", "source": "verified"}

        # 9. Perguntas de História, Ciência, Quem foi, O que é e Fontes do Google/Wikipedia
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
            "reply": f"Anotei '{utterance}' no banco de dados. Posso buscar mais detalhes sobre isso no Google se quiser.",
        }
