# ARC24 POLES-specific aggregate discrepancy — research investigation

**Observation date:** 24 October 2026. **Status:** source-derived arithmetic pattern and model-family research hypothesis, **not** evidence of physically inconsistent emissions, a failed database vetting process, or a verified I1/I2/I3 accounting grade.

## 1. What the local data actually show

The author ran `arc24-arithmetic` against the source-native, climate-vetted 24-case v1.1 World packet. Thirteen synthetic tests passed and the local source run generated exactly the following results at 2050:

| Status | Cases |
|---|---:|
| Exact raw-decimal `Emissions|CO2 − Emissions|CO2|Energy and Industrial Processes − Emissions|CO2|AFOLU = 0` | **5** |
| Nonzero raw-decimal residual | **14** |
| Cannot calculate due to missing source observations | **5** |
| Incompatible units for required terms | **0** |

Within the 14 nonzero cases, the author computed the **descriptive absolute relative residual** as `100 × abs(total − EIP − AFOLU) / max(1, abs(total), abs(EIP), abs(AFOLU))`, where every measured source term is in Mt CO2/year. The relative-error denominator is NOT a scientific quantization tolerance.

| Band | Count | Case IDs |
|---|---:|---|
| Below 0.001% | 9 | ARC24-01, -02, -05, -08, -11, -13, -14, -15, -18 |
| 0.001% to below 0.1% | 1 | ARC24-20 |
| 0.1% to below 1% | 0 | none |
| 1% to below 10% | **4** | **ARC24-06, -09, -12, -21** |
| 10% or more | 0 | none |

Four large-band cases:

| Case | Class | Model | Scenario label | Residual sign | Relative discrepancy band |
|---|---|---|---|---|---|
| ARC24-06 | C2 | POLES ENGAGE | EN_NPi2020_400f | Negative | 1–10% |
| ARC24-09 | C3 | POLES ENGAGE | EN_INDCi2030_500f | Negative | 1–10% |
| ARC24-12 | C4 | POLES ENGAGE | EN_NPi2020_1200f | Positive | 1–10% |
| ARC24-21 | C7 | POLES ENGAGE | EN_NPi2100_COV | Positive | 1–10% |

All **four** 1–10% differences observed in this 24-case purposive selection are from the same `POLES ENGAGE` model label. Their signs are **mixed** (two positive, two negative). This is a strong *triage reason* to investigate POLES-specific reporting first, not a statistically representative or causal conclusion: the sample was selected for low/median/high variable coverage, not sampled randomly across model versions. We have not counted every POLES run in the entire 1,202-case cohort. A model-specific reporting-boundary explanation is a hypothesis, **not proven**.

Separately, the earlier read-only `arc24-sign-screen` on the same real local packet found **8/24 negative signed net AFOLU** and **11/24 missing land sequestration values**. The two groups should not be confused with independent gross CDR estimates; missing remains missing.

## 2. Sources: what they establish and what remains unproven

- [IIASA IAMC variable naming guidance](https://docs.ece.iiasa.ac.at/standards/variables.html): IAMC variable names are semi-hierarchical, but numerical additivity of prefixed variables is **not mandatory**. Thus a nonzero total-EIP-AFOLU difference cannot, without source specification, be called a reporting error.
- [European Commission JRC model description](https://joint-research-centre.ec.europa.eu/what-we-do/scientific-tools-and-databases/poles/model_en): POLES explicitly derives fossil fuel combustion CO2 from its energy balance while agriculture/LULUCF GHG series are linked through GLOBIOM/G4M tables. Relevant to tracing the boundary, but the page describes **POLES-JRC** and cannot certify the actual **POLES ENGAGE** AR6 file emission aggregation.
- [IAMC POLES emissions documentation](https://www.iamcdocumentation.eu/Emissions_-_POLES): model-family description confirms direct energy/industry emissions and soft GLOBIOM/G4M agriculture/land representation. Does **not** supply an exact arithmetic identity for these four ENGAGE scenarios.
- [IPCC AR6 WGIII Chapter 3](https://www.ipcc.ch/report/ar6/wg3/chapter/chapter-3/): notes that CO2 sectors shown in some figures need not sum to total CO2; this **figure-specific caveat is not proof** of this exact variable-name discrepancy.
- [Prütz, Fuss and Rogelj (2025), Earth System Science Data, DOI 10.5194/essd-17-221-2025](https://essd.copernicus.org/articles/17/221/2025/): directly documents that AFOLU is signed **net** CO2, Land Use sequestration a distinct gross removal series, and land-removal reporting is incomplete/inconsistent across the AR6 ensemble. Does not independently establish a POLES total-EIP-AFOLU identity.
- [ENGAGE scenario explorer](https://engage-climate.org/explorer-tools/scenario-explorer/): publishes project-specific scenario and documentation links, which should be used to locate exact version-specific emission conventions. Presence of a scenario in an explorer alone is not an accounting specification.

## 3. Competing hypotheses to try to falsify

**H1 — alternate reporting boundaries/definitions.** The global total CO2, EIP and/or signed AFOLU definitions in POLES ENGAGE do not correspond to a mandated exact partition (e.g., a source/model-specific additional accounting term). Look for the actual 2021/2022 submission mapping and non-energy emissions metadata; **do not create an extra sector residual series without documentation**.

**H2 — accounting postprocessing/coupling difference.** The POLES energy emissions and imported GLOBIOM/G4M land emissions might be aggregated/adjusted differently between the total and sector exports. Verify if the exact ENGAGE source requires this; model coupling alone does not establish that the adjustment occurred.

**H3 — reporting numerical formatting.** Tiny nonzero differences (<0.001%) in other models might result from CSV serialization/rounding. Original export precision must be verified. The 1–10% group should not be dismissed as ordinary display rounding without inspecting original term scales and source precision. No tolerance was imposed.

**H4 — scenario-dependent offsets.** Two POLES cases have negative residuals and two positive; therefore any hypothesized missing/adjusted term must be allowed to change sign or differ by scenario, rather than assuming one fixed positive source.

**H5 — sampling artefact.** Under low/median/high-by-six-variable selection, POLES could be overrepresented or only certain POLES pathways could be selected. Compare with the full matched pool of POLES ENGAGE scenarios, without implying independence across pathways.

## 4. Next analysis in order

1. **Research the reporting equation:** look for a primary ENGAGE POLES dataset schema or author-authored methodology that specifies the variable mapping of total CO2, Energy and Industrial Processes CO2, signed net AFOLU CO2, and other carbon terms. Do not claim source-specific closure until this is found.
2. **Four-case in-depth residual inspection (private):** inspect exact original residual and all three term scales for ARC24-06/09/12/21. Share publicly only rounded dimensionless ratios and direction, not original AR6 source observations. Never describe the ratio as an I3 tolerance.
3. **Temporal falsification:** check the same four exact Model×Scenario pairs over multiple available years (e.g. 2030, 2040, 2050, 2060, 2070). Persistent residual structure may support a model-convention hypothesis; a 2050-only anomaly may indicate a different explanation. Values remain local under upstream data-license terms.
4. **Non-POLES controls:** investigate one exact-closing REMIND case (ARC24-03) and one tiny-residual non-POLES case on the same years. Identify sample-level/model-level denominators before reporting group contrasts.
5. **Only after documented physical mappings**, evaluate whether a positive gross-emissions inventory and separate disjoint atmospheric removal inventory can be reconstructed and whether source quantization allows numerical reconciliation. Seek external signoff for I3. Do not double-subtract gross land sequestration from signed net AFOLU; fossil CCS is not atmospheric removal.

## Status of claim

**Evidence-supported:** four POLES ENGAGE cases have 2050 reported-decimal residual magnitudes between 1% and 10% of the largest term; two residuals positive and two negative. **Not evidence-supported:** that POLES reports an incorrect total, that four independent models disagree, that fossil CCS/land removals explain the residual, or that any one case meets I3.

**Scope:** the selected 24 cases only. Not an estimate for all 1,202 vetted scenarios, and not independently externally reproduced.

## 5. Prepared five-year POLES temporal falsification (new code, not yet run locally)

The repository now contains a focused arc24-poles-timeline CLI and synthetic tests (not yet run on the author's machine). It reads the **original** World v1.1 CSV and the protected ARC24 packet, checks the CSV's SHA-256 matches the packet, verifies that the selected 2050 source observations match previous saved values, then examines the four known POLES cases in the years **2030, 2040, 2050, 2060 and 2070**. It reports unavailable year columns and missing observations explicitly, instead of silently treating them as zeros.

Public output contains only coded ARC24 case IDs, year, category, signed relative percentage bands and missing/absent-year statuses. It does not include model names, scenario names, original source values or absolute residual amounts. This is a descriptive source-arithmetic falsification check, not model validation, original source numerical precision or an I3 accounting certification.

Windows PowerShell:

    git pull --ff-only
    & .\.venv-messageix\Scripts\python.exe -m pytest -q tests/test_arc24_poles_timeline.py
    & .\.venv-messageix\Scripts\python.exe -m residual_pathways arc24-poles-timeline
    $t = Get-Content 'results/ar6-canonical-gate/arc24_poles_timeline_public.json' -Raw | ConvertFrom-Json
    $t.status
    $t.observations | Sort-Object case_id,year | Select-Object case_id,category,year,arithmetic_status,signed_residual_band | Format-Table -AutoSize

Expected public output: results/ar6-canonical-gate/arc24_poles_timeline_public.json. **The tool has been committed but has not yet been executed on the user's local source.** If the POLES discrepancy persists across the years, that supports a model-family convention *hypothesis*, not proof. If it appears only at 2050, the 2050-specific scenario/model-reporting hypothesis deserves attention instead.

## 6. Source-verified POLES timelines (author's local execution, 24 October 2026)

The user ran arc24-poles-timeline against the local World v1.1 and private ARC24 packets after five out of five synthetic tests passed. The source-lock, 2050 cross-check and all 20 case-year observations succeeded. **All 20 of 20 observed year/case residuals were nonzero at the reported decimal resolution.**

| Case / climate class | 2030 | 2040 | 2050 | 2060 | 2070 |
| --- | --- | --- | --- | --- | --- |
| ARC24-06 / C2 | +1–10% | +1–10% | −1–10% | −≥10% | −≥10% |
| ARC24-09 / C3 | +1–10% | +1–10% | −1–10% | −≥10% | −≥10% |
| ARC24-12 / C4 | +1–10% | +1–10% | +1–10% | +1–10% | −≥10% |
| ARC24-21 / C7 | +1–10% | +1–10% | +1–10% | +1–10% | +1–10% |

Signs follow source total minus EIP minus net AFOLU. Percent is absolute residual divided by maximum of 1, absolute total, absolute EIP, and absolute AFOLU, with all terms in Mt CO2/year. A band of 1–10% includes 1% and excludes 10%. Five observations are ≥10%. Three scenarios change sign within the observed grid; none of the 20 residuals is exactly zero. The exact cross-over year is not established. No confidential numerical emissions or absolute residuals are published.

These findings falsify a 2050-specific discrepancy for the four selected scenarios. They also disfavor a fixed-sign omitted source explanation. They **do not** identify a physical accounting error or a particular missing emission component; model export conventions and time-dependent land/process representations remain unverified.

### Newly located AR6 WGIII climate assessment processing control

The [AR6 climate-assessment workflow](https://climate-assessment.readthedocs.io/en/latest/general.html), linked to Kikstra et al. 2022 ([GMD paper](https://doi.org/10.5194/gmd-15-9075-2022)), specifically describes optional reported CO2 sectors Other, Waste, Other Capture and Removal, and Product Use. Under an alternate input route its reclassification step folds these additional variables into EIP, under stated nonoverlap assumptions. The software also documents a hierarchy check. This is **processing methodology**, not a proven equation for the original POLES ENGAGE outputs in the World CSV, and later online documentation may differ from the exact AR6 2022 processing version.

The first discriminating empirical check is therefore whether the four scenarios actually report those four optional CO2 variables, with compatible units, in the original data for 2030/2040/2050/2060/2070. Do not automatically add them to EIP: some may already overlap, may be missing, or may not be part of the intended global aggregate. Positive land sequestration and fossil CCS are **not** equivalent missing positive emissions.

**Review gate unchanged:** no I3 grade or independently validated source carbon closure for these four or any other selected case.
## 7. Prepared, not yet locally executed: optional-CO2 sector presence probe

The AR6 climate assessment documentation suggests an explicit falsification: some CO2 reporting inputs can contain additional categories named exactly **Emissions|CO2|Other**, **Emissions|CO2|Waste**, **Emissions|CO2|Other Capture and Removal** and **Emissions|CO2|Product Use**, which its alternate workflow may reclassify into the EIP category under a nonoverlap assumption. This is a documented *workflow* convention and **is not proof** that POLES ENGAGE submitted or requires these four terms.

A new local CLI, arc24-poles-optional-co2, scans the original v1.1 World CSV after verifying its SHA-256 against the already-saved private ARC24 packet. It examines only four known POLES scenarios across 2030, 2040, 2050, 2060 and 2070. It releases only coded case/year/variable **presence, positive/negative/zero, missing-year and incompatible-unit** statuses; no raw emissions quantities or per-scenario names. It never sums any optional variables, assumes that missing means zero or concludes any official reconciliation.

Run on the author's Windows PowerShell:

    git pull --ff-only
    & .\.venv-messageix\Scripts\python.exe -m pytest -q tests/test_arc24_poles_optional_co2.py
    & .\.venv-messageix\Scripts\python.exe -m residual_pathways arc24-poles-optional-co2
    $v = Get-Content 'results/ar6-canonical-gate/arc24_poles_optional_co2_public.json' -Raw | ConvertFrom-Json
    $v.status
    $v.status_by_optional_variable

**No actual four-case result has yet been observed for this new utility.** If these terms are not reported, the directly reported optional-sector hypothesis cannot explain the discrepancy without further source-specific documentation. If present, their overlap, inclusion in EIP, and original model units still require source verification before arithmetic corrections.

Reference: [AR6 WGIII climate assessment workflow](https://climate-assessment.readthedocs.io/en/latest/general.html), [associated 2022 methodology](https://doi.org/10.5194/gmd-15-9075-2022).