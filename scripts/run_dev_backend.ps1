<#
.SYNOPSIS
    Starts the TIDES-AI FastAPI backend in safe local development mode (Mock AI).

.DESCRIPTION
    Runs on 127.0.0.1:8000 using dedicated tides_dev.db and AI_PROVIDER=mock.
    Protects tides_ai.db from accidental writes.
#>

param (
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $ProjectRoot

# Ensure virtualenv python is available
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Error "Virtual environment python not found at $PythonExe"
    exit 1
}

# Run through the safe python runner
& $PythonExe "$PSScriptRoot\run_dev_backend.py" --host $HostAddress --port $Port
