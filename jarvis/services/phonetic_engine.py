"""Motor fonético de alta tolerância para variações do Português Brasileiro (PT-BR)."""

from __future__ import annotations

import difflib
import re
import unicodedata

# Substituições fonéticas ordenadas para equivalência fonológica brasileira
PHONETIC_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"ch|sh", re.I), "x"),
    (re.compile(r"c(?=[eéií])|ç|ss|sç|sc", re.I), "s"),
    (re.compile(r"c(?=[aáoóuú])|qu(?=[eéií])|k", re.I), "k"),
    (re.compile(r"g(?=[eéií])|j", re.I), "j"),
    (re.compile(r"gu(?=[eéií])", re.I), "g"),
    (re.compile(r"ph", re.I), "f"),
    (re.compile(r"lh", re.I), "l"),
    (re.compile(r"nh", re.I), "n"),
    (re.compile(r"rr", re.I), "r"),
    (re.compile(r"w", re.I), "v"),
    (re.compile(r"y", re.I), "i"),
    (re.compile(r"z\b", re.I), "s"),
    (re.compile(r"[eé]\b", re.I), "i"),
    (re.compile(r"[oó]\b", re.I), "u"),
)


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def phonetic_key(word: str) -> str:
    """Gera a chave fonética de uma palavra para comparação fonológica."""
    clean = _strip_accents(word.lower().strip())
    if not clean:
        return ""

    encoded = clean
    for pattern, replacement in PHONETIC_RULES:
        encoded = pattern.sub(replacement, encoded)

    # Remove consoantes repetidas consecutivas (ex: "kk" -> "k")
    dedup = re.sub(r"(.)\1+", r"\1", encoded)
    return dedup


class PhoneticEngine:
    """Decodifica pronúncias rápidas, contrações e gírias fonéticas em 0ms."""

    def __init__(self, alias_map: dict[str, str] | None = None) -> None:
        self._aliases: dict[str, str] = {
            "fortinaite": "fortnite", "fortinai": "fortnite", "forti": "fortnite", "fort": "fortnite",
            "mainecraft": "minecraft", "minecrafe": "minecraft", "mine": "minecraft",
            "bloco dinota": "bloco de notas", "bloco di nota": "bloco de notas", "bloco notas": "bloco de notas", "bloco": "bloco de notas",
            "calque": "calculadora", "calcula": "calculadora", "calc": "calculadora",
            "zap": "whatsapp", "whats": "whatsapp", "wats": "whatsapp", "uats": "whatsapp",
            "insta": "instagram", "feice": "facebook",
            "iutubi": "youtube", "iutube": "youtube",
            "ceessi": "counter-strike", "csdois": "counter-strike",
            "discordi": "discord", "ispotifai": "spotify", "spotfy": "spotify",
            "abre": "abrir", "inicia": "iniciar", "executa": "executar",
            "fecha": "fechar", "encerra": "encerrar", "toca": "tocar",
            "pesquise": "pesquisar", "navegador": "chrome",
            "chave": "jarvis", "chaves": "jarvis", "javi": "jarvis", "jardis": "jarvis", "charles": "jarvis",
        }
        if alias_map:
            self._aliases.update(alias_map)

    def normalize_utterance(self, utterance: str) -> str:
        """Aplica correções fonéticas imediatas palavra por palavra."""
        words = utterance.lower().split()
        if not words:
            return utterance

        result: list[str] = []
        i = 0
        while i < len(words):
            # Verifica bigramas (duas palavras consecutivas)
            if i + 1 < len(words):
                bigram = f"{words[i]} {words[i+1]}"
                if bigram in self._aliases:
                    result.append(self._aliases[bigram])
                    i += 2
                    continue

            unigram = words[i]
            matched = self._aliases.get(unigram)
            if matched:
                result.append(matched)
            else:
                # Tenta casamento fonético aproximado se houver similaridade alta
                best_alias = self._match_phonetic_alias(unigram)
                result.append(best_alias if best_alias else unigram)
            i += 1

        return " ".join(result)

    def _match_phonetic_alias(self, word: str, min_ratio: float = 0.82) -> str | None:
        target_key = phonetic_key(word)
        if len(target_key) < 3:
            return None

        best_match: str | None = None
        best_score = 0.0

        for alias, canonical in self._aliases.items():
            alias_key = phonetic_key(alias)
            ratio = difflib.SequenceMatcher(None, target_key, alias_key).ratio()
            if ratio > best_score and ratio >= min_ratio:
                best_score = ratio
                best_match = canonical

        return best_match
