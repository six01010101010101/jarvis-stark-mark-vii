"""Motor de autocorreção fonética e ortográfica de comandos de voz do Jarvis."""

from __future__ import annotations

import re
from typing import ClassVar

from jarvis.services.phonetic_engine import PhoneticEngine
from jarvis.text_utils import normalize


class SpeechCorrector:
    """Corrige distorções fonéticas do microfone, variações de 'Jarvis' e nomes truncados."""

    def __init__(self, phonetic_engine: PhoneticEngine | None = None) -> None:
        self._phonetic = phonetic_engine or PhoneticEngine()

    # Variações fonéticas comuns captadas pelo Google STT no lugar de "Jarvis"
    WAKE_VARIANTS: ClassVar[tuple[str, ...]] = (
        "chave", "chaves", "garvis", "jarve", "javes", "iarp", "charles",
        "serviço", "jarbas", "service", "dádivas", "jardis", "davis",
        "artes", "árvores", "jovens", "larvas", "já", "jar", "ja", "iarvis",
    )

    # Dicionário de expansões fonéticas para aplicativos e jogos populares
    APP_EXPANSIONS: ClassVar[tuple[tuple[re.Pattern[str], str], ...]] = (
        (re.compile(r"\b(?:fort|forti|fortinai)\b", re.I), "fortnite"),
        (re.compile(r"\b(?:mine|minecraf)\b", re.I), "minecraft"),
        (re.compile(r"\bbloco\s+(?:di\s*notas?|de\s*notas?|dinotas?|notas?)\b", re.I), "bloco de notas"),
        (re.compile(r"\b(?:whats|zap|whatssap|watssap|wats)\b", re.I), "whatsapp"),
        (re.compile(r"\b(?:tube|youtub|iotube|youtubiu)\b", re.I), "youtube"),
        (re.compile(r"\b(?:calque|calcula)\b", re.I), "calculadora"),
        (re.compile(r"\b(?:insta)\b", re.I), "instagram"),
        (re.compile(r"\b(?:face)\b", re.I), "facebook"),
        (re.compile(r"\b(?:tik|tok)\b", re.I), "tiktok"),
        (re.compile(r"\b(?:cs\s*go|cs2|cs)\b", re.I), "counter-strike"),
        (re.compile(r"\b(?:discordi|disc)\b", re.I), "discord"),
        (re.compile(r"\b(?:spotfy|spot)\b", re.I), "spotify"),
    )

    def repair_wake_word(self, utterance: str) -> str:
        """Converte termos foneticamente equivalentes ao início ou final da frase para 'jarvis'."""
        cleaned = normalize(utterance)
        cleaned = re.sub(r"\b(?:ja\s+vi|ja\s+vai|da\s+vi|dá\s+vi)\b", "jarvis", cleaned)
        tokens = cleaned.split()
        if not tokens:
            return utterance

        from jarvis.text_utils import is_wake_word
        for i, token in enumerate(tokens):
            if is_wake_word(token) or token in self.WAKE_VARIANTS:
                tokens[i] = "jarvis"
                break

        return " ".join(tokens)

    def expand_abbreviations(self, utterance: str) -> str:
        """Expande termos cortados pelo microfone (ex: 'fort' -> 'fortnite')."""
        result = utterance
        for pattern, replacement in self.APP_EXPANSIONS:
            result = pattern.sub(replacement, result)
        return result

    def correct(self, utterance: str) -> str:
        """Pipeline completa de autocorreção em tempo real com motor fonético PT-BR."""
        step1 = self.repair_wake_word(utterance)
        step2 = self.expand_abbreviations(step1)
        step3 = self._phonetic.normalize_utterance(step2)
        cleaned = " ".join(step3.split())
        return cleaned.replace("bloco de notas de notas", "bloco de notas")
