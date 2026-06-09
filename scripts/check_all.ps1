<#
.SYNOPSIS
Runs local AVGBuilder backend/frontend checks.

.DESCRIPTION
Checks Python backend compilation and frontend JavaScript syntax. This script
only touches AVGBuilder and does not modify DemoAVG.
#>
[CmdletBinding()]
param(
    [switch]$UseVenv
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
Set-Location $RepoRoot

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Command
    )
    Write-Host "`n==> $Name" -ForegroundColor Cyan
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
    Write-Host "PASS: $Name" -ForegroundColor Green
}

$Python = "python"
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if ($UseVenv -and (Test-Path $VenvPython)) {
    $Python = $VenvPython
}

Invoke-Step "Python backend compile" { & $Python -m compileall backend }
Invoke-Step "Frontend JavaScript syntax" { node --check frontend/app.js }
Invoke-Step "Git whitespace check" { git diff --check }

Write-Host "`nAll AVGBuilder checks passed." -ForegroundColor Green
