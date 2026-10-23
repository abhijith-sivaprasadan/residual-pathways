# Research Note 03 — Multi-year reporting robustness and N2O GWP convention sensitivity

**23 October 2026. Exploratory source-data study; neither canonical AR6 World v1.1 validation nor peer review.**

## Scientific question and source provenance

The public IIASA-labelled AR6 World *teaching release* was streamed again in GitHub Actions and matched by exact Model×Scenario to a third-party republished metadata workbook. Its content SHA-256 is 4cf39b6b0d968e25ed389318acb1674f92146f977e9db4bfb7970f048ff73977; metadata SHA-256 is 7d22453bdda52e95cea4df46d362018951dd7114e62f01f5bcea65d6e24a7790. The official restricted v1.1 exports have not been acquired or authenticated. The methods preserve zero versus missing and produce no original scenario values.

## First result: scenario reporting robustness

The four-year source audit emits **352 records**, one per climate category C1–C8 × year 2030/2050/2070/2100 × 11 precisely named IAMC variables. Each record contains the count of source-matched vetted Model×Scenario pairs, exact Model-label count, reporting count, scenario-weighted reporting fraction and mean within-exact-model-label reporting fraction.

The second weighting is a *label-based diagnostic only*. Distinct model labels may derive from the same scientific model family, so the measure is not an independent model-family ensemble, probabilistic climate forecast or model uncertainty interval. The full machine-readable data are in the [source-data CI artifacts](https://github.com/abhijith-sivaprasadan/residual-pathways/actions/runs/39973567325). All 2050 counts are independently checked against the previously pinned published category-level source audit. No interpolation, causal technology comparisons or population-emissions estimates are computed.

## Second result: N2O GWP100 assessment-version difference

The teaching source reports N2O in **kt N2O/year**, not CO2e or Mt N2O/year. Its gas-specific reporting coverage is 1,202/1,202 climate-vetted scenarios in 2050. For each category, mean N2O mass *among reporting scenarios* is divided by 1,000 to obtain Mt N2O/year, and evaluated using two published IPCC AR6 WGI Chapter 7 GWP100 reference factors on exactly the **same emissions values**: original 2021 factor 273 and corrected October 2025 value 267. Results from the actual-source CI run:

| Category | Reporting scenarios | Mean N2O MtCO2e/year, 2021 | Mean N2O MtCO2e/year, corrected 2025 | Difference MtCO2e/year |
|---|---:|---:|---:|---:|
| C1 | 97 | 2390.0 | 2337.5 | -52.5 |
| C2 | 133 | 2318.7 | 2267.7 | -51.0 |
| C3 | 311 | 2415.4 | 2362.3 | -53.1 |
| C4 | 159 | 2417.5 | 2364.4 | -53.1 |
| C5 | 212 | 2660.7 | 2602.2 | -58.5 |
| C6 | 97 | 2906.5 | 2842.6 | -63.9 |
| C7 | 164 | 3464.0 | 3387.9 | -76.1 |
| C8 | 29 | 3876.2 | 3791.0 | -85.2 |

The corrected metric changes the calculated N2O CO2e number by **−2.20%** for any fixed N2O mass, strictly because 267/273−1 ≈ −0.02198. This is a methodological metric change, **not a physical emissions reduction**, nor evidence of any mitigation policy effect. The category means are not a sum across scenarios: each scenario describes a different pathway. Scenario ensembles are not independently sampled future worlds.

Methane CO2e calculations remain blocked because this source-level variable does not establish a separate fossil versus non-fossil CH4 split for the selected reporting cohort. An already aggregated Kyoto Gases series is not blindly re-converted from CO2e. A complete multi-gas CO2e trajectory has therefore **not** been produced, and its reported source convention requires review.

Source references: [IPCC WGI Chapter 7](https://www.ipcc.ch/report/ar6/wg1/chapter/chapter-7/); [official 7 October 2025 errata](https://www.ipcc.ch/report/ar6/wg1/downloads/report/IPCC_AR6_WGI_Errata.pdf).

## Reproducibility and limitations

- [Real-data multi-year source run](https://github.com/abhijith-sivaprasadan/residual-pathways/actions/runs/39973567325).
- [Real-data gas source run](https://github.com/abhijith-sivaprasadan/residual-pathways/actions/runs/39973877646).
- [Derived gas mean table](../data/derived/n2o_metric_sensitivity_2050.csv).
- Code: cohort_robustness.py, nonco2_pilot.py, gwp.py and their paired tests.

Unreviewed source metadata, model-specific gas definitions, data access restrictions and GWP source conventions constrain interpretation. No scenario has acquired an I3 accounting grade. The final CO2-only residual-gross study is independent of this gas-convention pilot.
