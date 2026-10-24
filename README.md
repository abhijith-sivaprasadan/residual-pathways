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
#### POLES CO2 Other hypothesis: near-closure confirmed, exact decimal closure not found

On 2026-10-24 the author ran the corrected optional-sector and exact CO2 Other identity tests (**13/13 synthetic tests passed**). In the four POLES ENGAGE trajectories, **20/20** original-source case-years have the **same sign** for `Total−EIP−AFOLU` and reported `CO2|Other`. None closes at exact reported decimals, but **all 20** have a remaining difference below 0.001% of the largest compared source term. Combined with the preceding observation that each original residual was at least 1% of its major component scale, **Other explains the overwhelming share of the reported aggregate difference**. This is numerical evidence of an additional reported bookkeeping category, not a disjoint physical positive-gross/CDR accounting identity or original source-export precision certification.

The [ENGAGE Netzero Analysis source notebook](https://data.ece.iiasa.ac.at/engage-netzero-analysis/notebooks/1_categorization.html) explicitly computes Other as total minus AFOLU, **Energy Demand**, **Energy Supply**, and **Industrial Processes**—not the World AR6 combined Energy and Industrial Processes (EIP) series. A new **source-locked** `arc24-poles-eip-mapping` command tests both the notebook's *expanded* equation and whether the three detailed categories sum to reported EIP; results are pending local execution:

    python -m pytest -q tests/test_arc24_poles_eip_mapping.py
    python -m residual_pathways arc24-poles-eip-mapping

See [original-data investigation and full caveats](docs/arc24_poles_cluster_investigation_20261024.md).

#### Source-native detailed POLES hierarchy: local run completed

On 2026-10-24 the author ran the original-source-locked `arc24-poles-eip-mapping` command (seven of seven synthetic tests passed). For the **same four POLES ENGAGE case trajectories** in 2030/2040/2050/2060/2070, all 20 expanded-sector comparisons were computable and all yielded **nonzero** source decimal residuals of **less than 0.001%** of the maximum absolute compared emissions term. The separate detailed Energy Demand+Energy Supply+Industrial Processes sum was **not exactly equal to source-reported EIP in 19/20** cases, with one exact equal case. **The sizes of the 19 EIP/detail differences were not fully visible in the user's shared console output**, so no magnitude claim is made for that check.

The [primary ENGAGE Netzero Analysis notebook](https://data.ece.iiasa.ac.at/engage-netzero-analysis/notebooks/1_categorization.html) explicitly constructs CO2 Other as a residual from Total minus AFOLU minus the three detailed CO2 categories. The [AR6 climate-assessment workflow](https://climate-assessment.readthedocs.io/en/latest/general.html) separately documents reclassifying optional CO2 categories into EIP under an alternate input pathway. These are **different data-processing contexts**; the user-observed near-closures are numerically reproducible, but not source-precision certified or a physically disjoint gross-emissions/CDR partition. Verified I3=0.

Conserve analysis effort: summarize the already public EIP/detail residual magnitude bands, then prioritize model-version carbon-flow semantics, BECCS/land overlap and independent review rather than introducing more speculative correction terms. See [POLES investigation](docs/arc24_poles_cluster_investigation_20261024.md).

#### POLES arithmetic close-out and primary-source gross/CDR review (24 October 2026)

Final user-run public EIP-versus-detail size bins: **10 negative** and **9 positive** source-decimal differences, each less than 0.001% of the largest compared term; **1 exact** across 20 POLES case-years. The source-reported CO2 Other series accounts for nearly all earlier multi-percent 3-term CO2 arithmetic discrepancies; all 20 five-sector expanded results are likewise nonzero but less than 0.001%. **This closes the exploratory POLES arithmetic investigation.** No source-declared numeric quantization or physically disjoint positive gross-emissions/CDR decomposition has been verified.

A new [ARC24 gross emissions and atmospheric-removal scientific source dossier](docs/arc24_gross_cdr_source_review_dossier_20261024.md) prioritizes REMIND-MAgPIE ARC24-03 and POLES ARC24-06. Critically, Strefler et al. (2021), [*Carbon dioxide removal technologies are not born equal*](https://doi.org/10.1088/1748-9326/ac0a11), has authors' [AR6-aligned source dataset and analysis code](https://zenodo.org/records/5103024). The authors explicitly say they updated scenario names and variable categories to match AR6; **this is a promising independent source, not yet verified as the exact ARC24-03 SSP1 minCDR scenario**. Gross/net land sequestration, BECCS versus fossil CCS, DAC, physical overlap, original precision and independent I3 scientific review remain open.

#### Primary REMIND-MAgPIE ARC24-03 author's source crosswalk (prepared)

The next research stage moves beyond the completed POLES numeric near-reconciliation to a **source-version-checked gross emissions/CDR semantic review** of ARC24-03, REMIND-MAgPIE 2.1-4.2, CEMICS_SSP1-1p5C-minCDR. The [original authors' CEMICS Zenodo v2 archive](https://zenodo.org/records/5103024) explicitly notes its scenario and variable names were brought into alignment with AR6. An [independent pathway methodology](https://1p5ndc-pathways.climateanalytics.org/methodology) corroborates this exact model/scenario pair. The source file must still be compared **record by record** to AR6 World v1.1; a matching paper title or scenario name is not enough.

Local-only workflow:

    & .\scripts\fetch_cemics_v2.ps1
    & .\.venv-messageix\Scripts\python.exe -m pytest -q tests/test_arc24_cemics_crosswalk.py
    & .\.venv-messageix\Scripts\python.exe -m residual_pathways arc24-cemics-crosswalk

Source MIF (with trailing semicolon support), author Rmd/README and region crosswalk remain in ignored data/ar6-private/cemics-v2. The command validates the Zenodo author-file MD5 checksums, World SHA and saved ARC24-03 2050 observations, then writes a redacted variable-name/unit/status comparison to results/ar6-canonical-gate/arc24_cemics_source_crosswalk_public.json. **The new tests and actual source comparison have not yet been executed by the author.** Read the [study-source and carbon-flow evidence protocol](docs/arc24_cemics_v2_original_source_crosswalk.md) for blockers to any I3 classification.

##### Author R Markdown source-encoding fix (2026-10-24)

The original CEMICS v2 Zenodo download **succeeded locally** and verified all four archive MD5s. The 12 original synthetic tests passed, but the first real source crosswalk aborted while decoding the authors' Rmd or README using strict UTF-8; **no report was written**. The crosswalk now retains checksum verification and supports audited strict UTF-8, then legacy cp1252/latin-1 decoding for textual supporting sources, with explicit output encoding uncertainty and added regression tests. **The corrected crosswalk and added tests have not yet been run locally.** There is no reason to re-download verified original files.

    git pull --ff-only
    python -m pytest -q tests/test_arc24_cemics_crosswalk.py
    python -m residual_pathways arc24-cemics-crosswalk

Only a successful rerun can establish whether the exact author-archive ARC24-03 Model×Scenario×World×2050 source pair exists, what matches AR6 variable by variable, and what scientific semantic gaps remain. See the [CEMICS research crosswalk audit](docs/arc24_cemics_v2_original_source_crosswalk.md).

##### Important source-identity finding: ARC24-03 absent by exact name from authors' MIF

The author reran the repaired original CEMICS crosswalk after **18/18 tests passed**. All four published Zenodo v2 files had verified MD5 checksums and the exact original AR6 World selection remained unchanged, but the author MIF has **zero rows with the exact `CEMICS_SSP1-1p5C-minCDR` scenario identifier**. Consequently, zero exact model/scenario/2050 variables could be compared, and the R Markdown has zero exact-string occurrences. This is a **source-provenance gap, not a software error or evidence of physical non-closure**. The 2021 paper remains valuable for model-family CDR background, but an exact scientific source mapping has not been verified.

A targeted, source-MD5-locked `arc24-cemics-names` diagnostic now reports the authors' actual Model/Scenario labels, normalized textual matches and script line numbers, without exporting any original emissions values. This is a possible alias investigation **only**; a similarly named model run cannot automatically substitute for ARC24-03. The new command and synthetic tests are committed, **not yet run locally**:

    python -m pytest -q tests/test_arc24_cemics_name_inventory.py
    python -m residual_pathways arc24-cemics-names

See [CEMICS original-source reconciliation and negative result](docs/arc24_cemics_v2_original_source_crosswalk.md). **No source-backed gross positive CO2/removal decomposition has been established; I3=0.**

##### Original CEMICS archive inventory and alias-fingerprint gate (24 October 2026)

The author executed the new original MIF name inventory with **24/24 passing tests**: source has **147,534 rows**, one unversioned `REMIND-MAgPIE` Model label, 20 scenarios, **no exact or punctuation-normalized `CEMICS_SSP1-1p5C-minCDR` match**. It does contain SSP1-1p5C `noCDR` and `fullCDR` as distinct cases, each with 7,391 source rows. The published 2021 CDR paper describes a min CDR scenario, but this alone does **not** prove that original author `noCDR` equals AR6 versioned `minCDR` or that model exports are identical.

A new source-hashed **`arc24-cemics-alias-fingerprint`** command tests: author fullCDR versus AR6 fullCDR (control); author noCDR versus AR6 minCDR (hypothesis); and two crossed control pairs. It compares shared original variable names/units across up to nine years at exact reported decimals, while only coded status counts/bands and author scenario labels are publicly recorded. Neither an exact numeric fingerprint nor a textual name resemblance is an author-approved rename or a physically disjoint gross/CDR inventory. The newly committed tests and actual source scan **have not yet been executed locally**.

    python -m pytest -q tests/test_arc24_cemics_alias_fingerprint.py
    python -m residual_pathways arc24-cemics-alias-fingerprint

Review scientific limitations and all four scenarios in [CEMICS author-archive source crosswalk](docs/arc24_cemics_v2_original_source_crosswalk.md). I3 remains zero.

##### Real CEMICS alias run revealed duplicate author MIF Variable names (24 October 2026)

The source-locked CEMICS alias fingerprint's initial seven synthetic tests passed, but the real original MIF run raised `Duplicate authors' scenario/variable` before any result was written. That failure reflects our original oversimplified assumption that World-region Model+Scenario+Variable was a globally unique record key; the MIF specification permits Unit and extra metadata fields. **The local source was neither corrupted nor numerically disproven by this exception.**

The updated fingerprint preserves all source rows and uses **one unique common Unit record per source** for each variable. It reports `NO_SHARED_UNIT`, `AMBIGUOUS_MULTIPLE_SHARED_UNITS`, or `AMBIGUOUS_DUPLICATE_ROWS_SAME_UNIT` instead of silently discarding, averaging, or selecting ambiguous source rows. It also logs whether multiple author units occurred and excludes ambiguous/missing observations from the exact-match fraction. Added synthetic regression tests exercise repeated source variables across different units, same-unit duplicates, and ambiguous original AR6 observations. **Those new tests and the real archive comparison require rerunning locally.**

    python -m pytest -q tests/test_arc24_cemics_alias_fingerprint.py
    python -m residual_pathways arc24-cemics-alias-fingerprint

Consult [CEMICS source-provenance and duplicate key handling](docs/arc24_cemics_v2_original_source_crosswalk.md). The model-level noCDR/minCDR identity remains unproven and I3=0.

##### ARC24-03 / Strefler author source — controlled numerical crosswalk succeeds

**Original-data result, 24 October 2026:** ten of ten local regression tests passed, and the author-to-AR6 fingerprint successfully compared 517 shared World variables × nine years (4,653 paired recorded-decimal observations) with zero exclusions/ambiguities. Authors' `CEMICS_SSP1-1p5C-fullCDR` equals AR6 versioned `fullCDR` in **4,653/4,653** observations (same-label control). Authors' `CEMICS_SSP1-1p5C-noCDR` equals AR6 `CEMICS_SSP1-1p5C-minCDR` (registered ARC24-03) in **4,653/4,653** observations. Each crossed comparison matches only **1,604/4,653**, separating the trajectories. The author archive reports two multi-unit variables that were paired uniquely with original AR6 source Units; none was excluded.

**Evidence-status change:** The authors' AR6-aligned `noCDR` World emissions/removal outputs are now **numerically established as the original recorded series for ARC24-03's shared World subset**. A written author-approved name change and exact internal version/binary identity are still unverified. *Matching 4,653 outputs is not 4,653 independent physical accounting tests.* Atmospheric removal from biomass, DAC and land, gross fossil/industry emissions and source precision remain under source-semantic review; **I3=0**.

Further work is in [ARC24-03 physical carbon-flow semantic review](docs/arc24_03_physical_carbon_flow_semantic_review_20261024.md). It provides a bounded local PowerShell method to inspect **original authors' R Markdown formulas** and code references, plus the key questions required to construct an exhaustive nonoverlapping positive-emissions and atmospheric-CDR ledger. The controlled fingerprint is already complete; do not repeat it without new source questions.

##### Original CEMICS R Markdown now supplies study-defined carbon-flow selectors

The author read the verified `CDRoptions.Rmd` and found **original code-line evidence** that the internal SSP1-1p5C `noCDR` identifier is presented as **`min CDR`** in the authors' plot labels (lines 555–558 and 599–601), independently reinforcing the **4653/4653** source-decimal AR6 `minCDR` fingerprint. This is an author presentation-label corroboration, not yet an official release-version/name change statement.

The same script explicitly selects `Emissions|CO2|Gross Fossil Fuels and Industry` for a 2020–2050 annualized gross-emissions reduction rate, and treats `Emissions|CO2|Land|Land-use Change|Regrowth` **with a sign reversal** as its afforestation/regrowth CDR proxy. It separately selects Enhanced Weathering, Biomass CCS and Direct Air Capture sequestration series. These original terms are **not automatically mutually exclusive** or an exhaustive total gross/net identity. In particular, author regrowth and the selected ARC24 `Carbon Sequestration|Land Use` are **different source variable names**.

See [ARC24-03 source code semantic review](docs/arc24_03_physical_carbon_flow_semantic_review_20261024.md#5-actual-author-r-markdown-inspection--first-formula-level-findings-24-october-2026) for exact original code lines and the next bounded inspection of the as-yet unseen `CDRtotal` formula. No scientific I3 is claimed.

##### CEMICS actual author-defined carbon-flow accounting equation identified

The author has inspected **actual MD5-verified Strefler v2 R Markdown source lines 150–156**, not merely a study abstract. Their operational 2050 CO2 accounting is:

    CDRaff   = -Emissions|CO2|Land|Land-use Change|Regrowth
    CDRtotal = CDRaff + Carbon Sequestration|Enhanced Weathering + Carbon Sequestration|CCS|Biomass + Carbon Sequestration|Direct Air Capture
    CO2pos   = Emissions|CO2 + CDRtotal

**Neither separate fossil CCS nor `Carbon Sequestration|Land Use` enters this original Rmd four-term CDR formula.** Gross fossil+industrial CO2 is separately selected at Rmd lines 193–194, and cumulative negative net emissions are separately calculated from the negative part of net CO2 at lines 198–202. Thus the author's derived `CO2pos` is a *specific study-defined gross-like remainder*, not demonstrably the directly reported fossil+industry gross series, all-economy emissions or an independently validated physical mass balance.

A new MD5/SHA-locked **`arc24-cemics-author-accounting`** local command tests the original study's exact source variables and units at ARC24-03 2050, computes the operational formula only when all source streams match, and compares `CO2pos` with the distinct fossil+industry gross indicator using **only signed flags and coarse discrepancy bands** (never raw source observations). It refuses unverified/missing streams rather than substituting zero. New tests and real command execution are **pending**:

    python -m pytest -q tests/test_arc24_cemics_author_accounting.py
    python -m residual_pathways arc24-cemics-author-accounting

Full original line-specific evidence, a complete source-identity caveat and the research next gate are in [ARC24-03 original author carbon flow review](docs/arc24_03_physical_carbon_flow_semantic_review_20261024.md). This does NOT certify anthropogenic additionality, lifecycle net negative emissions, source precision or disjoint physical CDR; independent I3=0.

##### CEMICS author CDR2050 worksheet run: regrowth field-name preprocessing mismatch identified

Actual 2026-10-24 user run of `arc24-cemics-author-accounting` passed **8/8 synthetic tests** and checked the original MIF and World sources. At 2050, source matched Net CO2 (positive), AFOLU (positive), `Carbon Sequestration|Land Use` (positive), biomass CCS (positive), fossil CCS (positive), EW (zero) and DAC (zero). It **did not compute author `CDRtotal` or `CO2pos`**, because original Rmd selector `Emissions|CO2|Land|Land-use Change|Regrowth` was not found under that exact raw field name in the author's MIF. Conversely, separately reported `Gross Fossil Fuels and Industry` is present in the author's archive but **absent from AR6 World under exact name**. Neither absent variable should be silently imputed or equated with land aggregate.

Crucially, the original Rmd has an upstream `data <- deletePlus(data)` transformation (lines 144–145), and public MAgPIE reporting documentation may mark hierarchy branches as `|+|` or `|++|` (e.g. `Emissions|CO2|Land|Land-use Change|+|Regrowth`). **That specific raw-name hypothesis is not yet confirmed in the historical 2021 archive**. A new checksum-locked `arc24-cemics-field-lineage` tool inspects only original Regrowth and gross/land variable *names*, unit presence and hierarchical spelling candidates in author/AR6 source without exposing numeric observations or deriving a new accounting ledger. New tests and real scan remain pending.

    python -m pytest -q tests/test_arc24_cemics_field_lineage.py
    python -m residual_pathways arc24-cemics-field-lineage

See [ARC24-03 scientific source formula and regrowth name diagnosis](docs/arc24_03_physical_carbon_flow_semantic_review_20261024.md). Independent gross/atmospheric CDR I3 remains 0.

##### Real CEMICS raw Regrowth source located; 2021 deletePlus preprocessing verified

On 24 October 2026 the author ran the source-locked `arc24-cemics-field-lineage` (7/7 old synthetic tests passed): original Zenodo MIF for the ARC24-03-corresponding `noCDR` case has **exactly one** raw `Emissions|CO2|Land|Land-use Change|+|Regrowth` candidate, absent from AR6 World both with and without the hierarchy marker. This explains why the preceding postprocessed-Rmd selector `...|Land-use Change|Regrowth` had failed. Gross Fossil Fuels and Industry is similarly present in author's source with a single `Mt CO2/yr` record but **absent from the AR6 release**. Land Use sequestration is present in both exports but **is NOT the regrowth variable**.

The [2021 REMIND `deletePlus` implementation](https://rdrr.io/github/pik-piam/remind/src/R/deletePlus.R) directly removes standalone `+|`/`++|` variable hierarchy markers, corroborating the original Strefler Rmd line 145 `data <- deletePlus(data)`. The field-lineage CLI had a harmless **reporting-only `KeyError`** because it printed `hierarchy_marker_candidate_count` rather than the actual JSON field `marker_candidate_count`; its JSON was valid and the print key has now been fixed with a CLI regression test.

**Updated source-author study-only computation:** `arc24-cemics-author-accounting` can now use that **uniquely Rmd-deletePlus-mapped author-only raw regrowth stream** to calculate the original CDRtotal and CO2pos study definitions at 2050, while keeping source-verified AR6/author matching for net CO2, EW, biomass CCS and DAC and permitting only an explicitly named **author-only** Gross Fossil Fuels/Industry comparison. Original scenario numbers remain local; public output contains only signs, variable units, provenance and coarse gap bands. The new patch and regression tests are **committed but not yet locally executed**. No physical gross or durable atmospheric CDR I3 is claimed.

    python -m pytest -q tests/test_arc24_cemics_field_lineage.py tests/test_arc24_cemics_author_accounting.py
    python -m residual_pathways arc24-cemics-field-lineage
    python -m residual_pathways arc24-cemics-author-accounting

Source-specific evidence and interpretation boundary: [ARC24-03 original author carbon accounting](docs/arc24_03_physical_carbon_flow_semantic_review_20261024.md).

##### Actual original-author 2050 CDR formula reproduced: source-complete operational accounting; physical I3 remains zero

**User-run 24 Oct 2026 outcome:** field-lineage and original author accounting commands successfully completed with **20/20 synthetic regression tests passing**. MD5-verified original Strefler CEMICS author data + World v1.1 SHA source locks establish ARC24-03 2050 `CO2tot` positive, original unreported-in-AR6 plus-marked Regrowth flux negative (hence author's `CDRaff` positive), Biomass CCS positive, DAC zero, Enhanced Weathering zero. The explicit Rmd formula `CDRtotal=-Regrowth+EW+BECCS+DAC` now **computes successfully** and gives a positive operational CDR total. `CO2pos=CO2tot+CDRtotal` also computes successfully, positive.

The separately reported author-only `Emissions|CO2|Gross Fossil Fuels and Industry` is **positive but below derived `CO2pos`** by a nonzero difference of **≥10% of max(1, |CO2pos|, |gross_FI|)**. This is a **different-scope comparison, not a required carbon balance or error**. The author-only gross fossil/industry and signed Regrowth values are absent from the original AR6 World export under their raw/postprocessed names. `Carbon Sequestration|Land Use` is separately present in both sources and was **not substituted** for regrowth; fossil CCS positive but not counted as author study CDR.

The operational calculation's actual provenance and new >10% scope-difference finding are recorded in [original author carbon-flow source review §10](docs/arc24_03_physical_carbon_flow_semantic_review_20261024.md). No additional pseudo-reconciliation is warranted without original model-specific gross sector and signed net land accounting definitions. **I3=0; no certified physically complete/exclusive positive emissions or net durable atmospheric removal partition.**

##### CEMICS land/gross inventory expanded after overly narrow original two-name grep

The 2026-10-24 user's latest `context_name_inventory` output showed only original author `Emissions|CO2|Gross Fossil Fuels and Industry` and `Emissions|CO2|Land|Land-use Change|+|Regrowth` (both absent in AR6 World). **This does not prove those are the only original land/gross emissions components.** The initial internal context index only selected names containing `regrowth`, `gross fossil fuels`, or `land-use change`, and the PowerShell query filtered that small subset further. No other variable family had been inventoried.

The existing checksum-locked `arc24-cemics-field-lineage` command now additionally inventories actual `Emissions|CO2|Land`, gross CO2, fossil/industry, AFOLU/Other, land sequestration, broader forest-related emissions and CDR technology original variable-name families across the authors' MD5-verified MIF and the AR6 World v1.1 registered World scenario. Reports only names, original units, per-variable record counts and year-2050 presence, with a 180-name/per-group truncation flag. These are **overlapping code-defined name search buckets, not summed disjoint physical categories**. Expanded regression tests are committed but await real local execution.

    python -m pytest -q tests/test_arc24_cemics_field_lineage.py
    python -m residual_pathways arc24-cemics-field-lineage

Inspect the `expanded_emissions_family_inventory` object in `results/ar6-canonical-gate/arc24_cemics_field_lineage_public.json`. The [source-specific CEMICS carbon-flow review](docs/arc24_03_physical_carbon_flow_semantic_review_20261024.md) explains why the two-name grep is insufficient and why original reporting-code semantics remain required. Independently validated I3 is still **0**.

##### CEMICS original World land-emissions reporting families audited (actual 11-test run)

The author ran the expanded original source name audit on 24 Oct 2026: **11/11 synthetic regression tests passed**, real source-matched scan succeeded, and none of the name-family groups was truncated. Author-only `Emissions|CO2|Land|Land-use Change|+|Regrowth` was the **one** `Emissions|CO2|Land` export field; author-only `Emissions|CO2|Gross Fossil Fuels and Industry` was the **one** named gross-CO2 export field. The original author and AR6 share the net energy/industry, industry demand and AFOLU fields. AR6-only `Emissions|CO2|Other` is **not an observed original author MIF term**, and cannot be imputed zero. Critically, **both author and AR6 have `Carbon Sequestration|Land Use` AND `Carbon Sequestration|Land Use|Afforestation`**, separately from the original author-only signed Regrowth flux. These are source-export name findings; they do not exhaust underlying positive gross land emissions or establish carbon-flow disjointness.

Next bounded provenance test, now coded but NOT YET locally run: `arc24-cemics-field-lineage` includes `source_land_relationship_fingerprint` to contrast original **negative of signed Regrowth vs Land Use|Afforestation vs Land Use aggregate** over the nine tested years. It reports equality/mismatch counts, units, original source signs and absent years **without raw emissions numbers**, and retains `verified_i3=0` regardless of result. Matching a published source series does NOT prove physically additional or durable carbon removal.

    python -m pytest -q tests/test_arc24_cemics_field_lineage.py
    python -m residual_pathways arc24-cemics-field-lineage

Review the `source_land_relationship_fingerprint` object in the public JSON, and consult [ARC24-03 source flow review §§12–13](docs/arc24_03_physical_carbon_flow_semantic_review_20261024.md).
