"""Indicador LED de ativação por voz: mostra quando o J.A.R.V.I.S. ouviu o próprio nome."""

from __future__ import annotations

import tkinter as tk
from typing import Final

from jarvis.ui import theme

STANDBY: Final = "standby"
HEARD: Final = "heard"
DIALOGUE: Final = "dialogue"

_STYLES: Final[dict[str, tuple[str, str, str]]] = {
    # estado: (cor do LED, cor do texto, mensagem)
    STANDBY: ("#3A4A5A", "#5F7A90", "EM ESPERA // DIGA \"JARVIS\" PARA ATIVAR"),
    HEARD: ("#00FF66", "#00FF88", "JARVIS OUVIU VOCÊ"),
    DIALOGUE: ("#00FF66", "#00FF88", "CONVERSA ATIVA // PODE FALAR SEU PEDIDO"),
}


class WakeIndicator:
    """LED verde/cinza com legenda, atualizado com segurança a partir de qualquer thread."""

    def __init__(self, parent: tk.Widget, root: tk.Tk) -> None:
        self._root = root
        self._frame = tk.Frame(parent, bg=theme.BG_COLOR)
        self._frame.pack(pady=(0, 2))
        self._led = tk.Canvas(self._frame, width=16, height=16, bg=theme.BG_COLOR, highlightthickness=0)
        self._led.pack(side="left", padx=(0, 6))
        self._dot = self._led.create_oval(2, 2, 14, 14, fill=_STYLES[STANDBY][0], outline="")
        self._label = tk.Label(
            self._frame, text=_STYLES[STANDBY][2], bg=theme.BG_COLOR,
            fg=_STYLES[STANDBY][1], font=("Consolas", 9, "bold"),
        )
        self._label.pack(side="left")

    def set_state(self, state: str, heard: str = "") -> None:
        """Agenda a troca de estado na thread do Tkinter (STANDBY, HEARD ou DIALOGUE)."""
        if state not in _STYLES:
            raise ValueError(f"Estado de ativação desconhecido: {state}")
        self._root.after(0, lambda: self._apply(state, heard))

    def _apply(self, state: str, heard: str) -> None:
        led_color, text_color, message = _STYLES[state]
        if state == HEARD and heard:
            message = f"{message}: \"{heard[:28]}\""
        self._led.itemconfig(self._dot, fill=led_color)
        self._label.config(text=message, fg=text_color)
