"""Gerenciador do Proton VPN instalado na máquina Windows para alternância de redes."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import subprocess
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

POSSIBLE_EXE_PATHS: list[Path] = [
    Path(r"C:\Program Files\Proton\VPN\ProtonVPN.Launcher.exe"),
    Path(r"C:\Program Files\Proton\VPN\v5.1.9\ProtonVPN.Client.exe"),
    Path(r"C:\Program Files (x86)\Proton\VPN\ProtonVPN.Launcher.exe"),
    Path.home() / "AppData" / "Local" / "Programs" / "Proton" / "VPN" / "ProtonVPN.Launcher.exe",
]


class ProtonVPNManager:
    """Controle e monitoramento do Proton VPN para navegação e acesso a dados internacionais."""

    def __init__(self) -> None:
        self._exe_path = self._find_proton_exe()

    def _find_proton_exe(self) -> Path | None:
        """Localiza o binário do Proton VPN no disco local."""
        for path in POSSIBLE_EXE_PATHS:
            if path.exists():
                return path
        return None

    def is_installed(self) -> bool:
        """Indica se o Proton VPN foi localizado na máquina."""
        return self._exe_path is not None and self._exe_path.exists()

    def launch_client(self) -> bool:
        """Abre o cliente do Proton VPN para conexão pelo usuário."""
        if not self.is_installed() or self._exe_path is None:
            logger.warning("Proton VPN não instalado ou executável não encontrado.")
            return False
        try:
            subprocess.Popen([str(self._exe_path)], shell=False)
            logger.info("Cliente do Proton VPN iniciado: %s", self._exe_path)
            return True
        except Exception as exc:
            logger.error("Falha ao abrir Proton VPN: %s", exc)
            return False

    def is_connected(self) -> bool:
        """Verifica se há um túnel Proton/WireGuard ativo inspecionando adaptadores ou processos."""
        try:
            out = subprocess.check_output(
                ["tasklist", "/FI", "IMAGENAME eq ProtonVPN.WireGuardService.exe"],
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            return "ProtonVPN.WireGuardService" in out
        except Exception:
            return False

    def disconnect(self) -> bool:
        """Encerra os processos de túnel ou o cliente do Proton VPN para desativar a rede privada."""
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "ProtonVPN.Client.exe"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            logger.info("Comando de desconexão do Proton VPN executado com sucesso.")
            return True
        except Exception as exc:
            logger.error("Falha ao desconectar Proton VPN: %s", exc)
            return False

    def get_public_ip_info(self) -> dict[str, Any]:
        """Obtém o IP público atual e o país associado para auditoria da VPN."""
        try:
            req = urllib.request.Request("https://ipinfo.io/json", headers={"User-Agent": "JarvisMarkVII/1.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            return {
                "ip": str(data.get("ip", "desconhecido")),
                "country": str(data.get("country", "desconhecido")),
                "city": str(data.get("city", "")),
                "org": str(data.get("org", "")),
            }
        except Exception:
            return {"ip": "desconhecido", "country": "desconhecido", "city": "", "org": ""}
