param(
  [Parameter(Mandatory=$true)][string]$RepositoryRoot
)
$ErrorActionPreference = "Stop"
$source = Split-Path -Parent $PSScriptRoot
$backup = Join-Path $RepositoryRoot ("documentation_backup_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Path $backup | Out-Null

$replaceDirs = @("docs", "project/docs", "templates/project/docs")
foreach ($rel in $replaceDirs) {
  $target = Join-Path $RepositoryRoot $rel
  if (Test-Path $target) {
    $backupTarget = Join-Path $backup $rel
    New-Item -ItemType Directory -Path (Split-Path -Parent $backupTarget) -Force | Out-Null
    Move-Item $target $backupTarget
  }
}

foreach ($rel in @("README.md", "CONTRIBUTING.md", "SECURITY.md")) {
  $target = Join-Path $RepositoryRoot $rel
  if (Test-Path $target) { Move-Item $target (Join-Path $backup $rel) }
}

Copy-Item (Join-Path $source "docs") (Join-Path $RepositoryRoot "docs") -Recurse
Copy-Item (Join-Path $source "project/docs") (Join-Path $RepositoryRoot "project/docs") -Recurse
Copy-Item (Join-Path $source "templates/project/docs") (Join-Path $RepositoryRoot "templates/project/docs") -Recurse
foreach ($rel in @("README.md", "CONTRIBUTING.md", "SECURITY.md")) {
  Copy-Item (Join-Path $source $rel) (Join-Path $RepositoryRoot $rel)
}
Write-Host "Documentation replaced. Backup: $backup"
