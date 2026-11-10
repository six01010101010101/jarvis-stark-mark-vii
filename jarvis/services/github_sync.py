"""Sincronização e criação automática de repositório no GitHub via API e Git."""

from __future__ import annotations

import json
import logging
from pathlib import Path
import subprocess
import threading
import urllib.request

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_REPO_NAME = "jarvis-stark-mark-vii"


def _run_git(args: list[str], timeout: float = 20.0, input_text: str | None = None) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            args,
            cwd=str(PROJECT_ROOT),
            input=input_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=timeout,
            check=False,
        )
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        return proc.returncode, out.strip()
    except Exception as exc:
        return 1, str(exc)


def _get_git_credentials() -> tuple[str, str]:
    code, out = _run_git(["git", "credential", "fill"], input_text="protocol=https\nhost=github.com\n\n")
    user, token = "", ""
    if code == 0:
        for line in out.splitlines():
            if line.startswith("username="):
                user = line.split("=", 1)[1].strip()
            elif line.startswith("password="):
                token = line.split("=", 1)[1].strip()
    return user, token


def _ensure_remote_repo(user: str, token: str, repo_name: str) -> str:
    url = "https://api.github.com/user/repos"
    payload = json.dumps({
        "name": repo_name,
        "description": "J.A.R.V.I.S. Stark Industries Mark VII - Assistente de Voz Inteligente em Tempo Real (Python, SQLite, Gemini & Web)",
        "private": False,
        "auto_init": False,
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "Jarvis-Stark-Mark-VII",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            return data.get("clone_url") or f"https://github.com/{user}/{repo_name}.git"
    except Exception:
        return f"https://github.com/{user}/{repo_name}.git"


def sync_project_to_github(repo_name: str = DEFAULT_REPO_NAME, commit_msg: str = "feat: atualiza J.A.R.V.I.S. Mark VII") -> bool:
    """Inicializa repositório Git local, configura identidade, cria repo no GitHub e faz push."""
    if not (PROJECT_ROOT / ".git").exists():
        _run_git(["git", "init"])
        _run_git(["git", "branch", "-M", "main"])

    user, token = _get_git_credentials()
    git_user = user or "Ken"
    _run_git(["git", "config", "user.name", git_user])
    _run_git(["git", "config", "user.email", f"{git_user}@users.noreply.github.com"])

    _run_git(["git", "add", "-A"])
    _run_git(["git", "commit", "-m", commit_msg])

    _, remotes = _run_git(["git", "remote", "-v"])
    if "origin" not in remotes and user and token:
        remote_url = _ensure_remote_repo(user, token, repo_name)
        _run_git(["git", "remote", "add", "origin", remote_url])

    push_code, _ = _run_git(["git", "push", "-u", "origin", "main"], timeout=35.0)
    return push_code == 0


def sync_project_async(commit_msg: str = "feat: J.A.R.V.I.S. escuta ativa, banco SQLite e dialogo inteligente") -> None:
    """Executa o backup Git/GitHub em segundo plano sem bloquear a inicialização."""
    threading.Thread(
        target=sync_project_to_github,
        kwargs={"commit_msg": commit_msg},
        name="jarvis-github-sync",
        daemon=True,
    ).start()
