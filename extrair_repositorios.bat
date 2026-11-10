@echo off
title J.A.R.V.I.S. // PROCESSANDO REPOSITORIOS
cd /d "C:\Users\s6x12\Downloads\Jarvis"
echo ========================================================
echo    J.A.R.V.I.S. - PROCESSANDO REPOSITORIOS GITHUB
echo ========================================================
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -c "from jarvis.services.zip_extractor import extract_uploaded_zips; extract_uploaded_zips()"
) else (
    python -c "from jarvis.services.zip_extractor import extract_uploaded_zips; extract_uploaded_zips()"
)
echo.
echo ========================================================
echo    CONCLUIDO! TODOS OS REPOSITORIOS FORAM PROCESSADOS.
echo ========================================================
pause
