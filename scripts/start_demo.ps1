<#
.SYNOPSIS
    Starts the complete TIDES-AI OFFLINE stakeholder demonstration (backend + frontend).

.DESCRIPTION
    * Backend:  http://127.0.0.1:8000  (docs: /docs)  - tides_demo.db, uploads_demo\, MockAIGateway
    * Frontend: http://localhost:3000                 - Next.js production build
    No API keys are used and no external AI provider can be called (AI_PROVIDER=mock,
    ALLOW_UI_LIVE_EVALUATIONS=false, provider key variables blanked for both processes).

.PARAMETER Reset
    Wipe tides_demo.db and uploads_demo\ first (never touches tides_ai.db or tides_dev.db).

.PARAMETER Rebuild
    Force a fresh frontend production build.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\start_demo.ps1
    powershell -ExecutionPolicy Bypass -File scripts\start_demo.ps1 -Reset -Rebuild
#>
param(
    [switch]$Reset,
    [switch]$Rebuild,
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path "$PSScriptRoot\..").Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$NodeDir = Join-Path $Root ".node\node-v22.11.0-win-x64"
$Frontend = Join-Path $Root "frontend"
$Logs = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $Logs | Out-Null

if (-not (Test-Path $Python)) { throw "Python virtual environment not found at $Python" }
if (Test-Path (Join-Path $NodeDir "node.exe")) { $env:PATH = "$NodeDir;$env:PATH" }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw "Node.js not found (expected $NodeDir)" }

# Stop a previous demo started by this script
& (Join-Path $PSScriptRoot "stop_demo.ps1") -Quiet
& (Join-Path $PSScriptRoot "stop_live.ps1") -Quiet

# 1. Demo database
$initArgs = @((Join-Path $PSScriptRoot "init_demo_db.py"))
if ($Reset) { $initArgs += "--reset" }
& $Python @initArgs
if ($LASTEXITCODE -ne 0) { throw "Demo database initialisation failed" }

$demoEmail = (Get-Content (Join-Path $Root ".env.demo") | Where-Object { $_ -like "TIDES_DEMO_EMAIL=*" }) -replace "^TIDES_DEMO_EMAIL=", ""

# 2. Frontend build (NEXT_PUBLIC_* values are compiled into the bundle)
$envLocal = @(
    "NEXT_PUBLIC_API_URL=http://127.0.0.1:$BackendPort",
    "NEXT_PUBLIC_DEMO_MODE=true",
    "NEXT_PUBLIC_DEMO_LOGIN_EMAIL=$demoEmail",
    "NEXT_TELEMETRY_DISABLED=1"
) -join "`n"
$envLocalPath = Join-Path $Frontend ".env.local"
$previous = if (Test-Path $envLocalPath) { Get-Content $envLocalPath -Raw } else { "" }
Set-Content -Path $envLocalPath -Value $envLocal -Encoding utf8 -NoNewline
$needBuild = $Rebuild -or -not (Test-Path (Join-Path $Frontend ".next\BUILD_ID")) -or ($previous.Trim() -ne $envLocal.Trim())
if ($needBuild) {
    Write-Host "Building frontend (production)..."
    Push-Location $Frontend
    try { & npx next build *> (Join-Path $Logs "demo_frontend_build.log") } finally { Pop-Location }
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed - see logs\demo_frontend_build.log" }
}

# 3. Start backend (provider keys blanked in the child environment)
$env:ANTHROPIC_API_KEY = ""
$env:TAVILY_API_KEY = ""
$env:RESEARCH_API_KEY = ""
$env:AI_PROVIDER = "mock"
$backend = Start-Process -FilePath $Python -ArgumentList @((Join-Path $PSScriptRoot "run_demo_backend.py"), "--port", "$BackendPort") `
    -WorkingDirectory $Root -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $Logs "demo_backend.out.log") -RedirectStandardError (Join-Path $Logs "demo_backend.err.log")

# 4. Start frontend
$nextCmd = Join-Path $Frontend "node_modules\next\dist\bin\next"
$frontendProc = Start-Process -FilePath (Get-Command node).Source -ArgumentList @($nextCmd, "start", "-p", "$FrontendPort") `
    -WorkingDirectory $Frontend -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $Logs "demo_frontend.out.log") -RedirectStandardError (Join-Path $Logs "demo_frontend.err.log")

@{ backend = $backend.Id; frontend = $frontendProc.Id } | ConvertTo-Json | Set-Content (Join-Path $Logs "demo_pids.json") -Encoding utf8

# 5. Wait for both services
function Wait-Url($url, $seconds) {
    $deadline = (Get-Date).AddSeconds($seconds)
    while ((Get-Date) -lt $deadline) {
        try { $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3; if ($r.StatusCode -lt 500) { return $true } } catch { Start-Sleep -Milliseconds 700 }
    }
    return $false
}
$okBackend = Wait-Url "http://127.0.0.1:$BackendPort/health" 60
$okFrontend = Wait-Url "http://localhost:$FrontendPort/login" 60

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Yellow
Write-Host " TIDES-AI OFFLINE DEMONSTRATION" -ForegroundColor Yellow
Write-Host " MOCK DEMONSTRATION - OFFLINE SYNTHETIC RESULTS - NOT A REAL AI EVALUATION" -ForegroundColor Yellow
Write-Host "==================================================================" -ForegroundColor Yellow
Write-Host (" Frontend : http://localhost:{0}   [{1}]" -f $FrontendPort, $(if ($okFrontend) { "UP" } else { "NOT RESPONDING - see logs\demo_frontend.*.log" }))
Write-Host (" Backend  : http://127.0.0.1:{0}   [{1}]" -f $BackendPort, $(if ($okBackend) { "UP" } else { "NOT RESPONDING - see logs\demo_backend.*.log" }))
Write-Host (" API docs : http://127.0.0.1:{0}/docs" -f $BackendPort)
Write-Host (" Login    : {0}  (password: run  .venv\Scripts\python.exe scripts\init_demo_db.py --show-credentials)" -f $demoEmail)
Write-Host " Sample deck: demo_fixtures\cleanpower_systems_pitch_deck.pdf"
Write-Host " Stop with : powershell -ExecutionPolicy Bypass -File scripts\stop_demo.ps1"
if (-not ($okBackend -and $okFrontend)) { exit 1 }
