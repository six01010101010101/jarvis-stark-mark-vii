"""Servidor REST API ao vivo do J.A.R.V.I.S. (porta 8765) para VM, Banco e Integrações."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jarvis.services.collective_mind import JarvisCollectiveMind

logger = logging.getLogger(__name__)


class JarvisLiveAPIServer:
    """Disponibiliza endpoints REST em http://127.0.0.1:8765 para integrações locais e remotas."""

    def __init__(self, mind: JarvisCollectiveMind, host: str = "127.0.0.1", port: int = 8765) -> None:
        self.mind, self.host, self.port = mind, host, port
        self._server: HTTPServer | None = None

    def start_in_background(self) -> None:
        mind_ref = self.mind

        class Handler(BaseHTTPRequestHandler):
            def _send_json(self, data: dict[str, object], status: int = 200) -> None:
                body = json.dumps(data, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:
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
                    self._send_json({"error": "Endpoint não encontrado"}, 404)

            def do_POST(self) -> None:
                if self.path == "/api/v1/chat":
                    length = int(self.headers.get("Content-Length", 0))
                    payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                    user_msg = str(payload.get("message", "")).strip()
                    lang = str(payload.get("lang", "pt"))
                    reply, mode = mind_ref.think_and_reply(user_msg, in_patience_window=True, lang=lang)
                    self._send_json({"reply": reply, "intent_mode": mode})
                else:
                    self._send_json({"error": "Endpoint inválido"}, 404)

            def log_message(self, format: str, *args: object) -> None:
                pass

        def _serve() -> None:
            try:
                self._server = HTTPServer((self.host, self.port), Handler)
                print(f"[JARVIS API AO VIVO] 🌐 Servidor ativo em http://{self.host}:{self.port}/api/v1/status", flush=True)
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
