@echo off
title J.A.R.V.I.S. // STARK INDUSTRIES MARK VII
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo [ERRO] Ambiente virtual nao encontrado. Execute install.ps1 primeiro.
    pause
    exit /b 1
)

echo [STARK HUD] Sincronizando novos repositorios e arquivos recebidos...
.venv\Scripts\python.exe -c "from jarvis.services.zip_extractor import extract_uploaded_zips; extract_uploaded_zips()"

echo ========================================================
echo    J.A.R.V.I.S. - STARK INDUSTRIES MARK VII ONLINE
echo ========================================================
echo [STARK HUD] Liberando dispositivos de audio e microfone...
taskkill /F /IM pythonw.exe >nul 2>&1
echo Pressione Ctrl+C para encerrar o terminal.
echo.
.venv\Scripts\python.exe -m jarvis
pause
