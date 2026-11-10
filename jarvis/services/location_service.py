"""Serviço de geolocalização e diagnóstico de rede externa em tempo real."""

from __future__ import annotations

import json
import logging
import urllib.request

logger = logging.getLogger(__name__)

LOCATION_URL = "https://ipapi.co/json/"
TIMEOUT_SECONDS = 3.5


class LocationService:
    """Detecta a localização geográfica atual e o IP da conexão."""

    def __init__(self, fallback_city: str = "São Paulo") -> None:
        self._fallback_city = fallback_city

    def get_details(self) -> dict[str, str]:
        """Consulta dados geográficos via IP."""
        try:
            req = urllib.request.Request(LOCATION_URL, headers={"User-Agent": "JarvisAssistant/1.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return {
                "ip": str(data.get("ip", "desconhecido")),
                "city": str(data.get("city", self._fallback_city)),
                "region": str(data.get("region", "São Paulo")),
                "country": str(data.get("country_name", "Brasil")),
                "org": str(data.get("org", "Provedor de Internet")),
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao consultar localização: %s", exc)
            return {
                "ip": "indisponível",
                "city": self._fallback_city,
                "region": "SP",
                "country": "Brasil",
                "org": "Rede local",
            }

    def get_location_report(self) -> str:
        """Gera relatório de onde o assistente e o usuário estão localizados."""
        info = self.get_details()
        return (
            f"Senhor Ken, estamos localizados em {info['city']}, {info['region']}, {info['country']}. "
            f"Nossos sistemas estão conectados pelo provedor {info['org']}."
        )

    def get_ip_report(self) -> str:
        """Informa o IP público da máquina."""
        info = self.get_details()
        return f"O endereço de protocolo de internet externo desta estação é {info['ip']}, senhor."
