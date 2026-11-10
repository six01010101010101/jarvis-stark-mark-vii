"""Painel HUD Mark VII de Controle de Áudio, Microfone em Tempo Real, Ganho e Ciclo de Paciência."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk
from typing import Callable

from jarvis.speech.audio_stream import list_input_devices, pick_default_device_index
from jarvis.ui import theme


class StarkMicControlPanel(tk.Frame):
    """Painel HUD acoplável: seletor de microfone, medidor dB/RMS ao vivo e sliders de ganho e paciência."""

    def __init__(
        self,
        parent: tk.Widget,
        root: tk.Tk | None = None,
        on_device_selected: Callable[[int], None] | None = None,
        on_sensitivity_change: Callable[[float], None] | None = None,
        on_patience_change: Callable[[float], None] | None = None,
    ) -> None:
        super().__init__(
            parent,
            bg=theme.CARD_BG,
            highlightbackground=theme.ACCENT_CYAN,
            highlightthickness=1,
            padx=12,
            pady=8,
        )
        self._root = root or parent.winfo_toplevel()
        self._on_device_selected = on_device_selected
        self._on_sensitivity_change = on_sensitivity_change
        self._on_patience_change = on_patience_change
        self._sensitivity = 2.5
        self._thresh_pct = 30
        self.pack(fill="x", padx=16, pady=(2, 4))

        style = ttk.Style()
        try:
            style.theme_use("clam")
            style.configure(
                "Stark.TCombobox",
                fieldbackground="#0D1624",
                background=theme.ACCENT_CYAN,
                foreground=theme.ACCENT_CYAN,
            )
        except Exception:
            pass

        tk.Label(
            self,
            text="⚡ CONTROLE DE ÁUDIO & PACIÊNCIA MARK VII",
            bg=theme.CARD_BG,
            fg=theme.ACCENT_CYAN,
            font=("Consolas", 9, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        # 1. Seletor de Microfone Fácil conectado ao audio_stream.py
        dev_row = tk.Frame(self, bg=theme.CARD_BG)
        dev_row.pack(fill="x", pady=(0, 4))
        tk.Label(
            dev_row, text="Microfone:", bg=theme.CARD_BG, fg="#8AB4F8", font=("Consolas", 8)
        ).pack(side="left")

        self._devices = list_input_devices()
        self._dev_var = tk.StringVar()
        dev_names = [f"[{d.index}] {d.name[:34]}" for d in self._devices]
        default_idx = pick_default_device_index(self._devices)
        active_name = next((n for n in dev_names if f"[{default_idx}]" in n), dev_names[0] if dev_names else "Padrão")
        self._dev_var.set(active_name)

        self.mic_combo = ttk.Combobox(
            dev_row,
            textvariable=self._dev_var,
            values=dev_names,
            state="readonly",
            style="Stark.TCombobox",
            font=("Consolas", 8),
            width=32,
        )
        self.mic_combo.pack(side="left", padx=(6, 0), fill="x", expand=True)
        self.mic_combo.bind("<<ComboboxSelected>>", self._handle_combo_change)

        # 2. Medidor Visual de Voz em Tempo Real (Canvas HUD + Linha de Threshold)
        top_row = tk.Frame(self, bg=theme.CARD_BG)
        top_row.pack(fill="x")
        self._lbl_title = tk.Label(
            top_row, text="🎙️ CAPTAÇÃO AO VIVO:", bg=theme.CARD_BG, fg=theme.ACCENT_CYAN, font=("Consolas", 8, "bold")
        )
        self._lbl_title.pack(side="left")
        self._lbl_val = tk.Label(
            top_row, text="0% | 0 RMS (-60 dB)", bg=theme.CARD_BG, fg=theme.FG_COLOR, font=("Consolas", 8, "bold")
        )
        self._lbl_val.pack(side="right")

        self.meter_canvas = tk.Canvas(
            self, height=16, bg="#101926", highlightthickness=1, highlightbackground=theme.ACCENT_CYAN
        )
        self.meter_canvas.pack(fill="x", pady=(2, 6))

        # 3. Slider de Sensibilidade (Threshold)
        self.thresh_label = tk.Label(
            self,
            text="Sensibilidade / Ganho Acústico: 2.5x (Limiar 30%)",
            bg=theme.CARD_BG,
            fg="#E0FAFF",
            font=("Consolas", 8),
        )
        self.thresh_label.pack(anchor="w")
        self.thresh_slider = tk.Scale(
            self,
            from_=5,
            to=95,
            orient="horizontal",
            bg=theme.CARD_BG,
            fg=theme.ACCENT_CYAN,
            troughcolor="#101926",
            highlightthickness=0,
            showvalue=False,
            command=self._handle_thresh,
        )
        self.thresh_slider.set(30)
        self.thresh_slider.pack(fill="x", pady=(0, 4))

        # 4. Slider do Ciclo de Paciência (s)
        self.patience_label = tk.Label(
            self,
            text="Ciclo de Paciência (Escuta Contínua): 10s",
            bg=theme.CARD_BG,
            fg=theme.ALERT_GREEN,
            font=("Consolas", 8, "bold"),
        )
        self.patience_label.pack(anchor="w")
        self.patience_slider = tk.Scale(
            self,
            from_=3,
            to=25,
            orient="horizontal",
            bg=theme.CARD_BG,
            fg=theme.ACCENT_CYAN,
            troughcolor="#101926",
            highlightthickness=0,
            showvalue=False,
            command=self._handle_patience,
        )
        self.patience_slider.set(10)
        self.patience_slider.pack(fill="x")

        self._draw_meter(0.08, rms=0, noise=0, threshold=18, is_voice=False)

    def _handle_combo_change(self, _event: object) -> None:
        selected = self._dev_var.get()
        if selected.startswith("[") and "]" in selected:
            idx_str = selected[1:selected.index("]")]
            if idx_str.isdigit() and self._on_device_selected:
                self._on_device_selected(int(idx_str))

    def _handle_thresh(self, val: str) -> None:
        v = int(float(val))
        self._thresh_pct = v
        # Mais sensibilidade = menor limiar ou maior ganho (1.0x a 5.5x)
        self._sensitivity = round(1.0 + (v / 100.0) * 4.5, 1)
        self.thresh_label.config(text=f"Sensibilidade / Ganho Acústico: {self._sensitivity:.1f}x (Limiar {v}%)")
        if self._on_sensitivity_change:
            self._on_sensitivity_change(self._sensitivity)

    def _handle_patience(self, val: str) -> None:
        v = int(float(val))
        self.patience_label.config(text=f"Ciclo de Paciência (Escuta Contínua): {v}s")
        if self._on_patience_change:
            self._on_patience_change(float(v))

    def update_live_volume(self, level_0_to_100: float) -> None:
        self.update_level(level_0_to_100 / 100.0)

    def update_level(
        self,
        level: float,
        rms: int = 0,
        noise: int = 0,
        threshold: int = 18,
        is_voice: bool = False,
    ) -> None:
        self._root.after(0, lambda: self._draw_meter(level, rms, noise, threshold, is_voice))

    def _draw_meter(self, level: float, rms: int, noise: int, threshold: int, is_voice: bool) -> None:
        c = self.meter_canvas
        c.delete("all")
        raw_w = c.winfo_width()
        w = raw_w if raw_w > 100 else 350
        h = 16
        pct = max(0.0, min(level, 1.0))
        pct_display = int(pct * 100)
        db_val = int(20 * math.log10(max(rms, 1) / 32768.0))

        if is_voice or pct_display >= self._thresh_pct:
            self._lbl_title.config(text="🟢 CAPTANDO SUA VOZ:", fg=theme.ALERT_GREEN)
            self._lbl_val.config(text=f"{pct_display}% | {rms} RMS ({db_val} dB)", fg=theme.ALERT_GREEN)
            bar_color = theme.ALERT_GREEN
        else:
            self._lbl_title.config(text="🎙️ CAPTAÇÃO AO VIVO:", fg=theme.ACCENT_CYAN)
            self._lbl_val.config(text=f"{pct_display}% | {rms} RMS ({db_val} dB)", fg=theme.FG_COLOR)
            bar_color = theme.ACCENT_CYAN

        fill_w = max(4 if rms > 0 else 0, int(pct * w))
        c.create_rectangle(0, 0, fill_w, h, fill=bar_color, width=0)

        line_x = int((self._thresh_pct / 100.0) * w)
        c.create_line(line_x, 0, line_x, h, fill="#FF3366", width=2)


AudioMeterWidget = StarkMicControlPanel
