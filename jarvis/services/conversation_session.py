"""Gerenciador de sessão de conversa contínua, Ciclo de Paciência (10s) e Intuição de Raciocínio."""

from __future__ import annotations

import threading
import time
from typing import ClassVar

from jarvis.text_utils import normalize


class ConversationSession:
    """Controla o Ciclo de Paciência pós-fala (10s) e avalia a complexidade das perguntas."""

    CLOSE_TRIGGERS: ClassVar[tuple[str, ...]] = (
        "obrigado", "obrigada", "valeu", "era isso", "era so isso", "era só isso",
        "cancela", "cancelar", "pode descansar", "tchau", "nada nao", "nada não",
        "nao precisa", "não precisa", "so isso", "só isso", "dispensado",
    )

    DEEP_KEYWORDS: ClassVar[tuple[str, ...]] = (
        "explique", "analise", "codigo", "código", "arquitetura", "banco", "comparar",
        "pesquise", "relatorio", "relatório", "por que", "como funciona", "otimize",
        "debug", "historia", "história", "quem descobriu", "quem foi", "previsao", "clima",
    )

    def __init__(
        self,
        timeout_seconds: float = 10.0,
        patience_seconds: float | None = None,
        silence_tolerance: float = 2.2,
    ) -> None:
        base_patience = patience_seconds if patience_seconds is not None else timeout_seconds
        self.patience_seconds = float(base_patience)
        self.silence_tolerance = float(silence_tolerance)
        self._default_timeout = float(base_patience)
        self._lock = threading.Lock()
        self._active = False
        self._awaiting_answer = False
        self._pending_intent: str | None = None
        self._last_activity = 0.0
        self.active_until = 0.0
        self.is_in_patience_cycle = False

    def set_patience_seconds(self, seconds: float) -> None:
        """Ajusta o tempo do Ciclo de Paciência em tempo real pelo slider da HUD."""
        with self._lock:
            self.patience_seconds = max(2.0, min(60.0, float(seconds)))
            self._default_timeout = self.patience_seconds
            if self._active:
                self.active_until = time.time() + self.patience_seconds

    def activate_patience_window(self) -> None:
        """Acionado assim que o Jarvis termina de falar uma resposta (10s de escuta contínua)."""
        with self._lock:
            now_mono = time.monotonic()
            self._active = True
            self._last_activity = now_mono
            self.active_until = time.time() + self.patience_seconds
            self.is_in_patience_cycle = True

    def should_listen_without_wake_word(self) -> bool:
        """Retorna True se ainda estiver dentro da janela do Ciclo de Paciência ou diálogo ativo."""
        with self._lock:
            return self._is_active_unlocked()

    def remaining_patience(self) -> float:
        with self._lock:
            if not self._is_active_unlocked():
                return 0.0
            elapsed = time.monotonic() - self._last_activity
            return round(max(0.0, self._default_timeout - elapsed), 1)

    @classmethod
    def evaluate_query_complexity(cls, query: str) -> str:
        """
        Define a intuição do Jarvis:
        - 'FAST': Perguntas curtas/comandos (< 12 palavras) -> Resposta imediata (< 1.5s)
        - 'DEEP': Perguntas complexas/web/história -> Emite frase curta de raciocínio e elabora
        """
        words = query.strip().split()
        lower_q = query.lower()
        if len(words) < 12 and not any(k in lower_q for k in cls.DEEP_KEYWORDS):
            return "FAST"
        return "DEEP"

    def start_dialogue(self, awaiting_answer: bool = False, pending_intent: str | None = None) -> None:
        with self._lock:
            self._active = True
            self._awaiting_answer = awaiting_answer
            self._pending_intent = pending_intent
            self._last_activity = time.monotonic()
            self.active_until = time.time() + self.patience_seconds
            self.is_in_patience_cycle = True

    def mark_interaction(self, awaiting_answer: bool = False, pending_intent: str | None = None) -> None:
        with self._lock:
            self._active = True
            self._awaiting_answer = awaiting_answer
            if pending_intent is not None or not awaiting_answer:
                self._pending_intent = pending_intent
            self._last_activity = time.monotonic()
            self.active_until = time.time() + self.patience_seconds
            self.is_in_patience_cycle = True

    def close_dialogue(self) -> None:
        with self._lock:
            self._active = False
            self._awaiting_answer = False
            self._pending_intent = None
            self.is_in_patience_cycle = False
            self.active_until = 0.0

    def is_active(self) -> bool:
        with self._lock:
            return self._is_active_unlocked()

    def _is_active_unlocked(self) -> bool:
        if not self._active:
            return False
        timeout = self._default_timeout * 1.4 if self._awaiting_answer else self._default_timeout
        if time.monotonic() - self._last_activity > timeout:
            self._active = False
            self._awaiting_answer = False
            self._pending_intent = None
            self.is_in_patience_cycle = False
            return False
        return True

    def is_awaiting_answer(self) -> bool:
        with self._lock:
            return self._is_active_unlocked() and self._awaiting_answer

    def get_pending_intent(self) -> str | None:
        with self._lock:
            return self._pending_intent

    def resolve_utterance_with_pending(self, utterance: str) -> str:
        with self._lock:
            intent = self._pending_intent
            self._pending_intent = None
            self._awaiting_answer = False
        if not intent:
            return utterance
        norm = normalize(utterance)
        if intent == "open_app":
            if any(s in norm for s in ("youtube", "instagram", "whatsapp", "zap", "insta", "google", "spotify", "netflix", "tiktok")):
                return utterance
            if not any(norm.startswith(v) for v in ("abra", "abrir", "abre", "iniciar", "inicia", "executar", "executa")):
                return f"abrir {utterance}"
        elif intent == "close_app":
            if not any(norm.startswith(v) for v in ("feche", "fechar", "fecha", "encerrar", "encerra", "finalizar", "mata")):
                return f"fechar {utterance}"
        elif intent == "open_url":
            if not any(norm.startswith(v) for v in ("abrir", "site", "acessar", "http")):
                return f"abrir site {utterance}"
        elif intent == "play_media":
            if not any(norm.startswith(v) for v in ("tocar", "colocar", "ouvir", "video", "youtube")):
                return f"tocar {utterance}"
        elif intent == "record_note":
            if not any(norm.startswith(v) for v in ("anotar", "anote", "criar nota", "salvar nota")):
                return f"anotar {utterance}"
        return utterance

    def is_close_phrase(self, utterance: str) -> bool:
        norm = normalize(utterance)
        return any(trigger in norm for trigger in self.CLOSE_TRIGGERS)
