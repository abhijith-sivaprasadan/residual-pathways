# Westeros emissions cap numerical audit — read-only

This diagnostic follows the actual saved ixmp emissions-bound model output. The author reported model-year CO2 records of **350.5697571642012**, **568.5098361190279**, and **580.9204067167708** (Westeros node), plus an emissions bound of **500 MtCO2**. Their arithmetic mean is essentially 500; the model's real cap equation is **duration-weighted**, so the complete check must use saved periods and category mappings.

## Execute on the existing Windows installation

```powershell
cd 'E:\New folder (2)\MissionJob\residual-pathways'
git pull --ff-only
$env:IXMP_GAMS_PATH = 'C:\GAMS\54'
$env:Path = "C:\GAMS\54\apifiles\Java\api;C:\GAMS\54;$env:Path"

& .\.venv-messageix\Scripts\python.exe -m pytest -q tests/test_westeros_cap_audit.py

& .\.venv-messageix\Scripts\python.exe -m residual_pathways westeros-cap-check `
  --manifest 'results/messageix_private/20261023T230104Z_e182e730/manifest.private.json' `
  --output 'results/westeros_cap_check'

Get-Content 'results/westeros_cap_check/cap_reconciliation.json'
```

The command reads only the **persisted emissions-bound scenario, version 1** from the private ixmp database. It does not call GAMS or change scenario parameters. It selects only `Westeros` / `CO2` / `all`, never adds `World` and `Westeros` emissions, and verifies `cat_emission`, `cat_year`, and the 500 bound. It takes `duration_period` from the source scenario if present. For the pinned four-element [690, 700, 710, 720] `year` set, it can reconstruct the three 10-year model-period durations if none was stored, marking this derivation. It reads explicit `emission_scaling` and `historical_emission` where available; when scaling is absent the pinned [GAMS data_load code](https://github.com/iiasa/message_ix/blob/2d521407a430a08de997a771e7b38d88f7e7d2b6/message_ix/model/MESSAGE/data_load.gms) defaults it to 1, and missing historical-emission rows imply zero.

Possible statuses are `NUMERICALLY_SATURATED`, `WITHIN_BOUND_WITH_SLACK`, `APPARENT_BOUND_VIOLATION`, or `NOT_ESTABLISHED`. **A numeric saturation check is not independent GAMS execution, an equation dual, a calibrated shadow price, an AR6 result or a real national emissions quantity.** The `EMISSION_CONSTRAINT` equation records previously returned EMPTY, so the audit explicitly retains `shadow_price_status: NOT_ESTABLISHED`.

The command writes derived-only `cap_reconciliation.json` and its file hash `cap_reconciliation.sha256` to the gitignored `results/` folder. The full private manifest, source database, GAMS licence information, and original executed notebooks must not be published.

Scientific reference: [MESSAGEix 3.11.1 EMISSION_CONSTRAINT](https://docs.messageix.org/en/stable/model/MESSAGE/model_core.html): `sum(duration_period * emission_scaling * (EMISS + historical_emission)) / sum(duration_period) <= bound_emission`.
