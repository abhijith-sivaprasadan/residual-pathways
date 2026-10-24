# AR6 four-year research program — evidence and execution (24 October 2026)

**Status:** published coverage-only candidate; source-derived research manuscript and figures generator implemented. Source provenance and case-specific physical accounting remain open, not silently closed.

**Frozen source:** [tag `ar6-coverage-only-v0.1.0-candidate`](https://github.com/abhijith-sivaprasadan/residual-pathways/tree/ar6-coverage-only-v0.1.0-candidate), commit `e64156b7429441836d1fa3b1879d40d9aa814bb0`, SHA-256 `489a07276556fdb63774297fbb79fe78ed04ffec831ce05a22d4a338629168ba`. No source rows are committed.

## Track 1 — Descriptive research findings and reproducible figures

Implemented: `src/residual_pathways/coverage_findings.py`, `tests/test_coverage_findings.py`.

From the repository root:

~~~powershell
$py = '.\.venv-messageix\Scripts\python.exe'
& $py -m residual_pathways.coverage_findings --check-input atlas/data/coverage_release.json --output-dir docs/research/coverage_20261024
if ($LASTEXITCODE -ne 0) { throw 'Coverage manuscript/figures build failed' }
~~~

This **offline, standard-library-only** command checks exact SHA-256 and scientific schema before regenerating:

- `docs/research/coverage_20261024/ar6_reporting_coverage_results.md` — formal descriptive methodology, category comparison, reporting counts, year invariance, exact-label weighting sensitivity and limitations;
- `docs/research/coverage_20261024/ar6_presence_table.csv` — full 352-row category/year/variable count table, no scenario names, no original emissions quantities;
- `docs/research/coverage_20261024/figures/ar6_world_variable_coverage.svg` — 11-variable 2050 ensemble counts;
- `docs/research/coverage_20261024/figures/ar6_category_coverage_heatmap.svg` — seven focus variables across eight categories;
- `docs/research/coverage_20261024/figures/ar6_weighting_contrast.svg` — scenario versus *exact model-label*-weighted land-sequestration coverage.

Source-grounded findings: 1,202/1,202 net CO₂, CH₄ and N₂O; biomass CCS 1,145/1,202 (95.3%); fossil CCS 1,014 (84.4%); land-use sequestration 783 (65.1%); direct air capture 422 (35.1%); enhanced weathering 190 (15.8%). All four chosen years have identical *reporting-presence counts*, **not** necessarily identical numerical trajectories. DAC C6 42/97 (43.3%) versus C7 32/164 (19.5%); enhanced weathering C1 32/97 (33.0%) versus C4 6/159 (3.8%). These are **not** causal cross-category differences or model-family-independent frequencies.

A separate GitHub workflow builds the source-pinned paper and figures as a downloadable CI artifact; only the frozen aggregate JSON is used. Source citation: [Byers et al., AR6 v1.1](https://doi.org/10.5281/zenodo.7197970); [IIASA recommended citation](https://data.ene.iiasa.ac.at/ar6/static/About.html); [adapted dataset license](https://data.ene.iiasa.ac.at/ar6/static/License/Legal.html).

## Track 2 — Non-cohort metadata and official acquisition provenance

Official source references independently checked against [IIASA AR6 Explorer](https://iiasa.ac.at/models-tools-data/ar6-scenario-explorer-and-database) and [Zenodo v1.1](https://zenodo.org/records/7197970). The Zenodo record **restricts archive file access and redirects original downloads to the IIASA Explorer**, so it does not publish an independent official SHA-256 for these locally held binaries. The original `World_v1.1.csv` and metadata XLSX were provided on the author's computer; independent verification of the user's specific IIASA file-download event is not possible from catalogue pages or a matching local hash.

**Actual local worksheet classifier completed 24 October 2026:** all 2,304 identity-joined `meta` and 1,202 climate-vetted scenario metadata records agree exactly in both workbooks; 106,388 and 88,784 differing *cell coordinates* are due to positional layout, not changed joined values. `Illustrative_Pathways` has 39 position-only changes with the same normalized row multiset, `categories_indicators_doc` is identical, and **only `README` still has one genuinely different normalized cell**. The follow-on `metadata_readme_private` tool isolates that cell for strictly local human inspection and refuses changed source file hashes. See the [actual scientific audit results](ar6_20261024_local_audit_results.md). This evidence does not establish official publisher download provenance.

Run on the author's two already held workbooks, entirely offline (source rows and values stay private):

~~~powershell
$py = '.\.venv-messageix\Scripts\python.exe'
& $py -m residual_pathways.metadata_sheet_review `
  --official 'data/ar6-private/AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx' `
  --earlier 'data/ar6-private/earlier_thirdparty_metadata.xlsx' `
  --output 'results/ar6-canonical-gate/metadata_sheet_review_local.json'
if ($LASTEXITCODE -ne 0) { throw 'Worksheet content review failed' }
~~~

Only sheet-level counts/classifications are emitted: **no workbook values, scenario names, source models, per-row hashes or cell-level source contents**.

For acquisition provenance, `source_provenance_receipt.py` checks both locally held file bytes and writes an ignored private evidence manifest. **It does not certify origin** even if the author supplies an HTTPS link on an IIASA hostname:

~~~powershell
& $py -m residual_pathways.source_provenance_receipt `
  --world 'data/ar6-private/AR6_Scenarios_Database_World_v1.1.csv' `
  --metadata 'data/ar6-private/AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx' `
  --output 'data/ar6-private/acquisition_evidence_inventory.json'
~~~

If an actual original downloaded-link, official HTTP response/log or provider delivery email is available, preserve it **only** within `data/ar6-private` and provide a private JSON note containing the exact keys `download_origin_url`, `observed_utc`, `evidence_type`, `author_notes`. Then repeat with `--receipt data/ar6-private/download_receipt.json`. Never publish signed URL query strings, confirmation links, personal email metadata, passwords or session cookies. The redacted manifest still reads `publisher_origin_authentication=NOT_ESTABLISHED` until there is trustworthy publisher-side or independently corroborating acquisition evidence.

**Do not confuse account registration with receipt of either specific AR6 binary.** Without a publisher-authenticated content digest, distinct independent acquisition and byte comparison plus logged origin may strengthen confidence, but neither alone constitutes a publisher signature.

## Track 3 — Real model/scenario accounting identifiability

The original canonical-named selection has 24 coded ARC24 cases (three purposively selected in each C1–C8 category), seven with all six candidate variables and 19 with a computable arithmetic preflight. No case has completed a scientifically defensible I1/I2/I3 review; none is **automatically I0** due to review backlog. See the [model/source original evidence docket](../arc24_gross_cdr_source_review_dossier_20261024.md), [source crosswalk](../arc24_source_provenance_and_semantic_triage_20261024.md) and the [physical accounting protocol](../accounting_protocol.md).

Run the private evidence-docket preparation:

~~~powershell
& $py -m residual_pathways.arc24_review_docket `
  --packet 'data/ar6-private/canonical_selected24_packet.json' `
  --private-docket 'data/ar6-private/arc24_review_docket.json' `
  --public-queue 'results/ar6-canonical-gate/arc24_review_queue_public.json'
if ($LASTEXITCODE -ne 0) { throw 'ARC24 scientific docket preparation failed' }
~~~

This produces **11 unfilled evidence gates per case**, plus source-document leads for documented model labels. No private raw observations are copied to the docket. The public queue has **only coded IDs**, categories and pending statuses. Filling a checklist is a **human primary-source-review activity**, not something an automated script may infer from variable presence.

| Priority | Exact model label | Primary documentation / task | Current review conclusion |
| --- | --- | --- | --- |
| ARC24-03 | REMIND-MAgPIE 2.1-4.2 | Reconcile exact CEMICS SSP1 minCDR original source series to AR6, identify gross positive sectors vs regrowth/BECCS/DACCS/EW; **do not substitute main-text SSP2 figures**. [Study](https://doi.org/10.1088/1748-9326/ac0a11); [authors' archive](https://zenodo.org/records/5103024). | **NOT_DETERMINED**: original model/source-ledger crosswalk incomplete |
| ARC24-06, -09, -12, -21 | POLES ENGAGE | Determine if CO₂ Other is a **computed residual** rather than independent positive emissions, map linked GLOBIOM land flow and capture accounting. [POLES documentation](https://www.iamcdocumentation.eu/Emissions_-_POLES); [ENGAGE analysis](https://data.ece.iiasa.ac.at/engage-netzero-analysis/notebooks/1_categorization.html). | **NOT_DETERMINED**: no case-specific verified disjoint gross/CDR ledger |
| ARC24-15 | COFFEE 1.1 | Match specific AR6 configuration against more general COFFEE-TEA literature; avoid equating fossil storage with atmospheric CDR. [COFFEE emissions docs](https://www.iamcdocumentation.eu/Emissions_-_COFFEE-TEA). | **NOT_DETERMINED** |
| ARC24-18 | WITCH 5.0 | Validate 2021/2022 configuration and GLOBIOM linked AFOLU/CDR source definitions. [WITCH documentation](https://doc.witchmodel.org/model-scope.html). | **NOT_DETERMINED** |
| ARC24-24 | C8 source-selected missing-variable negative control | Establish exact absent or source-unreported terms; do not mistake blank as a zero or physical prohibition. | **NOT_DETERMINED** |

11 evidence gates: (1) original run/model/version; (2) World/2050 units, sign and scope; (3) gross positive processes; (4) net/gross AFOLU land baseline; (5) BECCS biogenic uptake and nonoverlap; (6) fossil CCS exclusion; (7) DAC/EW durable atmospheric removal; (8) exhaustiveness and disjointness; (9) **source-documented** numerical precision; (10) dual numerical/physical reconciliations; (11) independent second reviewer. A correct arithmetic result *cannot* substitute for physical source semantics.

## Reviewed source evidence for the two priority cases

The source-by-source verdict is now documented in [ARC24-03 / ARC24-06 primary accounting review](arc24_03_06_source_accounting_review_20261024.md). The authors' archived CEMICS `noCDR` series and AR6 `minCDR` World series already have **4,653/4,653 exact same-unit original-source decimal matches**, with crossed controls distinguishing `fullCDR`; this establishes strong *numerical source-series correspondence* for the tested scope, **not** a complete physical carbon ledger. The Strefler original Rmd explicitly defines four operational CDR categories (signed regrowth, enhanced weathering, biomass CCS and direct air capture) and `CO2pos = net + CDRtotal`; its output is derived by construction, not proof of independently exhaustive gross positives.

For ARC24-06 the original ENGAGE notebook's `Other` is a **computed postprocessing residual** in a separate v2.0 snapshot, not known to be an independently measured POLES source stream or directly mapped to the AR6 v1.1 `Other`. A new optional original-World v2.0 source bridge [`arc24_engage_v2_probe.py`](../../src/residual_pathways/arc24_engage_v2_probe.py) validates exact identity and units with the original AR6 file, otherwise fails without claiming an alias. The user's v2.0 dataset is not yet present in this conversation; execution requires a licensed original v2.0 download and leaves I3 = 0.

## Explicit stop rules

1. No physical gross emissions or atmospheric removals are reconstructed from the aggregate release. The finished coverage paper is a reporting-availability result, not a complete carbon mass balance.
2. Zero independently verified I3 means **no reviewed I3 finding**, not `I0=1,202` or `no I3 is possible`.
3. Neither an exact model-label balancing scheme nor the 24-case purposive sample estimates independent model-family prevalence.
4. Keep all original AR6 and CEMICS source rows, private review packets and acquisition tokens out of Git and CI. Do not publish private scenario-level signed emissions or reviewer notes.
5. Register any future genuine I0/I1/I2 decisions with cited model/version-specific primary documents; grant I3 only after exhaustive nonoverlapping physical flow reconciliation and independent reviewer attestation.
