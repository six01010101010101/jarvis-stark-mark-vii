"""Testes unitários para modo privado/confidencial do J.A.R.V.I.S."""

from __future__ import annotations

import pytest

from jarvis.commands.privacy_commands import (
    is_private_mode,
    privacy_commands,
    set_private_mode,
)
from jarvis.commands.registry import Outcome
from tests.fakes import make_context


def test_privacy_mode_toggle() -> None:
    set_private_mode(False)
    assert not is_private_mode()

    ctx = make_context()
    cmds = {c.name: c for c in privacy_commands()}

    # Ativa modo privado
    cmd_on = cmds["enable_private_mode"]
    assert cmd_on.matches("ativar modo privado")
    assert cmd_on.matches("modo anonimo")
    assert cmd_on.handler(ctx, "ativar modo privado") is Outcome.CONTINUE
    assert is_private_mode()

    # Desativa modo privado
    cmd_off = cmds["disable_private_mode"]
    assert cmd_off.matches("desativar modo privado")
    assert cmd_off.matches("sair do modo privado")
    assert cmd_off.handler(ctx, "desativar modo privado") is Outcome.CONTINUE
    assert not is_private_mode()
