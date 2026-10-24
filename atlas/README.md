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

The source-status banner deliberately distinguishes the initial publicly redistributed teaching-labelled AR6 input from direct publisher provenance. The user's independently obtained official-named World CSV was byte-identical at its SHA, but publisher-side acquisition receipt and the semantic equivalence of metadata workbooks are not yet checked. Co-reporting does not establish a complete source account.

## Scientific stop rules

1. Do not infer positive gross emissions as max(net, 0), or derive gross from incomplete net+CDR terms.
2. Fossil CO2 capture/storage is not atmospheric CDR simply because an IAMC name contains CCS.
3. CEMICS original study Regrowth CDR differs more than 10% from both AR6 Land Use and Land Use|Afforestation for all nine tested years. Do not substitute.
4. Two reported land-use sequestration names are numerically identical in the same tested scope; do not add them together as independent removals.
5. Zero currently verified I3 records is not proof that no real scenario could qualify after semantic review.
6. A GWP100 conversion change in N2O CO2e is not a physical emissions decline.

## Planned follow-on releases

1. Multi-year vetted coverage explorer (2030/2050/2070/2100) with model-family weighting, denominator disclosure and explicit non-coverage.
2. Reconciled source-provenance and metadata-workbook concordance audit; I0 data insufficiency and scientific REVIEW_PENDING as distinct fields.
3. Public, immutable coverage-only research release artifact accepted through PathwaysHub's exact-hash scientific contract.
4. Reviewed model-specific semantic explainers and fully versioned working paper / policy brief, without fabricating gross or removal totals.

This is a functional v1 atlas, not yet a complete final research paper or independently certified gross/CDR decomposition.

## Optional 2030–2100 coverage bundle

The 2026-10-24 release-gate branch adds a separate four-year, exact-variable presence explorer. It displays only a SHA-256-checked public coverage-only artifact, and remains unavailable until the author's local original-named v1.1 dataset audit produces and clears that artifact. It does not reinterpret unreviewed records as I0 or grant I3 status. See [local canonical release runbook](../docs/ar6_coverage_release_handoff.md).
