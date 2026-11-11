"""Testes automatizados do servidor Web e API REST do J.A.R.V.I.S."""

from __future__ import annotations

import json
import socket
import time
import urllib.request
from unittest.mock import MagicMock
import pytest

from jarvis.services.jarvis_api_server import JarvisLiveAPIServer


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return int(s.getsockname()[1])


@pytest.fixture
def running_server():
    port = _find_free_port()
    mock_mind = MagicMock()
    mock_mind.repo.get_recent_episodic_context.return_value = [{"role": "user", "content": "olá"}]
    mock_mind.repo.get_learned_facts.return_value = ["Fato de teste"]
    mock_mind.repo.record_telemetry_snapshot.return_value = {"cpu_percent": 12.5, "ram_used_gb": 4.2}
    mock_mind.think_and_reply.return_value = ("Resposta de teste do Jarvis", "DEEP_CONVERSATION")

    server = JarvisLiveAPIServer(mind=mock_mind, host="127.0.0.1", port=port)
    server.start_in_background()
    time.sleep(0.4)
    yield f"http://127.0.0.1:{port}"
    server.stop()


def test_serve_index_html(running_server: str):
    url = f"{running_server}/"
    with urllib.request.urlopen(url, timeout=3.0) as resp:
        assert resp.status == 200
        content = resp.read().decode("utf-8")
        assert "J.A.R.V.I.S." in content
        assert "STARK INDUSTRIES" in content


def test_serve_css_and_js(running_server: str):
    css_url = f"{running_server}/css/hud-tokens.css"
    with urllib.request.urlopen(css_url, timeout=3.0) as resp:
        assert resp.status == 200
        content = resp.read().decode("utf-8")
        assert "--hud-cyan" in content

    js_url = f"{running_server}/js/api-client.js"
    with urllib.request.urlopen(js_url, timeout=3.0) as resp:
        assert resp.status == 200
        content = resp.read().decode("utf-8")
        assert "JarvisApiClient" in content


def test_api_status_endpoint(running_server: str):
    url = f"{running_server}/api/v1/status"
    with urllib.request.urlopen(url, timeout=3.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["system"] == "J.A.R.V.I.S. Stark Mark VII"
        assert data["status"] == "ONLINE"


def test_api_chat_endpoint(running_server: str):
    url = f"{running_server}/api/v1/chat"
    payload = json.dumps({"message": "Olá Jarvis", "lang": "pt"}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "reply" in data
        assert data["reply"] == "Resposta de teste do Jarvis"


def test_nonexistent_route_404(running_server: str):
    url = f"{running_server}/arquivo_inexistente_xyz.html"
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(url, timeout=3.0)
    assert exc.value.code == 404
