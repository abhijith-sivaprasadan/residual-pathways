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

## Emissions-bound consistency: verified numerical saturation from saved ixmp

The upstream emissions-bound tutorial assigns `coal_ppl` an emission factor of **7.4 tCO2/kWa**, while defining a `bound_emission` of **500 MtCO2** for `GHG`, `all` technologies, and the `cumulative` year category. MESSAGEix's [EMISSION_CONSTRAINT formulation](https://docs.messageix.org/en/stable/model/MESSAGE/model_core.html) scales multi-period limits to an **average-annual** emission rate, weighted by each period's `duration_period`.

For the three listed periods **if their effective weights are equal, and if no other emissions or historical-emission terms apply**, the calculated average is:

```text
(47.37429150867584 + 76.82565352959837 + 78.50275766442846)
    * 7.4 / 3 = 500.000000 MtCO2 (average annual)
```

The exact numerical agreement is **strong evidence of a saturated emissions constraint**. The author's subsequent pasted diagnostic **does now include** saved `EMISS` and `bound_emission` records: emissions for Westeros are **350.5697571642012**, **568.5098361190279**, **580.9204067167708** in years 700, 710, 720, respectively. The saved cap is **500 MtCO2**. Their simple arithmetic average is **500.0000000000** within floating-point error. The same values also appear under `World` and must **not** be double-counted. The `EMISSION_CONSTRAINT` retrieval returned **EMPTY**, meaning no stored equation level/marginal was available. The later duration-weighted audit (reported below) resolved the necessary period lengths, mapping and scaling for numerical cap saturation. The actual constraint equation marginal remains unavailable, so a carbon shadow price remains **NOT_ESTABLISHED**.

**Do not describe the 500 figure as an unnormalized 30-year cumulative 500 MtCO2 budget.** Under the cited equation, the multi-year bound is normalized by the total duration.

## Scope and methodological cautions

- Baseline CO2 is **not a saved emissions output**: the baseline notebook contains no emission factor or `EMISS` accounting. One may construct an *explicitly labeled counterfactual estimate* by applying the same coal factor, but it must not be reported as baseline solver-measured emissions without a controlled emissions-enabled unbounded clone.
- The original two-tutorial economic difference initially confounded CO2 bookkeeping with its cap. The **subsequently solved three-case control** (reported below) isolates the cap by holding emissions accounting fixed in both constrained and unconstrained variants.
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

The controlled three-scenario comparison has since been solved locally (see below). Independent numerical reproduction and external review remain open.

## Follow-up diagnostic

The repository now implements `python -m residual_pathways westeros-cap-check --manifest PATH/TO/manifest.private.json --output results/westeros_cap_check`. It reads the original local ixmp scenario, verifies bound/category/period definitions, applies the exact duration-weighted average annual emissions equation and records a numerical saturation status. A missing or incompatible model-year mapping leaves the status `NOT_ESTABLISHED`; it cannot manufacture a shadow price. The author has since run this audit against the actual saved database; its observed outputs follow.

## Verified local duration-weighted cap reconciliation (2026-10-24 01:55 local)

The author supplied the actual `westeros-cap-check` terminal result and derived `cap_reconciliation.json`, not merely an equal-weight arithmetic assumption. **All eight mock tests passed**, and the analyzer connected to the same source HSQLDB scenario. The derived audit reports:

| Check | Saved-data result |
| --- | --- |
| Status | `NUMERICALLY_SATURATED` |
| Bound (MtCO2 average annual) | **500.0** |
| Reconstructed LHS (MtCO2 average annual) | **500.0** |
| Slack | **0.0** |
| Periods in `cumulative` | 700, 710, 720 |
| `duration_period` (source: `SAVED_SCENARIO_PARAMETER`) | 10, 10, 10 years |
| Emissions scaling | **1.0** (GAMS default where absent) |
| Tolerance | **0.0005** |
| Dual/shadow-price status | `NOT_ESTABLISHED` |

This upgrades the **numerical saturation** conclusion: it is no longer merely an equal-period hypothesis, because the saved model period durations were read and checked. It does **not** provide an observed `EMISSION_CONSTRAINT` dual, external replication, or carbon price. The cap checker did not rerun GAMS; the result is based on the author's locally persisted ixmp solution and provided transcript. An emissions-accounting/no-bound clone was subsequently solved successfully; its objective parity is described below.

## Actual third-scenario control solve (2026-10-24 02:24 local)

The author supplied terminal evidence of a successful additional **GAMS 54.6.0 / CPLEX LP** solve in a different, private ixmp HSQLDB. Five regression tests passed. The solver reported LP optimal, normal completion, and a high-precision objective of **159025.830480** (native units). The runner reported `ACTUAL_MESSAGEIX_GAMS_CONTROL_SOLVED`, with `baseline_vs_control.numerically_equivalent = true` and `cap_effect.difference_native = 32484.96875`. This solves the emissions-accounting-only case **without** the bound; no earlier solution was overwritten.

| Case | Emissions bookkeeping | 500 MtCO2 cap | Objective (persisted ixmp, native units) |
| --- | --- | --- | ---: |
| Baseline | No | No | 159025.828125 |
| Emissions-only control | Yes | No | ~159025.828125 (inferred from reported objective difference; confirm exact record below) |
| Emissions-constrained | Yes | Yes | 191510.796875 |

The difference **32484.96875**, or **about 20.4275%**, is specifically attributable to adding the emissions cap between the *two emissions-accounting-enabled* cases in this stylized fixed-input model, subject to the runner's source/control input-parameter parity checks and reported objective-equivalence gate. The exact saved control objective and technology rows should be independently inspected in the produced **private** `three_case_comparison.json` before attributing any particular change in dispatch/investment to the control. A shadow price remains unavailable.

The new control runner produced `results/westeros_control_private/20261024T002431Z_f8428b42/` locally; that folder contains a private HSQLDB and must **never** be committed. No raw GAMS transcript should be published because it contains licence and identity data. Both the solved scenario and research interpretation are educational, author-reported and not independently reproduced.

Next research priority: inspect the **three-case `ACT`, `CAP`, `CAP_NEW` columns** and derive sanitized evidence (including model and input-provenance pins) without adding private identifiers. Thereafter, vary the cap across several controlled levels to build a response curve and validate marginal-cost approximations with finite differences.
