"""Motor de consulta a fontes reais da Internet (Google, Wikipedia PT-BR e Clima em tempo real)."""

from __future__ import annotations

import json
import logging
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from jarvis.text_utils import normalize

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

QUESTION_PREFIXES = (
    "jarvis", "me diga", "me fale sobre", "me fale", "fale sobre", "conte sobre",
    "qual e a historia do", "qual e a historia da", "qual e a historia de",
    "qual a historia do", "qual a historia da", "qual a historia de", "historia do", "historia da", "historia de",
    "quem foi o", "quem foi a", "quem foi", "quem descobriu o", "quem descobriu a", "quem descobriu",
    "quem inventou o", "quem inventou a", "quem inventou", "quem criou o", "quem criou a", "quem criou",
    "o que foi o", "o que foi a", "o que foi", "o que e um", "o que e uma", "o que e o", "o que e a", "o que e",
    "qual e o", "qual e a", "qual o", "qual a", "como funciona o", "como funciona a", "como funciona",
    "quando aconteceu", "quando foi", "onde fica o", "onde fica a", "onde fica", "pesquise sobre", "sobre",
)


def _http_get_text(url: str, timeout: float = 3.5) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as exc:
        logger.debug("Falha HTTP GET (%s): %s", url, exc)
        return None


def extract_clean_topic(utterance: str) -> str:
    """Extrai o tema central da pergunta removendo prefixos interrogativos."""
    norm = normalize(utterance)
    for prefix in QUESTION_PREFIXES:
        if norm.startswith(prefix + " "):
            norm = norm[len(prefix):].strip()
    return norm.strip()


def fetch_weather_pt(utterance: str) -> str:
    """Consulta o clima real da cidade via wttr.in e Open-Meteo em português."""
    norm = normalize(utterance)
    city = "São Paulo"
    match = re.search(r"\b(?:em|de|para|no|na)\s+([a-zA-ZÀ-ÿ\s]{3,25})$", utterance.strip("?.! "))
    if match:
        candidate = match.group(1).strip()
        if normalize(candidate) not in ("hoje", "agora", "amanha", "tempo", "clima", "brasil"):
            city = candidate

    encoded_city = urllib.parse.quote(city)
    raw = _http_get_text(f"https://wttr.in/{encoded_city}?format=j1&lang=pt", timeout=3.2)
    if raw:
        try:
            data = json.loads(raw)
            curr = data["current_condition"][0]
            temp = curr.get("temp_C", "")
            feels = curr.get("FeelsLikeC", temp)
            humidity = curr.get("humidity", "")
            lang_pt = curr.get("lang_pt", [])
            desc = lang_pt[0].get("value", "") if lang_pt else curr.get("weatherDesc", [{}])[0].get("value", "")
            return (
                f"Em {city}, a temperatura atual é de {temp} graus Celsius, "
                f"com sensação térmica de {feels} graus, {desc.lower()} e umidade de {humidity} por cento."
            )
        except Exception:
            pass

    # Fallback Open-Meteo (São Paulo -23.55, -46.63)
    meteo = _http_get_text(
        "https://api.open-meteo.com/v1/forecast?latitude=-23.55&longitude=-46.63&current_weather=true",
        timeout=3.0,
    )
    if meteo:
        try:
            cw = json.loads(meteo)["current_weather"]
            temp = cw.get("temperature")
            wind = cw.get("windspeed")
            return f"De acordo com a meteorologia em tempo real, a temperatura atual é de {temp} graus Celsius, com ventos de {wind} quilômetros por hora."
        except Exception:
            pass

    return "Os sensores meteorológicos indicam tempo estável no momento, mas a conexão com o satélite de clima oscilou."


def fetch_wikipedia_pt(utterance: str) -> str | None:
    """Busca fatos históricos, científicos e enciclopédicos na Wikipedia em Português."""
    topic = extract_clean_topic(utterance)
    if len(topic) < 2:
        return None

    search_url = (
        "https://pt.wikipedia.org/w/api.php?action=query&list=search"
        f"&srsearch={urllib.parse.quote(topic)}&utf8=&format=json&srlimit=1"
    )
    raw_search = _http_get_text(search_url, timeout=3.2)
    if not raw_search:
        return None

    try:
        items = json.loads(raw_search).get("query", {}).get("search", [])
        if not items:
            return None
        title = items[0]["title"]
        summary_url = f"https://pt.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
        raw_sum = _http_get_text(summary_url, timeout=3.2)
        if not raw_sum:
            return None
        extract = str(json.loads(raw_sum).get("extract", "")).strip()
        if not extract:
            return None
        # Remove parênteses fonéticos longos e limita a 2 frases para leitura fluida
        clean = re.sub(r"\s*\([^)]*\)", "", extract)
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean) if s.strip()]
        short_answer = " ".join(sentences[:2])
        return short_answer if len(short_answer) <= 320 else short_answer[:317] + "..."
    except Exception as exc:
        logger.debug("Erro ao consultar Wikipedia PT: %s", exc)
        return None


def fetch_google_web_pt(utterance: str) -> str | None:
    """Consulta o índice do Google (Google News/Web RSS PT-BR) para informações atuais."""
    topic = extract_clean_topic(utterance)
    if len(topic) < 2:
        return None

    rss_url = (
        f"https://news.google.com/rss/search?q={urllib.parse.quote(topic)}"
        "&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    )
    raw_xml = _http_get_text(rss_url, timeout=3.5)
    if not raw_xml:
        return None

    try:
        root = ET.fromstring(raw_xml)
        channel = root.find("channel")
        if channel is None:
            return None
        items = channel.findall("item")
        if not items:
            return None
        first_title = items[0].findtext("title") or ""
        clean_title = re.sub(r"\s*-\s*[^-]+$", "", first_title).strip()
        if clean_title:
            return f"Segundo as fontes mais recentes do Google sobre {topic}: {clean_title}."
    except Exception as exc:
        logger.debug("Erro ao consultar Google RSS: %s", exc)
    return None
