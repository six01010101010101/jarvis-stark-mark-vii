"""Diálogo de configurações da conta e preferências de tratamento do usuário."""

from __future__ import annotations

import tkinter as tk
from typing import Callable


class AccountSettingsDialog(tk.Toplevel):
    """Janela modal para editar nome de usuário e como o Jarvis deve chamá-lo."""

    def __init__(
        self,
        parent: tk.Tk,
        current_name: str,
        current_title: str = "Senhor",
        on_save: Callable[[str, str], None] | None = None,
        bg_color: str = "#050b14",
        fg_color: str = "#E0F7FA",
        accent_color: str = "#00E5FF",
    ) -> None:
        super().__init__(parent)
        self.title("J.A.R.V.I.S. // Identidade do Usuário")
        self.geometry("380x280")
        self.resizable(False, False)
        self.configure(bg=bg_color)
        self._on_save = on_save

        # Título da seção
        header = tk.Label(
            self, text="CONFIGURAÇÕES DE CONTA & TRATAMENTO",
            font=("Segoe UI", 10, "bold"), fg=accent_color, bg=bg_color,
        )
        header.pack(pady=(16, 12))

        # Campo: Nome do Usuário
        tk.Label(self, text="Nome do Usuário:", font=("Segoe UI", 9), fg=fg_color, bg=bg_color).pack(anchor="w", padx=28)
        self._name_entry = tk.Entry(self, font=("Segoe UI", 10), bg="#0f1923", fg="#FFFFFF", insertbackground=accent_color)
        self._name_entry.insert(0, current_name)
        self._name_entry.pack(fill="x", padx=28, pady=(4, 12))

        # Campo: Como gostaria de ser chamado
        tk.Label(self, text="Como gostaria de ser chamado (Vocativo):", font=("Segoe UI", 9), fg=fg_color, bg=bg_color).pack(anchor="w", padx=28)
        self._title_entry = tk.Entry(self, font=("Segoe UI", 10), bg="#0f1923", fg="#FFFFFF", insertbackground=accent_color)
        self._title_entry.insert(0, current_title)
        self._title_entry.pack(fill="x", padx=28, pady=(4, 18))

        # Botão Salvar
        btn_frame = tk.Frame(self, bg=bg_color)
        btn_frame.pack(fill="x", padx=28, pady=8)

        save_btn = tk.Button(
            btn_frame, text="SALVAR PREFERÊNCIAS", font=("Segoe UI", 9, "bold"),
            bg="#004D61", fg="#FFFFFF", activebackground=accent_color, activeforeground="#000000",
            relief="flat", cursor="hand2", command=self._handle_save,
        )
        save_btn.pack(side="right", padx=4)

        cancel_btn = tk.Button(
            btn_frame, text="CANCELAR", font=("Segoe UI", 9),
            bg="#1c2530", fg="#B0BEC5", relief="flat", cursor="hand2", command=self.destroy,
        )
        cancel_btn.pack(side="right", padx=4)

    def _handle_save(self) -> None:
        name = self._name_entry.get().strip() or "Ken"
        title = self._title_entry.get().strip() or "Senhor"
        if self._on_save:
            self._on_save(name, title)
        self.destroy()
