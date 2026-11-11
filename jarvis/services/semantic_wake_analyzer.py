"""Analisador semântico para distinguir 'Chamar o Jarvis' de 'Perguntar SOBRE o Jarvis'."""

from __future__ import annotations

import re

from jarvis.text_utils import WAKE_ROOTS, is_wake_word, normalize


class SemanticWakeAnalyzer:
    """Impede que perguntas como 'Jarvis, o que seria o Jarvis?' caiam em saudações vazias."""

    QUESTION_INDICATORS = {
        "o que", "oq", "qual", "quais", "quem", "como", "por que", "porque", "por que",
        "onde", "quando", "seria", "funciona", "explica", "explique", "fale sobre",
        "me diga", "me diz", "acha", "opiniao", "opinião", "conselho", "ajuda", "ajude", "pode",
        "o que e", "o que e o", "quem e", "quem e o", "o que seria", "como funciona",
        "what", "who", "how", "why", "explain", "tell me",
    }

    @classmethod
    def is_real_question(cls, text: str) -> bool:
        """Verifica se a frase possui pronomes interrogativos ou pontuação de dúvida."""
        low = text.lower()
        return "?" in text or any(q in low for q in cls.QUESTION_INDICATORS)

    @classmethod
    def analyze_utterance(cls, raw_text: str, in_patience_window: bool = False, strict_wake: bool = True) -> dict[str, object]:
        """Classifica a fala em PURE_WAKE (apenas vocativo) ou DEEP_CONVERSATION (pergunta/comando)."""
        text = str(raw_text or "").strip()
        low_norm = normalize(text)
        low_norm = re.sub(r"\b(?:ja\s+vi|já\s+vi|ja\s+vai|já\s+vai|da\s+vi|dá\s+vi)\b", "jarvis", low_norm)
        tokens = low_norm.split()
        wake_indices = [i for i, t in enumerate(tokens) if is_wake_word(t)]
        has_wake = bool(wake_indices)

        if strict_wake and not has_wake and not in_patience_window:
            return {"should_process": False, "intent_mode": "IGNORE", "clean_query": ""}

        clean_query = text
        if has_wake:
            first_idx = wake_indices[0]
            if first_idx <= 2:
                # Remove apenas o primeiro vocativo de ativação mantendo a oração íntegra
                pattern = r"^\s*(?:oi|ola|olá|hey|ok|e ai|e aí|fala)?\s*(?:" + "|".join(WAKE_ROOTS) + r"\w*|chaves?|xaves?)[,!?.:\s]*"
                clean_query = re.sub(pattern, "", text, count=1, flags=re.IGNORECASE).strip()

        norm_query = normalize(clean_query)
        # Se após retirar o vocativo não restou nada, é estritamente uma chamada pura
        if not norm_query or norm_query in ("jarvis", "oi jarvis", "ola jarvis"):
            return {"should_process": True, "intent_mode": "PURE_WAKE", "clean_query": "Jarvis"}

        return {"should_process": True, "intent_mode": "DEEP_CONVERSATION", "clean_query": clean_query}
