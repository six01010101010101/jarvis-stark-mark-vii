"""Barra superior da HUD com máscara holográfica do Homem de Ferro, VPN, Conta e Janela."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from jarvis.ui.stark_hologram import StarkHologramMask


class HudTopBar(tk.Frame):
    """Barra de controle superior com logo holográfico, VPN, Tema, Conta e Maximizar/Minimizar."""

    def __init__(
        self,
        parent: tk.Misc,
        root: tk.Tk,
        bg: str = "#060A12",
        fg: str = "#00F0FF",
        on_vpn_toggle: Callable[[], None] | None = None,
        on_account_click: Callable[[], None] | None = None,
        on_theme_toggle: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent, bg=bg)
        self._root = root
        self._on_vpn = on_vpn_toggle
        self._on_account = on_account_click
        self._on_theme = on_theme_toggle
        self._is_maximized = False

        # 1. Logo Holográfico da Máscara do Homem de Ferro
        self.logo = StarkHologramMask(self, size=42, bg=bg)
        self.logo.pack(side="left", padx=(6, 4), pady=2)

        # 2. Título Central
        title_box = tk.Frame(self, bg=bg)
        title_box.pack(side="left", padx=4)
        self._lbl_title = tk.Label(title_box, text="J.A.R.V.I.S.", bg=bg, fg=fg, font=("Consolas", 13, "bold"))
        self._lbl_title.pack(anchor="w")
        self._lbl_sub = tk.Label(title_box, text="MARK VII // HOLO OS", bg=bg, fg="#FFB703", font=("Consolas", 7))
        self._lbl_sub.pack(anchor="w")

        # 3. Controles do Sistema e Janela (Lado Direito)
        btn_box = tk.Frame(self, bg=bg)
        btn_box.pack(side="right", padx=(2, 6))

        # Botão Fechar / Parar
        self._btn_min = tk.Button(btn_box, text="🗕", bg="#091726", fg=fg, font=("Segoe UI", 8, "bold"), bd=1, relief="ridge", width=2, command=self._root.iconify)
        self._btn_min.pack(side="right", padx=1)

        self._btn_max = tk.Button(btn_box, text="🗖", bg="#091726", fg=fg, font=("Segoe UI", 8, "bold"), bd=1, relief="ridge", width=2, command=self.toggle_maximize)
        self._btn_max.pack(side="right", padx=1)

        self._btn_theme = tk.Button(btn_box, text="🌓", bg="#091726", fg="#00FF88", font=("Segoe UI", 8, "bold"), bd=1, relief="ridge", width=2, command=self._handle_theme)
        self._btn_theme.pack(side="right", padx=1)

        self._btn_vpn = tk.Button(btn_box, text="🛡️ VPN", bg="#003B5C", fg=fg, font=("Consolas", 7, "bold"), bd=1, relief="ridge", command=self._handle_vpn)
        self._btn_vpn.pack(side="right", padx=2)

        self._btn_account = tk.Button(btn_box, text="👤", bg="#091726", fg=fg, font=("Segoe UI", 8), bd=1, relief="ridge", width=2, command=self._handle_account)
        self._btn_account.pack(side="right", padx=1)

    def toggle_maximize(self) -> None:
        """Alterna a janela entre tamanho compacto e maximizado."""
        try:
            if not self._is_maximized:
                self._root.state("zoomed")
                self._is_maximized = True
                self._btn_max.config(text="🗗")
            else:
                self._root.state("normal")
                self._is_maximized = False
                self._btn_max.config(text="🗖")
        except Exception:
            pass

    def _handle_vpn(self) -> None:
        if self._on_vpn:
            self._on_vpn()

    def _handle_account(self) -> None:
        if self._on_account:
            self._on_account()

    def _handle_theme(self) -> None:
        if self._on_theme:
            self._on_theme()

    def set_palette(self, bg: str, fg: str) -> None:
        """Ajusta a paleta de cores da barra ao alternar temas."""
        self.configure(bg=bg)
        self._lbl_title.configure(bg=bg, fg=fg)
        self._lbl_sub.configure(bg=bg)
        self.logo.set_palette(glow=fg, bg=bg)
