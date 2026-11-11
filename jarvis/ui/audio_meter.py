"""Painel HUD Mark VII: Seletor de Microfone, Medidor dB/RMS, Sensibilidade, Paciência e Poliglota."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk
from typing import Callable

from jarvis.speech.audio_stream import list_input_devices, pick_default_device_index
from jarvis.ui import theme


class StarkMicControlPanel(tk.Frame):
    """Painel HUD acoplável: seletor de microfone, medidor dB/RMS ao vivo, ganho, paciência e idioma."""

    def __init__(
        self,
        parent: tk.Widget,
        root: tk.Tk | None = None,
        on_device_selected: Callable[[int], None] | None = None,
        on_sensitivity_change: Callable[[float], None] | None = None,
        on_patience_change: Callable[[float], None] | None = None,
        on_language_change: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(
            parent, bg=theme.CARD_BG, highlightbackground=theme.ACCENT_CYAN,
            highlightthickness=1, padx=12, pady=6,
        )
        self._root = root or parent.winfo_toplevel()
        self._on_device_selected = on_device_selected
        self._on_sensitivity_change = on_sensitivity_change
        self._on_patience_change = on_patience_change
        self.on_language_change = on_language_change
        self._sensitivity, self._thresh_pct = 3.0, 45
        self.pack(fill="x", padx=16, pady=(2, 4))

        style = ttk.Style()
        try:
            style.theme_use("clam")
            style.configure("Stark.TCombobox", fieldbackground="#0D1624", background=theme.ACCENT_CYAN, foreground=theme.ACCENT_CYAN)
        except Exception:
            pass

        tk.Label(self, text="⚡ CONTROLE DE ÁUDIO, PACIÊNCIA & POLIGLOTA", bg=theme.CARD_BG, fg=theme.ACCENT_CYAN, font=("Consolas", 9, "bold")).pack(anchor="w", pady=(0, 3))

        # 1. Seletor de Microfone
        dev_row = tk.Frame(self, bg=theme.CARD_BG)
        dev_row.pack(fill="x", pady=(0, 3))
        tk.Label(dev_row, text="Microfone:", bg=theme.CARD_BG, fg="#8AB4F8", font=("Consolas", 8)).pack(side="left")

        self._devices = list_input_devices()
        self._dev_var = tk.StringVar()
        dev_names = [f"[{d.index}] {d.name[:34]}" for d in self._devices]
        default_idx = pick_default_device_index(self._devices)
        self._dev_var.set(next((n for n in dev_names if f"[{default_idx}]" in n), dev_names[0] if dev_names else "Padrão"))

        self.mic_combo = ttk.Combobox(dev_row, textvariable=self._dev_var, values=dev_names, state="readonly", style="Stark.TCombobox", font=("Consolas", 8), width=32)
        self.mic_combo.pack(side="left", padx=(6, 0), fill="x", expand=True)
        self.mic_combo.bind("<<ComboboxSelected>>", self._handle_combo_change)

        # 2. Medidor Visual de Voz em Tempo Real
        top_row = tk.Frame(self, bg=theme.CARD_BG)
        top_row.pack(fill="x")
        self._lbl_title = tk.Label(top_row, text="🎙️ CAPTAÇÃO AO VIVO:", bg=theme.CARD_BG, fg=theme.ACCENT_CYAN, font=("Consolas", 8, "bold"))
        self._lbl_title.pack(side="left")
        self._lbl_val = tk.Label(top_row, text="0% | 0 RMS (-60 dB)", bg=theme.CARD_BG, fg=theme.FG_COLOR, font=("Consolas", 8, "bold"))
        self._lbl_val.pack(side="right")

        self.meter_canvas = tk.Canvas(self, height=14, bg="#101926", highlightthickness=1, highlightbackground=theme.ACCENT_CYAN)
        self.meter_canvas.pack(fill="x", pady=(2, 4))

        # 3. Slider de Sensibilidade (Threshold)
        self.thresh_label = tk.Label(self, text="Sensibilidade / Ganho Acústico: 3.0x (Alta Captação)", bg=theme.CARD_BG, fg="#E0FAFF", font=("Consolas", 8))
        self.thresh_label.pack(anchor="w")
        self.thresh_slider = tk.Scale(self, from_=5, to=95, orient="horizontal", bg=theme.CARD_BG, fg=theme.ACCENT_CYAN, troughcolor="#101926", highlightthickness=0, showvalue=False, command=self._handle_thresh)
        self.thresh_slider.set(45)
        self.thresh_slider.pack(fill="x", pady=(0, 3))

        # 4. Slider do Ciclo de Paciência (s)
        self.patience_label = tk.Label(self, text="Ciclo de Paciência (Escuta Contínua): 10s", bg=theme.CARD_BG, fg=theme.ALERT_GREEN, font=("Consolas", 8, "bold"))
        self.patience_label.pack(anchor="w")
        self.patience_slider = tk.Scale(self, from_=3, to=25, orient="horizontal", bg=theme.CARD_BG, fg=theme.ACCENT_CYAN, troughcolor="#101926", highlightthickness=0, showvalue=False, command=self._handle_patience)
        self.patience_slider.set(10)
        self.patience_slider.pack(fill="x", pady=(0, 3))

        # 5. Seletor e Botão de Idioma (Modo Poliglota)
        tk.Label(self, text="Idioma de Reconhecimento & Resposta:", bg=theme.CARD_BG, fg="#8AB4F8", font=("Consolas", 8)).pack(anchor="w")
        self.lang_options = [
            ("auto", "🌐 Auto-Detectar (Poliglota)"),
            ("pt", "🇧🇷 Português (pt-BR)"),
            ("en", "🇺🇸 English (en-US)"),
            ("es", "🇪🇸 Español (es-ES)"),
            ("ja", "🇯🇵 日本語 (ja-JP)"),
            ("fr", "🇫🇷 Français (fr-FR)"),
            ("de", "🇩🇪 Deutsch (de-DE)"),
        ]
        self.lang_combo = ttk.Combobox(self, values=[label for _, label in self.lang_options], state="readonly", style="Stark.TCombobox", font=("Consolas", 8), width=36)
        self.lang_combo.current(1)
        self.lang_combo.pack(fill="x", pady=(2, 3))
        self.lang_combo.bind("<<ComboboxSelected>>", self._handle_language_select)

        self.polyglot_btn = tk.Button(
            self, text="🌐 ATIVAR ESCUTA MULTI-IDIOMA (AUTO)", bg="#0D1F33", fg=theme.ACCENT_CYAN,
            activebackground=theme.ACCENT_CYAN, activeforeground=theme.CARD_BG,
            font=("Consolas", 8, "bold"), relief="flat", cursor="hand2", command=self._toggle_polyglot_mode,
        )
        self.polyglot_btn.pack(fill="x")
        self._draw_meter(0.08, rms=0, noise=0, threshold=18, is_voice=False)

    def _handle_combo_change(self, _event: object) -> None:
        sel = self._dev_var.get()
        if sel.startswith("[") and "]" in sel and sel[1:sel.index("]")].isdigit() and self._on_device_selected:
            self._on_device_selected(int(sel[1:sel.index("]")]))

    def _handle_thresh(self, val: str) -> None:
        v = int(float(val))
        self._thresh_pct, self._sensitivity = v, round(1.0 + (v / 100.0) * 4.5, 1)
        self.thresh_label.config(text=f"Sensibilidade / Ganho Acústico: {self._sensitivity:.1f}x (Limiar {v}%)")
        if self._on_sensitivity_change:
            self._on_sensitivity_change(self._sensitivity)

    def _handle_patience(self, val: str) -> None:
        v = int(float(val))
        self.patience_label.config(text=f"Ciclo de Paciência (Escuta Contínua): {v}s")
        if self._on_patience_change:
            self._on_patience_change(float(v))

    def _handle_language_select(self, _event: object) -> None:
        idx = self.lang_combo.current()
        if idx >= 0:
            code, _ = self.lang_options[idx]
            is_auto = code == "auto"
            self.polyglot_btn.config(
                text="✅ MODO POLIGLOTA ATIVO (OUVINDO TODAS AS LÍNGUAS)" if is_auto else "🌐 ATIVAR ESCUTA MULTI-IDIOMA (AUTO)",
                fg=theme.ALERT_GREEN if is_auto else theme.ACCENT_CYAN,
            )
            if self.on_language_change:
                self.on_language_change(code)

    def _toggle_polyglot_mode(self) -> None:
        self.lang_combo.current(0)
        self.polyglot_btn.config(text="✅ MODO POLIGLOTA ATIVO (OUVINDO TODAS AS LÍNGUAS)", fg=theme.ALERT_GREEN)
        if self.on_language_change:
            self.on_language_change("auto")

    def update_live_volume(self, level_0_to_100: float) -> None:
        self.update_level(level_0_to_100 / 100.0)

    def update_level(self, level: float, rms: int = 0, noise: int = 0, threshold: int = 18, is_voice: bool = False) -> None:
        self._root.after(0, lambda: self._draw_meter(level, rms, noise, threshold, is_voice))

    def _draw_meter(self, level: float, rms: int, noise: int, threshold: int, is_voice: bool) -> None:
        c = self.meter_canvas
        c.delete("all")
        w = c.winfo_width() if c.winfo_width() > 100 else 350
        pct = max(0.0, min(level, 1.0))
        pct_display = int(pct * 100)
        db_val = int(20 * math.log10(max(rms, 1) / 32768.0))
        active = is_voice or pct_display >= self._thresh_pct
        self._lbl_title.config(text="🟢 CAPTANDO VOZ HUMANA:" if active else "🎙️ CAPTAÇÃO AO VIVO:", fg=theme.ALERT_GREEN if active else theme.ACCENT_CYAN)
        self._lbl_val.config(text=f"{pct_display}% | {rms} RMS ({db_val} dB)", fg=theme.ALERT_GREEN if active else theme.FG_COLOR)
        c.create_rectangle(0, 0, max(4 if rms > 0 else 0, int(pct * w)), 14, fill=theme.ALERT_GREEN if active else theme.ACCENT_CYAN, width=0)
        line_x = int((self._thresh_pct / 100.0) * w)
        c.create_line(line_x, 0, line_x, 14, fill="#FF3366", width=2)


AudioMeterWidget = StarkMicControlPanel
