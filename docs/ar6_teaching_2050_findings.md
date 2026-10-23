# AR6 World teaching release: empirical reporting coverage and identifiability preflight

**23 October 2026 — research pilot, not peer-reviewed, not official full-v1.1 verification.**

## Research question and scope

What proportion of model/scenario pathways actually co-report common net CO2 and carbon-removal-related IAMC variables, and how does the coverage change after selecting climate-assessed and vetted scenarios?

A real 361.8 MB published **IIASA-labelled teaching subset** was processed by streamed Python, not a generated toy dataset. It is hosted as [AR6 World data, Zenodo 20056332](https://zenodo.org/records/20056332), which explicitly describes it as a teaching subset. It is NOT the authenticated, licence-gated official AR6 World v1.1 file until its content is compared with that official source. The metadata workbook was read from the independently redistributed witch-team GitHub file; its SHA-256 is recorded in the derived summary. Source provenance is therefore secondary and conditional.

**Reproduce:** [successful GitHub Actions workflow](https://github.com/abhijith-sivaprasadan/residual-pathways/actions/runs/39963627518), aggregate-only [artifact](https://github.com/abhijith-sivaprasadan/residual-pathways/actions/runs/39963627518/artifacts/12504929274), [machine-readable summary](../data/derived/ar6_teaching_2050_summary.json). The raw licensed dataset is not committed or redistributed.

## Data methods

Input: 693,299 CSV IAMC series; 2,298 unique World-region Model × Scenario pairs. For each exact IAMC variable string and year 2050, count whether the model-scenario has a **finite reported numerical value** (including zero); absent/blank values are missing, not zero. Units are collected and retained; no unreviewed conversion or variable synonym inference occurs.

The metadata book exposes a chapter-3 climate-vetted sheet (1,202 model-scenarios), an all-metadata sheet (2,304), and auxiliary sheets. The climate-vetted sheet matched all 1,202 scenarios to source. Of 2,304 general metadata scenarios, 2,298 matched source; six did not. The other 1,096 World source scenarios consist of 587 failed-vetting and 509 non-climate-assessed model-scenarios. These populations must never be pooled under a single "vetted" denominator.

### 2050 reporting availability across all 2,298 World source pairs

| Exact IAMC variable | Model-scenario pairs reporting | Source unit |
|---|---:|---|
| Emissions\|CO2 | 1,863 | Mt CO2/yr |
| Emissions\|CO2\|Energy | 1,291 | Mt CO2/yr |
| Emissions\|CO2\|AFOLU | 1,779 | Mt CO2/yr |
| Carbon Sequestration\|CCS\|Fossil | 1,444 | Mt CO2/yr |
| Carbon Sequestration\|CCS\|Biomass | 1,646 | Mt CO2/yr |
| Carbon Sequestration\|Direct Air Capture | 477 | Mt CO2/yr |
| Emissions\|CH4 | 1,786 | Mt CH4/yr |
| Emissions\|N2O | 1,789 | kt N2O/yr |

### Coverage in the 1,202 climate-vetted scenarios

All these vetted scenarios report aggregate Emissions|CO2 for 2050. Counts below are **not** CDR deployment or technology-use counts. A finite zero reports coverage, not activity.

| AR6 climate-assessment class | Models × scenarios | Have reported DAC variable | Co-report six selected CO2/CCS/DAC variables |
|---|---:|---:|---:|
| C1 | 97 | 38 | 27 |
| C2 | 133 | 32 | 17 |
| C3 | 311 | 127 | 96 |
| C4 | 159 | 57 | 51 |
| C5 | 212 | 87 | 73 |
| C6 | 97 | 42 | 34 |
| C7 | 164 | 32 | 26 |
| C8 | 29 | 7 | 6 |
| **Vetted total** | **1,202** | **422** | **330** |

In the vetted subset, DAC variable reporting is 422/1,202 = 35.1%. Joint reporting of all six candidate variables is 330/1,202 = 27.5%. These are **descriptive coverage ratios**, not estimates of technology contributions, abatement, or probability of success.

For comparison, the metadata sheet identifies 587 failed-vetting World pairs (539 report aggregate CO2, 44 report DAC, 32 co-report all six), and 509 with no climate assessment (122 report aggregate CO2, 11 report DAC, 0 co-report all six). Reporting density strongly depends on the scenario population selected. This finding matters whenever authors compare IAM cohorts with different vetting requirements.

## Identifiability assessment: why this is not a gross-emissions estimate

The six co-reported variable labels in the first pilot are aggregate Emissions|CO2; Emissions|CO2|Energy; Emissions|CO2|AFOLU; fossil CCS; biomass CCS; and Direct Air Capture. Their joint presence **is not sufficient** to reconstruct gross positive atmospheric emissions. In particular:
- An aggregate CO2 series and nested sectoral series are not disjoint addends.
- AFOLU CO2 is a **net** source/sink balance in published definitions, so negative net AFOLU must not be equated with physically complete gross land removals. A 2025 Earth System Science Data study distinguishes net AFOLU from the separately reported Carbon Sequestration|Land Use gross-removal proxy: [Prütz et al. (2025)](https://doi.org/10.5194/essd-17-221-2025).
- Fossil point-source CCS reduces fossil CO2 emitted to atmosphere but is not itself atmospheric removal. BECCS requires consistent system boundaries and permanence/supply-chain treatment; DAC variable presence does not identify storage durability or actual nonzero deployment.
- The first six-name pilot omits specific land-use sequestration and enhanced weathering variables. The extended source audit now includes these additional candidate names, but still does not establish an exhaustive CDR partition.
- Source precision, consistent partition/exhaustiveness, temporal harmonisation, source model conventions and residual numerical identity have not been independently reviewed.

**Verified I3 count: 0, because I3 has not been established or evaluated.** This is NOT an assertion that zero scenarios could qualify after full semantic audit. Do not map the 330 co-reporting scenarios to 330 gross-reconstructible cases.

## Extended land-use and industrial CO2 candidate audit

A second actual-data run added three previously absent exact-name candidates: Emissions|CO2|Energy and Industrial Processes, Carbon Sequestration|Land Use, and Carbon Sequestration|Enhanced Weathering. Their 2050 reporting counts across all 2,298 World source pairs are 1,811, 904, and 201, respectively. The teaching CSV SHA-256 is 4cf39b6b0d968e25ed389318acb1674f92146f977e9db4bfb7970f048ff73977.

Two stricter candidate intersections were measured within the 1,202 climate-vetted model-scenarios:

- Set A: EIP net CO2, AFOLU net CO2, Land Use sequestration, biomass CCS, and DAC all have reported values.
- Set B: the same five variables plus fossil point-source CCS also have reported values.

| Climate category | Vetted pairs | Set A reported | Set B reported |
|---|---:|---:|---:|
| C1 | 97 | 30 | 19 |
| C2 | 133 | 26 | 13 |
| C3 | 311 | 94 | 66 |
| C4 | 159 | 56 | 50 |
| C5 | 212 | 80 | 66 |
| C6 | 97 | 38 | 30 |
| C7 | 164 | 20 | 17 |
| C8 | 29 | 1 | 0 |
| **Total** | **1,202** | **345 (28.7%)** | **261 (21.7%)** |

These are co-reporting *presence* sets only. Neither set establishes an exhaustive nonoverlapping partition, a verified physical source boundary, or a unique inversion from sectoral net to positive gross emissions. Consequently neither 345 nor 261 is the number of I3-identifiable scenarios. A genuine I3 determination requires source-specific reviewed variables, scope, sign conventions, precision and explicit numerical/materiality reconciliation.

Reproducible source-derived evidence: [expanded CI run](https://github.com/abhijith-sivaprasadan/residual-pathways/actions/runs/39965219473) and the [aggregate JSON summary](../data/derived/ar6_teaching_2050_summary.json).

## Research implications

The key empirically substantiated result is a **reporting and sample-selection bottleneck**. The nominal 2,298-pair source pool collapses to 1,202 climate-vetted cases and then to 330 simultaneously reporting these six names. The remaining source semantics could reduce the usable cohort further. Reporting requirements must be predefined to avoid biased post-hoc comparisons between model families or warming categories.

The N2O source reports kt N2O/yr rather than Mt N2O/yr, while CH4 is Mt CH4/yr. A dedicated GWP unit test was added to convert kt to Mt *before* applying a documented assessment factor; no dataset-derived multigas CO2e trajectories have yet been computed.

## Next formal gates

1. Obtain the **canonical official** AR6 World v1.1 CSV and metadata XLSX via [IIASA Scenario Explorer](https://data.ece.iiasa.ac.at/ar6/#/downloads); document hashes, licence and any differences from teaching release/redistributed metadata.
2. Extend exact-name variable candidates to Energy and Industrial Processes net CO2; Land Use CDR, enhanced weathering, and any additional source-reviewed pathways; recompute both climate-vetted and unvetted coverage.
3. Build a variable-by-variable scope dictionary using official protocol + peer-reviewed methodological definitions (e.g. Prütz et al. 2025; [IPCC AR6 WGI/WGIII](https://www.ipcc.ch/report/ar6/)).
4. Independently audit 20–30 varied scenarios for additive scope, double-counting, sign convention and precision. Apply I0–I3 and dual materiality/rounding tests to verified partitions only.
5. Report sensitivity of coverage to year, vetted population, model family and source geography before substantive IAM interpretation. Complete MESSAGEix/GAMS controlled solve separately.

## Citations and rights

- [IIASA AR6 Scenario Explorer and Database](https://iiasa.ac.at/models-tools-data/ar6-scenario-explorer-and-database); [formal AR6 v1.1 record](https://zenodo.org/records/7197970).
- [IIASA-labelled AR6 World teaching release, May 2026](https://zenodo.org/records/20056332), whose scope is described as a teaching subset.
- [Prütz et al. (2025), ESSD 17, 221–231](https://doi.org/10.5194/essd-17-221-2025).
- [Grant et al. (2023), global fossil reduction pathways](https://www.nature.com/articles/s41467-023-41105-z), discusses missing CDR reporting and excluding scenarios with unreported methods.
- [GitHub workflow and derived aggregate artifact](https://github.com/abhijith-sivaprasadan/residual-pathways/actions/runs/39963627518).

This repository distributes only compact aggregate counts, reproducibility code and citations, not the original scenario ensemble or copied individual model submissions.
