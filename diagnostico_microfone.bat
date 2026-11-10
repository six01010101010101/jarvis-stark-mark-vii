@echo off
title J.A.R.V.I.S. // TESTE E DIAGNOSTICO DO MICROFONE
cd /d "%~dp0"

echo ========================================================
echo    J.A.R.V.I.S. - DIAGNOSTICO ACUSTICO E TESTE DE VOZ
echo ========================================================
echo.
.venv\Scripts\python.exe testar_microfone.py
echo.
pause
