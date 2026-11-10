"""Gerenciamento e reparo automático do atalho do J.A.R.V.I.S. na Área de Trabalho."""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LAUNCHER_BAT = PROJECT_ROOT / "INICIAR_JARVIS.bat"

DESKTOP_DIRS = (
    Path.home() / "OneDrive" / "Área de Trabalho",
    Path.home() / "Desktop",
    Path(r"C:\Users\Public\Desktop"),
)


def repair_desktop_shortcut() -> bool:
    """Repara ou cria o atalho Jarvis.lnk e o script Iniciar Jarvis.bat na Área de Trabalho."""
    created = False
    vbs_content = f"""
Set oWS = WScript.CreateObject("WScript.Shell")
targetBat = "{str(LAUNCHER_BAT).replace('\\', '\\\\')}"
workDir = "{str(PROJECT_ROOT).replace('\\', '\\\\')}"

Sub MakeLnk(desktopPath)
    On Error Resume Next
    Dim oLink
    Set oLink = oWS.CreateShortcut(desktopPath & "\\Jarvis.lnk")
    oLink.TargetPath = targetBat
    oLink.WorkingDirectory = workDir
    oLink.Description = "J.A.R.V.I.S. - Stark Industries Mark VII"
    oLink.WindowStyle = 1
    oLink.Save
End Sub

MakeLnk "{str(Path.home() / 'OneDrive' / 'Área de Trabalho').replace('\\', '\\\\')}"
MakeLnk "{str(Path.home() / 'Desktop').replace('\\', '\\\\')}"
"""
    try:
        temp_vbs = Path(tempfile.gettempdir()) / "repair_jarvis_shortcut.vbs"
        temp_vbs.write_text(vbs_content, encoding="utf-8")
        subprocess.run(
            ["cscript", "//nologo", str(temp_vbs)],
            capture_output=True,
            timeout=5,
            check=False,
        )
        temp_vbs.unlink(missing_ok=True)
        created = True
        logger.info("Atalho Jarvis.lnk atualizado para apontar para %s", LAUNCHER_BAT)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha ao atualizar Jarvis.lnk via VBScript: %s", exc)

    # Cria também o executável direto Iniciar Jarvis.bat na Área de Trabalho
    direct_bat_content = f"""@echo off
title J.A.R.V.I.S. - STARK INDUSTRIES
cd /d "{PROJECT_ROOT}"
call "{LAUNCHER_BAT}"
"""
    for d in DESKTOP_DIRS:
        if d.exists():
            try:
                bat_path = d / "INICIAR_JARVIS.bat"
                bat_path.write_text(direct_bat_content, encoding="utf-8")
                logger.info("Criado inicializador direto: %s", bat_path)
            except OSError:
                pass

    return created
