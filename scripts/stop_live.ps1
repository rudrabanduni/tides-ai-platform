<#
.SYNOPSIS
    Stops the demo backend and frontend processes started by scripts\start_demo.ps1.
#>
param([switch]$Quiet)
$Root = (Resolve-Path "$PSScriptRoot\..").Path
$pidFile = Join-Path $Root "logs\live_pids.json"
if (-not (Test-Path $pidFile)) { if (-not $Quiet) { Write-Host "No running live instance recorded." }; return }
$pids = Get-Content $pidFile -Raw | ConvertFrom-Json
foreach ($name in @("backend", "frontend")) {
    $id = $pids.$name
    if ($id) {
        try {
            Stop-Process -Id $id -Force -ErrorAction Stop
            if (-not $Quiet) { Write-Host "Stopped $name (PID $id)" }
        } catch {
            if (-not $Quiet) { Write-Host "$name (PID $id) was not running" }
        }
    }
}
Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
