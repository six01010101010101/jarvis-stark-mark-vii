"""Widget de monitoramento acústico em tempo real (Nível VU + Sensibilidade de Áudio HUD)."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk
from typing import Callable

from jarvis.speech.audio_stream import list_input_devices, pick_default_device_index
from jarvis.ui import theme


class AudioMeterWidget:
    """Barra de nível e sensibilidade de áudio em tempo real com controle de ganho."""

    def __init__(
        self,
        parent: tk.Widget,
        root: tk.Tk,
        on_device_selected: Callable[[int], None] | None = None,
        on_sensitivity_change: Callable[[float], None] | None = None,
    ) -> None:
        self._root = root
        self._on_device_selected = on_device_selected
        self._on_sensitivity_change = on_sensitivity_change
        self._sensitivity = 2.5
        self._frame = tk.Frame(parent, bg=theme.BG_COLOR)
        self._frame.pack(fill="x", padx=16, pady=(2, 4))

        # Linha 1: Nível do Microfone (%, RMS e dB)
        top_row = tk.Frame(self._frame, bg=theme.BG_COLOR)
        top_row.pack(fill="x")

        self._lbl_title = tk.Label(
            top_row, text="🎙️ NÍVEL DO MICROFONE:", bg=theme.BG_COLOR, fg=theme.ACCENT_CYAN,
            font=("Consolas", 8, "bold"),
        )
        self._lbl_title.pack(side="left")

        self._lbl_val = tk.Label(
            top_row, text="0% | 0 RMS (-60 dB)", bg=theme.BG_COLOR, fg=theme.FG_COLOR,
            font=("Consolas", 8, "bold"),
        )
        self._lbl_val.pack(side="right")

        # Barra Gráfica LED (24 segmentos + marcador de limiar)
        self._canvas = tk.Canvas(
            self._frame, height=16, bg=theme.CARD_BG,
            highlightthickness=1, highlightbackground=theme.ACCENT_CYAN,
        )
        self._canvas.pack(fill="x", pady=(2, 4))

        # Linha 2: Sensibilidade de Áudio + Botões [-] [+]
        sens_row = tk.Frame(self._frame, bg=theme.BG_COLOR)
        sens_row.pack(fill="x", pady=(0, 4))

        self._lbl_sens = tk.Label(
            sens_row,
            text="SENSIBILIDADE: 2.5x (ALTA) | Ruído: 0 | Limiar: 18 RMS",
            bg=theme.BG_COLOR, fg="#00FF88", font=("Consolas", 8, "bold"),
        )
        self._lbl_sens.pack(side="left")

        btn_plus = tk.Button(
            sens_row, text="+", width=2, bg=theme.ACTIVE_BTN_BG, fg=theme.FG_COLOR,
            font=("Consolas", 8, "bold"), bd=1, relief="ridge",
            command=lambda: self._adjust_sensitivity(0.5),
        )
        btn_plus.pack(side="right", padx=(2, 0))

        btn_minus = tk.Button(
            sens_row, text="-", width=2, bg=theme.INACTIVE_BTN_BG, fg=theme.FG_COLOR,
            font=("Consolas", 8, "bold"), bd=1, relief="ridge",
            command=lambda: self._adjust_sensitivity(-0.5),
        )
        btn_minus.pack(side="right", padx=(2, 2))

        # Linha 3: Seletor de dispositivos de áudio
        dev_row = tk.Frame(self._frame, bg=theme.BG_COLOR)
        dev_row.pack(fill="x")

        tk.Label(
            dev_row, text="PORTA:", bg=theme.BG_COLOR, fg=theme.MUTED_COLOR, font=("Consolas", 8)
        ).pack(side="left")

        self._devices = list_input_devices()
        self._dev_var = tk.StringVar()
        dev_names = [f"[{d.index}] {d.name[:35]}" for d in self._devices]
        default_idx = pick_default_device_index(self._devices)
        active_name = next((n for n in dev_names if f"[{default_idx}]" in n), dev_names[0] if dev_names else "")
        if active_name:
            self._dev_var.set(active_name)

        self._combo = ttk.Combobox(
            dev_row, textvariable=self._dev_var, values=dev_names,
            state="readonly", font=("Consolas", 8), width=32,
        )
        self._combo.pack(side="left", padx=6, fill="x", expand=True)
        self._combo.bind("<<ComboboxSelected>>", self._handle_combo_change)

        self._draw_meter(0.08, rms=0, noise=0, threshold=18, is_voice=False)

    @property
    def sensitivity(self) -> float:
        return self._sensitivity

    def _adjust_sensitivity(self, delta: float) -> None:
        self._sensitivity = max(1.0, min(6.0, round(self._sensitivity + delta, 1)))
        if self._on_sensitivity_change:
            self._on_sensitivity_change(self._sensitivity)
        self._lbl_sens.config(
            text=f"SENSIBILIDADE: {self._sensitivity:.1f}x ({self._sens_label()}) | Ajustada!"
        )

    def _sens_label(self) -> str:
        if self._sensitivity >= 4.0:
            return "MÁXIMA"
        if self._sensitivity >= 2.0:
            return "ALTA"
        return "NORMAL"

    def _handle_combo_change(self, _event: object) -> None:
        selected_text = self._dev_var.get()
        if selected_text.startswith("[") and "]" in selected_text:
            idx_str = selected_text[1:selected_text.index("]")]
            if idx_str.isdigit() and self._on_device_selected:
                self._on_device_selected(int(idx_str))

    def update_level(
        self,
        level: float,
        rms: int = 0,
        noise: int = 0,
        threshold: int = 18,
        is_voice: bool = False,
    ) -> None:
        """Atualiza a barra visual de nível, RMS/dB e sensibilidade na thread do Tkinter."""
        self._root.after(0, lambda: self._draw_meter(level, rms, noise, threshold, is_voice))

    def _draw_meter(
        self,
        level: float,
        rms: int = 0,
        noise: int = 0,
        threshold: int = 18,
        is_voice: bool = False,
    ) -> None:
        c = self._canvas
        c.delete("all")
        raw_w = c.winfo_width()
        w = raw_w if raw_w > 100 else 340
        h = 16

        pct = max(0.0, min(level, 1.0))
        pct_display = int(pct * 100)
        db_val = int(20 * math.log10(max(rms, 1) / 32768.0))

        if is_voice or pct > 0.22:
            self._lbl_title.config(text="🟢 CAPTANDO SUA VOZ:", fg="#00FF88")
            self._lbl_val.config(text=f"{pct_display}% | {rms} RMS ({db_val} dB)", fg="#00FF88")
        else:
            self._lbl_title.config(text="🎙️ NÍVEL DO MICROFONE:", fg=theme.ACCENT_CYAN)
            self._lbl_val.config(text=f"{pct_display}% | {rms} RMS ({db_val} dB)", fg=theme.FG_COLOR)

        self._lbl_sens.config(
            text=f"SENSIBILIDADE: {self._sensitivity:.1f}x ({self._sens_label()}) | Ruído:{noise:3d} | Limiar:{threshold:3d}",
            fg="#00FF88" if is_voice else theme.ACCENT_CYAN,
        )

        total_blocks = 24
        block_w = max(4, (w - (total_blocks * 2)) // total_blocks)
        active_blocks = max(1 if rms > 0 else 0, int(pct * total_blocks))

        for i in range(total_blocks):
            x1 = i * (block_w + 2) + 2
            x2 = x1 + block_w
            if i < active_blocks:
                if i >= int(total_blocks * 0.75):
                    color = "#FFD700"
                elif is_voice or i >= int(total_blocks * 0.30):
                    color = "#00FF88"
                else:
                    color = theme.ACCENT_CYAN
            else:
                color = "#132232"
            c.create_rectangle(x1, 2, x2, h - 2, fill=color, outline="")

        # Linha vertical indicadora do limiar de sensibilidade (gatilho de voz)
        trig_x = int(min(0.30, max(0.12, threshold / 250.0)) * w)
        c.create_line(trig_x, 0, trig_x, h, fill="#FF5555", width=2)
