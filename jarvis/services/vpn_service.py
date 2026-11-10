"""Detecção de VPN ativa no sistema (ProtonVPN, WireGuard) e diagnóstico de rede."""

from __future__ import annotations

import csv
import io
import logging
import subprocess

logger = logging.getLogger(__name__)

VPN_PROCESS_KEYWORDS = ("protonvpn", "proton", "wireguard", "openvpn")


class VpnDetector:
    """Verifica processos ativos no Windows para identificar túneis de VPN."""

    @staticmethod
    def is_vpn_active() -> bool:
        """Retorna True se algum processo de VPN como o ProtonVPN estiver em execução."""
        try:
            res = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                errors="ignore",
                check=False,
            )
            reader = csv.reader(io.StringIO(res.stdout))
            for row in reader:
                if row:
                    exe = row[0].lower()
                    if any(kw in exe for kw in VPN_PROCESS_KEYWORDS):
                        return True
        except Exception as exc:
            logger.debug("Falha ao consultar tasklist para VPN: %s", exc)
        return False

    @staticmethod
    def print_vpn_status_hud(vpn_active: bool) -> None:
        """Exibe o diagnóstico Stark no terminal sobre o estado da VPN."""
        if vpn_active:
            print("\n==========================================================================", flush=True)
            print(" 🛡️ [BLINDAGEM VPN ATIVADA] ProtonVPN Detectado em Execução", flush=True)
            print(" ⚡ O Google Speech público bloqueia IPs de VPN gratuita.", flush=True)
            print(" 🚀 J.A.R.V.I.S. ativou a Transcrição Neural Autenticada Gemini (100% Imune)!", flush=True)
            print("==========================================================================\n", flush=True)
