"""Controle profundo do Google Chrome, navegação e reprodução de vídeos no YouTube."""

from __future__ import annotations

import ctypes
import logging
import subprocess
import urllib.parse
import webbrowser

logger = logging.getLogger(__name__)

# Códigos de teclas virtuais do Windows (User32)
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_STOP = 0xB2
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_SPACE = 0x20
KEYEVENTF_KEYUP = 0x0002


class BrowserAndMediaController:
    """Automação de navegador e controle direto de execução de mídia e YouTube."""

    def play_youtube_search(self, query: str) -> bool:
        """Abre o YouTube com a busca específica para reprodução da música ou vídeo."""
        clean_q = query.strip()
        encoded = urllib.parse.quote_plus(clean_q)
        url = f"https://www.youtube.com/results?search_query={encoded}"
        return self.open_in_browser(url)

    def open_in_browser(self, url: str) -> bool:
        """Abre a URL no Google Chrome preferencialmente ou no navegador padrão."""
        try:
            # Tenta executar via Google Chrome se disponível no path ou registro
            subprocess.Popen(["cmd.exe", "/c", "start", "chrome", url], shell=False)
            logger.info("URL aberta no Chrome: %s", url)
            return True
        except Exception:
            try:
                webbrowser.open(url)
                logger.info("URL aberta no navegador padrão: %s", url)
                return True
            except Exception as exc:
                logger.error("Falha ao abrir navegador: %s", exc)
                return False

    def toggle_play_pause(self) -> bool:
        """Emite evento de teclado multimídia nativo do Windows para pausar ou despausar."""
        try:
            # Dispara tecla VK_MEDIA_PLAY_PAUSE globalmente
            ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_KEYUP, 0)
            logger.info("Evento VK_MEDIA_PLAY_PAUSE enviado ao sistema.")
            return True
        except Exception as exc:
            logger.error("Falha ao enviar tecla multimídia: %s", exc)
            return False

    def stop_media(self) -> bool:
        """Para a reprodução multimídia em execução."""
        try:
            ctypes.windll.user32.keybd_event(VK_MEDIA_STOP, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_MEDIA_STOP, 0, KEYEVENTF_KEYUP, 0)
            return True
        except Exception:
            return False

    def next_track(self) -> bool:
        """Avança para a próxima faixa ou vídeo."""
        try:
            ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, KEYEVENTF_KEYUP, 0)
            return True
        except Exception:
            return False

    def previous_track(self) -> bool:
        """Volta para a faixa ou vídeo anterior."""
        try:
            ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, KEYEVENTF_KEYUP, 0)
            return True
        except Exception:
            return False
