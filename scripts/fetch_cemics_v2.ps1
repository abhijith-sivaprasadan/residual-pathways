# Fetch the public authors' AR6-aligned CEMICS v2 research archive.
# Keeps originals locally in data/ar6-private; checks publisher-listed MD5
# rather than trusting a filename or an interrupted download.
param(
    [string]$Directory = "data/ar6-private/cemics-v2"
)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Path $Directory -Force | Out-Null
$base = "https://zenodo.org/records/5103024/files/"
$files = @(
    @{Name="CDRoptionsAR6_complete.mif"; MD5="efbc4f82b0163da790f370775a37cfe7"},
    @{Name="CDRoptions.Rmd"; MD5="66923e9fbbeec5113849e2566d486c29"},
    @{Name="readme_zenodo.txt"; MD5="e0d133b76db3fd3ccb95f06279197ff0"},
    @{Name="regionmappingH12.csv"; MD5="9d59c73f814f6a0fcea89a3bbe591c0a"}
)
foreach ($entry in $files) {
    $destination = Join-Path $Directory $entry.Name
    $expected = $entry.MD5
    if (Test-Path $destination) {
        $hash = (Get-FileHash -LiteralPath $destination -Algorithm MD5).Hash.ToLowerInvariant()
        if ($hash -eq $expected) {
            Write-Host ("Already checked " + $entry.Name)
            continue
        }
        throw ("Existing file has incorrect MD5; do not overwrite without inspection: " + $destination)
    }
    $tmp = $destination + ".partial"
    if (Test-Path $tmp) { Remove-Item -LiteralPath $tmp -Force }
    $uri = $base + [uri]::EscapeDataString($entry.Name) + "?download=1"
    Write-Host ("Downloading original from Zenodo: " + $entry.Name)
    try {
        Invoke-WebRequest -Uri $uri -OutFile $tmp -MaximumRedirection 5
        $hash = (Get-FileHash -LiteralPath $tmp -Algorithm MD5).Hash.ToLowerInvariant()
        if ($hash -ne $expected) {
            throw ("Zenodo-listed MD5 mismatch for " + $entry.Name + " (got " + $hash + ")")
        }
        Move-Item -LiteralPath $tmp -Destination $destination
    } catch {
        if (Test-Path $tmp) { Remove-Item -LiteralPath $tmp -Force }
        throw
    }
}
Write-Host "All four source archives have the official Zenodo v2 MD5 checksums."
Write-Host ("Source archive location: " + (Resolve-Path $Directory).Path)
Write-Host "Do not commit these original files or AR6 observations to Git."
