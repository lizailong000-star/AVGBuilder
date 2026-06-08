param(
    [string]$Remote = "origin",
    [string]$Branch = "",
    [switch]$RunChecks,
    [switch]$SkipServerProbe,
    [switch]$Yes
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir
Set-Location $Root

if (-not (Test-Path ".\.git")) {
    throw "This script must run from AVGBuilder repository root."
}

if ($RunChecks) {
    $checkArgs = @()
    if ($SkipServerProbe) { $checkArgs += "-SkipServerProbe" }
    & .\scripts\check_all.ps1 @checkArgs
    if ($LASTEXITCODE -ne 0) { throw "Checks failed. Push aborted." }
}

Write-Host "== AVGBuilder status =="
git status --short
if ($LASTEXITCODE -ne 0) { throw "git status failed" }

$dirty = git status --porcelain
if (-not [string]::IsNullOrWhiteSpace($dirty)) {
    Write-Host ""
    Write-Host "AVGBuilder has uncommitted changes. Commit or stash before push." -ForegroundColor Red
    exit 1
}

$DemoAvg = "D:\GitHub\DemoAVG"
if (Test-Path $DemoAvg) {
    Write-Host ""
    Write-Host "== DemoAVG status (read-only guard) =="
    git -C $DemoAvg status --short
    if ($LASTEXITCODE -ne 0) { throw "git status failed for DemoAVG" }
}

if ([string]::IsNullOrWhiteSpace($Branch)) {
    $Branch = git branch --show-current
}
if ([string]::IsNullOrWhiteSpace($Branch)) {
    throw "Cannot determine current branch. Pass -Branch explicitly."
}

Write-Host ""
Write-Host "Ready to push AVGBuilder only: $Remote $Branch"

if (-not $Yes) {
    $answer = Read-Host "Type PUSH to continue"
    if ($answer -ne "PUSH") {
        Write-Host "Push cancelled."
        exit 0
    }
}

git push $Remote $Branch
if ($LASTEXITCODE -ne 0) { throw "git push failed" }

Write-Host "Push completed: $Remote $Branch" -ForegroundColor Green
