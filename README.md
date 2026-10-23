# ResidualPathways

Independent, open-source research on the coverage and comparability of integrated assessment model (IAM) scenario data, with an eventual focus on residual gross CO2 emissions, atmospheric removal, CCS, and controlled mitigation-technology sensitivities.

**Status:** Executable IAMC tutorial-data research baseline. **Not yet:** an AR6 ensemble study, a residual-gross-emissions estimate, or a MESSAGEix model implementation. No affiliation with or endorsement by IIASA or its Exploring Real Zero project is implied.

## Reproduce the first empirical exercise

The first release works with the official pyam tutorial dataset, which contains real CD-LINKS scenario submissions; this is a teaching dataset, not a curated cohort supporting gross-emissions accounting.

1. Install Python >=3.10 and run: python -m pip install -e ".[dev]"
2. Download the exact upstream file: python -m residual_pathways fetch-tutorial --output data/tutorial_data.csv
3. Run: python -m residual_pathways analyze --input data/tutorial_data.csv --output results/tutorial --pyam-check
4. Test: python -m pytest -q

Outputs: coverage.json, model_comparison.csv, results.json, report.md, co2_2050.svg, and release/manifest.json. See docs/initial_findings.md for the first source-derived results. No downloaded source CSV is committed. The source is revision-pinned; hashes and sample counts are generated for each local run.

The scenario-comparison script selects an explicit three-model, six-scenario cohort (MESSAGEix-GLOBIOM 1.0, REMIND-MAgPIE 1.7-3.0, IMAGE 3.0.1) in the World region and records reported Emissions|CO2 trajectories. These are **not** gross residual emissions. CD-LINKS is historical scenario research and does not describe present-day model configurations.

## Research questions

- How much IAMC reporting is available across model/scenario/variable/year combinations?
- Which comparison sets remain after explicit matching of scenario, region, variable, unit, and year?
- Which observations support a verified gross/net/removal decomposition, and which lack necessary accounting detail?
- In later work, how do controlled changes to technology growth, CO2 storage and removal assumptions alter stylised MESSAGEix solutions?

See docs/protocol.md and docs/roadmap.md. A deliberately conservative I0-I3 decision routine never infers gross from aggregate reported CO2 alone.

## Boundaries and reproducibility

- Real upstream source: https://github.com/IAMconsortium/pyam/blob/88706bd70051ff630b73096c050e3697364e2302/docs/tutorials/tutorial_data.csv
- A successful data-processing run is **not** external physical validation or IAM calibration.
- Source-provided IAMC scenario units and definitions are preserved. Missing values are not zero.
- A claimed I3 reconciliation requires compatible, exhaustive, non-overlapping positive-emission/removal components, documented source precision and numerical/materiality tests.
- No confidential/scenario-license-restricted database or simulated gross-emissions dataset is republished.
- Project B (PathwaysHub) consumes a versioned release contract; it cannot modify this repository's scientific outputs.

## Next scientific gates

AR6 access/license assessment; real variable-coverage pilot; source precision pilot; accounting dictionary; cross-model stratification; a successful logged MESSAGEix/GAMS Westeros solve before any MESSAGEix expertise claim; independent review and report.

License: MIT for original repository code, upstream datasets retain their own terms.

## AR6 World variable-availability audit (implemented; requires authorized source download)

The streaming `audit-ar6` command audits a locally downloaded AR6 v1.1 World CSV and exports model-scenario counts, variable-coverage denominators and source SHA-256 without publishing underlying scenario values. It does **not** claim gross-emissions identifiability from variable names. Instructions: [docs/ar6_access.md](docs/ar6_access.md).

## Controlled synthetic HiGHS experiments

The model-sensitivity command solves six hypothetical electricity/CO2 cases with SciPy/HiGHS. This is a real mathematical solve, but not an empirical IAM study or MESSAGEix execution. See docs/controlled_experiments.md for full methodology.

## Full decadal comparison

The tutorial run also generates a sign-aware 2010–2100 (10-year step) comparison and a decadal report. Negative published aggregate CO2 is not positive gross emissions, but does not by itself establish removal categories. See generated decadal_report.md in GitHub Actions artifacts.

## AR6 metadata-stratified coverage

The audit-ar6-strata command joins user-downloaded AR6 World observations to the associated official metadata via exact model-scenario identities and emits class-level variable-presence counts, denominators and hashes. Requires the original data under applicable access terms and a chosen actual metadata category header. See docs/ar6_metadata_protocol.md.

## Execute the V3 gates

See docs/v3_execution_runbook.md for the reproducible full workflow, licensed local AR6 source instructions, scientific identifiability criteria and the MESSAGEix/GAMS solve prerequisite. The gams-preflight command records tooling readiness without falsely claiming a solver run.
