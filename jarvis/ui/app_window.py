"""Interface holográfica Tony Stark Mark VII com holograma 3D, parada imediata e chat ao vivo."""

from __future__ import annotations

from datetime import datetime
import math
import threading
import tkinter as tk
from typing import Callable

from jarvis.ui import theme
from jarvis.ui.audio_meter import StarkMicControlPanel
from jarvis.ui.hud_top_bar import HudTopBar
from jarvis.ui.wake_indicator import WakeIndicator


class JarvisWindow:
    """Interface HUD pesada em Python com holograma 3D, chat em tempo real e botão de parada imediata."""

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
        on_interrupt: Callable[[], None] | None = None,
    ) -> None:
        self._root, self._on_start = root, on_start
        self._on_voice_change, self._on_device_selected = on_voice_change, on_device_selected
        self._on_sensitivity_change, self._on_patience_change = on_sensitivity_change, on_patience_change
        self._on_language_change, self._on_text_command, self._on_interrupt = on_language_change, on_text_command, on_interrupt
        self._speaking, self._theme_mode = threading.Event(), "dark"
        self._is_active, self._angle_y, self._pulse_val = False, 0.0, 0.0

        root.title(theme.WINDOW_TITLE)
        root.resizable(True, True)
        root.configure(bg=theme.BG_COLOR)

        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{theme.WINDOW_GEOMETRY}+{max(0, (sw - 520) // 2)}+{max(0, (sh - 860) // 2)}")
        root.lift()
        root.attributes("-topmost", True)
        root.after(1500, lambda: root.attributes("-topmost", False))

        self._top_bar = HudTopBar(root, root=root, bg=theme.BG_COLOR, fg=theme.FG_COLOR, on_vpn_toggle=self._toggle_vpn, on_account_click=self._open_account, on_theme_toggle=self._toggle_theme)
        self._top_bar.pack(fill="x", padx=10, pady=(2, 2))

        self._wake_led = WakeIndicator(root, root)
        self._canvas = tk.Canvas(root, width=theme.CANVAS_SIZE, height=theme.CANVAS_SIZE, bg=theme.BG_COLOR, highlightthickness=0, cursor="hand2")
        self._canvas.pack(pady=1)
        self._canvas.bind("<Button-1>", lambda _: self._handle_start())

        vf = tk.Frame(root, bg=theme.BG_COLOR)
        vf.pack(pady=2)
        self._btn_male = tk.Button(vf, text="♂ JARVIS (MASC)", bg=theme.ACTIVE_BTN_BG, fg=theme.FG_COLOR, font=("Consolas", 8, "bold"), bd=1, relief="ridge", command=lambda: self._select_voice("male"))
        self._btn_male.pack(side="left", padx=6)
        self._btn_female = tk.Button(vf, text="♀ AUXILIAR (FEM)", bg=theme.INACTIVE_BTN_BG, fg=theme.MUTED_COLOR, font=("Consolas", 8, "bold"), bd=1, relief="ridge", command=lambda: self._select_voice("female"))
        self._btn_female.pack(side="left", padx=6)

        self._meter = StarkMicControlPanel(root, root=root, on_device_selected=on_device_selected, on_sensitivity_change=on_sensitivity_change, on_patience_change=on_patience_change, on_language_change=on_language_change)
        self._build_chat_panel(root)

        self._status_bar = tk.Label(root, text=theme.INITIAL_TEXT, bg=theme.CARD_BG, fg=theme.FG_COLOR, highlightbackground=theme.ACCENT_CYAN, highlightthickness=1, font=("Consolas", 8, "bold"), wraplength=theme.LABEL_WRAP, padx=10, pady=4)
        self._status_bar.pack(pady=(2, 6), fill="x", padx=16)

        self._render_frame()
        self._animate()
        root.after(600, self._handle_start)

    def _toggle_vpn(self) -> None:
        from jarvis.services.proton_vpn import ProtonVPNManager
        vpn = ProtonVPNManager()
        if vpn.is_installed():
            vpn.launch_client()
            self.show_status("PROTON VPN // CONEXÃO INICIADA")
        else:
            self.show_status("PROTON VPN // NÃO LOCALIZADO")

    def _open_account(self) -> None:
        from jarvis.ui.account_dialog import AccountSettingsDialog
        AccountSettingsDialog(self._root, current_name="Ken", current_title="Senhor", on_save=lambda n, t: self.show_status(f"CONTA ATUALIZADA: {n} ({t})"))

    def _toggle_theme(self) -> None:
        self._theme_mode = "light" if self._theme_mode == "dark" else "dark"
        pal = theme.get_theme_palette(self._theme_mode)
        self._root.configure(bg=pal["bg"])
        self._top_bar.set_palette(pal["bg"], pal["fg"])
        self._canvas.configure(bg=pal["bg"])
        self.show_status(f"TEMA // {self._theme_mode.upper()}")

    def _build_chat_panel(self, parent: tk.Misc) -> None:
        cb = tk.Frame(parent, bg=theme.CARD_BG, highlightbackground=theme.ACCENT_CYAN, highlightthickness=1, padx=8, pady=5)
        cb.pack(pady=3, fill="both", expand=True, padx=16)
        tk.Label(cb, text="💬 CONVERSA AO VIVO // VOCÊ & J.A.R.V.I.S.", bg=theme.CARD_BG, fg=theme.ACCENT_COLOR, font=("Consolas", 8, "bold")).pack(anchor="w", pady=(0, 3))

        lf = tk.Frame(cb, bg="#040810")
        lf.pack(fill="both", expand=True)
        sb = tk.Scrollbar(lf, bg=theme.CARD_BG)
        sb.pack(side="right", fill="y")

        self._chat_log = tk.Text(lf, height=7, bg="#040810", fg="#E0F7FA", font=("Consolas", 9), wrap="word", state="disabled", bd=0, padx=6, pady=4, yscrollcommand=sb.set)
        self._chat_log.pack(side="left", fill="both", expand=True)
        sb.config(command=self._chat_log.yview)

        for tag, col, f in [("time", "#4A7A96", ("Consolas", 8)), ("user_lbl", theme.ALERT_GREEN, ("Consolas", 9, "bold")), ("user_txt", "#D8FFE8", ("Consolas", 9)), ("jarvis_lbl", theme.FG_COLOR, ("Consolas", 9, "bold")), ("jarvis_txt", "#B8F4FF", ("Consolas", 9))]:
            self._chat_log.tag_config(tag, foreground=col, font=f)

        row = tk.Frame(cb, bg=theme.CARD_BG)
        row.pack(fill="x", pady=(4, 0))
        self._chat_entry = tk.Entry(row, bg="#091726", fg=theme.FG_COLOR, insertbackground=theme.FG_COLOR, font=("Consolas", 9), bd=1, relief="solid")
        self._chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._chat_entry.bind("<Return>", lambda _: self._submit_text())

        tk.Button(row, text="ENVIAR", bg=theme.ACTIVE_BTN_BG, fg=theme.FG_COLOR, font=("Consolas", 8, "bold"), bd=1, relief="ridge", command=self._submit_text).pack(side="left", padx=(0, 4))
        tk.Button(row, text="⛔ PARAR", bg="#5A0000", fg="#FF7777", font=("Consolas", 8, "bold"), bd=1, relief="ridge", command=self._handle_stop).pack(side="right")

    def _handle_stop(self) -> None:
        if self._on_interrupt:
            self._on_interrupt()
        if self._on_text_command:
            self._on_text_command("jarvis pare")

    def _submit_text(self) -> None:
        txt = self._chat_entry.get().strip()
        if txt:
            self._chat_entry.delete(0, "end")
            if self._on_text_command:
                self._on_text_command(txt)

    def append_chat(self, role: str, text: str) -> None:
        def _ins() -> None:
            self._chat_log.config(state="normal")
            self._chat_log.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] ", "time")
            if role == "user":
                self._chat_log.insert("end", "👤 VOCÊ: ", "user_lbl")
                self._chat_log.insert("end", f"{text}\n", "user_txt")
            else:
                self._chat_log.insert("end", "🤖 J.A.R.V.I.S.: ", "jarvis_lbl")
                self._chat_log.insert("end", f"{text}\n\n", "jarvis_txt")
            self._chat_log.see("end")
            self._chat_log.config(state="disabled")
        self._root.after(0, _ins)

    def _select_voice(self, profile: str) -> None:
        is_m = profile == "male"
        self._btn_male.config(bg=theme.ACTIVE_BTN_BG if is_m else theme.INACTIVE_BTN_BG, fg=theme.FG_COLOR if is_m else theme.MUTED_COLOR)
        self._btn_female.config(bg=theme.INACTIVE_BTN_BG if is_m else theme.ACTIVE_BTN_BG, fg=theme.MUTED_COLOR if is_m else theme.FG_COLOR)
        if self._on_voice_change:
            self._on_voice_change(profile)

    def _render_frame(self) -> None:
        c, cx, cy = self._canvas, theme.CANVAS_SIZE // 2, theme.CANVAS_SIZE // 2
        c.delete("all")
        pulse = math.sin(self._pulse_val) * (6 if self._speaking.is_set() else 2.5)
        wire = theme.HOLO_GREEN if self._speaking.is_set() else theme.HOLO_CYAN
        c.create_oval(cx - 78 - pulse, cy - 78 - pulse, cx + 78 + pulse, cy + 78 + pulse, outline=theme.MUTED_COLOR, width=1)
        cos_y, sin_y = math.cos(math.radians(self._angle_y)), math.sin(math.radians(self._angle_y))
        proj = [(cx + (x * cos_y + z * sin_y) * (150 / (-x * sin_y + z * cos_y + 145)), cy + y * (150 / (-x * sin_y + z * cos_y + 145))) for x, y, z in theme.IRONMAN_3D_VERTICES]
        for i1, i2 in theme.IRONMAN_3D_EDGES:
            c.create_line(proj[i1][0], proj[i1][1], proj[i2][0], proj[i2][1], fill=wire, width=2)
        rc = 11 + pulse * 0.5
        c.create_oval(cx - rc, cy - rc + 6, cx + rc, cy + rc + 6, outline=wire, fill=theme.HOLO_CORE, width=2)

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
