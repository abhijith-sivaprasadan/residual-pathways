# Canonical AR6 metadata + four-year Atlas coverage handoff

The merged implementation prepares a candidate, coverage-only, non-I3 scientific release. The two required original-named World/metadata v1.1 files remain on the author's Windows computer, not in GitHub. File matching cannot authenticate the IIASA acquisition route.

Previously locally reported SHA-256:
- World CSV: 4cf39b6b0d968e25ed389318acb1674f92146f977e9db4bfb7970f048ff73977
- New metadata XLSX: fd1bc32db8463769e18f0560ced603a49598c12e1abfa06787ff763c55f06716
- Earlier third-party XLSX: 7d22453bdda52e95cea4df46d362018951dd7114e62f01f5bcea65d6e24a7790

## Commands to run in Windows PowerShell

From your current clone:

~~~powershell
cd 'E:\New folder (2)\MissionJob\residual-pathways'
git switch main
git pull --ff-only
& .\.venv-messageix\Scripts\python.exe -m pip install -e '.[metadata]'
& .\.venv-messageix\Scripts\python.exe -m pytest -q tests/test_metadata_concordance.py tests/test_coverage_release.py
~~~

If the older metadata file is missing, fetch this pinned public-redistribution version, verify its SHA-256 as above, and keep it in the ignored private folder:

~~~powershell
$old='data\ar6-private\earlier_thirdparty_metadata.xlsx'
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/witch-team/energy-jobs-dataset-iiasadb/23e446a3de0a6d59243a536740576ab386e56ccc/AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx' -OutFile $old
(Get-FileHash $old -Algorithm SHA256).Hash.ToLowerInvariant()
~~~

Generate normalized worksheet/cell and exact Model+Scenario difference counts, then the source-derived four-year reporting analysis:

~~~powershell
$world='data\ar6-private\AR6_Scenarios_Database_World_v1.1.csv'
$official='data\ar6-private\AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx'
$old='data\ar6-private\earlier_thirdparty_metadata.xlsx'
$comparison='results\ar6-canonical-gate\metadata_concordance_public.json'
$robustness='results\ar6-canonical-gate\robustness_canonical_4years.json'

& .\.venv-messageix\Scripts\python.exe -m residual_pathways.metadata_concordance --official $official --earlier $old --output $comparison
if ($LASTEXITCODE -ne 0) { throw 'Metadata comparison failed' }
& .\.venv-messageix\Scripts\python.exe -m residual_pathways cohort-robustness --input $world --metadata $official --metadata-sheet meta_Ch3vetted_withclimate --candidates config/ar6_variable_candidates.json --output $robustness
if ($LASTEXITCODE -ne 0) { throw 'Four-year coverage computation failed' }
& .\.venv-messageix\Scripts\python.exe -m residual_pathways.coverage_release --robustness $robustness --concordance $comparison --expected-world-sha256 4cf39b6b0d968e25ed389318acb1674f92146f977e9db4bfb7970f048ff73977 --expected-metadata-sha256 fd1bc32db8463769e18f0560ced603a49598c12e1abfa06787ff763c55f06716 --output atlas/data/coverage_release.json
if ($LASTEXITCODE -ne 0) { throw 'Coverage release gate failed' }
~~~

The last command creates two local outputs: atlas/data/coverage_release.json and atlas/data/coverage_release.json.sha256. The Atlas loads them only when both are present and their checksums agree.

## Remaining release gate

1. Inspect workbook differences across sheets and source-joined Model+Scenario records. Hash differences alone do not determine category concordance.
2. Verify direct publisher acquisition receipt privately, source fingerprints, 1,202 source-matched climate-vetted model/scenario pairs and exact count integrity.
3. Check permission and privacy constraints before committing aggregate public outputs. No original AR6 rows, individual scenario names, or private CEMICS values may be distributed.
4. Commit both outputs together, create an immutable release tag, then test an actual PathwaysHub hash-verified handoff and browser rendering.
5. Run the Atlas locally using: python -m http.server 8765 --directory atlas . Visit http://localhost:8765/#coverage .

Until the candidate release has been generated and reviewed, the Atlas continues to show its separate 2050 public snapshot and the four-year display remains unavailable. This is deliberate.

**Scientific status:** zero independently verified I3 cases; REVIEW_PENDING is not the same as insufficient data (I0). Presence counts cannot establish a physically exhaustive, nonoverlapping gross/CDR partition. Equal weighting by exact model names is **not** independent model-family weighting.
