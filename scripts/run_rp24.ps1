# PowerShell 7 / Windows: regenerate local private RP24 review packet.
# Nothing is uploaded. Original source values remain on this computer.
param(
    [string]$SourceCSV = "data/ar6-private/AR6-demo-data.csv",
    [string]$MetadataXlsx = "data/ar6-private/AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx"
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    if (-not (Test-Path $SourceCSV)) {
        throw "Source CSV not found. Obtain the publicly available teaching-release CSV in data/ar6-private."
    }
    if (-not (Test-Path $MetadataXlsx)) {
        throw "Metadata XLSX not found. Obtain the v1.1 metadata workbook in data/ar6-private."
    }
    $sourceExpected = "4cf39b6b0d968e25ed389318acb1674f92146f977e9db4bfb7970f048ff73977"
    $metaExpected = "7d22453bdda52e95cea4df46d362018951dd7114e62f01f5bcea65d6e24a7790"
    $sourceHash = (Get-FileHash -Algorithm SHA256 $SourceCSV).Hash.ToLowerInvariant()
    $metadataHash = (Get-FileHash -Algorithm SHA256 $MetadataXlsx).Hash.ToLowerInvariant()
    if ($sourceHash -ne $sourceExpected -or $metadataHash -ne $metaExpected) {
        throw "Hash mismatch: the requested analysis matches only the documented teaching CSV and redistributed workbook, not unverified inputs."
    }
    python -m pip install -e ".[metadata]"
    if ($LASTEXITCODE -ne 0) { throw "Python dependency installation failed" }
    $argsList = @(
        "-m", "residual_pathways", "case-audit",
        "--input", $SourceCSV,
        "--metadata", $MetadataXlsx,
        "--metadata-sheet", "meta_Ch3vetted_withclimate",
        "--candidates", "config/ar6_variable_candidates.json",
        "--public-output", "results/ar6-teaching-pilot/case_audit_24_public.json",
        "--private-output", "data/ar6-private/case_audit_review_packet.json",
        "--year", "2050"
    )
    & python @argsList
    if ($LASTEXITCODE -ne 0) { throw "RP24 selection failed" }
    $report = Get-Content "results/ar6-teaching-pilot/case_audit_24_public.json" -Raw | ConvertFrom-Json
    Write-Host "Cases selected: $($report.summary.case_count)"
    Write-Host "Complete six-variable cases: $($report.summary.six_complete_cases)"
    Write-Host "Three-term arithmetic diagnostic possible: $($report.summary.three_term_diagnostics_available)"
    Write-Host "Private packet: data/ar6-private/case_audit_review_packet.json"
    Write-Warning "Never commit or upload the private packet; it contains original source identifiers and values."
    Write-Warning "No model-specific scientific review or I3 conclusion has been performed."
}
finally {
    Pop-Location
}
