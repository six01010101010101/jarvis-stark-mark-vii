@echo off
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "PYTHONUNBUFFERED=1"
title J.A.R.V.I.S. // STARK INDUSTRIES MARK VII
color 0B
cd /d "C:\Users\s6x12\Downloads\Jarvis"

echo ===============================================================================
echo                J.A.R.V.I.S. - STARK INDUSTRIES MARK VII
echo ===============================================================================
echo [STARK HUD] Encerrando processos residuais de audio e microfone...
taskkill /F /IM pythonw.exe >nul 2>&1

echo [STARK HUD] Localizando ambiente Python...
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo.
echo ===============================================================================
echo [STARK HUD] Inicializando J.A.R.V.I.S. com escuta ativa e voz cinematografica...
echo ===============================================================================
echo.

"%PYTHON_EXE%" -u -m jarvis

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ALERTA] Aplicacao finalizada com codigo de saida: %ERRORLEVEL%.
)
echo.
echo Pressione qualquer tecla para fechar esta janela...
pause >nul
