@echo off
chcp 65001 >nul
title J.A.R.V.I.S. // CRIAR E SALVAR REPOSITORIO NO GITHUB
color 0B
cd /d "C:\Users\s6x12\Downloads\Jarvis"

echo ===============================================================================
echo        J.A.R.V.I.S. - BACKUP E SINCRONIZACAO COM O GITHUB
echo ===============================================================================
echo.

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" -c "from jarvis.services.github_sync import sync_project_to_github; ok = sync_project_to_github(); print('[GITHUB] Sincronizado com sucesso!' if ok else '[GITHUB] Verifique a conexao.')"

echo.
echo ===============================================================================
echo [CONCLUIDO] Repositorio https://github.com/six01010101010101/jarvis-stark-mark-vii atualizado!
echo ===============================================================================
pause
