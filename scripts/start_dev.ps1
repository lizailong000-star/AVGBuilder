param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$NoReload
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir
Set-Location $Root

Write-Host "AVGBuilder dev server"
Write-Host "Root: $Root"

if (-not (Test-Path ".\backend\app.py")) {
    throw "backend/app.py not found. Run this script from AVGBuilder repository."
}

$python = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }

try {
    & $python -c "import uvicorn" 2>$null
} catch {
    Write-Host "uvicorn not found. Installing requirements..."
    & $python -m pip install -r requirements.txt
}

$reloadArgs = @()
if (-not $NoReload) {
    $reloadArgs += "--reload"
}

Write-Host "Starting: http://$HostAddress`:$Port"
& $python -m uvicorn backend.app:app --host $HostAddress --port $Port @reloadArgs
