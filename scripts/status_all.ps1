param(
    [string]$DemoAvgPath = "D:\GitHub\DemoAVG"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir

function Show-RepoStatus($Name, $Path) {
    Write-Host ""
    Write-Host "== $Name =="
    Write-Host "Path: $Path"

    if (-not (Test-Path $Path)) {
        Write-Host "Missing path" -ForegroundColor Yellow
        return
    }

    git -C $Path rev-parse --is-inside-work-tree | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Not a git repository" -ForegroundColor Yellow
        return
    }

    $branch = git -C $Path branch --show-current
    $head = git -C $Path log -1 --oneline
    Write-Host "Branch: $branch"
    Write-Host "HEAD: $head"
    Write-Host "Status:"
    $status = git -C $Path status --short
    if ([string]::IsNullOrWhiteSpace($status)) {
        Write-Host "  clean"
    } else {
        $status | ForEach-Object { Write-Host "  $_" }
    }
}

Show-RepoStatus "AVGBuilder" $Root
Show-RepoStatus "DemoAVG (read-only check)" $DemoAvgPath
