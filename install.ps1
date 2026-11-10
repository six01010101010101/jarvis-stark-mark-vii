# Instalador do J.A.R.V.I.S. para Windows.
# Uso: powershell -ExecutionPolicy Bypass -File install.ps1
$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

function Find-Python {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:ProgramFiles\Python312\python.exe"
    )
    foreach ($path in $candidates) { if (Test-Path $path) { return $path } }
    $cmd = Get-Command python.exe -ErrorAction SilentlyContinue | Where-Object { $_.Source -notlike '*WindowsApps*' }
    if ($cmd) { return $cmd.Source }
    return $null
}

$python = Find-Python
if (-not $python) {
    Write-Host 'Instalando Python 3.12 via winget...'
    winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements
    $python = Find-Python
    if (-not $python) { throw 'Python nao encontrado apos a instalacao.' }
}
Write-Host "Python: $python"

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    Write-Host 'Criando ambiente virtual (.venv)...'
    & $python -m venv .venv
}
$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'

Write-Host 'Instalando dependencias...'
& $venvPython -m pip install --upgrade pip --quiet
& $venvPython -m pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar as dependencias.' }

Write-Host 'Executando testes...'
& $venvPython -m pytest
if ($LASTEXITCODE -ne 0) { throw 'Os testes falharam.' }

if (-not (Test-Path '.env')) {
    Copy-Item '.env.example' '.env'
    Write-Host 'Arquivo .env criado. Preencha GEMINI_API_KEY e JARVIS_USER_NAME.'
}

$desktop = [Environment]::GetFolderPath('Desktop')
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path $desktop 'Jarvis.lnk'))
$shortcut.TargetPath = Join-Path $PSScriptRoot '.venv\Scripts\pythonw.exe'
$shortcut.Arguments = '-m jarvis'
$shortcut.WorkingDirectory = $PSScriptRoot
$shortcut.Description = 'J.A.R.V.I.S. - Assistente de voz'
$shortcut.Save()
Write-Host "Atalho criado em: $desktop\Jarvis.lnk"
Write-Host 'Instalacao concluida.'
