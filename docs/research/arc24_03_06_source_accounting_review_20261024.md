# Two-case scientific accounting review: ARC24-03 and ARC24-06

**Review date:** 24 October 2026. **Purpose:** separate (a) original variable/run data identity, (b) source-authored arithmetic conventions, and (c) independently established physical gross-emissions and atmospheric-removal partitions. These are **not equivalent tests**. Status for both cases remains **NOT_DETERMINED; verified I3 = 0**.

## A. ARC24-03 — REMIND–MAgPIE / CEMICS SSP1 minimum CDR

### Source/run numerical crosswalk: confirmed, within the tested scope

The author previously independently downloaded the [Strefler et al. Zenodo v2 archive](https://zenodo.org/records/5103024) and validated its publisher-listed MD5 for `CDRoptionsAR6_complete.mif` (`efbc4f82b0163da790f370775a37cfe7`). The author then ran the source-locked `arc24-cemics-alias-fingerprint` against the v1.1 World CSV.

| Pre-registered pairing | Exact original reported-decimal+unit matches | Different |
| --- | ---: | ---: |
| Original `CEMICS_SSP1-1p5C-fullCDR` → AR6 `CEMICS_SSP1-1p5C-fullCDR` | 4,653 / 4,653 | 0 |
| Original `CEMICS_SSP1-1p5C-noCDR` → AR6 `CEMICS_SSP1-1p5C-minCDR` | 4,653 / 4,653 | 0 |
| Original `fullCDR` → AR6 `minCDR` | 1,604 / 4,653 | 3,049 |
| Original `noCDR` → AR6 `fullCDR` | 1,604 / 4,653 | 3,049 |

The fingerprint is 517 *shared reported variable names* × 9 years, **not 4,653 statistically independent observations**. The authors' own MD5-pinned `CDRoptions.Rmd` calls the `noCDR` branch “min CDR” in multiple SSP1 plotting label vectors (reported source lines 555–558, 599–601). The source numerical fingerprint and original Rmd both support a **strong source-series mapping** from archived noCDR to AR6 minCDR. The Strefler et al. 2021 peer-reviewed [paper](https://doi.org/10.1088/1748-9326/ac0a11) reports study model **REMIND–MAgPIE 2.1.1–4.2.1**, consistent with, but more specific than, the coarse AR6 `REMIND-MAgPIE 2.1-4.2` name. A separately signed source-submission metadata record spelling out the precise rename, run binary, configuration and export pipeline remains unavailable. See [existing exact crosswalk](../arc24_cemics_v2_original_source_crosswalk.md) and [near-contemporary `reportEmi` source review](../arc24_03_2021_remind_reportEmi_source_audit.md).

### Author-defined accounting: identifiable, but not a physically verified exhaustive ledger

The authors' original Rmd lines 150–156 explicitly define these study-analysis measures:

~~~r
CO2tot <- data[,,"Emissions|CO2 (Mt CO2/yr)"]
CDRaff <- -data[,,"Emissions|CO2|Land|Land-use Change|Regrowth (Mt CO2/yr)"]
CDRew <- data[,,"Carbon Sequestration|Enhanced Weathering (Mt CO2/yr)"]
CDRbeccs <- data[,,"Carbon Sequestration|CCS|Biomass (Mt CO2/yr)"]
CDRdaccs <- data[,,"Carbon Sequestration|Direct Air Capture (Mt CO2/yr)"]
CDRtotal <- CDRaff + CDRew + CDRbeccs + CDRdaccs
CO2pos <- CO2tot + CDRtotal
~~~

This **verifies the exact research-analysis calculation** used by the study for `CDRtotal` and `CO2pos` and explicitly does **not** treat fossil CCS as one of its four operational CDR terms. However, `CO2pos` is calculated from net total + chosen CDR basket, so its apparent balance with those terms is **true by construction**. It is not independent proof that `CO2pos` is all-sector positive gross physical emissions or that the four basket terms are net, additional, durable and mutually exclusive. The original source `Emissions|CO2|Gross Fossil Fuels and Industry` is a **different narrower metric**; the local real-source sign/band assessment reports that the Rmd-derived positive-side `CO2pos` is >10% different on its own scale. This is a **different-system-boundary comparison**, not a model conservation violation.

The source Rmd's afforestation term is `-Emissions|CO2|Land|Land-use Change|Regrowth`, **not** `Carbon Sequestration|Land Use` and not `Carbon Sequestration|Land Use|Afforestation`. The author's original World audit found >10% source-series difference for the Regrowth-based author CDR versus both selected land-uptake series at nine tested years; replacing Regrowth by Land Use is demonstrably unsupported. Original model land/biomass netting, technology-specific capture-to-permanent-storage ratios, lifecycle emissions, physical completeness, source quantization, and independent I3 reviewer signoff remain open.

**Verdict ARC24-03:**
- Exact overlapping numerical series **CONFIRMED FOR 517 × 9 MATCHED SOURCE CELLS**.
- Study-defined operational four-category CDR accounting **SOURCE-DEFINED**, not physically verified.
- Exhaustive disjoint positive emission process inventory **NOT ESTABLISHED**.
- Exhaustive additional durable atmospheric-removal inventory **NOT ESTABLISHED**.
- Scientific I0/I1/I2/I3 **NOT_DETERMINED**; I3 confirmed **0**.

## B. ARC24-06 — POLES ENGAGE / EN_NPi2020_400f

### Separate version-specific source chain, not a single assumed dataset

The [ENGAGE Global Scenarios v2.0 record](https://doi.org/10.5281/zenodo.5553976) is an author-published **2021 separate dataset**. The [original IIASA analysis](https://github.com/iiasa/ENGAGE-netzero-analysis/tree/2d2be452dceed13b9671941fe5af7094a0e12956) (source commit `2d2be452dceed13b9671941fe5af7094a0e12956`, categorization notebook blob SHA `618bd2f3ef61d6076cdffdc9a2a2cd9497d19411`) explicitly consumes the source snapshot, and the preceding data-preparation notebook reads `ENGAGE_scenario_data_world_r2.0.csv` and R5 regional data. The snapshot and original v2.0 World data are **not committed** in that MIT-licensed notebook repository; its own [data README](https://github.com/iiasa/ENGAGE-netzero-analysis/blob/2d2be452dceed13b9671941fe5af7094a0e12956/data/README.md) directs researchers to the licensed ENGAGE Scenario Explorer.

[Cell 6 of the source categorization notebook](https://data.ece.iiasa.ac.at/engage-netzero-analysis/notebooks/1_categorization.html) **calculates** `Emissions|CO2|Other` as total CO₂ minus the four reported category streams `AFOLU`, `Energy|Demand`, `Energy|Supply` and `Industrial Processes`. Cell 7 separately computes `Energy|Demand|Other` as residual of demand minus Industry, Transportation and Residential & Commercial. This is **direct proof for that ENGAGE analysis processing pipeline**, not direct proof the IPCC AR6 v1.1 `POLES ENGAGE` `Other` field was generated by the exact same source routine.

In the user's **distinct AR6 v1.1 World release**, the prior original-source locked probes showed the four POLES scenarios' 20 case/year total-minus-EIP-minus-signed-AFOLU residuals were **nonzero**, but the `Other` series approximated them within 0.001% of the original source scale, and none equalled exactly at printed decimal precision. A detailed 20-case/year comparison of the ENGAGE notebook's explicit branches also found 20/20 nonzero residuals (all below 0.001% scale), while detailed Demand+Supply+Industrial Processes equalled separately reported EIP in only 1/20 years. **These are separate, correlated arithmetic comparisons, not independent physical validation.** There is no published original quantization convention permitting us to label the small discrepancies “rounding errors.”

**New auditable bridge:** `src/residual_pathways/arc24_engage_v2_probe.py` compares a locally downloaded, original-named ENGAGE v2.0 World CSV against the *already pinned* original AR6 v1.1 World and `ARC24-06` private packet. Exact `Model + Scenario + World + Variable + Unit + Year` records are compared using original Decimal strings, and the notebook's postprocessed Other is checked separately as a **derived formula**. It emits only coded comparison statuses, series names and source hashes, never original emissions quantities or scenario identity. If the exact case is absent from v2.0, it records `ENGAGE_V2_EXACT_MODEL_SCENARIO_NOT_FOUND`, not an alias or a false zero. **No actual ENGAGE v2.0 World source has been acquired or run through this new bridge yet.**

Run only after acquiring the licensed [ENGAGE v2.0 World dataset](https://data.ece.iiasa.ac.at/engage) and leaving it unchanged at `data/ar6-private/ENGAGE_scenario_data_world_r2.0.csv`:

~~~powershell
$py = '.\.venv-messageix\Scripts\python.exe'
& $py -m pytest -q tests/test_arc24_engage_v2_probe.py
& $py -m residual_pathways.arc24_engage_v2_probe
if ($LASTEXITCODE -ne 0) { throw 'ENGAGE source v2.0 crosswalk failed' }
$a = Get-Content results/ar6-canonical-gate/arc24_poles_engage_v2_probe_public.json -Raw | ConvertFrom-Json
$a.status
$a.source_reported_decimal_status_counts
$a.derived_notebook_other_status_counts
~~~

**Verdict ARC24-06:**
- ENGAGE analysis v2.0 `Other` is **known to be derived algebraically** in its published figure-processing notebook.
- Related AR6 POLES `Other` is **reported and numerically close to the named AR6 category gap**, not strictly equal in printed decimals.
- Exact input-source `ENGAGE v2.0 → IPCC AR6 v1.1` version/case mapping, export transformations and native source quantization **NOT ESTABLISHED**.
- No disjoint all-sector positive gross inventory or mutually exclusive net durable atmospheric removal accounting **ESTABLISHED**.
- Scientific I0/I1/I2/I3 **NOT_DETERMINED**; I3 confirmed **0**.

## C. What would actually close I3 science (both)

The essential evidence is a **case/version-specific physical process accounting map**, not more aggregate equality checks: explicitly identified independent positive emissions streams; signed AFOLU/net land baseline; biomass atmospheric uptake and storage/energy-lifecycle boundaries; fossil CCS avoided emissions excluded from CDR; durable DACCS and weathering accounted without nested overlap; completeness proof of all residual process streams; primary export precision (not just CSV trailing decimals); and external independent scientific review. [IAMC variable names are semi-hierarchical and may be nonadditive](https://docs.ece.iiasa.ac.at/standards/variables.html). A case may remain **REVIEW_PENDING** because evidence is missing; this must not be silently classified I0.

The next source-specific dependency for ARC24-03 is the dated original model reporting and `Emi`→`Emissions` export transformation used in the Strefler v2 MIF. For ARC24-06, the next decisive empirical comparison is ENGAGE v2.0 primary World case/variable concordance with AR6 v1.1, or a source-team original export declaration. Neither task requires inventing physical gross totals.

## D. Original ENGAGE v2.0 World file obtained: exact AR6 source case absent (user-run 24 October 2026)

The project author downloaded an original-named `ENGAGE_scenario_data_world_r2.0.csv` to ignored `data/ar6-private` (94,560,538 bytes; author-observed SHA-256 `c92b8944b1d2a71eed7a07702c42e48f6f3e3eee59a4404d145d0babc61315da`). This is a **local file fingerprint**, not an independently authenticated IIASA acquisition checksum.

Five synthetic probe tests passed. The actual `arc24_engage_v2_probe` run confirmed **508 original AR6 rows** for `POLES ENGAGE` / `EN_NPi2020_400f` but **zero ENGAGE v2.0 World rows under that exact Model+Scenario identity**. The earlier probe printed 55 `ENGAGE_V2_SOURCE_VARIABLE_ABSENT` checks (11 variables × 5 years) and five incomplete derived-`Other` years. **Correct interpretation: these are 55 unassessed comparison slots because the entire source pair was missing**, not proof that the 11 variables were physically or statistically absent in related ENGAGE scenarios. The probe now emits `unassessed_comparison_slots=55` and `unassessed_notebook_years=5`, with empty per-variable comparison arrays whenever the source pair is absent. No numeric source matching occurred.

The negative finding could mean a model label variant, changed scenario label, an AR6-only run, or a different ENGAGE release. No one of these is established. New `src/residual_pathways/arc24_engage_v2_identity_inventory.py` scans only `World` case names in the exact 94.56 MB author-held file, verifies its author-observed SHA and the previously selected private ARC24-06 packet, and reports **aggregate counts** for exact-model, exact-scenario, casefold, normalized-punctuation, POLES-family prefix and lexical candidates. Up to 12 candidate source identities are written **only** to ignored `data/ar6-private/engage_v2_candidate_identities_private.json`, without any numeric observations. Do **not** treat lexical similarities or matching prefixes as an author-approved alias or numerical origin.

~~~powershell
$py = '.\\.venv-messageix\\Scripts\\python.exe'
& $py -m pytest -q tests/test_arc24_engage_v2_probe.py tests/test_arc24_engage_v2_identity_inventory.py
if ($LASTEXITCODE -ne 0) { throw 'Identity inventory regression tests failed' }
& $py -m residual_pathways.arc24_engage_v2_identity_inventory
if ($LASTEXITCODE -ne 0) { throw 'ENGAGE source identity inventory failed' }
$identity = Get-Content 'results/ar6-canonical-gate/engage_v2_identity_inventory_public.json' -Raw | ConvertFrom-Json
$identity | Select-Object status,exact_model_label_found,exact_scenario_pairs_across_all_model_labels,distinct_world_model_scenario_pairs,poles_containing_model_label_count,poles_scenario_prefix_matches,poles_scenario_lexical_similarity_at_least_0_75,verified_i3 | Format-List
~~~

Only if the name inventory uncovers an interesting source identity should a separately registered, source-specific original-decimal comparison be designed, with positive/negative controls as for CEMICS. **No automatic aliases; no physical gross or durable CDR I3 promotion.**
