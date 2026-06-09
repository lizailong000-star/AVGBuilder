<#
.SYNOPSIS
Safely pushes the current AVGBuilder branch after checks.

.DESCRIPTION
This script only pushes AVGBuilder. It refuses to push main/master unless
-AllowMain is provided, runs local checks first by default, and never modifies
DemoAVG.
#>
[CmdletBinding()]
param(
    [string]$Remote = "origin",
    [string]$Branch,
    [switch]$AllowMain,
    [switch]$SkipChecks
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
Set-Location $RepoRoot

if (-not $Branch) {
    $Branch = (git branch --show-current).Trim()
}
if (-not $Branch) {
    throw "Could not determine current branch."
}

if ((($Branch -eq "main") -or ($Branch -eq "master")) -and (-not $AllowMain)) {
    throw "Refusing to push '$Branch'. Create a feature branch or rerun with -AllowMain."
}

$Pending = git status --short
if ($Pending) {
    Write-Host "Uncommitted changes detected:" -ForegroundColor Yellow
    $Pending
    throw "Commit or stash changes before pushing."
}

if (-not $SkipChecks) {
    & (Join-Path $RepoRoot "scripts\check_all.ps1")
}

Write-Host "Pushing $Branch to $Remote/$Branch" -ForegroundColor Green
git push -u $Remote $Branch
