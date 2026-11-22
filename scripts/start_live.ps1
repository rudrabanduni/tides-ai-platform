<#
.SYNOPSIS
    Starts TIDES-AI in LIVE mode: real Claude evaluations, $0.60 ceiling per evaluation.

.DESCRIPTION
    1. Asks for your Anthropic API key in a HIDDEN prompt (nothing is shown, saved or logged).
    2. Runs a two-call canary (well under $0.01) to prove the key and settings work.
    3. Starts the backend (http://127.0.0.1:8000) and frontend (http://localhost:3000) on the
       separate live database tides_live.db.
    The key lives only in the memory of the running backend. Run again after a reboot.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\start_live.ps1
#>
param([int]$BackendPort = 8000, [int]$FrontendPort = 3000, [switch]$Rebuild)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path "$PSScriptRoot\..").Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$NodeDir = Join-Path $Root ".node\node-v22.11.0-win-x64"
$Frontend = Join-Path $Root "frontend"
$Logs = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $Logs | Out-Null
if (Test-Path (Join-Path $NodeDir "node.exe")) { $env:PATH = "$NodeDir;$env:PATH" }

# Stop the demo or a previous live instance (same ports)
& (Join-Path $PSScriptRoot "stop_demo.ps1") -Quiet
& (Join-Path $PSScriptRoot "stop_live.ps1") -Quiet

Write-Host ""
Write-Host "TIDES-AI LIVE MODE - real Claude evaluations (max `$0.60 each)" -ForegroundColor Cyan
$secure = Read-Host "Paste your Anthropic API key and press Enter (it will not be shown)" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try { $key = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
$key = $key.Trim()
if (-not $key) { throw "No key entered." }

& $Python (Join-Path $PSScriptRoot "live_instance.py") | Out-Host
$liveEmail = (Get-Content (Join-Path $Root ".env.live") | Where-Object { $_ -like "TIDES_LIVE_EMAIL=*" }) -replace "^TIDES_LIVE_EMAIL=", ""

# Key only in this process's environment, inherited by the canary and the backend.
$env:ANTHROPIC_API_KEY = $key
Remove-Variable key
try {
    Write-Host "Running live canary (2 tiny calls)..."
    $canary = & $Python (Join-Path $PSScriptRoot "live_canary.py")
    $canary | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "Live canary failed - nothing was started. Details: logs\live_canary.json" }
    $modeLine = $canary | Where-Object { $_ -like "AI_STRUCTURED_THINKING_MODE=*" } | Select-Object -Last 1
    $env:AI_STRUCTURED_THINKING_MODE = ($modeLine -replace "^AI_STRUCTURED_THINKING_MODE=", "")

    # Frontend build without demo hints
    $envLocal = @("NEXT_PUBLIC_API_URL=http://127.0.0.1:$BackendPort", "NEXT_PUBLIC_DEMO_MODE=false", "NEXT_TELEMETRY_DISABLED=1") -join "`n"
    $envLocalPath = Join-Path $Frontend ".env.local"
    $previous = if (Test-Path $envLocalPath) { Get-Content $envLocalPath -Raw } else { "" }
    Set-Content -Path $envLocalPath -Value $envLocal -Encoding utf8 -NoNewline
    if ($Rebuild -or ($previous.Trim() -ne $envLocal.Trim()) -or -not (Test-Path (Join-Path $Frontend ".next\BUILD_ID"))) {
        Write-Host "Building frontend..."
        Push-Location $Frontend
        try { & npx next build *> (Join-Path $Logs "live_frontend_build.log") } finally { Pop-Location }
        if ($LASTEXITCODE -ne 0) { throw "Frontend build failed - see logs\live_frontend_build.log" }
    }

    $backend = Start-Process -FilePath $Python -ArgumentList @((Join-Path $PSScriptRoot "run_live_backend.py"), "--port", "$BackendPort") `
        -WorkingDirectory $Root -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $Logs "live_backend.out.log") -RedirectStandardError (Join-Path $Logs "live_backend.err.log")
} finally {
    # Remove the key from this shell once the backend has inherited it.
    Remove-Item Env:\ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
}

$nextCmd = Join-Path $Frontend "node_modules\next\dist\bin\next"
$frontendProc = Start-Process -FilePath (Get-Command node).Source -ArgumentList @($nextCmd, "start", "-p", "$FrontendPort") `
    -WorkingDirectory $Frontend -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $Logs "live_frontend.out.log") -RedirectStandardError (Join-Path $Logs "live_frontend.err.log")
@{ backend = $backend.Id; frontend = $frontendProc.Id } | ConvertTo-Json | Set-Content (Join-Path $Logs "live_pids.json") -Encoding utf8

function Wait-Url($url, $seconds) {
    $deadline = (Get-Date).AddSeconds($seconds)
    while ((Get-Date) -lt $deadline) {
        try { $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3; if ($r.StatusCode -lt 500) { return $true } } catch { Start-Sleep -Milliseconds 700 }
    }
    return $false
}
$okB = Wait-Url "http://127.0.0.1:$BackendPort/health" 60
$okF = Wait-Url "http://localhost:$FrontendPort/login" 60
Write-Host ""
Write-Host "================ TIDES-AI LIVE MODE ================" -ForegroundColor Cyan
Write-Host (" App      : http://localhost:{0}  [{1}]" -f $FrontendPort, $(if ($okF) { "UP" } else { "NOT RESPONDING" }))
Write-Host (" Backend  : http://127.0.0.1:{0}  [{1}]" -f $BackendPort, $(if ($okB) { "UP" } else { "NOT RESPONDING" }))
Write-Host (" Login    : {0}  (password: .venv\Scripts\python.exe scripts\live_instance.py --show-credentials)" -f $liveEmail)
Write-Host " Budget   : max `$0.60 per evaluation"
Write-Host " Stop     : powershell -ExecutionPolicy Bypass -File scripts\stop_live.ps1"
Write-Host "====================================================" -ForegroundColor Cyan
if (-not ($okB -and $okF)) { exit 1 }
