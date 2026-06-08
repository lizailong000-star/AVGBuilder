param(
    [switch]$SkipServerProbe,
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir
Set-Location $Root

$failed = $false

function Step($Name, [scriptblock]$Action) {
    Write-Host ""
    Write-Host "== $Name =="
    try {
        & $Action
        Write-Host "OK: $Name"
    } catch {
        Write-Host "FAILED: $Name" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        $script:failed = $true
    }
}

$python = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }

Step "Python backend compile" {
    & $python -m compileall backend
    if ($LASTEXITCODE -ne 0) { throw "compileall failed with exit code $LASTEXITCODE" }
}

Step "Frontend JavaScript syntax" {
    & node --check frontend/app.js
    if ($LASTEXITCODE -ne 0) { throw "node --check failed with exit code $LASTEXITCODE" }
}

Step "Git status: AVGBuilder" {
    git status --short
    if ($LASTEXITCODE -ne 0) { throw "git status failed for AVGBuilder" }
}

$DemoAvg = "D:\GitHub\DemoAVG"
if (Test-Path $DemoAvg) {
    Step "Git status: DemoAVG (read-only)" {
        git -C $DemoAvg status --short
        if ($LASTEXITCODE -ne 0) { throw "git status failed for DemoAVG" }
    }
} else {
    Write-Host ""
    Write-Host "SKIP: DemoAVG not found at $DemoAvg"
}

if (-not $SkipServerProbe) {
    Step "Optional server probe" {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri "$BaseUrl/api/ai/capabilities" -TimeoutSec 3
            Write-Host "HTTP $($response.StatusCode): $BaseUrl/api/ai/capabilities"
        } catch {
            Write-Host "WARN: Server probe failed. Start dev server first with powershell -ExecutionPolicy Bypass -File scripts/start_dev.ps1, or run scripts/check_all.ps1 -SkipServerProbe. Detail: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
if ($failed) {
    Write-Host "CHECK RESULT: FAILED" -ForegroundColor Red
    exit 1
}

Write-Host "CHECK RESULT: OK" -ForegroundColor Green
