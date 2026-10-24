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

**24 October 2026 update:** the author independently downloaded a local official-named AR6 World v1.1 CSV from the IIASA explorer and found it **byte-for-byte identical** to the previous public [2026 teaching-labelled CSV](https://zenodo.org/records/20056332): SHA-256 `4cf39b6b0d968e25ed389318acb1674f92146f977e9db4bfb7970f048ff73977`, 361,767,203 bytes. The local official-named metadata XLSX differs at the **file hash** level from the older third-party workbook (`fd1bc32db8463769e18f0560ced603a49598c12e1abfa06787ff763c55f06716` versus `7d22453b...`); worksheet-level value differences remain untested. Independent publisher-side hash/source authentication and model-specific accounting semantics still require review. The previous teaching-labelled source audit and actual source-native ARC24 selection are exploratory analyses, **not a completed AR6 I3 scientific study**. See [source fingerprint and model-documentation triage](docs/arc24_source_provenance_and_semantic_triage_20261024.md).

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

## Registered RP24 forensic case preflight

The case-audit command deterministically selects three source-matched climate-vetted scenarios in each C1-C8 category based on low/median/high completeness across six exactly named CO2/CCS/CDR variables. It checks source reporting, compatible units and availability of an exploratory aggregate-minus-EIP-minus-AFOLU calculation. It does NOT carry out the human scientific assessment or certify I1-I3.

    python -m residual_pathways case-audit --input data/ar6-private/AR6-demo-data.csv --metadata data/ar6-private/AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx --candidates config/ar6_variable_candidates.json --public-output results/ar6-teaching-pilot/case_audit_24_public.json --private-output data/ar6-private/case_audit_review_packet.json

The CI run uploads a coded, no-source-values public case register; original model/scenario identities, values and blank review forms remain in the local-only packet. See [Research Note 02](docs/research_note_02.md), the [24-case coded register](data/derived/rp24_case_register.csv), and [RP24 registered methods](docs/case_audit_protocol.md). To regenerate the local-only model/scenario reviewer packet on Windows PowerShell, run scripts/run_rp24.ps1 after placing the exact hash-verified study inputs in data/ar6-private.

## Research outputs for external readers

[Research Note 03](docs/research_note_03.md) reports model-label and year coverage and source-grounded N2O metric sensitivity. [Innovation hypotheses](data/derived/innovation_gap_register.csv) are literature topic-linked but untested, not causal estimates. Run python -m residual_pathways publish-brief to generate a one-page [source-scoped policy briefing](docs/communication_readme.md), a publication-oriented coverage SVG and source SHA manifest. All are exploratory teaching-source products, not IIASA publications.

## Actual GAMS/MESSAGEix Westeros gate

With your own correctly installed GAMS licence, run the documented [source-pinned official Westeros experiments](docs/messageix_westeros.md). The CLI command westeros-validate runs three actual GAMS-backed MESSAGEix solves: the official tutorial baseline, one wind-capital-cost change, and the official emissions bound. It writes success metadata **only after** every solve succeeds. Ordinary license-free CI tests orchestration but does not pretend to run GAMS. This is a stylized training model, not an AR6 ensemble calculation.

## Licensed MESSAGEix Westeros (local execution)

We have a GAMS-free tested, locally executable runner for official pinned MESSAGEix v3.11.1 Westeros baseline and CO2 emissions-bound notebooks. The licensed solve must be performed on a machine with installed GAMS/Java; GitHub CI makes no solve claim. See [Windows clone, setup and execution guide](docs/messageix_westeros_local.md), plus scripts/setup_westeros_windows.ps1 and requirements-messageix.txt. No GAMS license file or secrets belong in Git.

## Export local Westeros evidence to PathwaysHub

After a real successful local run, use `python -m residual_pathways westeros-export --input PATH/TO/manifest.private.json --output results/westeros_handoff` to create an allowlisted SHA-256 evidence bundle without rerunning GAMS. The companion `pathways_hub consume-westeros` validates the separate `pathways-handoff.westeros.v1` schema, hashes and two scenario objectives while explicitly retaining `AUTHOR_REPORTED_LOCAL` provenance. See [Windows two-repo handoff](docs/westeros_handoff.md). Neither unit tests nor CI claim to have executed licensed GAMS.

## Explain the saved Westeros technology response

Use `python -m residual_pathways westeros-analyze --manifest results/messageix_private/20261023T230104Z_e182e730/manifest.private.json --output results/westeros_analysis` in the existing MESSAGEix Windows environment to read the **already solved** ixmp database (no new GAMS run). The analyzer compares stored `ACT`, `CAP`, and `CAP_NEW` by technology/year, writes CSV/JSON, produces three native-unit SVG charts, a caveated report and a SHA-256 inventory. It refuses missing persisted solutions and does not fill missing values with zero. Baseline emissions were not modelled, so neither a CO2 reduction nor a carbon shadow price is asserted. See [analysis methods, command and limitations](docs/westeros_analysis.md). CI tests mock stored data only.

**First actual saved-solution finding (2026-10-24):** coal activity decreases by 12.725 GWa (year 710) and 37.053 GWa (year 720), matched by wind increases at fixed grid/lighting service. The 20.4275% higher objective is established; the emissions cap is numerically saturated using saved 10-year period durations; the constraint marginal/carbon shadow price remains unavailable. See [scope-limited Westeros result note](docs/westeros_findings_20261024.md).

### Saved emissions-bound reconciliation (no new solve)

The local follow-up extracted CO2 `EMISS` records of **350.569757**, **568.509836**, and **580.920407** for Westeros in 700/710/720, against a `bound_emission` of **500 MtCO2**. The cap audit subsequently used the saved 10/10/10-year period durations, category mappings and emissions values to establish a numerical average of 500 with zero slack. The `World` records duplicate Westeros's reported values, and `EMISSION_CONSTRAINT` was empty; neither an independently validated model dual nor a carbon price was obtained. The author has completed the `westeros-cap-check` diagnostic against the private saved run with `NUMERICALLY_SATURATED`; see [emissions cap audit instructions](docs/westeros_cap_audit.md).

### Isolate the CO2-cap causal effect (one new licensed solve)

`python -m residual_pathways westeros-no-cap-control --manifest results/messageix_private/20261023T230104Z_e182e730/manifest.private.json --output results/westeros_control_private` clones the already-solved emissions-bound case to a **separate local ixmp database**, removes only `bound_emission`, preserves CO2 emissions accounting, and solves one new control. The result compares objectives and ACT/CAP/CAP_NEW for baseline, emissions-bookkeeping-only and emissions-constrained models. **A new local control solve completed successfully on 2026-10-24**: GAMS/CPLEX reported LP optimal and normal completion, the runner reported `ACTUAL_MESSAGEIX_GAMS_CONTROL_SOLVED`, numerical objective equivalence with baseline, and a 32484.96875 native-unit attributable cap effect. See [three-case experiment and evidence](docs/westeros_control_experiment.md).

### Three-scenario result confirmed; case-study generator available

The locally solved CO2-accounting-only control reproduces the saved baseline **exactly** at native objective precision (**159025.828125**) and for all six author-shared coal/wind ACT records. The capped objective is **191510.796875**: imposing the duration-weighted 500 MtCO2 cap raises the objective by **32484.96875** (**20.427479694974863%**) and shifts coal activity to wind by 12.725198 GWa in model year 710 and 37.052798 GWa in year 720. This is an author-reported educational Westeros result, not an independent reproduction or AR6 finding.

A new, no-GAMS `westeros-case-study` command reads the actual private `three_case_comparison.json` and saved `cap_reconciliation.json`, revalidates **all 36** ACT/CAP/CAP_NEW rows and numerical checks, and writes allowlisted Markdown/JSON/CSV/SVG figures plus exact SHA-256 file inventory under gitignored `results/westeros_case_study`. This derived report **has not yet been run on the author's actual files**. See [case-study instructions](docs/westeros_three_case_case_study.md).

### Canonical AR6 v1.1 source and RP24 review gate (pending official acquisition)

**Source issue:** our 24 model-scenario RP24 cases were selected from the public **teaching** AR6 World subset. The original official IIASA World v1.1 CSV and climate metadata remain unauthenticated; no individual scenario has been certified I1-I3. The official v1.1 release is accessed through the IIASA [AR6 Explorer](https://data.ene.iiasa.ac.at/ar6/#/downloads) under its source license, not by renaming the teaching file.

A new local-only **`ar6-canonical-select`** command derives a fresh 24-case cohort directly from original locally downloaded official-named files, generating a public coded selection and gitignored private scientific review packet; the original teaching RP24 packet is **not needed**. The optional `ar6-canonical-gate` command compares the earlier teaching-derived 24 cases against the user-obtained canonical-named files, checking identities, climate categories, variables, units and 2050 values. Hash agreement and local filenames **cannot independently authenticate official provenance**. No I3 or scientific-review pass is granted automatically. New regression tests use **synthetic** official-named fixtures only; actual direct-file testing is pending. See [official AR6 acquisition, local PowerShell invocation, and scientific review queue](docs/ar6_canonical_rp24_gate.md).

### Signed AR6 land-emissions screening: REMIND vs POLES (2026-10-24)

The author inspected seven reported 2050 variable signs in two climate-vetted source records, `ARC24-03` (REMIND-MAgPIE CEMICS minimum-CDR) and `ARC24-06` (POLES ENGAGE). **AFOLU is positive in REMIND and negative in POLES, while reported land sequestration is positive in both; REMIND DAC is a recorded zero, not missing.** Prütz et al. (2025), [ESSD doi:10.5194/essd-17-221-2025](https://doi.org/10.5194/essd-17-221-2025), identify AR6 AFOLU as a **net** CO2 variable and land sequestration as a separately reported **gross sink**, highlighting cross-model comparability issues. No gross-emissions or CDR partition has been certified; the original accounting classes remain undetermined.

After `git pull --ff-only`, run `python -m pytest -q tests/test_arc24_sign_screen.py` and `python -m residual_pathways arc24-sign-screen` against the existing local private ARC24 packet to produce a redacted, 24-case sign matrix. All tests are **synthetic**, and the new CLI has not yet been executed against the author's actual locally held packet. See [model-specific sign and semantic review](docs/arc24_source_provenance_and_semantic_triage_20261024.md).


### ARC24 actual 24-case sign screen and private aggregate arithmetic follow-up

The author completed the real local 24-case sign screen on 2026-10-24 after **9/9 synthetic regression tests**. **Eight** selected cases have negative signed net AFOLU CO2; **eleven** have no separately reported 2050 land-sequestration value. Neither can be equated to a source-verified gross land-removal measurement, and the purposive selection does not give an ensemble-wide frequency estimate. I3 scientific reviews remain **0**.

The next **arc24-arithmetic** command reads the original locally protected selected 24-case packet and checks the exact raw-decimal relationship for reported CO2 total minus energy/industrial CO2 minus net AFOLU. It generates coded statuses publicly, stores original source values and residuals **only in data/ar6-private**, and never claims physical gross/atmospheric-removal closure:

    python -m pytest -q tests/test_arc24_aggregate_arithmetic.py
    python -m residual_pathways arc24-arithmetic

This new code has been committed but **has not yet run on the author's actual local data**. For source-specific review limitations and instructions see [ARC24 scientific triage](docs/arc24_source_provenance_and_semantic_triage_20261024.md).


### ARC24 POLES ENGAGE residual cluster — targeted source review

The author locally classified the 2050 reported net-CO2 aggregate residual for all 24 source-selected cases using a *descriptive* ratio to the largest reported term. Of the **14 nonzero** residual cases, **9** are below 0.001%, **one** falls between 0.001% and 0.1%, and **four** fall between 1% and 10%. **All four** of the larger residuals occur in **POLES ENGAGE** (ARC24-06/09/12/21 across categories C2/C3/C4/C7), with two positive and two negative residuals. There are also five exact and five missing-data cases.

A common model-specific emission-scope or reporting-convention explanation is a **hypothesis**, not proof of a model error. IAMC variable hierarchy does not require additivity; source precision and ENGAGE-version-specific mappings need primary documentation. The purposive ARC24 selection cannot estimate full AR6 ensemble frequencies. See the [POLES-focused scientific investigation and falsification plan](docs/arc24_poles_cluster_investigation_20261024.md). All 24 gross/net/CDR accounting grades remain NOT_DETERMINED; verified I3=0.


#### Four POLES cases: temporal falsification prepared

A source-locked, local-only scan of **2030, 2040, 2050, 2060, 2070** is now available to check whether the four POLES ENGAGE 2050 residuals occur in other years. Run the synthetic tests and the real-input CLI from the repo:

    python -m pytest -q tests/test_arc24_poles_timeline.py
    python -m residual_pathways arc24-poles-timeline

The CLI checks the actual World v1.1 file SHA-256 against the private ARC24 selection packet, crosschecks the selected 2050 source values, and emits public **coded signed percentage bands** only. Original observations, absolute values and model/scenario identities stay in the private source files. The new utility is **committed but not yet locally executed**; cross-year results and physical explanations must not be invented. See [POLES residual investigation](docs/arc24_poles_cluster_investigation_20261024.md).

#### Confirmed POLES 2030–2070 persistence and optional-sector follow-up

The author executed the source-locked POLES timeline CLI on local World v1.1 data (five synthetic tests passed), finding **20/20 nonzero reported-decimal net-CO2 aggregation residuals** across the four selected POLES ENGAGE scenarios in 2030, 2040, 2050, 2060 and 2070. **Three scenarios change residual sign**, and **five case-years have a relative magnitude of at least 10%**, under the registered descriptive denominator. This is not evidence of a faulty model or a source-verified positive-gross/CDR partition. See the [POLES evidence-led investigation](docs/arc24_poles_cluster_investigation_20261024.md).

A new source-locked read-only CLI, **arc24-poles-optional-co2**, checks whether these four original POLES cases report the four additional CO2 sectors recognized by the AR6 WGIII climate assessment workflow (Other, Waste, Other Capture and Removal, Product Use), and outputs only code/variable presence and signs. No unverified sector summation is performed. The new tests **have not yet been run locally**:

    python -m pytest -q tests/test_arc24_poles_optional_co2.py
    python -m residual_pathways arc24-poles-optional-co2

#### POLES reported CO2 Other: source-backed candidate accounting explanation

The author's original World v1.1 source check reports **Emissions|CO2|Other** in **all 20** four-POLES-scenario/year observations, with **13 positive and 7 negative** entries. Waste, Other Capture and Removal, and Product Use are not reported in any of those 20. The aggregate total-minus-EIP-minus-net-AFOLU residuals also have **13 positive and 7 negative signs**. This coincidence motivated a stricter **per-case/year numeric check**, not a claim of reconciliation.

The [primary ENGAGE Netzero Analysis source notebook](https://data.ece.iiasa.ac.at/engage-netzero-analysis/notebooks/1_categorization.html) *explicitly derives* the Other CO2 category as total CO2 minus AFOLU, Energy Demand, Energy Supply and Industrial Processes for the ENGAGE v2.0 analysis dataset. That is **strong evidence of a residual-sector convention in a related ENGAGE analysis**, but the exact AR6 World POLES export and whether EIP exactly sums those detailed sectors remain to be proven. The AR6 climate-assessment workflow separately reclassifies certain optional categories to EIP in an alternate pathway. Do not conflate them.

The author's earlier optional-sector synthetic test failed because an over-broad string assertion found the model label in a generic prose warning; **not because original scenario identifiers or source values were emitted**. The generic text has been corrected and privacy checks strengthened, **pending local retest**.

To directly test the proposed original reported-decimal identity without publishing original values:

    python -m pytest -q tests/test_arc24_poles_optional_co2.py tests/test_arc24_poles_other_identity.py
    python -m residual_pathways arc24-poles-other-identity

Details and scientific limits: [POLES longitudinal accounting investigation](docs/arc24_poles_cluster_investigation_20261024.md). All I3 determinations still pending.