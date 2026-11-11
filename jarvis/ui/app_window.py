"""Interface holográfica Tony Stark Mark VII: Holograma 3D, Microfone e Painel de Conversa Ao Vivo."""

from __future__ import annotations

from datetime import datetime
import math
import threading
import tkinter as tk
from typing import Callable

from jarvis.ui import theme
from jarvis.ui.audio_meter import StarkMicControlPanel
from jarvis.ui.wake_indicator import WakeIndicator


class JarvisWindow:
    """Interface HUD pesada em Python com holograma 3D, controles de áudio e conversa em tempo real."""

    def __init__(
        self,
        root: tk.Tk,
        on_start: Callable[[], None],
        on_voice_change: Callable[[str], None] | None = None,
        on_device_selected: Callable[[int], None] | None = None,
        on_sensitivity_change: Callable[[float], None] | None = None,
        on_patience_change: Callable[[float], None] | None = None,
        on_language_change: Callable[[str], None] | None = None,
        on_text_command: Callable[[str], None] | None = None,
    ) -> None:
        self._root = root
        self._on_start = on_start
        self._on_voice_change = on_voice_change
        self._on_device_selected = on_device_selected
        self._on_sensitivity_change = on_sensitivity_change
        self._on_patience_change = on_patience_change
        self._on_language_change = on_language_change
        self._on_text_command = on_text_command
        self._speaking = threading.Event()
        self._is_active = False
        self._angle_y = 0.0
        self._pulse_val = 0.0
        self._active_voice = "male"

        root.title(theme.WINDOW_TITLE)
        root.resizable(True, True)
        root.configure(bg=theme.BG_COLOR)

        screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()
        pos_x = max(0, (screen_w - 480) // 2)
        pos_y = max(0, (screen_h - 880) // 2)
        root.geometry(f"{theme.WINDOW_GEOMETRY}+{pos_x}+{pos_y}")
        root.lift()
        root.attributes("-topmost", True)
        root.after(1500, lambda: root.attributes("-topmost", False))

        self._title = tk.Label(root, text="J.A.R.V.I.S.", bg=theme.BG_COLOR, fg=theme.FG_COLOR, font=("Consolas", 16, "bold"))
        self._title.pack(pady=(4, 0))
        self._subtitle = tk.Label(root, text="STARK INDUSTRIES // MARK VII HUD", bg=theme.BG_COLOR, fg=theme.ACCENT_COLOR, font=("Consolas", 8))
        self._subtitle.pack(pady=(0, 2))

        self._wake_led = WakeIndicator(root, root)

        self._canvas = tk.Canvas(root, width=theme.CANVAS_SIZE, height=theme.CANVAS_SIZE, bg=theme.BG_COLOR, highlightthickness=0, cursor="hand2")
        self._canvas.pack(pady=1)
        self._canvas.bind("<Button-1>", lambda _: self._handle_start())

        voice_frame = tk.Frame(root, bg=theme.BG_COLOR)
        voice_frame.pack(pady=2)
        self._btn_male = tk.Button(
            voice_frame, text="♂ VOZ DO JARVIS (ORIGINAL)", bg=theme.ACTIVE_BTN_BG, fg=theme.FG_COLOR,
            font=("Consolas", 8, "bold"), bd=1, relief="ridge", command=lambda: self._select_voice("male"),
        )
        self._btn_male.pack(side="left", padx=6)
        self._btn_female = tk.Button(
            voice_frame, text="♀ VOZ AUXILIAR (FEM)", bg=theme.INACTIVE_BTN_BG, fg=theme.MUTED_COLOR,
            font=("Consolas", 8, "bold"), bd=1, relief="ridge", command=lambda: self._select_voice("female"),
        )
        self._btn_female.pack(side="left", padx=6)

        self._meter = StarkMicControlPanel(
            root,
            root=root,
            on_device_selected=self._on_device_selected,
            on_sensitivity_change=self._on_sensitivity_change,
            on_patience_change=self._on_patience_change,
            on_language_change=self._on_language_change,
        )

        self._build_chat_panel(root)

        self._status_bar = tk.Label(
            root, text=theme.INITIAL_TEXT, bg=theme.CARD_BG, fg=theme.FG_COLOR,
            highlightbackground=theme.ACCENT_CYAN, highlightthickness=1,
            font=("Consolas", 8, "bold"), wraplength=theme.LABEL_WRAP, padx=10, pady=4,
        )
        self._status_bar.pack(pady=(2, 6), fill="x", padx=16)

        self._render_frame()
        self._animate()
        root.after(600, self._handle_start)

    def _build_chat_panel(self, parent: tk.Misc) -> None:
        chat_box = tk.Frame(parent, bg=theme.CARD_BG, highlightbackground=theme.ACCENT_CYAN, highlightthickness=1, padx=8, pady=5)
        chat_box.pack(pady=3, fill="both", expand=True, padx=16)

        hdr = tk.Label(chat_box, text="💬 CONVERSA AO VIVO // VOCÊ & J.A.R.V.I.S.", bg=theme.CARD_BG, fg=theme.ACCENT_COLOR, font=("Consolas", 8, "bold"))
        hdr.pack(anchor="w", pady=(0, 3))

        log_frame = tk.Frame(chat_box, bg="#040810")
        log_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(log_frame, bg=theme.CARD_BG)
        scrollbar.pack(side="right", fill="y")

        self._chat_log = tk.Text(
            log_frame, height=7, bg="#040810", fg="#E0F7FA", font=("Consolas", 9),
            wrap="word", state="disabled", bd=0, padx=6, pady=4, yscrollcommand=scrollbar.set,
        )
        self._chat_log.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self._chat_log.yview)

        self._chat_log.tag_config("time", foreground="#4A7A96", font=("Consolas", 8))
        self._chat_log.tag_config("user_lbl", foreground=theme.ALERT_GREEN, font=("Consolas", 9, "bold"))
        self._chat_log.tag_config("user_txt", foreground="#D8FFE8", font=("Consolas", 9))
        self._chat_log.tag_config("jarvis_lbl", foreground=theme.FG_COLOR, font=("Consolas", 9, "bold"))
        self._chat_log.tag_config("jarvis_txt", foreground="#B8F4FF", font=("Consolas", 9))

        input_row = tk.Frame(chat_box, bg=theme.CARD_BG)
        input_row.pack(fill="x", pady=(4, 0))
        self._chat_entry = tk.Entry(input_row, bg="#091726", fg=theme.FG_COLOR, insertbackground=theme.FG_COLOR, font=("Consolas", 9), bd=1, relief="solid")
        self._chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self._chat_entry.bind("<Return>", lambda _: self._submit_text())
        tk.Button(
            input_row, text="ENVIAR", bg=theme.ACTIVE_BTN_BG, fg=theme.FG_COLOR,
            font=("Consolas", 8, "bold"), bd=1, relief="ridge", command=self._submit_text,
        ).pack(side="right")

    def _submit_text(self) -> None:
        txt = self._chat_entry.get().strip()
        if not txt:
            return
        self._chat_entry.delete(0, "end")
        if self._on_text_command:
            self._on_text_command(txt)

    def append_chat(self, role: str, text: str) -> None:
        """Adiciona uma fala sua ou do J.A.R.V.I.S. ao painel de conversa em tempo real."""
        def _insert() -> None:
            ts = datetime.now().strftime("%H:%M:%S")
            self._chat_log.config(state="normal")
            self._chat_log.insert("end", f"[{ts}] ", "time")
            if role == "user":
                self._chat_log.insert("end", "👤 VOCÊ: ", "user_lbl")
                self._chat_log.insert("end", f"{text}\n", "user_txt")
            else:
                self._chat_log.insert("end", "🤖 J.A.R.V.I.S.: ", "jarvis_lbl")
                self._chat_log.insert("end", f"{text}\n\n", "jarvis_txt")
            self._chat_log.see("end")
            self._chat_log.config(state="disabled")
        self._root.after(0, _insert)

    def _select_voice(self, profile: str) -> None:
        self._active_voice = profile
        is_m = profile == "male"
        self._btn_male.config(bg=theme.ACTIVE_BTN_BG if is_m else theme.INACTIVE_BTN_BG, fg=theme.FG_COLOR if is_m else theme.MUTED_COLOR)
        self._btn_female.config(bg=theme.INACTIVE_BTN_BG if is_m else theme.ACTIVE_BTN_BG, fg=theme.MUTED_COLOR if is_m else theme.FG_COLOR)
        if self._on_voice_change:
            self._on_voice_change(profile)

    def _render_frame(self) -> None:
        c = self._canvas
        c.delete("all")
        cx, cy = theme.CANVAS_SIZE // 2, theme.CANVAS_SIZE // 2
        pulse = math.sin(self._pulse_val) * (6 if self._speaking.is_set() else 2.5)
        wire_color = theme.HOLO_GREEN if self._speaking.is_set() else theme.HOLO_CYAN
        r_outer = 78 + pulse
        c.create_oval(cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer, outline=theme.MUTED_COLOR, width=1)
        rad = math.radians(self._angle_y)
        cos_y, sin_y = math.cos(rad), math.sin(rad)
        projected = [
            (cx + (x * cos_y + z * sin_y) * (150 / (-x * sin_y + z * cos_y + 145)), cy + y * (150 / (-x * sin_y + z * cos_y + 145)))
            for x, y, z in theme.IRONMAN_3D_VERTICES
        ]
        for idx1, idx2 in theme.IRONMAN_3D_EDGES:
            p1, p2 = projected[idx1], projected[idx2]
            c.create_line(p1[0], p1[1], p2[0], p2[1], fill=wire_color, width=2)
        r_core = 11 + pulse * 0.5
        c.create_oval(cx - r_core, cy - r_core + 6, cx + r_core, cy + r_core + 6, outline=wire_color, fill=theme.HOLO_CORE, width=2)

    def _animate(self) -> None:
        if self._is_active:
            self._angle_y = (self._angle_y + (4.0 if self._speaking.is_set() else 1.8)) % 360
            self._pulse_val += 0.22 if self._speaking.is_set() else 0.08
            self._render_frame()
        self._root.after(theme.ANIMATION_INTERVAL_MS, self._animate)

    def _handle_start(self) -> None:
        if not self._is_active:
            self._is_active = True
            self._status_bar.config(text="SISTEMA ATIVO // ESCUTANDO...")
            self._on_start()

    def update_mic_level(self, level: float, rms: int = 0, noise: int = 0, threshold: int = 18, is_voice: bool = False) -> None:
        self._meter.update_level(level, rms=rms, noise=noise, threshold=threshold, is_voice=is_voice)

    def show_status(self, text: str) -> None:
        self._root.after(0, lambda: self._status_bar.config(text=text.upper()))

    def set_wake_state(self, state: str, heard: str = "") -> None:
        self._wake_led.set_state(state, heard)

    def set_speaking(self, speaking: bool) -> None:
        self._speaking.set() if speaking else self._speaking.clear()

    @property
    def is_speaking(self) -> bool:
        return self._speaking.is_set()

    def mark_stopped(self, error_message: str | None = None) -> None:
        self._is_active = False
        self._root.after(0, lambda: self._status_bar.config(text=(error_message or "SISTEMA EM ESPERA").upper()))
