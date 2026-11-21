<#
.SYNOPSIS
    Secure Launcher for TIDES-AI Controlled One-Time Claude Live Evaluation.
.DESCRIPTION
    Prompts for the Anthropic API key via non-echoing hidden terminal input (Read-Host -AsSecureString).
    Temporarily supplies the key in process memory to scripts/run_one_time_live_eval.py,
    then securely removes it immediately from environment and memory upon exit or cancellation.
    Fails closed if the key is empty.
    Defaults to safe dry-run mode unless -ExecuteLive is explicitly provided.
.PARAMETER ExecuteLive
    Explicit switch to authorize paid live API calls against Anthropic within the $0.35 USD limit.
.PARAMETER ReuseExistingExtraction
    Explicit switch to reuse pre-extracted canonical claims for CleanPower Systems (9b8174247d774a1fa927a432b12564eb).
.PARAMETER ReuseStartupId
    Explicit startup application ID to reuse existing extracted claims for.
.PARAMETER StethaimPilot
    Explicit switch to target the real-startup pilot for STETHAIM Pvt. Ltd. (Neumo Rex) using multi-document inputs.
.PARAMETER StartupId
    Explicit target startup UUID in isolated tides_dev.db to evaluate using its registered source documents.
.PARAMETER Petrevolt
    Convenience switch resolving to PETREVOLT ENERGY SOLUTIONS PVT LTD (1b5de317-6e56-4dcb-ada9-28ab9adf8c0c).
.PARAMETER RecoverDomain
    Canonical domain key to reassess during domain recovery (default: founder_team).
.PARAMETER RecoverExtractionStage
    Extraction stage key to recover when resuming an EXTRACTION_FAILED run (e.g., financials_support or auto).
#>
param(
    [switch]$ExecuteLive,
    [switch]$ReuseExistingExtraction,
    [string]$ReuseStartupId,
    [switch]$StethaimPilot,
    [string]$StartupId,
    [switch]$Petrevolt,
    [string]$RecoverEvaluationId,
    [string]$RecoverStartupId,
    [string]$RecoverDomain = "founder_team",
    [string]$RecoverExtractionStage
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Error "Virtual environment Python not found at $pythonExe. Ensure .venv is active."
    exit 1
}

$extraArgs = @()
if (-not [string]::IsNullOrWhiteSpace($RecoverEvaluationId)) {
    $extraArgs += @("--recover-evaluation-id", $RecoverEvaluationId)
    if (-not [string]::IsNullOrWhiteSpace($RecoverStartupId)) {
        $extraArgs += @("--recover-startup-id", $RecoverStartupId)
    }
    if (-not [string]::IsNullOrWhiteSpace($RecoverExtractionStage)) {
        $extraArgs += @("--recover-extraction-stage", $RecoverExtractionStage)
    } elseif (-not [string]::IsNullOrWhiteSpace($RecoverDomain)) {
        $extraArgs += @("--recover-domain", $RecoverDomain)
    }
} elseif ($Petrevolt -or (-not [string]::IsNullOrWhiteSpace($StartupId))) {
    if ($StethaimPilot -or $ReuseExistingExtraction -or (-not [string]::IsNullOrWhiteSpace($ReuseStartupId))) {
        Write-Error "Cannot combine -Petrevolt / -StartupId with -StethaimPilot or CleanPower reuse flags."
        exit 1
    }
    if ($Petrevolt) {
        $extraArgs += @("--petrevolt")
    }
    if (-not [string]::IsNullOrWhiteSpace($StartupId)) {
        $extraArgs += @("--startup-id", $StartupId)
    }
} elseif ($StethaimPilot) {
    if ($ReuseExistingExtraction -or (-not [string]::IsNullOrWhiteSpace($ReuseStartupId))) {
        Write-Error "Cannot combine -StethaimPilot with -ReuseExistingExtraction or -ReuseStartupId. STETHAIM requires fresh multi-document extraction."
        exit 1
    }
    $extraArgs += @("--stethaim-pilot")
} else {
    if ($ReuseExistingExtraction -and [string]::IsNullOrWhiteSpace($ReuseStartupId)) {
        $ReuseStartupId = "9b8174247d774a1fa927a432b12564eb"
    }
    if (-not [string]::IsNullOrWhiteSpace($ReuseStartupId)) {
        $extraArgs += @("--reuse-startup-id", $ReuseStartupId)
    }
}

# If -ExecuteLive is not specified, run safely in dry-run mode
if (-not $ExecuteLive) {
    Write-Host "`n======================================================================" -ForegroundColor Cyan
    Write-Host "  TIDES-AI: DRY-RUN / PREPARATION MODE" -ForegroundColor Cyan
    Write-Host "  No live API calls will be made without the -ExecuteLive switch." -ForegroundColor Cyan
    Write-Host "======================================================================`n" -ForegroundColor Cyan
    & $pythonExe "scripts/run_one_time_live_eval.py" @extraArgs
    exit $LASTEXITCODE
}

# Derive shared configuration from scripts/run_one_time_live_eval.py to prevent banner drift
$cfg = $null
try {
    $cfgJson = & $pythonExe -c "import json; from scripts.run_one_time_live_eval import get_launcher_config; print(json.dumps(get_launcher_config()))" 2>$null
    if ($cfgJson) {
        $cfg = $cfgJson | ConvertFrom-Json
    }
} catch {
    # Non-fatal fallback to known baseline constants
}

$stageCount = if ($cfg -and $cfg.extraction_stages_count) { $cfg.extraction_stages_count } else { 10 }
$extCapStr = if ($cfg -and $cfg.extraction_token_cap_str) { $cfg.extraction_token_cap_str } else { "2,400-4,096 tokens across 10 stages" }
$domainCapStr = if ($cfg -and $cfg.domain_token_caps_str) { $cfg.domain_token_caps_str } else { "<= 900 tokens/batch (19 batches, <= 5 criteria/batch)" }
$revCap = if ($cfg -and $cfg.reviewer_token_cap) { $cfg.reviewer_token_cap } else { 2400 }
$budgetUsd = if ($cfg -and $cfg.budget_ceiling_usd) { "{0:N2}" -f $cfg.budget_ceiling_usd } else { "0.35" }
$bufferedInr = if ($cfg -and $cfg.buffered_ceiling_inr) { "{0:N2}" -f $cfg.buffered_ceiling_inr } else { "39.65" }
$fastModel = if ($cfg -and $cfg.fast_extraction_model) { $cfg.fast_extraction_model } else { "claude-haiku-5-5" }
$reasoningModel = if ($cfg -and $cfg.reasoning_model) { $cfg.reasoning_model } else { "claude-sonnet-5-5" }

Write-Host "`n======================================================================" -ForegroundColor Yellow
Write-Host "  TIDES-AI: SECURE ONE-TIME CLAUDE LIVE EVALUATION LAUNCHER" -ForegroundColor Yellow
Write-Host "  Budget Ceiling: `$$budgetUsd USD (<= INR $bufferedInr)" -ForegroundColor Yellow
if (-not [string]::IsNullOrWhiteSpace($RecoverEvaluationId)) {
    if (-not [string]::IsNullOrWhiteSpace($RecoverExtractionStage)) {
        $recStartup = if (-not [string]::IsNullOrWhiteSpace($RecoverStartupId)) { $RecoverStartupId } else { "TARGET_STARTUP_REQUIRED" }
        Write-Host "  Mode: Targeted extraction recovery ($RecoverExtractionStage), obeying cumulative ceiling" -ForegroundColor Yellow
        Write-Host "  Evaluation ID: $RecoverEvaluationId" -ForegroundColor Yellow
        Write-Host "  Startup ID: $recStartup" -ForegroundColor Yellow
        Write-Host "  Models: $fastModel (Remaining extraction), $reasoningModel (6 domains + Supervisory Review)" -ForegroundColor Yellow
        Write-Host "  Output Token Caps: Extraction $extCapStr; Domains $domainCapStr; Reviewer $revCap tokens" -ForegroundColor Yellow
    } else {
        $recStartup = if (-not [string]::IsNullOrWhiteSpace($RecoverStartupId)) { $RecoverStartupId } else { "a246f3a5-b797-43fc-9dc3-3e603e3b37b9" }
        $recDomain = if (-not [string]::IsNullOrWhiteSpace($RecoverDomain)) { $RecoverDomain } else { "founder_team" }
        Write-Host "  Target: STETHAIM Pvt. Ltd. (Neumo Rex)" -ForegroundColor Yellow
        Write-Host "  Mode: Targeted recovery, not full extraction" -ForegroundColor Yellow
        Write-Host "  Evaluation ID: $RecoverEvaluationId" -ForegroundColor Yellow
        Write-Host "  Startup ID: $recStartup" -ForegroundColor Yellow
        Write-Host "  Requested Domain: $recDomain" -ForegroundColor Yellow
        Write-Host "  Document Extraction Calls: 0 (SKIPPED)" -ForegroundColor Yellow
        Write-Host "  Models: $reasoningModel (Reasoning & Review; Haiku extraction SKIPPED)" -ForegroundColor Yellow
        Write-Host "  Output Token Caps: Domain ($recDomain) 2,400 tokens; Reviewer $revCap tokens" -ForegroundColor Yellow
    }
} elseif ($Petrevolt -or (-not [string]::IsNullOrWhiteSpace($StartupId))) {
    $targetDisplay = if ($Petrevolt) { "PETREVOLT ENERGY SOLUTIONS PVT LTD (1b5de317-6e56-4dcb-ada9-28ab9adf8c0c)" } else { "Target Startup ID: $StartupId" }
    Write-Host "  Target: $targetDisplay" -ForegroundColor Yellow
    Write-Host "  Extraction Mode: FRESH $stageCount-STAGE EXTRACTION FROM REGISTERED DOCUMENTS" -ForegroundColor Yellow
    Write-Host "  Models: $fastModel ($stageCount Staged Extractions), $reasoningModel (Reasoning & Review)" -ForegroundColor Yellow
    Write-Host "  Output Token Caps: Extraction $extCapStr; Domains $domainCapStr; Reviewer $revCap tokens" -ForegroundColor Yellow
} elseif ($StethaimPilot) {
    Write-Host "  Target: STETHAIM Pvt. Ltd. (Neumo Rex)" -ForegroundColor Yellow
    Write-Host "  Sector / Stage: MedTech | Stage 4 (Agreement Signing, Round Status: Passed)" -ForegroundColor Yellow
    Write-Host "  Input Documents: Applications.xlsx, Shikha_Behera_CV-2.docx, NEW PITCH DECK STETHAIM.pdf" -ForegroundColor Yellow
    Write-Host "  Privacy: Aadhaar, Phone, Email, Residential Address EXCLUDED" -ForegroundColor Yellow
    Write-Host "  Extraction Mode: FRESH $stageCount-STAGE EXTRACTION (Zero CleanPower reuse)" -ForegroundColor Yellow
    Write-Host "  Models: $fastModel ($stageCount Staged Extractions), $reasoningModel (Reasoning & Review)" -ForegroundColor Yellow
    Write-Host "  Output Token Caps: Extraction $extCapStr; Domains $domainCapStr; Reviewer $revCap tokens" -ForegroundColor Yellow
} elseif (-not [string]::IsNullOrWhiteSpace($ReuseStartupId)) {
    Write-Host "  Target: CleanPower Systems (PDF Fixture)" -ForegroundColor Yellow
    Write-Host "  Extraction Mode: REUSE EXISTING CLAIMS ($ReuseStartupId)" -ForegroundColor Yellow
    Write-Host "  Models: $reasoningModel (Reasoning & review; Haiku extraction SKIPPED)" -ForegroundColor Yellow
    Write-Host "  Output Token Caps: Domains $domainCapStr; Reviewer $revCap tokens (Gateway forwarded)" -ForegroundColor Yellow
} else {
    Write-Host "  Target: CleanPower Systems (PDF Fixture)" -ForegroundColor Yellow
    Write-Host "  Extraction Mode: FULL EXTRACTION FROM FIXTURE ($stageCount Stages)" -ForegroundColor Yellow
    Write-Host "  Models: $fastModel (Extraction), $reasoningModel (Reasoning & Review)" -ForegroundColor Yellow
    Write-Host "  Output Token Caps: Extraction $extCapStr; Domains $domainCapStr; Reviewer $revCap tokens" -ForegroundColor Yellow
}
Write-Host "  External Research: DISABLED (0 Tavily queries)" -ForegroundColor Yellow
Write-Host "======================================================================`n" -ForegroundColor Yellow

# Secure Prompt: non-echoing hidden terminal input
$secureKey = Read-Host -Prompt "Enter Anthropic API Key (hidden, will not echo to screen)" -AsSecureString

# Extract in-memory plain text without echoing or saving to console history
$bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
$plainKey = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)

if ([string]::IsNullOrWhiteSpace($plainKey)) {
    Write-Host "`n[SECURITY ERROR] Anthropic API key cannot be empty. Aborting live evaluation." -ForegroundColor Red
    exit 1
}

$exitCode = 0
try {
    # Set key only in current process environment for child execution
    $env:ANTHROPIC_API_KEY = $plainKey
    $env:AI_PROVIDER = "anthropic"

    Write-Host "`nCredentials received in memory. Initiating controlled live evaluation..." -ForegroundColor Green
    & $pythonExe "scripts/run_one_time_live_eval.py" --execute-live @extraArgs
    $exitCode = $LASTEXITCODE
}
finally {
    # Secure cleanup: Wipe plain text key from memory and environment
    $plainKey = $null
    $secureKey = $null
    Remove-Item Env:\ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
    [System.GC]::Collect()
    Write-Host "`n[SECURITY] Anthropic API Key securely cleared from process environment." -ForegroundColor Gray
}

exit $exitCode
