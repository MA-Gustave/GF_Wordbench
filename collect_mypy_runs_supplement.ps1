[CmdletBinding()]
param(
    [Parameter()]
    [string]$RepositoryRoot = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = (Resolve-Path -LiteralPath $RepositoryRoot).Path
if (-not (Test-Path -LiteralPath (Join-Path $root "pyproject.toml") -PathType Leaf)) {
    throw "RepositoryRoot must contain pyproject.toml: $root"
}

$relativeFiles = @(
    "src/gf_wordbench/runs/models/results.py",
    "src/gf_wordbench/runs/stage_executor.py",
    "src/gf_wordbench/runs/history.py",
    "src/gf_wordbench/runs/continuation.py",
    "src/gf_wordbench/runs/finalizer.py",
    "src/gf_wordbench/runs/progress.py",
    "src/gf_wordbench/runs/result_builder.py",
    "tests/unit/runs/test_preflight.py",
    "tests/unit/runs/test_lifecycle.py",
    "tests/unit/runs/test_result_builder.py",
    "tests/unit/runs/test_planner.py",
    "tests/unit/runs/test_stage_executor.py",
    "tests/unit/runs/test_history.py",
    "tests/unit/runs/test_budgets.py",
    "tests/unit/runs/test_orchestrator.py",
    "tests/unit/runs/test_identity_and_paths.py"
)

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputRoot = Join-Path $root ".wordbench-diagnostics\mypy-runs-supplement\$stamp"
$payloadRoot = Join-Path $outputRoot "payload"
New-Item -ItemType Directory -Path $payloadRoot -Force | Out-Null

$missing = [System.Collections.Generic.List[string]]::new()

foreach ($relative in $relativeFiles) {
    $source = Join-Path $root $relative
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        $missing.Add($relative)
        continue
    }

    $destination = Join-Path $payloadRoot $relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination -Force
}

if ($missing.Count -gt 0) {
    throw "Missing requested files:`n$($missing -join "`n")"
}

$inventory = Get-ChildItem -LiteralPath $payloadRoot -File -Recurse |
    Sort-Object FullName |
    ForEach-Object {
        [pscustomobject]@{
            Path = [System.IO.Path]::GetRelativePath($payloadRoot, $_.FullName).Replace("\", "/")
            Size = $_.Length
            SHA256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }

$inventory | Export-Csv `
    -LiteralPath (Join-Path $payloadRoot "inventory.csv") `
    -NoTypeInformation `
    -Encoding utf8

$zipPath = Join-Path $outputRoot "GF_Wordbench_mypy_runs_supplement_$stamp.zip"
Compress-Archive -LiteralPath (Join-Path $payloadRoot "*") -DestinationPath $zipPath -Force

Write-Host ""
Write-Host "Runs supplement created:"
Write-Host $zipPath
Write-Host "Files: $($relativeFiles.Count)"
