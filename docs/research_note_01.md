# Research Note 01 — What can a reported IAMC CO2 trajectory actually identify?

**Author:** Abhijith Sivaprasadan  
**Date:** 23 October 2026  
**Status:** Reproducible exploratory pilot / methods note; not submitted for peer review  
**Repository:** ResidualPathways v0.1  
**Scope:** Source-reported historical CD-LINKS tutorial data + separate hypothetical optimisation exercise. This is not an IPCC AR6 full-ensemble analysis, not a residual gross emissions estimate, and not an IIASA publication.

## Abstract

Attributing future emissions gaps to technological constraints requires identifying the reporting boundary of each CO2 variable and distinguishing positive atmospheric emissions, avoided emissions via fossil point-source CCS, and actual carbon dioxide removals. This pilot establishes a software-audited IAMC data processing baseline and tests a deliberately limited synthetic technology sensitivity model. We reproduce 18 matched World-region Emissions|CO2 model-scenario observations for 2050, and 180 matching decadal observations from 2010–2100 in a pinned published pyam/CD-LINKS tutorial sample. Cross-model observed 2050 ranges vary markedly by scenario. Nine out of 18 2100 observations in the matched subset are negative; therefore the signed reported variable cannot be assumed to measure positive gross atmospheric emissions. No exhaustive accounting partition is documented for these observations; zero are classified as I3. A distinct, hypothetical SciPy/HiGHS linear programme demonstrates reproducible sensitivity to renewable limits, fossil CCS storage and atmospheric removal capacity without claiming IAM or real-world causal results.

## 1. Research motivation

Integrated assessment model outputs are frequently compared under familiar variable names, but a matching label is not enough to establish common physical boundaries or harmonised technology assumptions. The underlying accounting questions are: (1) what emissions sources and removals are included, (2) is each component disjoint, (3) what is reported/observed rather than reconstructed, and (4) what precision supports the aggregate identity?

A key motivating literature source is Ganti et al. (2024), which examines the role of CO2 removal in climate pathways. The source is used here for conceptual motivation only, not for an empirical replication. The AR6 database itself is documented and curated separately by IIASA/IAMC.

## 2. Data and analytical methods

Input: the official IAMconsortium/pyam tutorial_data.csv from pinned Git revision 88706bd70051ff630b73096c050e3697364e2302, with recorded source SHA-256 and upstream Git blob. CD-LINKS scenarios are historical examples, not current model implementations. The input includes 1,026 IAMC series.

Our parser enforces unique Model / Scenario / Region / Variable / Unit identities, validates annual numeric values, and distinguishes absent from zero observations. An independent pyam import checks total parsed observations. The comparative subset requires exact World, Emissions|CO2, Mt CO2/yr, year and scenario matches for three distinct model versions: IMAGE 3.0.1, MESSAGEix-GLOBIOM 1.0 and REMIND-MAgPIE 1.7-3.0. These labels are source identifiers; the project does not itself run those IAMs.

A fixed-source 2050 reference file is checked observation by observation in CI. Decadal comparisons repeat the same matching without interpolating absent years, output each observation and record positive/negative/zero counts. Model spread is min–max across three structurally distinct models: not a probability interval, sensitivity experiment or harmonised policy effect.

Accounting identifiability:
- I0: no usable reviewed accounting partition.
- I1: reviewed aggregate net with no constituent partition.
- I2: partial constituent information or unreconciled/overlapping partition.
- I3: exhaustive physically disjoint positive emissions/removal constituents, traceable source precision, dual numerical/materiality reconciliation and source-reviewed semantics.

The present tutorial sample is assigned I0: no net/gross/CDR classification is assumed from its variable title alone.

## 3. Results: source-reported 2050 CO2

All values are published reported World Emissions|CO2 in Mt CO2/year, *not inferred gross residual emissions*.

| CD-LINKS scenario | Minimum | Maximum | Difference across selected models |
|---|---:|---:|---:|
| INDCi | 43,695.41 | 49,784.94 | 6,089.53 |
| NPi | 49,334.01 | 56,121.09 | 6,787.08 |
| NPi2020_1000 | 10,289.42 | 12,753.84 | 2,464.42 |
| NPi2020_1600 | 16,377.44 | 25,181.96 | 8,804.52 |
| NPi2020_400 | 94.59 | 2,737.84 | 2,643.25 |
| NoPolicy | 54,471.30 | 65,153.27 | 10,681.96 |

The complete, machine-readable 18 model-scenario values and source-reference verification are in data/derived/verified_tutorial_comparison_2050.json. The full ten-year-step series generates 180 reported values (18 per decade); the count that is negative rises to 9/18 by 2100. Negative signed aggregate reported CO2 is logically inconsistent with interpreting it as *positive gross emissions*. It does not establish which atmospheric CDR pathways, fossil carbon storage or land terms are present. No causal attribution is justified.

## 4. Separate solved educational experiment

A hypothetical single-period electricity supply optimisation fixes annual demand at 100 TWh and chooses renewable generation, fossil generation, fossil CO2 capture, and DAC atmospheric removal. The objective is a synthetic cost minimum, and the net emissions ceiling is an internally defined Mt CO2 limit. We distinguish positive atmospheric emissions after fossil point-source CCS from true atmospheric DAC removal: fossil CCS is *not* negative emissions.

The following are actual SciPy/HiGHS solves of **author-chosen hypothetical parameters** (million USD objective):

| Experiment | Renewable generation TWh | Fossil CCS Mt | DAC Mt | Net CO2 Mt | Objective million USD |
|---|---:|---:|---:|---:|---:|
| Baseline | 60 | 13 | 0 | 25 | 5,544 |
| Renewable deployment limited | 30 | 30 | 5.5 | 25 | 6,442.5 |
| Fossil CO2 storage limited | 60 | 10 | 3 | 25 | 5,805 |
| No atmospheric removal | 60 | 13 | 0 | 25 | 5,544 |
| Stringent emissions ceiling | 60 | 20 | 0 | 18 | 5,880 |
| Joint severe limits | — | — | — | — | Infeasible |

These numbers demonstrate the pipeline's ability to distinguish constraints and avoid falsely forcing feasibility, **not** the effect of technological innovation on global real-world emissions. No real costs, technology availabilities or scenario relationships were calibrated. The model is not MESSAGEix.

## 5. Gas accounting and GWP versioning

A separate conversion helper enforces explicitly selected GWP100, individual raw-gas mass units and fossil/non-fossil methane identity. IPCC AR6 WGI Chapter 7 original values and the 7 October 2025 errata differ; scientific comparisons must not silently mix published assessment versions. No gas-specific World AR6 dataset has yet been analysed.

## 6. Reproducibility and QA

All publication-derived numerical observations can be regenerated via the main CLI and are checked in CI against source; all hypothetical optimisation cases are actually solved with SciPy/HiGHS, with feasibility and expected-value tests. Output artifacts carry fingerprints and declared limits on meaning. A separate cross-repository CI pipeline validates results.json and the supplementary decadal trajectory SHA-256 before PathwaysHub generates an evidence-constrained workstream status briefing.

The first numerical parity test caught an independently authored 2040/2050 column offset: QA-001 documents its detection and correction. This episode illustrates that reproducible-looking outputs are not sufficient without an independent source-to-output check.

## 7. Limitations and next scientific gates

1. Obtain authorized AR6 World v1.1 and metadata indicators. The full database has its own license and is not reproduced in this repository.
2. Complete source-specific variable semantics, model-category cohort and 20–30 case reporting audits; inspect source precision. Current I3 coverage is not inferable from the tutorial.
3. Execute an actual official MESSAGEix Westeros baseline with GAMS and a suitable license, retaining solver logs. Only then claim framework execution.
4. Design and run controlled experiments within the same identified IAM framework; the synthetic HiGHS system is not interchangeable with it.
5. Evaluate CH4/N2O reporting conventions and methane origin at source, documenting the GWP version used.
6. Obtain independent technical scrutiny and produce an appropriately scoped manuscript. Cross-team coordination requires real consenting participants.

**Conclusion:** The current defensible scientific result is an audited coverage/comparability pilot and a clear demonstration of why a reported signed CO2 variable cannot be relabelled positive gross residual emissions. The broader technology-constrained residual-emissions research question remains open pending primary AR6 and model-solving evidence.

## References

1. IAMconsortium, pyam official revision-pinned CD-LINKS tutorial dataset: https://github.com/IAMconsortium/pyam/blob/88706bd70051ff630b73096c050e3697364e2302/docs/tutorials/tutorial_data.csv
2. IIASA, IPCC AR6 Scenario Explorer and Database: https://iiasa.ac.at/models-tools-data/ar6-scenario-explorer-and-database
3. AR6 scenarios database, Zenodo 7197970 and redistribution conditions: https://zenodo.org/records/7197970
4. Ganti et al. (2024), Evaluating the near- and long-term role of carbon dioxide removal in meeting global climate objectives. Communications Earth & Environment 5, 377: https://doi.org/10.1038/s43247-024-01527-z
5. AR6 scenarios database: an assessment of current practices and future recommendations. npj Climate Action (2023): https://doi.org/10.1038/s44168-023-00050-9
6. IPCC AR6 Working Group I, Chapter 7: https://www.ipcc.ch/report/ar6/wg1/chapter/chapter-7/
7. IPCC WGI errata page: https://www.ipcc.ch/report/ar6/wg1/about/errata/
8. Official MESSAGEix Westeros tutorials: https://docs.messageix.org/en/stable/tutorials.html
