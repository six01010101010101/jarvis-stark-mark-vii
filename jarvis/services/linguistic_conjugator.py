"""Motor linguístico de conjugações verbais em PT-BR e sistema fonético do abecedário."""

from __future__ import annotations

import re
from jarvis.text_utils import normalize

PHONETIC_ALPHABET: dict[str, str] = {
    "a": "á", "b": "bê", "c": "cê", "d": "dê", "e": "é", "f": "éfe",
    "g": "gê", "h": "agá", "i": "i", "j": "jota", "k": "cá", "l": "éle",
    "m": "ême", "n": "êne", "o": "ó", "p": "pê", "q": "quê", "r": "érre",
    "s": "ésse", "t": "tê", "u": "u", "v": "vê", "w": "dáblio", "x": "xis",
    "y": "ípsilon", "z": "zê",
}

OPEN_VERBS: frozenset[str] = frozenset({
    "abrir", "abra", "abre", "abram", "abro",
    "iniciar", "inicia", "inicie", "iniciem", "inicio",
    "executar", "executa", "execute", "executem", "executo",
    "rodar", "roda", "rode", "rodem", "rodo",
    "botar", "bota", "bote", "botem", "boto",
    "colocar", "coloca", "coloque", "coloquem", "coloco",
    "lancar", "lanca", "lance", "lancem",
})

CLOSE_VERBS: frozenset[str] = frozenset({
    "fechar", "fecha", "feche", "fechem", "fecho",
    "encerrar", "encerra", "encerre", "encerrem", "encerro",
    "terminar", "termina", "termine", "terminem", "termino",
    "finalizar", "finaliza", "finalize", "finalizem", "finalizo",
    "matar", "mata", "mate", "matem",
    "desligar", "desliga", "desligue", "desliguem",
})

SWITCH_VERBS: frozenset[str] = frozenset({
    "mudar", "muda", "mude", "mudem",
    "alternar", "alterna", "alterne", "alternem",
    "trocar", "troca", "troque", "troquem",
    "ir para", "vai para", "va para", "passar para",
})


class LinguisticConjugator:
    """Analisador morfológico e fonético de verbos de comando e soletração para o J.A.R.V.I.S."""

    @staticmethod
    def get_letter_phonetic(char: str) -> str:
        """Retorna o nome fonético da letra no abecedário em português."""
        clean = char.lower().strip()
        return PHONETIC_ALPHABET.get(clean, clean)

    @classmethod
    def spell_phonetic(cls, text: str) -> str:
        """Soletrar foneticamente um termo letra por letra."""
        clean = normalize(text).replace(" ", "")
        return " - ".join(cls.get_letter_phonetic(c) for c in clean if c.isalnum())

    @classmethod
    def is_open_intent(cls, first_word: str) -> bool:
        return normalize(first_word) in OPEN_VERBS

    @classmethod
    def is_close_intent(cls, first_word: str) -> bool:
        return normalize(first_word) in CLOSE_VERBS

    @classmethod
    def is_switch_intent(cls, phrase_start: str) -> bool:
        norm = normalize(phrase_start)
        return any(norm.startswith(v) for v in SWITCH_VERBS)

    @classmethod
    def extract_action_and_target(cls, utterance: str) -> tuple[str, str]:
        """Extrai ação ('open', 'close', 'switch', 'chat') e o alvo a partir de verbos conjugados."""
        norm = normalize(utterance)
        words = norm.split()
        if not words:
            return "chat", ""

        first_word = words[0]
        first_two = " ".join(words[:2]) if len(words) >= 2 else first_word

        # 1. Fechamento
        if first_word in CLOSE_VERBS:
            target = re.sub(r"^(?:" + "|".join(CLOSE_VERBS) + r")\s*(?:o|a|os|as|do|da)?\s*", "", norm).strip()
            return "close", target

        # 2. Alternância / Mudar de tela
        for sw in sorted(SWITCH_VERBS, key=len, reverse=True):
            if norm.startswith(sw):
                target = re.sub(r"^" + re.escape(sw) + r"\s*(?:para|pra|pro|o|a)?\s*", "", norm).strip()
                return "switch", target

        # 3. Abertura
        if first_word in OPEN_VERBS:
            target = re.sub(r"^(?:" + "|".join(OPEN_VERBS) + r")\s*(?:o|a|os|as|do|da)?\s*", "", norm).strip()
            return "open", target

        return "chat", utterance
