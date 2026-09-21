# Build standalone Windows distribution for Local AI.
$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

Write-Host "Using Python: $Python"
Write-Host "Installing packaging extras..."
& $Python -m pip install -e ".[packaging]"

Write-Host "Running PyInstaller..."
$Spec = Join-Path $PSScriptRoot "local_ai.spec"
& $Python -m PyInstaller --noconfirm --clean --distpath (Join-Path $PSScriptRoot "dist") --workpath (Join-Path $PSScriptRoot "build") $Spec

$Exe = Join-Path $PSScriptRoot "dist\LocalAI\LocalAI.exe"
Write-Host "Done. Output: $Exe"
