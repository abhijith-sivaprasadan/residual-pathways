# Empirical pilot: CO2 comparison across three published IAMC model series

**Status:** verified descriptive research exercise, not residual gross-emissions inference. Source: official pyam IAMC tutorial file from historical CD-LINKS pathways, [fixed upstream revision](https://github.com/IAMconsortium/pyam/blob/88706bd70051ff630b73096c050e3697364e2302/docs/tutorials/tutorial_data.csv), Git blob `34886a95402d1be3e38f7218925680d5b59344a1`.

The supplied IAMC dataset includes 1,026 input rows, eight distinct model versions and six substantive variables. Three selected models report common World-region Emissions|CO2 observations for six CD-LINKS scenarios in 2050: **18 matched model-scenario observations**.

## 2050 source-reported CO2

All values below are **Mt CO2/year**, and use exact matching on scenario, region, variable and unit. The min-max range is descriptive model spread, not uncertainty of a probabilistic ensemble.

| Scenario | Minimum | Maximum | Cross-model range |
|---|---:|---:|---:|
| CD-LINKS_INDCi | 42441.67 | 44642.92 | 2201.25 |
| CD-LINKS_NPi | 47276.79 | 50722.06 | 3445.27 |
| CD-LINKS_NPi2020_1000 | 18357.99 | 23754.92 | 5396.93 |
| CD-LINKS_NPi2020_1600 | 24293.52 | 33271.93 | 8978.41 |
| CD-LINKS_NPi2020_400 | 7860.05 | 12039.06 | 4179.01 |
| CD-LINKS_NoPolicy | 50476.05 | 57830.79 | 7354.74 |

Data file: [exact 18 observations](../data/derived/verified_tutorial_comparison_2050.json). CI independently recomputes the same observations from the upstream CSV and checks each number.

## Interpretation

Common scenario labels alone do **not** establish harmonized assumptions or causal comparability across IAMs. This is a data-handling and descriptive-analysis result. The aggregate variable `Emissions|CO2` cannot be identified from this sample as fully reported *gross positive emissions*, atmospheric removals, or even an independently reviewed *net* reporting boundary. **Zero** cases are promoted to accounting class I3. The range must not be described as an innovation-gap effect.

The next distinct empirical study is the AR6 variable-coverage and removals-semantics audit. This pilot does not use the AR6 full database and does not run MESSAGEix.
