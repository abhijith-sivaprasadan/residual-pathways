# Westeros three-scenario case study: derived-only publication workflow

**Evidence state:** the author solved the official baseline, an emissions-enabled constrained scenario, and one new emissions-enabled but uncapped control on Windows with MESSAGEix 3.11.1, GAMS 54.6.0 and CPLEX. Control and baseline objectives, and all six submitted coal/wind activity comparisons, matched. A separate saved-parameter audit confirmed a numerically saturated average-annual CO2 cap of 500. This newly authored publication workflow has **not yet been executed on the real locally saved JSON inputs**.

## PowerShell commands (Windows)

From the existing checkout, run the tests and then produce a local-only report package:

    cd 'E:\New folder (2)\MissionJob\residual-pathways'
    git pull --ff-only
    & .\.venv-messageix\Scripts\python.exe -m pytest -q tests/test_westeros_case_study.py
    & .\.venv-messageix\Scripts\python.exe -m residual_pathways westeros-case-study --control-json 'results/westeros_control_private/20261024T002431Z_f8428b42/three_case_comparison.json' --cap-json 'results/westeros_cap_check/cap_reconciliation.json' --output 'results/westeros_case_study'

The cap JSON must have the original adjacent cap_reconciliation.sha256 checksum file.

This command **does not connect to ixmp or GAMS**, create scenarios, rerun solves or ingest solver logs. It verifies the source run, original objective/parameter check statuses, all three objective values, all 36 complete model variable/technology/year results, calculated deltas, paired coal/wind generation, saved period lengths, emission scaling and separate numerical cap audit.

## Derived outputs, all under the gitignored results folder

- case_study.md: scientific question, experimental design, result tables, methods and clear limitations.
- case_study.json: only validated and allowlisted values.
- generation_mix.svg: three scenarios by model year with coal and wind generation activity.
- objective_comparison.svg: three stored native-unit objectives.
- technology_comparisons.csv: revalidated model variable, technology, year and differences.
- publication_manifest.json: source JSON hashes and SHA-256 plus byte lengths of every generated file.

The generator does not forward unknown or private input JSON fields. It does not copy personal names, GAMS licence/account information, local paths, GDX, HSQLDB or console logs. **Review all output files before committing any of them.** Hashes verify byte integrity, not independent GAMS execution.

The validation gate requires control ACT parity with the baseline, but reports CAP and CAP_NEW parity separately, because equal objective values alone do not imply identical decision-variable values. If it sees missing data, a changed source objective, mismatched calculation, nonfinite numbers or inconsistent cap audit, it rejects the case without upgrading the evidence status.

## Main confirmed observation

The objective for baseline and no-cap control is **159025.828125**, while the capped objective is **191510.796875**, a **32484.968750** native-unit increase (**20.4274797%**) specifically associated with the cap in this fixed-input model. The capped case substitutes **12.725198 GWa** of wind for coal in 710 and **37.052798 GWa** in 720, retaining total coal plus wind activity. The separate cap audit showed saved durations of 10, 10 and 10 years and **zero numerical slack** at an annual average of **500 MtCO2**.

The fictional Westeros tutorial is not a calibrated regional energy-system forecast, IAMC/AR6 result or scientific peer-reviewed finding. The saved equation marginal was unavailable, so **carbon shadow price is NOT_ESTABLISHED**. The case study does not invent emissions outputs for the baseline or control.

See the research note and the control-runner documentation for provenance, environmental setup and remaining independent reproduction steps.
