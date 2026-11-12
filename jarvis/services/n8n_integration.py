"""Integração com ecossistema de fluxos e webhooks de automação N8N."""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from jarvis.security.security_guard import SecurityGuard

logger = logging.getLogger(__name__)

DEFAULT_N8N_URL = "http://127.0.0.1:5678/webhook/jarvis"


class N8NWorkflowConnector:
    """Cliente HTTP resiliente para orquestração de workflows e automações no N8N."""

    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = webhook_url or os.getenv("N8N_WEBHOOK_URL", DEFAULT_N8N_URL)

    def trigger_workflow(self, action: str, data: dict[str, object] | None = None, timeout: float = 3.5) -> dict[str, object]:
        """Envia evento de automação para o webhook do N8N de forma segura."""
        payload = {
            "source": "jarvis-stark-mark-vii",
            "action": SecurityGuard.sanitize_command_argument(action),
            "data": data or {},
        }
        raw_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        if len(raw_body) > 65536:
            return {"status": "error", "message": "Payload excede o limite seguro de 64KB."}

        req = urllib.request.Request(
            self.webhook_url,
            data=raw_body,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "Jarvis-Stark-Mark-VII/1.0",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status_code = response.getcode()
                resp_data = response.read().decode("utf-8")
                parsed = json.loads(resp_data) if resp_data else {}
                return {"status": "success", "code": status_code, "response": parsed}
        except urllib.error.URLError as err:
            logger.debug("N8N offline ou indisponível (%s): %s", self.webhook_url, err)
            return {"status": "offline", "message": "Servidor N8N não acessível no momento."}
        except Exception as exc:
            logger.error("Erro ao comunicar com N8N: %s", exc)
            return {"status": "error", "message": str(exc)}

    def check_connection(self) -> bool:
        """Verifica se o endpoint N8N está online."""
        try:
            req = urllib.request.Request(self.webhook_url, method="HEAD")
            with urllib.request.urlopen(req, timeout=1.5):
                return True
        except Exception:
            return False
