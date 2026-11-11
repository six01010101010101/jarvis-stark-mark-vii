"""Utilitários de normalização de texto, reconhecimento fonético de wake words e comandos."""

from __future__ import annotations

import difflib
import re
import unicodedata

WAKE_ROOTS = ("jarv", "iarv", "jarb", "iarb", "javi", "chav", "xav")
WAKE_WORDS = {
    # Nomes canônicos e variações diretas
    "jarvis", "jarbas", "iarvis", "iarbas", "jarves", "jervis",
    "jarvi", "jarviz", "garvis", "iarve", "jarve", "jar", "jari",
    # Transcrições fonéticas frequentes em PT-BR pelo Google STT
    "chave", "chaves", "chavez", "xave", "xaves", "xavez",
    "javi", "javis", "javes", "jabes", "java", "jardis",
    "charles", "charle", "xarles", "davis", "davi", "daviz", "david",
    "travis", "traves", "arvis", "servico", "serviço",
}
GREETING_PREFIXES = (
    "oi", "ola", "olá", "e", "ai", "aí", "ei", "opa", "fala", "olha",
    "por", "favor", "por favor", "por gentileza", "bom", "dia", "boa", "tarde", "noite",
)


def normalize(text: str) -> str:
    """Converte para minúsculas, remove acentos, pontuação e espaços extras."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    without_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    cleaned = re.sub(r"[^\w\s]", " ", without_accents)
    return " ".join(cleaned.split())


def text_after(text: str, keyword: str) -> str:
    """Retorna o trecho que vem após a palavra-chave (comparação normalizada)."""
    words = text.split()
    key_words = normalize(keyword).split()
    size = len(key_words)
    for index in range(len(words) - size + 1):
        if [normalize(w) for w in words[index:index + size]] == key_words:
            return " ".join(words[index + size:]).strip()
    return ""


def is_wake_word(token: str, fuzzy_ratio: float = 0.75) -> bool:
    """Verifica se uma palavra corresponde a variações, fonética ou aproximação de 'Jarvis'."""
    norm = normalize(token)
    if not norm:
        return False
    if norm in WAKE_WORDS or any(norm.startswith(root) for root in WAKE_ROOTS):
        return True

    # Algoritmo de fuzzy ratio do repositório de referência (repo_4 - isair/jarvis)
    if len(norm) >= 3:
        ratio = difflib.SequenceMatcher(a="jarvis", b=norm).ratio()
        if ratio >= fuzzy_ratio:
            return True

    try:
        from jarvis.services.phonetic_engine import phonetic_key
        key = phonetic_key(norm)
        if key in ("jarvis", "jarvi", "xavis", "xavi", "javis", "javi", "davis", "davi", "xarles", "zavis"):
            return True
    except ImportError:
        pass
    return False


def extract_wake_and_command(utterance: str, _wake_word: str = "jarvis") -> tuple[bool, str]:
    """Identifica se a wake word foi dita (mesmo foneticamente distorcida) e extrai o comando anexo."""
    norm = normalize(utterance)
    # Trata transcrições fonéticas comuns de duas palavras captadas pelo Google STT
    norm = re.sub(r"\b(?:ja\s+vi|já\s+vi|ja\s+vai|já\s+vai|da\s+vi|dá\s+vi)\b", "jarvis", norm)
    tokens = norm.split()
    wake_indices = [i for i, t in enumerate(tokens) if is_wake_word(t)]
    if not wake_indices:
        return False, ""

    first_wake = wake_indices[0]
    after = tokens[first_wake + 1:]
    before = tokens[:first_wake]

    # Se a palavra Jarvis é o sujeito/objeto de pergunta (ex: "o que é o Jarvis?"), não remove a palavra
    is_q = any(q in norm for q in ("o que", "quem", "como", "por que", "qual", "seria", "funciona", "explica", "acha")) or "?" in utterance
    if before and not after and is_q:
        return True, norm

    remaining = after if after else before

    while remaining and remaining[0] in GREETING_PREFIXES:
        remaining.pop(0)

    return True, " ".join(remaining).strip()


def split_compound_commands(command_str: str) -> list[str]:
    """Divide comandos compostos (ex: 'abrir bloco de notas e calculadora')."""
    raw_parts = [command_str]
    for delimiter in (" e tambem ", " e depois ", " e "):
        new_parts = []
        for part in raw_parts:
            new_parts.extend(part.split(delimiter))
        raw_parts = new_parts

    parts: list[str] = []
    current_action = ""
    for part in raw_parts:
        p = part.strip()
        if not p:
            continue
        words = p.split()
        action_verbs = (
            "abrir", "abre", "iniciar", "inicia", "executar", "executa", "lançar", "lança", "rodar", "roda",
            "fechar", "fecha", "encerrar", "encerra", "finalizar", "finaliza", "matar", "mata", "terminar", "termina",
            "tocar", "colocar",
        )
        if words[0] in action_verbs:
            current_action = words[0]
            parts.append(p)
        else:
            if current_action:
                parts.append(f"{current_action} {p}")
            else:
                parts.append(p)
    return parts
