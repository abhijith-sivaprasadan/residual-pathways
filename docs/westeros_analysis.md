# Analyze saved Westeros solutions without rerunning GAMS

The \`westeros-analyze\` command reads the original private ixmp/HSQLDB saved scenario versions. It creates derived CSV, JSON, SVG charts and a SHA-256 file inventory without changing or re-solving scenarios.

## Windows execution

From your existing Windows checkout, run:

\`\`\`powershell
cd 'E:\New folder (2)\MissionJob\residual-pathways'
git pull --ff-only

$env:IXMP_GAMS_PATH = 'C:\GAMS\54'
$env:Path = "C:\GAMS\54\apifiles\Java\api;C:\GAMS\54;$env:Path"

& .\.venv-messageix\Scripts\python.exe -m residual_pathways westeros-analyze --manifest 'results/messageix_private/20261023T230104Z_e182e730/manifest.private.json' --output 'results/westeros_analysis'
\`\`\`

Check the resulting \`results/westeros_analysis/report.md\`, \`summary.json\`, \`technology_comparison.csv\` and three SVG charts (\`act_comparison.svg\`, \`cap_comparison.svg\`, \`cap_new_comparison.svg\`). The \`analysis_manifest.json\` records SHA-256 digests of these exact derived output files. Everything stays in \`results/\` (gitignored).

## Definitions

The official v3.11.1 [baseline Westeros tutorial](https://github.com/iiasa/message_ix/blob/2d521407a430a08de997a771e7b38d88f7e7d2b6/tutorial/westeros/westeros_baseline.ipynb) has technologies \`coal_ppl\`, \`wind_ppl\`, \`grid\` and \`bulb\` in model years 700, 710 and 720. The [emissions-bound tutorial](https://github.com/iiasa/message_ix/blob/2d521407a430a08de997a771e7b38d88f7e7d2b6/tutorial/westeros/westeros_emissions_bounds.ipynb) clones the baseline, adds CO2 emission accounting for coal and a multi-period emissions bound.

- \`ACT\`: sum directly observed model activity across vintages/modes for the single annual time slice; no subannual sum without duration weights.
- \`CAP\`: sum directly observed installed capacities across vintages by technology/active year.
- \`CAP_NEW\`: annually averaged new-capacity decisions by technology/investment year. It is **not** a cumulative investment total.
- The output preserves recorded native model units and never silently replaces a missing technology-year entry with zero. A numeric delta is shown only when both scenarios contain saved values.

**Important emissions boundary:** The baseline tutorial does not model CO2 emission factors, so the saved baseline solution does *not* provide a modelled emissions quantity directly comparable with \`EMISS\` in the bounded scenario. The analyzer includes raw \`EMISS\`, \`bound_emission\` and \`EMISSION_CONSTRAINT\` records (if available) without summing overlapping technology categories. Both binding status and shadow price remain \`NOT_ESTABLISHED\` until validated independently.

The core [MESSAGEix emission-bound equation](https://docs.messageix.org/en/v3.11.1/model/MESSAGE/model_core.html) normalizes multi-period emissions by summed period durations. The source's \`type_year=cumulative\` label alone is not proof of an unnormalized multi-decade cumulative 500 MtCO2 total.

The analysis checks the saved ixmp objective against the verified private manifest and reads **specific stored scenario versions**, not whichever version happens to be the database default. It cannot authenticate a GAMS licence, certify a scientific result or independently reproduce the solve. Raw solver logs, GDX, HSQLDB and executed notebooks must stay private.

## Local tests

\`\`\`powershell
& .\.venv-messageix\Scripts\python.exe -m pytest -q tests/test_westeros_analysis.py
\`\`\`

These are **synthetic mock-backed tests**, not independent solver executions. A real technology-shift interpretation should be written only after the user's local database read succeeds and the resulting rows have been inspected.
