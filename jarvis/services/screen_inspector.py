"""Inspeção de tela e captura visual do ambiente Windows (inspirado no Jarvis de isair)."""

from __future__ import annotations

import ctypes
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent.parent / "screenshots"


@dataclass(frozen=True)
class ScreenInfo:
    """Informações contextuais da área de trabalho ativa."""

    window_title: str
    width: int
    height: int
    screenshot_path: Path | None = None

    def describe(self) -> str:
        res = f"{self.width}x{self.height}"
        title = self.window_title if self.window_title else "Área de Trabalho / Sem foco"
        if self.screenshot_path and self.screenshot_path.exists():
            return f"Janela ativa: '{title}' em {res}. Captura salva em {self.screenshot_path.name}."
        return f"Janela ativa: '{title}' em {res}."


class ScreenInspector:
    """Serviço de análise de tela, resolução e registro fotográfico da área de trabalho."""

    def __init__(self, target_dir: Path = DEFAULT_SCREENSHOTS_DIR) -> None:
        self._target_dir = target_dir
        self._target_dir.mkdir(parents=True, exist_ok=True)

    def get_active_window_title(self) -> str:
        """Obtém o título da janela atualmente em primeiro plano no Windows."""
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return "Área de Trabalho"
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            return buff.value.strip() or "Janela sem título"
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao obter janela ativa: %s", exc)
            return "Indisponível"

    def get_resolution(self) -> tuple[int, int]:
        """Obtém largura e altura da tela principal."""
        try:
            user32 = ctypes.windll.user32
            w = user32.GetSystemMetrics(0)
            h = user32.GetSystemMetrics(1)
            return int(w), int(h)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao obter resolução: %s", exc)
            return 1920, 1080

    def capture_screenshot(self) -> Path | None:
        """Captura o frame atual da tela e grava em arquivo PNG timestamped."""
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = self._target_dir / filename

        try:
            # Tenta utilizar Pillow ImageGrab se disponível
            from PIL import ImageGrab

            img = ImageGrab.grab()
            img.save(str(filepath), "PNG")
            logger.info("Screenshot gravado via PIL em %s", filepath)
            return filepath
        except ImportError:
            logger.info("PIL indisponível; disparando atalho nativo de captura do Windows.")
            self._trigger_native_windows_snip()
            return None
        except Exception as exc:  # noqa: BLE001
            logger.error("Erro ao gravar screenshot: %s", exc)
            self._trigger_native_windows_snip()
            return None

    def _trigger_native_windows_snip(self) -> None:
        """Dispara Win + Shift + S como fallback nativo do Windows."""
        try:
            user32 = ctypes.windll.user32
            user32.keybd_event(0x5B, 0, 0, 0)  # LWIN
            user32.keybd_event(0x10, 0, 0, 0)  # SHIFT
            user32.keybd_event(0x53, 0, 0, 0)  # 'S'
            user32.keybd_event(0x53, 0, 0x0002, 0)  # KEYUP
            user32.keybd_event(0x10, 0, 0x0002, 0)
            user32.keybd_event(0x5B, 0, 0x0002, 0)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao emitir atalho de captura: %s", exc)

    def inspect(self, take_screenshot: bool = True) -> ScreenInfo:
        """Realiza a inspeção completa do estado visual atual da máquina."""
        title = self.get_active_window_title()
        w, h = self.get_resolution()
        saved_path = self.capture_screenshot() if take_screenshot else None
        return ScreenInfo(window_title=title, width=w, height=h, screenshot_path=saved_path)
