[CmdletBinding()]
param(
    [string] $RepoRoot = "C:\mycode\Grammatical_Framework\GF_Wordbench\GF_Wordbench",
    [string] $EnglishPath = "C:\mycode\Grammatical_Framework\gf-rgl\src\english",
    [switch] $SkipFullSuite,
    [switch] $NoPause
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Les codes non nuls des programmes externes sont traités par Invoke-Step.
# Cela empêche PowerShell 7.3+ de quitter avant la création du rapport.
$PSNativeCommandUseErrorActionPreference = $false

# L'anglais est une fixture explicite de validation. Il ne devient jamais
# une valeur par défaut du code de production.

$OverallCode = 0
$TranscriptStarted = $false
$WorkRoot = $null
$Logs = $null
$Runs = $null
$Diagnostics = $null
$Archive = $null
$Results = [System.Collections.Generic.List[object]]::new()

function Add-StepResult {
    param(
        [Parameter(Mandatory)]
        [string] $Name,

        [Parameter(Mandatory)]
        [string] $Result,

        [AllowNull()]
        [Nullable[int]] $ExitCode,

        [Parameter(Mandatory)]
        [string] $Log
    )

    [void] $script:Results.Add(
        [pscustomobject]@{
            Step     = $Name
            Result   = $Result
            ExitCode = $ExitCode
            Log      = $Log
        }
    )
}

function Add-SkippedStep {
    param(
        [Parameter(Mandatory)]
        [string] $Name,

        [Parameter(Mandatory)]
        [string] $Reason
    )

    Add-StepResult `
        -Name $Name `
        -Result "SKIP" `
        -ExitCode $null `
        -Log $Reason

    Write-Host "SKIP $Name : $Reason" -ForegroundColor Yellow
}

function Invoke-Step {
    param(
        [Parameter(Mandatory)]
        [string] $Name,

        [Parameter(Mandatory)]
        [scriptblock] $Action,

        [switch] $Required
    )

    $LogPath = Join-Path $script:Logs "$Name.txt"

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "ÉTAPE : $Name"
    Write-Host "Journal : $LogPath"
    Write-Host "============================================================"

    $global:LASTEXITCODE = 0
    $Code = 0
    $FailureText = $null

    try {
        & $Action 2>&1 |
            Tee-Object -FilePath $LogPath |
            ForEach-Object {
                Write-Host $_
            }

        if ($null -ne $LASTEXITCODE) {
            $Code = [int] $LASTEXITCODE
        }
    }
    catch {
        $Code = 1
        $FailureText = $_.Exception.Message

        @(
            ""
            "ERREUR POWERSHELL"
            $FailureText
            ""
            $_.ScriptStackTrace
            ""
            ($_ | Format-List * -Force | Out-String)
        ) |
            Tee-Object -FilePath $LogPath -Append |
            ForEach-Object {
                Write-Host $_
            }
    }

    if ($Code -eq 0) {
        Add-StepResult `
            -Name $Name `
            -Result "PASS" `
            -ExitCode 0 `
            -Log $LogPath

        Write-Host "PASS : $Name" -ForegroundColor Green
    }
    else {
        Add-StepResult `
            -Name $Name `
            -Result "FAIL" `
            -ExitCode $Code `
            -Log $LogPath

        Write-Host "FAIL : $Name (code $Code)" -ForegroundColor Red

        if ($FailureText) {
            Write-Host $FailureText -ForegroundColor Red
        }

        if ($Required) {
            $script:OverallCode = 1
        }
    }

    return [int] $Code
}

function Resolve-EnglishLanguagePath {
    param(
        [Parameter(Mandatory)]
        [string] $RequestedPath,

        [Parameter(Mandatory)]
        [string] $RepositoryRoot
    )

    $RepositoryParent = Split-Path $RepositoryRoot -Parent
    $FrameworkParent = Split-Path $RepositoryParent -Parent

    $Candidates = @(
        $RequestedPath,
        "C:\mycode\Grammatical_Framework\gf-rgl\src\english",
        (Join-Path $RepositoryParent "gf-rgl\src\english"),
        (Join-Path $FrameworkParent "gf-rgl\src\english")
    ) |
        Where-Object {
            $_ -and (Test-Path -LiteralPath $_ -PathType Container)
        } |
        Select-Object -Unique

    $Resolved = $Candidates |
        Select-Object -First 1

    if (-not $Resolved) {
        Write-Host ""
        Write-Warning "Le répertoire anglais n'a pas été trouvé automatiquement."
        $Resolved = Read-Host "Entre le chemin complet de gf-rgl\src\english"
    }

    if (-not (Test-Path -LiteralPath $Resolved -PathType Container)) {
        throw "Répertoire anglais introuvable : $Resolved"
    }

    return (Resolve-Path -LiteralPath $Resolved).Path
}

try {
    if ($PSVersionTable.PSVersion.Major -lt 7) {
        throw "Ce script exige PowerShell 7 ou plus récent."
    }

    if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) {
        throw "Dépôt introuvable : $RepoRoot"
    }

    $RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
    Set-Location $RepoRoot

    $EnglishPath = Resolve-EnglishLanguagePath `
        -RequestedPath $EnglishPath `
        -RepositoryRoot $RepoRoot

    $RglSourceRoot = Split-Path $EnglishPath -Parent
    $RglRoot = Split-Path $RglSourceRoot -Parent
    $EnglishEntry = Join-Path $EnglishPath "LangEng.gf"

    if (-not (Test-Path -LiteralPath $EnglishEntry -PathType Leaf)) {
        throw "Fichier anglais attendu introuvable : $EnglishEntry"
    }

    $Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $OutputParent = Split-Path $RepoRoot -Parent
    $WorkRoot = Join-Path `
        $OutputParent `
        "GF_Wordbench_english_validation_$Stamp"

    $Logs = Join-Path $WorkRoot "logs"
    $Runs = Join-Path $WorkRoot "runs"
    $Diagnostics = Join-Path $WorkRoot "diagnostics"
    $Archive = "$WorkRoot.zip"

    New-Item -ItemType Directory -Force `
        -Path $WorkRoot, $Logs, $Runs, $Diagnostics |
        Out-Null

    $TranscriptPath = Join-Path $Logs "00-console-transcript.txt"
    Start-Transcript -Path $TranscriptPath -Force | Out-Null
    $TranscriptStarted = $true

    Write-Host ""
    Write-Host "GF Wordbench — validation anglaise"
    Write-Host "Dépôt             : $RepoRoot"
    Write-Host "Langue anglaise   : $EnglishPath"
    Write-Host "Entrée anglaise   : $EnglishEntry"
    Write-Host "RGL root           : $RglRoot"
    Write-Host "Rapport            : $WorkRoot"
    Write-Host ""

    # Câblage local de test uniquement.
    $env:WORDBENCH_DIAG_REPO_ROOT = $RepoRoot
    $env:WORDBENCH_DIAG_LANGUAGE_PATH = $EnglishPath
    $env:WORDBENCH_DIAG_RGL_ROOT = $RglRoot
    $env:WORDBENCH_DIAG_OUTPUT_ROOT = $Runs
    $env:WORDBENCH_DIAG_ARTIFACT_DIR = $Diagnostics
    $env:PYTHONUTF8 = "1"
    $env:PYTHONIOENCODING = "utf-8"

    $Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"

    if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
        Write-Host "Création de .venv..."

        $PyLauncher = Get-Command py -ErrorAction SilentlyContinue

        if (-not $PyLauncher) {
            throw "Le lanceur Python 'py' est introuvable."
        }

        & py -m venv .venv

        if ($LASTEXITCODE -ne 0) {
            throw "La création de .venv a échoué avec le code $LASTEXITCODE."
        }
    }

    $GfCommand = Get-Command gf -ErrorAction SilentlyContinue
    $GfExecutable = $null

    if ($GfCommand) {
        if ($GfCommand.Source) {
            $GfExecutable = $GfCommand.Source
        }
        elseif ($GfCommand.Path) {
            $GfExecutable = $GfCommand.Path
        }
        else {
            $GfExecutable = "gf"
        }

        $env:WORDBENCH_DIAG_GF_EXECUTABLE = $GfExecutable
        Write-Host "GF executable      : $GfExecutable"
    }
    else {
        Remove-Item Env:WORDBENCH_DIAG_GF_EXECUTABLE `
            -ErrorAction SilentlyContinue

        Write-Warning (
            "GF est absent du PATH. Les tests sans compilation seront exécutés; " +
            "les tests GF réels seront marqués SKIP."
        )
    }

    $PipUpgradeCode = Invoke-Step `
        -Name "01-pip-upgrade" `
        -Required `
        -Action {
            & $Python -m pip install --upgrade pip
        }

    $InstallCode = Invoke-Step `
        -Name "02-install-dev" `
        -Required `
        -Action {
            & $Python -m pip install -e ".[dev]"
        }

    $EnvironmentReady = (
        ([int] $PipUpgradeCode -eq 0) -and
        ([int] $InstallCode -eq 0)
    )

    Write-Host (
        "Environnement prêt : {0} (pip={1}, install={2})" -f
        $EnvironmentReady,
        $PipUpgradeCode,
        $InstallCode
    )

    if ($EnvironmentReady) {
        Invoke-Step `
            -Name "03-package-version" `
            -Required `
            -Action {
                & $Python -c `
                    "import gf_wordbench; print(gf_wordbench.__version__)"
            } |
            Out-Null

        Invoke-Step `
            -Name "04-compileall" `
            -Required `
            -Action {
                & $Python -m compileall -q src tools scripts
            } |
            Out-Null

        Invoke-Step `
            -Name "05-cli-help" `
            -Required `
            -Action {
                & $Python -m gf_wordbench --help
            } |
            Out-Null

        Invoke-Step `
            -Name "06-english-language-probe" `
            -Required `
            -Action {
                & $Python -m gf_wordbench `
                    language probe `
                    $EnglishPath `
                    --rgl-root $RglRoot `
                    --verbose
            } |
            Out-Null

        Invoke-Step `
            -Name "07-english-probe-warning-contract" `
            -Required `
            -Action {
                $ProbeContractScript = @'
import os
from pathlib import Path

from gf_wordbench.projects.languages.public import probe_language_path

result = probe_language_path(
    Path(os.environ["WORDBENCH_DIAG_LANGUAGE_PATH"]),
    explicit_rgl_root=Path(os.environ["WORDBENCH_DIAG_RGL_ROOT"]),
    require_unambiguous_suffix=False,
)

print(f"resolved: {result.resolved}")
print(f"status: {result.status}")
print(f"diagnostics: {len(result.diagnostics)}")

if not result.resolved:
    raise SystemExit("English language did not resolve.")

errors = [
    diagnostic
    for diagnostic in result.diagnostics
    if str(getattr(diagnostic, "severity", "")).casefold() == "error"
]
if errors:
    for diagnostic in errors:
        print(
            "ERROR "
            f"{getattr(diagnostic, 'code', 'UNKNOWN')}: "
            f"{getattr(diagnostic, 'message', diagnostic)}"
        )
    raise SystemExit("Language probe returned error diagnostics.")

allowed_warning_codes = {"GF-WB-CONFIG-260"}
unexpected_warnings = [
    diagnostic
    for diagnostic in result.diagnostics
    if (
        str(getattr(diagnostic, "severity", "")).casefold() == "warning"
        and str(getattr(diagnostic, "code", "")) not in allowed_warning_codes
    )
]
if unexpected_warnings:
    for diagnostic in unexpected_warnings:
        print(
            "UNEXPECTED WARNING "
            f"{getattr(diagnostic, 'code', 'UNKNOWN')}: "
            f"{getattr(diagnostic, 'message', diagnostic)}"
        )
    raise SystemExit("Unexpected language-probe warning.")

expected = [
    diagnostic
    for diagnostic in result.diagnostics
    if str(getattr(diagnostic, "code", "")) == "GF-WB-CONFIG-260"
]
if expected:
    print(
        "EXPECTED WARNING GF-WB-CONFIG-260: "
        "multiple standard RGL module suffixes were detected."
    )
else:
    print(
        "INFO: GF-WB-CONFIG-260 was not emitted; "
        "the language still resolved without error."
    )
'@

                $ProbeContractScript | & $Python -
            } |
            Out-Null

        Invoke-Step `
            -Name "08-english-diagnostic-no-compile" `
            -Required `
            -Action {
                & $Python -m gf_wordbench `
                    validate `
                    --language-path $EnglishPath `
                    --rgl-root $RglRoot `
                    --mode diagnostic `
                    --no-compile `
                    --out-root $Runs `
                    --verbose
            } |
            Out-Null

        if ($GfExecutable) {
            Invoke-Step `
                -Name "09-english-probe-with-gf" `
                -Required `
                -Action {
                    & $Python -m gf_wordbench `
                        language probe `
                        $EnglishPath `
                        --rgl-root $RglRoot `
                        --gf-exe $GfExecutable `
                        --probe-gf `
                        --verbose
                } |
                Out-Null

            Invoke-Step `
                -Name "10-english-quick-compile" `
                -Required `
                -Action {
                    & $Python -m gf_wordbench `
                        validate `
                        --language-path $EnglishEntry `
                        --rgl-root $RglRoot `
                        --gf-exe $GfExecutable `
                        --mode quick `
                        --out-root $Runs `
                        --verbose
                } |
                Out-Null
        }
        else {
            Add-SkippedStep `
                -Name "09-english-probe-with-gf" `
                -Reason "GF absent du PATH."

            Add-SkippedStep `
                -Name "10-english-quick-compile" `
                -Reason "GF absent du PATH."
        }

        Invoke-Step `
            -Name "11-diagnostics-safe-suite" `
            -Required `
            -Action {
                & $Python tools/diagnostics/run_safe_suite.py
            } |
            Out-Null

        Invoke-Step `
            -Name "12-pytest-collection" `
            -Required `
            -Action {
                & $Python -m pytest --collect-only -q
            } |
            Out-Null

        $TargetCandidates = @(
            "tests/contracts",
            "tests/components/test_bootstrap.py",
            "tests/components/test_cli_gui_parity.py",
            "tests/unit/entrypoints",
            "tests/unit/projects",
            "tests/unit/state",
            "tests/unit/runs",
            "tests/unit/validation"
        )

        $TargetedTests = @(
            $TargetCandidates |
                Where-Object {
                    Test-Path -LiteralPath $_
                }
        )

        if ($TargetedTests.Count -gt 0) {
            Invoke-Step `
                -Name "13-language-targeted-tests" `
                -Required `
                -Action {
                    & $Python -m pytest @TargetedTests -q
                } |
                Out-Null
        }
        else {
            Add-SkippedStep `
                -Name "13-language-targeted-tests" `
                -Reason "Aucune cible de test attendue n'existe."
        }

        if ($SkipFullSuite) {
            Add-SkippedStep `
                -Name "14-full-test-suite" `
                -Reason "Option -SkipFullSuite."
        }
        else {
            Invoke-Step `
                -Name "14-full-test-suite" `
                -Required `
                -Action {
                    & $Python -m pytest -q
                } |
                Out-Null
        }
    }
    else {
        $OverallCode = 1

        foreach ($Name in @(
            "03-package-version",
            "04-compileall",
            "05-cli-help",
            "06-english-language-probe",
            "07-english-probe-warning-contract",
            "08-english-diagnostic-no-compile",
            "09-english-probe-with-gf",
            "10-english-quick-compile",
            "11-diagnostics-safe-suite",
            "12-pytest-collection",
            "13-language-targeted-tests",
            "14-full-test-suite"
        )) {
            Add-SkippedStep `
                -Name $Name `
                -Reason "Installation de l'environnement échouée."
        }
    }

    Invoke-Step `
        -Name "15-production-language-leak-gate" `
        -Required `
        -Action {
            $SearchTargets = @(
                (Join-Path $RepoRoot "src\gf_wordbench"),
                (Join-Path $RepoRoot "launch_cli.bat"),
                (Join-Path $RepoRoot "launch_gui.bat")
            )

            $Patterns = @(
                'src[\\/]+english',
                'LangEng\.gf',
                'GrammarEng\.gf',
                'AllEng\.gf'
            )

            $Files = foreach ($Target in $SearchTargets) {
                if (Test-Path -LiteralPath $Target -PathType Container) {
                    Get-ChildItem -LiteralPath $Target -Recurse -File |
                        Where-Object {
                            $_.Extension -in @(
                                ".py",
                                ".pyw",
                                ".json",
                                ".toml",
                                ".bat"
                            )
                        }
                }
                elseif (Test-Path -LiteralPath $Target -PathType Leaf) {
                    Get-Item -LiteralPath $Target
                }
            }

            $Hits = @(
                $Files |
                    Select-String `
                        -Pattern $Patterns `
                        -CaseSensitive:$false
            )

            if ($Hits.Count -gt 0) {
                $Hits |
                    ForEach-Object {
                        "{0}:{1}: {2}" -f `
                            $_.Path,
                            $_.LineNumber,
                            $_.Line.Trim()
                    }

                throw (
                    "$($Hits.Count) référence(s) anglaise(s) codée(s) en dur " +
                    "détectée(s) dans le code générique."
                )
            }

            Write-Host (
                "PASS: aucun chemin ou entrypoint anglais codé en dur " +
                "dans le code générique."
            )
        } |
        Out-Null

    Invoke-Step `
        -Name "16-git-diff-check" `
        -Required `
        -Action {
            git -c core.autocrlf=false diff --check
        } |
        Out-Null

    git branch --show-current `
        *> (Join-Path $Logs "17-git-branch.txt")

    git status --short `
        *> (Join-Path $Logs "18-git-status.txt")

    git diff --stat `
        *> (Join-Path $Logs "19-git-diff-stat.txt")

    git diff `
        *> (Join-Path $Logs "20-git-diff.patch")
}
catch {
    $OverallCode = 1

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "ERREUR NON GÉRÉE" -ForegroundColor Red
    Write-Host "============================================================"
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host $_.ScriptStackTrace

    if ($Logs -and (Test-Path -LiteralPath $Logs)) {
        $_ |
            Format-List * -Force |
            Out-String |
            Set-Content `
                -LiteralPath (Join-Path $Logs "UNHANDLED_ERROR.txt") `
                -Encoding UTF8
    }
}
finally {
    if ($TranscriptStarted) {
        try {
            Stop-Transcript | Out-Null
        }
        catch {
            # Le transcript ne doit jamais masquer l'erreur principale.
        }
    }
}

try {
    if ($WorkRoot -and (Test-Path -LiteralPath $WorkRoot)) {
        $SummaryPath = Join-Path $WorkRoot "VALIDATION_SUMMARY.txt"

        $Summary = $Results |
            Format-Table -AutoSize |
            Out-String

        @(
            "GF Wordbench — validation anglaise"
            "Date : $(Get-Date -Format o)"
            "Code global : $OverallCode"
            ""
            $Summary
        ) |
            Set-Content -LiteralPath $SummaryPath -Encoding UTF8

        Write-Host ""
        Write-Host $Summary

        if ($Archive) {
            Compress-Archive `
                -Path (Join-Path $WorkRoot "*") `
                -DestinationPath $Archive `
                -Force
        }
    }
}
catch {
    $OverallCode = 1
    Write-Host ""
    Write-Warning "Impossible de finaliser l'archive : $($_.Exception.Message)"
}

Write-Host ""
Write-Host "============================================================"
Write-Host "VALIDATION TERMINÉE"
Write-Host "============================================================"
Write-Host "Code global : $OverallCode"

if ($WorkRoot) {
    Write-Host "Rapport     : $WorkRoot"
}

if ($Archive -and (Test-Path -LiteralPath $Archive)) {
    Write-Host "Archive     : $Archive"
}

Write-Host ""

if ($OverallCode -eq 0) {
    Write-Host "Tous les contrôles requis ont réussi." -ForegroundColor Green
}
else {
    Write-Host (
        "Un ou plusieurs contrôles ont échoué. " +
        "Consulte les journaux avant de modifier ou fusionner le dépôt."
    ) -ForegroundColor Red
}

if (-not $NoPause) {
    [void] (Read-Host "Appuie sur Entrée pour fermer")
}

# Aucun appel à exit : la fenêtre reste ouverte jusqu'à la confirmation.
$global:LASTEXITCODE = $OverallCode
