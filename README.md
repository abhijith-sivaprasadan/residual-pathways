# ResidualPathways

Independent open-source research on IAM scenario reporting, residual-emissions identifiability and controlled optimisation experiments.

[![IAMC baseline](https://github.com/abhijith-sivaprasadan/residual-pathways/actions/workflows/ci.yml/badge.svg)](https://github.com/abhijith-sivaprasadan/residual-pathways/actions/workflows/ci.yml)
[![AR6 source pilot](https://github.com/abhijith-sivaprasadan/residual-pathways/actions/workflows/ar6-public-source-pilot.yml/badge.svg)](https://github.com/abhijith-sivaprasadan/residual-pathways/actions/workflows/ar6-public-source-pilot.yml)

**Independent project, not affiliated with or endorsed by IIASA or IPCC.** Variable availability is not the same thing as an exhaustive, verified gross/net/removal accounting identity.

## Verified empirical research to date

- Publicly published IIASA-labelled AR6 World **teaching release** (Zenodo 20056332): 693,299 source IAMC series; 2,298 World model-scenario pairs; 1,202 match the separately republished v1.1 climate-vetted metadata; 422 vetted scenarios report a 2050 direct-air-capture variable and 330 simultaneously report the first six CO2/CCS/DAC candidate names. **No gross emissions have been reconstructed.**
- Historical real CD-LINKS tutorial series: 18 exactly matched 2050 source-reported CO2 observations from three historical model versions and six shared scenarios; 180 signed observations across 2010–2100. Nine of 18 observations in 2100 are negative. **These are not gross residual emissions.**
- Six real SciPy/HiGHS optimisation runs with hypothetical renewable limits, fossil CCS, DAC and net caps. This is a separate synthetic exercise, **not** an IAM or MESSAGEix/GAMS solve.

**Results:** [AR6 2050 empirical findings](docs/ar6_teaching_2050_findings.md), [reproducible aggregate counts](data/derived/ar6_teaching_2050_summary.json), [first CD-LINKS findings](docs/initial_findings.md), [Research Note 01](docs/research_note_01.md).

### Source and scientific limitations

The public [2026 teaching release](https://zenodo.org/records/20056332) has **not been hash-matched to the authenticated official AR6 World v1.1 assessment download**. The v1.1 metadata workbook was independently redistributed by a third-party GitHub repository, not obtained directly from the official IIASA endpoint. Findings are properly described as an exploratory teaching-source audit, not a finished AR6 ensemble study.

All current real-source cases remain at I0 (no independently source-verified exhaustive partition). This does **not** prove no real scenarios can ever qualify for I3; it means we have not established them. Land-use CO2 can be net, and fossil point-source CCS is avoided emissions rather than atmospheric carbon removal. Consult the [source-referenced preliminary semantic dictionary](config/variable_semantics_preliminary.json).

## Reproduce the published IAMC tutorial results

Requires Python 3.10+.

    python -m pip install -e ".[dev]"
    python -m pytest -q
    python -m residual_pathways fetch-tutorial --output data/tutorial_data.csv
    python -m residual_pathways analyze --input data/tutorial_data.csv --output results/tutorial --pyam-check

This downloads and parses the pinned public pyam/CD-LINKS tutorial dataset, produces JSON, CSV, charts, decadal signed observations and a hash-bound release manifest. It checks source observations with pyam. No raw data are committed.

## Run the empirical AR6 coverage audit

The [public teaching-source GitHub workflow](.github/workflows/ar6-public-source-pilot.yml) downloads the legally public source and a content-verified but independently redistributed v1.1 metadata workbook, runs the streaming source audit and tests climate-vetted vs broader metadata populations. Only small aggregate JSON reports are uploaded as artifacts.

For research on **canonical** AR6 v1.1, obtain the source through the [IIASA Scenario Explorer](https://data.ece.iiasa.ac.at/ar6/#/downloads) under its terms and keep large files out of Git. Follow [AR6 source access instructions](docs/ar6_access.md) and the [metadata protocol](docs/ar6_metadata_protocol.md).

    python -m residual_pathways audit-ar6 --input data/AR6_Scenarios_Database_World_v1.1.csv --candidates config/ar6_variable_candidates.json --output results/ar6/coverage_2050.json
    python -m residual_pathways audit-ar6-strata --input data/AR6_Scenarios_Database_World_v1.1.csv --metadata data/AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx --metadata-sheet meta_Ch3vetted_withclimate --category-column Category --candidates config/ar6_variable_candidates.json --output results/ar6/vetted_2050.json

The metadata sheet choice is compulsory for multi-sheet XLSX and ensures the 1,202 climate-vetted cases are not conflated with the 2,304-row broader metadata source. The sources are hashed and user-provided variable names must match exactly. Missing values are never filled with zero. Neither an aggregate emission series nor nested components are treated as a verified physical gross identity.

## Controlled modelling and methods

    python -m residual_pathways model-sensitivity --output results/model_sensitivity
    python -m residual_pathways gams-preflight --output results/gams_preflight.json

The first command executes the **actual SciPy/HiGHS** synthetic experiments. The second documents tooling readiness while explicitly declaring that no MESSAGEix/GAMS Westeros solve has occurred. See [controlled experiment limitations](docs/controlled_experiments.md).

The evidence ladder is I0 (no reviewed identity), I1 (reviewed net only), I2 (partial or unreconciled components), I3 (exhaustive nonoverlapping physically compatible components, source precision, dual reconciliation). No current empirical output is assigned I3.

Read the [scientific protocol](docs/protocol.md), [v3 execution runbook](docs/v3_execution_runbook.md), [open research tasks](https://github.com/abhijith-sivaprasadan/residual-pathways/issues), and companion [PathwaysHub](https://github.com/abhijith-sivaprasadan/pathways-hub).

MIT license applies to original code. Upstream data have separate access and redistribution terms.
