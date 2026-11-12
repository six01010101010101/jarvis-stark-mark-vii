"""Módulo de blindagem para servidores REST API do J.A.R.V.I.S. (Rate Limiting e Headers OWASP)."""

from __future__ import annotations

import collections
import time

SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data:;",
}


class APIShield:
    """Controle de taxa (Rate Limiting por IP) e injeção de cabeçalhos de segurança defensivos."""

    def __init__(self, max_requests: int = 60, window_seconds: float = 60.0, max_payload_bytes: int = 65536) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_payload_bytes = max_payload_bytes
        self._ip_history: dict[str, collections.deque[float]] = {}

    def is_rate_limited(self, client_ip: str) -> bool:
        """Verifica se o IP solicitante ultrapassou a cota permitida dentro da janela temporal."""
        now = time.monotonic()
        if client_ip not in self._ip_history:
            self._ip_history[client_ip] = collections.deque()

        queue = self._ip_history[client_ip]
        cutoff = now - self.window_seconds
        while queue and queue[0] < cutoff:
            queue.popleft()

        if len(queue) >= self.max_requests:
            return True

        queue.append(now)
        return False

    def validate_payload_size(self, content_length: int) -> bool:
        """Valida se o corpo da requisição não excede o limite máximo permitido contra DoS."""
        return 0 <= content_length <= self.max_payload_bytes

    @staticmethod
    def get_security_headers() -> dict[str, str]:
        """Retorna dicionário de cabeçalhos compatíveis com os padrões OWASP."""
        return dict(SECURITY_HEADERS)
