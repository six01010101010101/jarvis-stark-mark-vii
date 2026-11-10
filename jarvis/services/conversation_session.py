"""Gerenciador de sessão de conversa contínua e diálogo multi-turn do J.A.R.V.I.S."""

from __future__ import annotations

import threading
import time
from typing import ClassVar

from jarvis.text_utils import normalize


class ConversationSession:
    """Mantém o assistente ouvindo respostas imediatas sem exigir que o usuário repita a wake word."""

    CLOSE_TRIGGERS: ClassVar[tuple[str, ...]] = (
        "obrigado", "obrigada", "valeu", "era isso", "era so isso", "era só isso",
        "cancela", "cancelar", "pode descansar", "tchau", "nada nao", "nada não",
        "nao precisa", "não precisa", "so isso", "só isso", "dispensado",
    )

    def __init__(self, timeout_seconds: float = 12.0) -> None:
        self._default_timeout = timeout_seconds
        self._lock = threading.Lock()
        self._active = False
        self._awaiting_answer = False
        self._pending_intent: str | None = None
        self._last_activity = 0.0

    def start_dialogue(self, awaiting_answer: bool = False, pending_intent: str | None = None) -> None:
        """Inicia uma conversa contínua."""
        with self._lock:
            self._active = True
            self._awaiting_answer = awaiting_answer
            self._pending_intent = pending_intent
            self._last_activity = time.monotonic()

    def mark_interaction(self, awaiting_answer: bool = False, pending_intent: str | None = None) -> None:
        """Registra interação recente, estendendo a janela de diálogo."""
        with self._lock:
            self._active = True
            self._awaiting_answer = awaiting_answer
            if pending_intent is not None or not awaiting_answer:
                self._pending_intent = pending_intent
            self._last_activity = time.monotonic()

    def close_dialogue(self) -> None:
        """Encerra a conversa e devolve o assistente ao estado de espera pela wake word."""
        with self._lock:
            self._active = False
            self._awaiting_answer = False
            self._pending_intent = None

    def is_active(self) -> bool:
        """Verifica se a sessão de diálogo ainda está dentro da janela de tempo."""
        with self._lock:
            return self._is_active_unlocked()

    def _is_active_unlocked(self) -> bool:
        """Avalia expiração da sessão; deve ser chamado com o lock já adquirido."""
        if not self._active:
            return False
        timeout = 45.0 if self._awaiting_answer else self._default_timeout
        if time.monotonic() - self._last_activity > timeout:
            self._active = False
            self._awaiting_answer = False
            self._pending_intent = None
            return False
        return True

    def is_awaiting_answer(self) -> bool:
        """Indica se o Jarvis acabou de fazer uma pergunta e aguarda a resposta direta."""
        with self._lock:
            return self._is_active_unlocked() and self._awaiting_answer

    def get_pending_intent(self) -> str | None:
        with self._lock:
            return self._pending_intent

    def resolve_utterance_with_pending(self, utterance: str) -> str:
        """Aplica contexto da pergunta pendente à resposta isolada do usuário."""
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
        """Detecta frases de encerramento da conversa."""
        norm = normalize(utterance)
        return any(trigger in norm for trigger in self.CLOSE_TRIGGERS)
