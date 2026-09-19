[CmdletBinding()]
param(
    [Parameter()]
    [string]$RepositoryRoot = (Get-Location).Path,

    [Parameter()]
    [string]$ExistingMypyLog = "mypy.log",

    [Parameter()]
    [switch]$SkipMypy
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = (Resolve-Path -LiteralPath $RepositoryRoot).Path
$pyproject = Join-Path $root "pyproject.toml"
if (-not (Test-Path -LiteralPath $pyproject -PathType Leaf)) {
    throw "RepositoryRoot must contain pyproject.toml: $root"
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputRoot = Join-Path $root ".wordbench-diagnostics\mypy-campaign\$stamp"
$payloadRoot = Join-Path $outputRoot "payload"
New-Item -ItemType Directory -Path $payloadRoot -Force | Out-Null

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$flatLog = Join-Path $outputRoot "mypy.flat.log"
$mypyExitCode = 0

if (-not $SkipMypy) {
    Push-Location $root
    try {
        & python -m mypy `
            --no-pretty `
            --no-color-output `
            --show-error-codes `
            --show-column-numbers `
            src/gf_wordbench tests scripts 2>&1 |
            Tee-Object -FilePath $flatLog
        $mypyExitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
}
else {
    $existing = Join-Path $root $ExistingMypyLog
    if (-not (Test-Path -LiteralPath $existing -PathType Leaf)) {
        throw "Existing Mypy log not found: $existing"
    }

    $raw = [System.IO.File]::ReadAllBytes($existing)
    $encoding = if (
        $raw.Length -ge 2 -and
        $raw[0] -eq 0xFF -and
        $raw[1] -eq 0xFE
    ) {
        [System.Text.Encoding]::Unicode
    }
    else {
        [System.Text.UTF8Encoding]::new($false)
    }

    $text = $encoding.GetString($raw)
    [System.IO.File]::WriteAllText(
        $flatLog,
        $text,
        [System.Text.UTF8Encoding]::new($false)
    )
}

$errorPattern = [regex]::new(
    '^(?<path>(?:src|tests|scripts|tools)[\\/][^:]+):' +
    '(?<line>\d+)(?::(?<column>\d+))?: error: ' +
    '(?<message>.*?)(?:\s+\[(?<code>[^\]]+)\])?$',
    [System.Text.RegularExpressions.RegexOptions]::CultureInvariant
)

$errors = foreach ($line in Get-Content -LiteralPath $flatLog -Encoding utf8) {
    $match = $errorPattern.Match($line)
    if (-not $match.Success) {
        continue
    }

    [pscustomobject]@{
        Path = $match.Groups["path"].Value.Replace("\", "/")
        Line = [int]$match.Groups["line"].Value
        Column = if ($match.Groups["column"].Success) {
            [int]$match.Groups["column"].Value
        }
        else {
            $null
        }
        Code = $match.Groups["code"].Value
        Message = $match.Groups["message"].Value
    }
}

$errorFiles = $errors |
    Group-Object -Property Path |
    Sort-Object -Property Count -Descending |
    ForEach-Object {
        $codes = $_.Group |
            Group-Object -Property Code |
            Sort-Object -Property Count -Descending |
            ForEach-Object { "$($_.Name):$($_.Count)" }

        [pscustomobject]@{
            Path = $_.Name
            Errors = $_.Count
            Codes = $codes -join ";"
        }
    }

$errorCsv = Join-Path $outputRoot "mypy-errors.csv"
$errorFiles | Export-Csv -LiteralPath $errorCsv -NoTypeInformation -Encoding utf8

$errorList = Join-Path $outputRoot "mypy-error-files.txt"
$errorFiles.Path | Set-Content -LiteralPath $errorList -Encoding utf8

$excludedDirectoryNames = [System.Collections.Generic.HashSet[string]]::new(
    [string[]]@(
        ".git",
        ".venv",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".wordbench-diagnostics",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "htmlcov",
        "runs"
    ),
    [System.StringComparer]::OrdinalIgnoreCase
)

function Test-IsExcluded {
    param([Parameter(Mandatory)][string]$RelativePath)

    foreach ($part in ($RelativePath -split "[\\/]")) {
        if ($excludedDirectoryNames.Contains($part)) {
            return $true
        }
        if ($part -like "run_*") {
            return $true
        }
    }
    return $false
}

function Copy-RepositoryFile {
    param([Parameter(Mandatory)][System.IO.FileInfo]$File)

    $relative = [System.IO.Path]::GetRelativePath($root, $File.FullName)
    if (Test-IsExcluded -RelativePath $relative) {
        return
    }

    $destination = Join-Path $payloadRoot $relative
    $destinationDirectory = Split-Path -Parent $destination
    New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
    Copy-Item -LiteralPath $File.FullName -Destination $destination -Force
}

$rootFiles = @(
    "pyproject.toml",
    "README.md",
    "CONTRIBUTING.md",
    "LICENSE.md",
    "DOCUMENT_MANIFEST.json",
    ".gitignore",
    "launch_cli.bat",
    "launch_gui.bat",
    "launch_diagnostics.bat"
)

foreach ($relative in $rootFiles) {
    $candidate = Join-Path $root $relative
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        Copy-RepositoryFile -File (Get-Item -LiteralPath $candidate)
    }
}

$sourceRoots = @(
    "src",
    "tests",
    "scripts",
    "tools",
    "docs",
    "templates",
    "project",
    ".github"
)

foreach ($relativeRoot in $sourceRoots) {
    $candidateRoot = Join-Path $root $relativeRoot
    if (-not (Test-Path -LiteralPath $candidateRoot -PathType Container)) {
        continue
    }

    Get-ChildItem -LiteralPath $candidateRoot -File -Recurse |
        ForEach-Object { Copy-RepositoryFile -File $_ }
}

Copy-Item -LiteralPath $flatLog -Destination (Join-Path $payloadRoot "mypy.flat.log")
Copy-Item -LiteralPath $errorCsv -Destination (Join-Path $payloadRoot "mypy-errors.csv")
Copy-Item -LiteralPath $errorList -Destination (Join-Path $payloadRoot "mypy-error-files.txt")

$existingLogPath = Join-Path $root $ExistingMypyLog
if (Test-Path -LiteralPath $existingLogPath -PathType Leaf) {
    Copy-Item -LiteralPath $existingLogPath -Destination (Join-Path $payloadRoot "mypy.original.log")
}

$inventory = Get-ChildItem -LiteralPath $payloadRoot -File -Recurse |
    Sort-Object -Property FullName |
    ForEach-Object {
        [pscustomobject]@{
            Path = [System.IO.Path]::GetRelativePath($payloadRoot, $_.FullName).Replace("\", "/")
            Size = $_.Length
            SHA256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }

$inventoryPath = Join-Path $payloadRoot "inventory.csv"
$inventory | Export-Csv -LiteralPath $inventoryPath -NoTypeInformation -Encoding utf8

$summary = [ordered]@{
    generated_at = (Get-Date).ToString("o")
    repository_root = $root
    mypy_exit_code = $mypyExitCode
    mypy_error_count = @($errors).Count
    mypy_error_file_count = @($errorFiles).Count
    payload_file_count = @($inventory).Count + 1
}
$summaryPath = Join-Path $payloadRoot "campaign-summary.json"
$summary | ConvertTo-Json -Depth 4 |
    Set-Content -LiteralPath $summaryPath -Encoding utf8

$zipPath = Join-Path $outputRoot "GF_Wordbench_mypy_campaign_$stamp.zip"
Compress-Archive -Path (Join-Path $payloadRoot "*") -DestinationPath $zipPath -Force

Write-Host ""
Write-Host "Mypy campaign package created:"
Write-Host $zipPath
Write-Host ""
Write-Host "Mypy errors: $(@($errors).Count)"
Write-Host "Files with errors: $(@($errorFiles).Count)"
Write-Host "Mypy exit code: $mypyExitCode"

exit 0
