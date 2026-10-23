# Westeros research note 04 — technology substitution under an emissions bound

**Evidence:** author-provided terminal transcript of a real local read of the saved ixmp database, dated 2026-10-24. The analysis program reported `LOCAL_STORED_IXMP_ANALYSIS`, 36 paired technology-year records across `ACT`, `CAP`, and `CAP_NEW`, and six hashed local outputs. Nine analyzer unit tests passed. **The derived outputs and their hash manifest have not been independently re-read or published here.**

**Source model:** official educational MESSAGEix 3.11.1 Westeros baseline and [emissions-bound notebooks](https://github.com/iiasa/message_ix/tree/2d521407a430a08de997a771e7b38d88f7e7d2b6/tutorial/westeros), upstream commit `2d521407a430a08de997a771e7b38d88f7e7d2b6`. The figures below are **fictional model-year and technology values, not real-world national energy projections**.

## What the solved model shows

The emissions-bound case has a persisted objective of **191510.796875** versus **159025.828125** in the baseline (native objective units). The difference is **32484.96875**, or **20.42748%**. Saved ixmp values have slightly less precision than those printed in the GAMS/CPLEX terminal log.

| Year | Baseline coal ACT | Bound coal ACT | Baseline wind ACT | Bound wind ACT | Bound wind generation share |
| --- | ---: | ---: | ---: | ---: | ---: |
| 700 | 47.374292 | 47.374292 | 13.736820 | 13.736820 | 22.478% |
| 710 | 89.550852 | 76.825654 | 1.560259 | 14.285458 | 15.679% |
| 720 | 115.555556 | 78.502758 | 0.000000 | 37.052798 | 32.065% |

`ACT` is the annual activity in the tutorial's GWa energy-production scale, summed over saved vintages for each technology and model year; this is not installed capacity.

**Paired change:** in 710, coal ACT decreases **12.725198 GWa** and wind ACT increases **12.725198 GWa**. In 720, coal ACT decreases **37.052798 GWa** and wind ACT increases **37.052798 GWa**. The differences cancel within numerical precision.

The electricity balance is consistent with the tutorial's 90% grid efficiency:

| Year | Coal + wind supply, either scenario (GWa) | Grid and bulb useful activity (GWa) |
| --- | ---: | ---: |
| 700 | 61.111111 | 55 |
| 710 | 91.111111 | 82 |
| 720 | 115.555556 | 104 |

Thus the observed change is a **technology-mix substitution at fixed delivered services**, not demand destruction. The unchanged grid and bulb activity directly supports this interpretation.

## Capacity and investment indicators

| Year | Change coal CAP | Change wind CAP | Change coal CAP_NEW | Change wind CAP_NEW |
| --- | ---: | ---: | ---: | ---: |
| 700 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 710 | -12.725198 | +35.347773 | -1.272520 | +3.534777 |
| 720 | -37.052798 | +102.924439 | -2.432760 | +6.757667 |

`CAP` is installed capacity at an active model year. `CAP_NEW` is a **yearly average new-capacity decision over the model period**, not a simple cumulative investment. The large additional wind CAP relative to its ACT is consistent with its tutorial capacity factor (0.36 versus 1.0 for coal); this does not by itself attribute the full increase in system costs.

## Emissions-bound consistency: suggestive, not yet fully audited

The upstream emissions-bound tutorial assigns `coal_ppl` an emission factor of **7.4 tCO2/kWa**, while defining a `bound_emission` of **500 MtCO2** for `GHG`, `all` technologies, and the `cumulative` year category. MESSAGEix's [EMISSION_CONSTRAINT formulation](https://docs.messageix.org/en/stable/model/MESSAGE/model_core.html) scales multi-period limits to an **average-annual** emission rate, weighted by each period's `duration_period`.

For the three listed periods **if their effective weights are equal, and if no other emissions or historical-emission terms apply**, the calculated average is:

```text
(47.37429150867584 + 76.82565352959837 + 78.50275766442846)
    * 7.4 / 3 = 500.000000 MtCO2 (average annual)
```

The exact numerical agreement is **strong evidence of a saturated emissions constraint**. The author's subsequent pasted diagnostic **does now include** saved `EMISS` and `bound_emission` records: emissions for Westeros are **350.5697571642012**, **568.5098361190279**, **580.9204067167708** in years 700, 710, 720, respectively. The saved cap is **500 MtCO2**. Their simple arithmetic average is **500.0000000000** within floating-point error. The same values also appear under `World` and must **not** be double-counted. The `EMISSION_CONSTRAINT` retrieval returned **EMPTY**, meaning no stored equation level/marginal was available. The transcript still does not establish saved `duration_period`, `cat_year`, `emission_scaling`, or `historical_emission` inputs. A full binding test should inspect these and the correct time-type mappings; without this, a formal constraint or shadow-price statement remains **NOT_ESTABLISHED**.

**Do not describe the 500 figure as an unnormalized 30-year cumulative 500 MtCO2 budget.** Under the cited equation, the multi-year bound is normalized by the total duration.

## Scope and methodological cautions

- Baseline CO2 is **not a saved emissions output**: the baseline notebook contains no emission factor or `EMISS` accounting. One may construct an *explicitly labeled counterfactual estimate* by applying the same coal factor, but it must not be reported as baseline solver-measured emissions without a controlled emissions-enabled unbounded clone.
- The economic difference compares two official tutorials, one adding CO2 emissions accounting **and** its cap. A three-scenario experiment (baseline; emissions-enabled but unbounded; emissions-enabled and bounded) would better isolate the causal effect of the cap.
- No numerical carbon shadow price is interpreted here. Shadow prices require validated equation-index selection, unit and time normalization, and LP dual checks.
- Numerical zero such as -3.55e-15 is treated as floating-point noise, not a physical wind decrease.
- All observations come from the author's reported local educational run, without independent licensed-GAMS execution or scientific peer review. Nothing here measures real AR6 emissions, gross-versus-net accounting, fossil CCS or CDR.

## Next verification

Read the exact local saved emissions records and period metadata before strengthening the binding claim:

```powershell
cd 'E:\New folder (2)\MissionJob\residual-pathways'
$s = Get-Content 'results/westeros_analysis/summary.json' -Raw | ConvertFrom-Json
$s.emissions_bound | ConvertTo-Json -Depth 16
```

A genuine controlled three-scenario emissions sensitivity and an independent numerical reproduction remain the next higher scientific-evidence steps.

## Follow-up diagnostic

The repository now implements `python -m residual_pathways westeros-cap-check --manifest PATH/TO/manifest.private.json --output results/westeros_cap_check`. It reads the original local ixmp scenario, verifies bound/category/period definitions, applies the exact duration-weighted average annual emissions equation and records a numerical saturation status. A missing or incompatible model-year mapping leaves the status `NOT_ESTABLISHED`; it cannot manufacture a shadow price. The audit has not been executed against the author's saved database yet, only developed with mock fixtures.
