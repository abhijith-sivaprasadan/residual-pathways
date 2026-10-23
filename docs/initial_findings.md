# Empirical pilot: reported 2050 CO2 across three IAMC model families

Source: official [pyam CD-LINKS tutorial data](https://github.com/IAMconsortium/pyam/blob/88706bd70051ff630b73096c050e3697364e2302/docs/tutorials/tutorial_data.csv), upstream Git blob `34886a95402d1be3e38f7218925680d5b59344a1`. **This is published tutorial scenario data, not the AR6 scenario ensemble.**

The input contains 1,026 IAMC series from eight model versions. Exact matching identifies six shared scenarios for three selected models at World/Emissions|CO2/Mt CO2/yr/2050, yielding 18 model-scenario observations.

## Observed 2050 values from the public dataset

| Scenario | Min (Mt CO2/yr) | Max (Mt CO2/yr) | Cross-model range (Mt CO2/yr) |
|---|---:|---:|---:|
| CD-LINKS_INDCi | 43695.41 | 49784.94 | 6089.53 |
| CD-LINKS_NPi | 49334.01 | 56121.09 | 6787.08 |
| CD-LINKS_NPi2020_1000 | 10289.42 | 12753.84 | 2464.42 |
| CD-LINKS_NPi2020_1600 | 16377.44 | 25181.96 | 8804.52 |
| CD-LINKS_NPi2020_400 | 94.59 | 2737.84 | 2643.25 |
| CD-LINKS_NoPolicy | 54471.30 | 65153.27 | 10681.96 |

The exact 18 numerical values are recorded in [the source-derived JSON](../data/derived/verified_tutorial_comparison_2050.json). The CI pipeline reruns the independent Python IAMC reader and checks the complete model/scenario/year/variable/unit key and value for every observation.

## Interpretation and limitations

- The file reports `Emissions|CO2`, not a reviewed, exhaustive partition into positive gross emissions and atmospheric removals.
- **I3 coverage is zero and is not inferred from this sample.**
- Shared scenario labels do not establish common technology assumptions or controlled causal comparisons. The range is descriptive model spread.
- A future AR6 database study requires an explicit accounting dictionary, model/scenario cohort rules and variable-coverage audit.
- No MESSAGEix or GAMS optimisation experiment was run for this result.

## Provenance and correction

The first independently recorded reference table erroneously read the column at zero-based index 8 (2040) while labelling it 2050. The strict comparison against the Python pipeline caught the mismatch in CI; the reference was replaced using the explicit header lookup `headers.indexOf("2050")`. The original Python analysis reads the year by name and did not have this error. See [QA incident 001](QA_incident_001.md).
