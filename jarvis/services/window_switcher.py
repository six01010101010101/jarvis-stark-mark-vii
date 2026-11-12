"""Gerenciamento de janelas Win32: Alt+Tab, Área de Trabalho, Gerenciador de Tarefas e foco."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import logging
import subprocess
from jarvis.security.security_guard import SecurityGuard
from jarvis.text_utils import normalize

logger = logging.getLogger(__name__)

VK_TAB = 0x09
VK_MENU = 0x12  # Alt
VK_LWIN = 0x5B  # Windows key
KEYEVENTF_KEYUP = 0x0002
SW_RESTORE = 9


class WindowSwitcher:
    """Controlador nativo de janelas para alternância multitarefas no Windows."""

    @staticmethod
    def trigger_alt_tab() -> bool:
        """Executa a combinação Alt+Tab para alternar entre janelas ativas."""
        try:
            user32 = ctypes.windll.user32
            user32.keybd_event(VK_MENU, 0, 0, 0)
            user32.keybd_event(VK_TAB, 0, 0, 0)
            user32.keybd_event(VK_TAB, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
            return True
        except Exception as exc:
            logger.error("Falha ao disparar Alt+Tab: %s", exc)
            return False

    @staticmethod
    def show_desktop() -> bool:
        """Minimiza todas as janelas e exibe a Área de Trabalho (Win+D)."""
        try:
            user32 = ctypes.windll.user32
            user32.keybd_event(VK_LWIN, 0, 0, 0)
            user32.keybd_event(0x44, 0, 0, 0)  # 'D'
            user32.keybd_event(0x44, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
            return True
        except Exception as exc:
            logger.error("Falha ao mostrar Área de Trabalho: %s", exc)
            return False

    @staticmethod
    def open_task_manager() -> bool:
        """Abre ou traz para o primeiro plano o Gerenciador de Tarefas do Windows."""
        try:
            subprocess.Popen(["taskmgr.exe"], shell=False)
            return True
        except Exception as exc:
            logger.error("Falha ao abrir Gerenciador de Tarefas: %s", exc)
            return False

    @classmethod
    def switch_to_app(cls, target_name: str) -> bool:
        """Localiza janela visível correspondente ao nome e traz para o primeiro plano."""
        clean = SecurityGuard.sanitize_command_argument(target_name)
        if not clean or not SecurityGuard.is_safe_shell_input(clean):
            return False

        norm_target = normalize(clean)
        found_hwnd: int | None = None
        user32 = ctypes.windll.user32

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def enum_windows_callback(hwnd: int, _lparam: int) -> bool:
            nonlocal found_hwnd
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = normalize(buff.value)
            if norm_target in title or (norm_target == "chrome" and "google chrome" in title) or (
                norm_target == "navegador" and any(b in title for b in ("chrome", "edge", "firefox", "opera"))
            ):
                found_hwnd = hwnd
                return False  # Interrompe busca
            return True

        try:
            user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)
            if found_hwnd:
                user32.ShowWindow(found_hwnd, SW_RESTORE)
                user32.BringWindowToTop(found_hwnd)
                user32.SetForegroundWindow(found_hwnd)
                return True
        except Exception as exc:
            logger.debug("Falha na enumeração de janelas: %s", exc)

        return False
