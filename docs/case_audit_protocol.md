# RP24 — 24-case accounting preflight protocol

Status: executable automated source preflight. NOT a completed 24-case expert accounting audit.

## Registered sample

The unit is one World-region Model×Scenario pair with a climate-vetted metadata identity. The source is the publicly released IIASA-labelled AR6 teaching CSV (Zenodo 20056332), and the metadata source is a separately redistributed v1.1 sheet. Neither has been hash-compared with the official gated canonical v1.1 data.

For each of the eight climate categories C1–C8, rank all source-matched scenarios by the count (0–6) of six reported, unit-compatible 2050 candidate variables: EIP CO2, AFOLU CO2, land-use sequestration, biomass CCS, fossil CCS and direct air capture. Select the lowest, lower-median and highest ranked cases, with ties broken by a fixed SHA-256 ordering. This yields exactly 24 distinct cases: three per category. The algorithm is purposive and deterministic, NOT a probability sample; it cannot estimate population I3 rates.

## Automated diagnostics

Record exact-year presence, units, missingness and count of compatible reported variables. In the local-only packet, also include original source values, Model/Scenario identities and a candidate arithmetic difference (reported aggregate CO2 minus EIP minus AFOLU), only when the three source units are identical Mt CO2/year. That arithmetic is explicitly not a source-reviewed emissions identity. A zero difference does not establish gross emissions or removal partition completeness. No arbitrary rounding tolerance is applied.

Every case remains NOT_REVIEWED, accounting grade NOT_DETERMINED and I3=false until model-specific scientific definitions and physical accounting have been reviewed. Zero verified I3 is not a finding that zero scenarios could eventually qualify.

## Reproduce

Run with the checked teaching-source CSV and metadata spreadsheet:

    python -m residual_pathways case-audit --input data/ar6-private/AR6-demo-data.csv --metadata data/ar6-private/AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx --metadata-sheet meta_Ch3vetted_withclimate --candidates config/ar6_variable_candidates.json --public-output results/ar6-teaching-pilot/case_audit_24_public.json --private-output data/ar6-private/case_audit_review_packet.json

The GitHub CI uploads only the public coded register. The local packet contains original model identities, scenario names and observation values and must NOT be committed or uploaded. The source files and private packet are excluded from Git.

## What completing the human review requires

For each case, locate source model/version-specific documentation and variable definitions, source and metadata hashes, nested versus disjoint sector boundaries, positive gross/signed net/land sinks, fossil CCS versus true atmospheric CDR, unreported removal terms, original numerical precision and an explicit full-component reconciliation. Record primary references for every decision and seek independent verification for any I3 claim. The software cannot supply expert review by filling evidence fields automatically.

## Scientific acceptance

Only after the source-specific semantic gates are satisfied should a case be classified I1 (verified net only) or I2 (partial/unreconciled). I3 requires a verified exhaustive non-overlapping positive-emissions/removal partition and separate numerical/materiality tests. The present source preflight proves none of these for any case.

## Primary standards and interpretive controls

- IPCC AR6 WGIII Annex III (Scenarios and modelling methods): https://www.ipcc.ch/report/ar6/wg3/downloads/report/IPCC_AR6_WGIII_Annex-III.pdf — describes the submission template, quality-control process and climate-scenario categorisation. It documents historical CO2 EIP+AFOLU validation but does not independently establish a complete positive-gross/CDR partition for each model.
- IIASA IAMC variable format guide: https://docs.ece.iiasa.ac.at/standards/variables.html — the hierarchy is semi-hierarchical and additivity is not guaranteed. A matching prefix is not proof that any particular components are disjoint or sum to an aggregate.
- IIASA IAMC emissions variable conventions: https://data.ene.iiasa.ac.at/database/emissions.html — explains sector emissions and CDR-related variable structures. Specific model-scenario reporting scope still requires model documentation.
- IPCC AR6 WGIII Chapter 3: https://www.ipcc.ch/report/ar6/wg3/chapter/chapter-3/ — separates energy, industry, AFOLU and other CDR categories conceptually.

Case reviewers must cite original model papers, source reporting protocols and compatible units/precision; the four general references above are context, not case-specific I3 evidence.
