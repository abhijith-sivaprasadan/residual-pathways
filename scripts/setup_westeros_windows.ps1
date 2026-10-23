# Run from the residual-pathways clone. Does not request/copy GAMS license.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    if (-not (Get-Command gams -ErrorAction SilentlyContinue)) {
        throw "GAMS is not on PATH. Install/activate GAMS via the official installer and reopen PowerShell."
    }
    if (-not (Get-Command java -ErrorAction SilentlyContinue)) {
        throw "Java runtime not on PATH. Install Java or use the MESSAGEix conda instructions."
    }
    if (-not (Test-Path ".venv-messageix/Scripts/python.exe")) {
        py -3.11 -m venv .venv-messageix
        if ($LASTEXITCODE -ne 0) { throw "Python 3.11 environment creation failed" }
    }
    $python = Join-Path $root ".venv-messageix/Scripts/python.exe"
    & $python -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed" }
    & $python -m pip install -e . -r requirements-messageix.txt
    if ($LASTEXITCODE -ne 0) { throw "Package installation failed" }
    & $python -m residual_pathways.messageix_westeros --preflight
    if ($LASTEXITCODE -ne 0) { throw "Preflight failed" }
    Write-Host "Now run from repo root:"
    Write-Host '  & .\.venv-messageix\Scripts\python.exe -m residual_pathways.messageix_westeros'
    Write-Warning "Keep all GAMS license files and access codes outside the Git repository."
}
finally {
    Pop-Location
}
