# Build standalone Windows distribution for Local AI.
$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $Root

Write-Host "Installing packaging extras..."
python -m pip install -e ".[packaging]"

Write-Host "Running PyInstaller..."
$Spec = Join-Path $PSScriptRoot "local_ai.spec"
python -m PyInstaller --noconfirm --clean --distpath (Join-Path $PSScriptRoot "dist") --workpath (Join-Path $PSScriptRoot "build") $Spec

Write-Host "Done. Output: packaging/windows/dist/LocalAI/"
