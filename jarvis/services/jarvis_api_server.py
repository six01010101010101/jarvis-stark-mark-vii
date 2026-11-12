"""Servidor REST API e Web Frontend ao vivo com blindagem APIShield e OWASP."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
import mimetypes
from pathlib import Path
import threading
from typing import TYPE_CHECKING

from jarvis.security.api_shield import APIShield
from jarvis.security.security_guard import SecurityGuard

if TYPE_CHECKING:
    from jarvis.services.collective_mind import JarvisCollectiveMind

logger = logging.getLogger(__name__)
WEB_DIR = Path(__file__).resolve().parent.parent.parent / "web"


class JarvisLiveAPIServer:
    """Disponibiliza endpoints REST e o aplicativo Web HUD protegidos por APIShield."""

    def __init__(self, mind: JarvisCollectiveMind, host: str = "127.0.0.1", port: int = 8765) -> None:
        self.mind, self.host, self.port = mind, host, port
        self.shield = APIShield(max_requests=120, window_seconds=60.0, max_payload_bytes=65536)
        self._server: HTTPServer | None = None

    def start_in_background(self) -> None:
        mind_ref = self.mind
        shield_ref = self.shield

        class Handler(BaseHTTPRequestHandler):
            def _apply_security_headers(self) -> None:
                for header, value in shield_ref.get_security_headers().items():
                    self.send_header(header, value)

            def _send_json(self, data: dict[str, object], status: int = 200) -> None:
                body = json.dumps(data, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(body)))
                self._apply_security_headers()
                self.end_headers()
                self.wfile.write(body)

            def _serve_static_file(self, rel_path: str) -> None:
                clean_path = rel_path.split("?")[0].strip("/")
                target = WEB_DIR / ("index.html" if not clean_path else clean_path)
                if not SecurityGuard.is_safe_path(target, base_dir=WEB_DIR) or not target.is_file():
                    self._send_json({"error": "Acesso negado ou arquivo não encontrado"}, 404)
                    return
                try:
                    ctype, _ = mimetypes.guess_type(str(target))
                    data = target.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", ctype or "application/octet-stream")
                    self.send_header("Content-Length", str(len(data)))
                    self._apply_security_headers()
                    self.end_headers()
                    self.wfile.write(data)
                except Exception as exc:
                    logger.debug("Falha ao servir arquivo estático: %s", exc)
                    self._send_json({"error": "Erro interno ao ler arquivo"}, 500)

            def do_GET(self) -> None:
                client_ip = self.client_address[0]
                if shield_ref.is_rate_limited(client_ip):
                    self._send_json({"error": "Limite de requisições excedido (Rate Limit)"}, 429)
                    return

                if self.path == "/api/v1/status":
                    self._send_json({
                        "system": "J.A.R.V.I.S. Stark Mark VII",
                        "status": "ONLINE",
                        "collective_mind": True,
                        "recent_memory": mind_ref.repo.get_recent_episodic_context(limit=5),
                    })
                elif self.path == "/api/v1/memory":
                    self._send_json({
                        "facts": mind_ref.repo.get_learned_facts(limit=20),
                        "history": mind_ref.repo.get_recent_episodic_context(limit=20),
                    })
                elif self.path == "/api/v1/telemetry":
                    self._send_json(mind_ref.repo.record_telemetry_snapshot())
                else:
                    self._serve_static_file(self.path)

            def do_POST(self) -> None:
                client_ip = self.client_address[0]
                if shield_ref.is_rate_limited(client_ip):
                    self._send_json({"error": "Limite de requisições excedido (Rate Limit)"}, 429)
                    return

                if self.path == "/api/v1/chat":
                    length = int(self.headers.get("Content-Length", 0))
                    if not shield_ref.validate_payload_size(length):
                        self._send_json({"error": "Payload excede o tamanho máximo permitido"}, 413)
                        return

                    payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                    user_msg = str(payload.get("message", "")).strip()
                    is_valid, reason = SecurityGuard.validate_chat_input(user_msg)
                    if not is_valid:
                        self._send_json({"error": f"Entrada inválida: {reason}"}, 400)
                        return

                    lang = str(payload.get("lang", "pt"))
                    reply, mode = mind_ref.think_and_reply(user_msg, in_patience_window=True, lang=lang)
                    safe_reply = SecurityGuard.redact_secrets(reply)
                    self._send_json({"reply": safe_reply, "intent_mode": mode})
                else:
                    self._send_json({"error": "Endpoint inválido"}, 404)

            def log_message(self, format: str, *args: object) -> None:
                pass

        def _serve() -> None:
            try:
                self._server = HTTPServer((self.host, self.port), Handler)
                print(f"[JARVIS WEB & API] 🌐 Painel Seguro ativo em http://{self.host}:{self.port}/", flush=True)
                self._server.serve_forever()
            except Exception as exc:
                print(f"[JARVIS API Aviso Porta {self.port}]: {exc}", flush=True)

        threading.Thread(target=_serve, name="jarvis-api-daemon", daemon=True).start()

    def stop(self) -> None:
        if self._server:
            try:
                self._server.shutdown()
            except Exception:
                pass
