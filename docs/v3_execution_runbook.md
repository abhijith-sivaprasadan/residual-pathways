# V3 reproducibility runbook — actual execution gates

## A. Already reproducible without restricted data

Install Python 3.10+ and project dependencies: python -m pip install -e ".[dev]"

1. Run tests: python -m pytest -q
2. Fetch exact official pyam tutorial release: python -m residual_pathways fetch-tutorial --output data/tutorial_data.csv
3. Verify and analyze the real tutorial data: python -m residual_pathways analyze --input data/tutorial_data.csv --output results/tutorial --pyam-check
4. Solve the six synthetic capacity/CO2 experiments: python -m residual_pathways model-sensitivity --output results/model_sensitivity
5. Produce non-invasive MESSAGEix/GAMS readiness record: python -m residual_pathways gams-preflight --output results/gams_preflight.json

Expected educational IAMC outputs include source/metric hashes, 18 matched 2050 observations, 180 decadal signed observations, nine negative 2100 reports, and I3=0. The optimization outputs are hypothetical and must never be combined with the published scenario values as though they were model-generated or calibrated evidence.

## B. Official AR6 World v1.1 data: legally permitted local copy required

1. Open the official scenario explorer: https://data.ene.iiasa.ac.at/ar6/#/downloads
2. Follow the service's guest or registered download process and review its use/redistribution terms.
3. Obtain the World v1.1 CSV and metadata indicators v1.1 XLSX; keep the raw data out of the repository.
4. Inspect the actual XLSX header names to choose the climate category header. Preserve original Model+Scenario joins.
5. Run source-availability report:
   python -m residual_pathways audit-ar6 --input data/AR6_Scenarios_Database_World_v1.1.csv --candidates config/ar6_variable_candidates.json --output results/ar6/coverage_2050.json --year 2050
6. Run stratified audit:
   python -m residual_pathways audit-ar6-strata --input data/AR6_Scenarios_Database_World_v1.1.csv --metadata data/AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx --category-column "ACTUAL_CLASS_HEADER" --output results/ar6/stratified_2050.json --year 2050
7. Log source file hashes and exact model/scenario denominators, missing categories, variable definitions, gas metrics, precision and reporting scope. Never infer I3 from presence alone.

**Current blocker:** Original AR6 full data/metadata are not available to this repository's automated environment. The commands have passed unit/fixture tests, not actual AR6 research tests.

## C. Verified accounting and source precision

Do a human-reviewed 20–30 case audit across compatible model/scenario categories. Do not equate CCUS fossil capture with atmospheric removal. For I3 require verified positive and negative components that are exhaustive and non-overlapping, source-documented precision, and reconciliation materiality/rounding checks. Report I0–I2 and model-family missingness explicitly. If no I3 cases exist, publish an identifiability finding rather than a fabricated gross-emissions estimate.

For methane/N2O explicitly select corrected AR6 2025 GWP100 or original 2021 assessment and preserve raw gas mass, horizon and origins; do not reconvert existing CO2e.

## D. MESSAGEix/GAMS gate

- Check https://docs.messageix.org/en/stable/install.html for current GAMS requirements; confirm license before solving.
- Download version-pinned official Westeros notebook and any accompanying tutorial dependencies.
- Run baseline and record GAMS/solver/model versions, licensing feasibility (without secrets), input hashes, objective and solver status.
- Change one factor at a time in controlled experiment; verify dimensions and objective comparability.
- The existing SciPy/HiGHS exercise is a different mathematical model; label distinctly.

## E. Research operations and real external verification

PathwaysHub can verify source artifact bytes and generate a briefing and a synthetic issue/review exercise. A legitimate EXTERNALLY_EXERCISED case study needs two consenting independent non-author participants, actual submissions/reviews and explicit publication consent, plus authentication and evidence preservation. No such exercise has occurred in the implemented CI.

## F. Scientific exit criteria

A research article should include data access/license table, variable dictionary and checks, model-category cohort definitions, audited exclusions and coverage, non-CO2 GWP source versions, registered sensitivity design, reproducible scripts and results, assumptions/limitations, and independent technical review. A functioning codebase is not itself a completed research paper.

## D2. GAMS licence active — two-scenario tutorial run achieved locally

On 2026-10-24 the author provided a Windows execution transcript confirming optimal GAMS 54.6.0/CPLEX solutions for the official MESSAGEix 3.11.1 Westeros baseline and emissions-bound notebooks, followed by runner status `ACTUAL_MESSAGEIX_GAMS_SOLVED`. See [the local two-scenario runner](messageix_westeros_local.md) and the [scope-limited PathwaysHub record](https://github.com/abhijith-sivaprasadan/pathways-hub/blob/main/docs/messageix_local_run.md). Private run artifacts are not in Git and CI has not independently re-executed the solver. The separate three-scenario `westeros-validate` wind capex perturbation remains unverified locally; **do not mark its three-solve G0-3 gate passed** until its own success manifest exists.
