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
echo [STARK HUD] Removendo inicializacao automatica do Windows e processos duplicados...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "JarvisAssistant" /f >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python' -and $_.CommandLine -match 'jarvis' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1

echo [STARK HUD] Localizando ambiente Python...
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo.
echo ===============================================================================
echo [STARK HUD] Inicializando instancia unica do J.A.R.V.I.S. Mark VII...
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
