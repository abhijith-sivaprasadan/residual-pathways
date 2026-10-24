# Residual Pathways Atlas

An independently authored source-evidence-first interactive web dashboard inspired by the Finnish Grid Atlas product approach: fast navigation, rich comparisons, original-source traceability and visible uncertainty. It does not reuse Finnish Grid Atlas artwork, markup or data, and is not operated or endorsed by IIASA/IPCC.

## Live site and code

- Vercel: https://residual-pathways-atlas.vercel.app/
- Static web app: [index.html](index.html), [styles.css](styles.css), [app.js](app.js)
- Bundled source-backed public evidence: [data/atlas.json](data/atlas.json)
- Model review: [ARC24-03](../docs/arc24_03_physical_carbon_flow_semantic_review_20261024.md)
- Companion ops app: https://github.com/abhijith-sivaprasadan/pathways-hub

The Vercel project is linked to the source GitHub repository with Root Directory = atlas and no framework build. Its public files are ordinary static HTML/CSS/JS and the JSON snapshot.

## First release: implemented views

| View | Source scope | Limit |
| --- | --- | --- |
| Overview | Climate-vetted World reporting counts | 1,202 scenarios, 422 DAC-reporting, 330 six-variable-co-reporting, **0 verified I3** |
| Coverage | Eight C1–C8 climate categories, 2050 | Interactively switch reporting sets and count/share, CSV export |
| Models | 18 source-reported historical CD-LINKS tutorial net-CO2 values | Three model versions; distinct from AR6 vetted cohort; **not gross CO2** |
| Non-CO2 | N2O GWP100 metric reference pilot | Source masses fixed; original 273 vs corrected 267 is a method change |
| Modelling | Three author-reported locally solved Westeros cases | Educational model; not an AR6 scenario or independently replicated solver log |
| Innovation gaps | Twelve citation-linked research hypotheses; searchable by topic and sector | Unreviewed candidate topics, no causal emission shares or certified implementation impacts |
| Operations | PathwaysHub 25-item author-reported milestone snapshot | Simulation-only is not actual international coordination |
| Methods | Scientific protocol and CEMICS original source audit | Source-name availability is not an exhaustive, physically disjoint ledger |

The dashboard includes none of the local original AR6 World source rows, privately held original CEMICS carbon observations, GAMS/solver license files, user credentials or original private model databases.

## Rebuild from the repository's public derived source records

Run from the ResidualPathways repository root:

    python atlas/build_data.py --check
    python atlas/build_data.py
    python -m http.server 8765 --directory atlas

Open http://localhost:8765/. Serving over HTTP permits JavaScript to fetch the local JSON.

Refresh the public milestone snapshot, when you have a local PathwaysHub checkout, with:

    python atlas/build_data.py --hub "..\pathways-hub\protocols\workstream_v3.json"

Review the generated public JSON changes before committing. This optional read does not attest external human review or real partner participation.

## Release checks

The .github/workflows/atlas-pages.yml workflow checks JavaScript syntax, re-generates the public bundle for a deterministic equality check, verifies reporting denominators and claim boundaries, and stores the validated static files as a GitHub Actions artifact. Production publishing is handled through the separate Git-connected Vercel deployment; the repository has not enabled GitHub Pages.

The source-status banner distinguishes the earlier publicly redistributed teaching-labelled AR6 input from direct publisher provenance. The author's downloaded original-named World CSV matched the earlier source SHA. The workbook identity-joined `Model + Scenario` records matched in both 2,304-row and 1,202-row metadata sheets, although cell-coordinate differences and other non-cohort sheets remain unresolved. Publisher acquisition receipt/authentication is not independently verified. Co-reporting does not establish a complete source account.

## Scientific stop rules

1. Do not infer positive gross emissions as max(net, 0), or derive gross from incomplete net+CDR terms.
2. Fossil CO2 capture/storage is not atmospheric CDR simply because an IAMC name contains CCS.
3. CEMICS original study Regrowth CDR differs more than 10% from both AR6 Land Use and Land Use|Afforestation for all nine tested years. Do not substitute.
4. Two reported land-use sequestration names are numerically identical in the same tested scope; do not add them together as independent removals.
5. Zero currently verified I3 records is not proof that no real scenario could qualify after semantic review.
6. A GWP100 conversion change in N2O CO2e is not a physical emissions decline.

## Published four-year coverage-only candidate — 24 October 2026

The C1–C8, 2030/2050/2070/2100 exact-source-variable reporting-presence aggregate is [version-tagged](https://github.com/abhijith-sivaprasadan/residual-pathways/tree/ar6-coverage-only-v0.1.0-candidate) at commit `e64156b7429441836d1fa3b1879d40d9aa814bb0`, with SHA-256 `489a07276556fdb63774297fbb79fe78ed04ffec831ce05a22d4a338629168ba`. The artifact contains 352 aggregate rows (8 climate categories × 4 years × 11 variables), drawn from a locally matched cohort of 1,202 scenarios. The author's Vercel HTTP download matched the tagged SHA; Vercel separately reported the production deployment as READY for that commit. The independent PathwaysHub intake of the real candidate returned `ACCEPTED_COVERAGE_ONLY_UNREVIEWED`; a wrong pin was rejected. No original AR6 source rows or model–scenario identities are published as part of this candidate.

This is an **author-reviewed public reporting-coverage candidate**, not publisher-authenticated source provenance or independently reviewed physical gross/CDR accounting. `REVIEW_PENDING`, `i3_verified=0`, and `physical_accounting=NOT_ESTABLISHED` remain explicit. The six low missingness counts repeated across years were documented in the [audit](../docs/ar6_coverage_publication_audit_20261024.md). The annotated Git tag exists; a separate GitHub Releases entry has not been created, and tag mutation requires repository protections to prevent it.

## Planned follow-on releases

1. Evolve the published 2030–2100 exact-name coverage explorer with explicit missingness and robust model-**family** weighting, distinct from the existing exact-name model-label-balanced view.
2. Independently authenticate publisher provenance, reconcile remaining non-cohort metadata differences, and review the distinction between scientific I0 and REVIEW_PENDING.
3. Protect the existing annotated release tag, and make later releases reproducible with recorded upstream receipts and public acceptance checks.
4. Publish reviewed model-specific semantic explainers, a working paper and a policy brief without fabricating gross or atmospheric-removal totals.

This is a functional v1 atlas, not yet a complete final research paper or independently certified gross/CDR decomposition.

## AR6 attribution and provenance

Coverage graphics and tables are independently derived from the **AR6 Scenarios Database v1.1**: Byers, E., Krey, V., Kriegler, E., Riahi, K., Schaeffer, R., et al. (2022), Integrated Assessment Modeling Consortium & IIASA, [DOI 10.5281/zenodo.7197970](https://doi.org/10.5281/zenodo.7197970). Source copyright remains with contributing institutions and modelling teams. This project changes the source into category-level reporting-presence counts and fractions, not original scenario observations. The [AR6-specific adapted CC BY 4.0 legal code](https://data.ene.iiasa.ac.at/ar6/static/License/Legal.html) restricts substantial raw-data redistribution; it is **not** an unrestricted CC BY 4.0 source data license. Independent project, no IIASA/IPCC endorsement. Author-reported source hashes are not independent publisher authentication. See the [publication readiness audit](../docs/ar6_coverage_publication_audit_20261024.md).

## Optional 2030–2100 coverage bundle

The four-year exact-variable reporting-presence explorer is now active whenever the browser fetches both the [published artifact](data/coverage_release.json) and its [SHA-256 sidecar](data/coverage_release.json.sha256), verifies the checksum and confirms the scientific scope. This does not reinterpret `REVIEW_PENDING` as I0 or grant I3 status. See the [source/runbook](../docs/ar6_coverage_release_handoff.md) and [release audit](../docs/ar6_coverage_publication_audit_20261024.md).
