"""Serviço de informações meteorológicas em tempo real para o J.A.R.V.I.S."""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

DEFAULT_CITY = "São Paulo"
TIMEOUT_SECONDS = 3.5


class WeatherService:
    """Consulta dados de clima e previsão do tempo via API meteorológica em tempo real."""

    def __init__(self, default_city: str = DEFAULT_CITY) -> None:
        self._default_city = default_city

    def get_current_weather(self, city: str | None = None) -> str:
        """Obtém a temperatura atual, sensação térmica e condições do céu."""
        target_city = (city or self._default_city).strip()
        encoded = urllib.parse.quote(target_city)
        url = f"https://wttr.in/{encoded}?format=j1"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "JarvisAssistant/1.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            current = data["current_condition"][0]
            temp_c = current.get("temp_C", "--")
            feels_c = current.get("FeelsLikeC", temp_c)
            desc_pt = current.get("lang_pt", [{}])[0].get("value")
            if not desc_pt:
                desc_pt = current.get("weatherDesc", [{}])[0].get("value", "tempo estável")
            humidity = current.get("humidity", "--")

            return (
                f"A temperatura atual em {target_city} é de {temp_c}°C, "
                f"com sensação térmica de {feels_c}°C, {desc_pt.lower()} "
                f"e umidade relativa do ar em {humidity}%, senhor."
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao obter clima para %s: %s", target_city, exc)
            return f"Não foi possível consultar as estações meteorológicas para {target_city} no momento, senhor."

    def get_forecast(self, city: str | None = None) -> str:
        """Obtém a previsão do tempo para o dia seguinte."""
        target_city = (city or self._default_city).strip()
        encoded = urllib.parse.quote(target_city)
        url = f"https://wttr.in/{encoded}?format=j1"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "JarvisAssistant/1.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            # Dia seguinte é o índice 1 na lista de previsão
            tomorrow = data.get("weather", [])[1] if len(data.get("weather", [])) > 1 else None
            if not tomorrow:
                return f"Não encontrei dados de previsão futura para {target_city}, senhor."

            max_temp = tomorrow.get("maxtempC", "--")
            min_temp = tomorrow.get("mintempC", "--")
            hourly = tomorrow.get("hourly", [{}])[4]
            desc_pt = hourly.get("lang_pt", [{}])[0].get("value")
            if not desc_pt:
                desc_pt = hourly.get("weatherDesc", [{}])[0].get("value", "tempo estável")

            return (
                f"A previsão para amanhã em {target_city} indica {desc_pt.lower()}, "
                f"com máxima prevista de {max_temp}°C e mínima de {min_temp}°C, senhor."
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao obter previsão para %s: %s", target_city, exc)
            return f"Não foi possível acessar a previsão estendida para {target_city}, senhor."
