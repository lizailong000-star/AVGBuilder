<#
.SYNOPSIS
Shows Git status for AVGBuilder and DemoAVG without modifying either repo.

.DESCRIPTION
The script defaults DemoAVG to a sibling folder next to AVGBuilder. Override
-DemoAVGPath if your checkout is elsewhere. All Git commands are read-only.
#>
[CmdletBinding()]
param(
    [string]$DemoAVGPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AVGBuilderPath = Split-Path -Parent $ScriptDir
if (-not $DemoAVGPath) {
    $DemoAVGPath = Join-Path (Split-Path -Parent $AVGBuilderPath) "DemoAVG"
}

function Show-RepoStatus {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Path
    )

    Write-Host "`n== $Name ==" -ForegroundColor Cyan
    Write-Host "Path: $Path"
    if (-not (Test-Path $Path)) {
        Write-Host "Missing path" -ForegroundColor Yellow
        return
    }
    if (-not (Test-Path (Join-Path $Path ".git"))) {
        Write-Host "Not a Git repository" -ForegroundColor Yellow
        return
    }

    git -C $Path branch --show-current
    git -C $Path log -1 --oneline
    $Status = git -C $Path status --short
    if ($Status) {
        Write-Host "Working tree changes:" -ForegroundColor Yellow
        $Status
    } else {
        Write-Host "Working tree clean" -ForegroundColor Green
    }
}

Show-RepoStatus "AVGBuilder" $AVGBuilderPath
Show-RepoStatus "DemoAVG (read-only status check)" $DemoAVGPath
