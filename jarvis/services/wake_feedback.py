"""Feedback de ativação por voz: sinal verde no CMD e na interface quando 'Jarvis' é ouvido."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from jarvis.contracts import WakeSignal

if TYPE_CHECKING:
    from jarvis.services.audio_effects import StarkSoundPlayer

STANDBY = "standby"
HEARD = "heard"
DIALOGUE = "dialogue"

_GREEN = "\033[92m"
_GRAY = "\033[90m"
_RESET = "\033[0m"
_LINE = "=" * 74


class WakeFeedback:
    """Centraliza os sinais de 'ouvi você' (LED, CMD e som), sem lógica de decisão."""

    def __init__(self, signal: WakeSignal | None = None, sounds: StarkSoundPlayer | None = None) -> None:
        self._signal = signal
        self._sounds = sounds
        self._state: str | None = None
        self._lock = threading.Lock()

    def play(self) -> None:
        """Toca imediatamente o efeito sonoro de confirmação da wake word (stark_wake.wav)."""
        if self._sounds:
            self._sounds.play_wake()

    def wake_heard(self, heard: str) -> None:
        """Acende o sinal verde e registra no CMD que o nome 'Jarvis' foi reconhecido."""
        print(f"\n{_GREEN}{_LINE}", flush=True)
        print(f"🟢🟢🟢 [JARVIS OUVIU VOCÊ] Ativação reconhecida na fala: \"{heard}\"", flush=True)
        print(f"{_LINE}{_RESET}", flush=True)
        if self._sounds:
            self._sounds.play_wake()
        self._set(HEARD, heard)

    def dialogue_open(self) -> None:
        """Indica que o Jarvis está aguardando o pedido do usuário."""
        print(f"{_GREEN}🎙️ [CONVERSA ATIVA] Pode falar seu pedido — não precisa repetir 'Jarvis'.{_RESET}", flush=True)
        self._set(DIALOGUE)

    def ignored_in_standby(self, text: str) -> None:
        """Registra no CMD uma fala ouvida sem a palavra de ativação."""
        print(
            f"{_GRAY}💤 [EM ESPERA] Ouvi \"{text}\", mas sem o nome 'Jarvis'. "
            f"Diga \"Jarvis\" para ativar.{_RESET}",
            flush=True,
        )
        self._set(STANDBY)

    def sync(self, dialogue_active: bool) -> None:
        """Ajusta o LED ao estado real da sessão (só redesenha quando o estado muda)."""
        target = DIALOGUE if dialogue_active else STANDBY
        with self._lock:
            current = self._state
        if current == target or (current == HEARD and dialogue_active):
            return
        if target == STANDBY and current is not None:
            print(f"{_GRAY}💤 [EM ESPERA] Conversa encerrada. Diga \"Jarvis\" para ativar.{_RESET}", flush=True)
        self._set(target)

    def _set(self, state: str, heard: str = "") -> None:
        with self._lock:
            self._state = state
        if self._signal:
            self._signal.set_wake_state(state, heard)
