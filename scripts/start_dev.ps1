<#
.SYNOPSIS
Starts AVGBuilder's local FastAPI development server.

.DESCRIPTION
This script only operates inside the AVGBuilder repository. It does not read,
write, or modify DemoAVG. It creates/uses the local AVGBuilder virtual
environment, installs AVGBuilder requirements, and starts uvicorn on 127.0.0.1.
#>
[CmdletBinding()]
param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$NoReload,
    [switch]$SkipInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
Set-Location $RepoRoot

Write-Host "AVGBuilder dev server" -ForegroundColor Cyan
Write-Host "Repository: $RepoRoot"

$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating local virtual environment: .venv" -ForegroundColor Yellow
    python -m venv .venv
}

if (-not $SkipInstall) {
    Write-Host "Installing AVGBuilder requirements..." -ForegroundColor Yellow
    & $VenvPython -m pip install -r requirements.txt
}

$ReloadArgs = @()
if (-not $NoReload) {
    $ReloadArgs += "--reload"
}

Write-Host "Starting http://$HostAddress`:$Port" -ForegroundColor Green
& $VenvPython -m uvicorn backend.app:app --host $HostAddress --port $Port @ReloadArgs
