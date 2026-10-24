# AR6 coverage-only candidate — publication readiness audit

**Review date:** 24 October 2026. **Decision:** `HOLD_PUBLIC_ARTIFACT`. This records terminal/browser results reported by the local author, public license sources, and repository contract checks; it is **not** an independent inspection of the author's private source files or a publisher attestation.

## Source- and contract-bounded findings

| Gate | Observation | State |
| --- | --- | --- |
| Matching climate-vetted `Model + Scenario` cohort | Author's local `cohort-robustness` run reported 1,202 eligible metadata records and 1,202 World matches | AUTHOR_REPORTED_LOCAL_PASS |
| Four-year reporting matrix | C1–C8 × 2030/2050/2070/2100 × 11 exact-name variable labels = 352 records | AUTHOR_REPORTED_LOCAL_PASS |
| SHA-256 artifact | Locally generated `atlas/data/coverage_release.json` and separately recomputed SHA-256: `489a07276556fdb63774297fbb79fe78ed04ffec831ce05a22d4a338629168ba` | AUTHOR_REPORTED_LOCAL_PASS; **candidate, not tagged** |
| Metadata workbook comparison | Two workbooks share 2,304 matching `meta` identities and 1,202 matching climate-vetted identities; 0 shared identity-record differences and 0 identities unique to either workbook. Positional cell differences: 106,388 and 88,784 respectively; remaining sheets also differ at 40 coordinates total. | IDENTITY_RECORD_EQUIVALENT; OTHER_SHEETS_UNRESOLVED |
| Dashboard | Author reports all six browser acceptance checks passed on a localhost HTTP server | AUTHOR_REPORTED_LOCAL_PASS; **not independent automated browser QA** |
| Independent publisher authentication | Original-named source fingerprints and a stated IIASA-download route are recorded; upstream download receipt/digest not independently verified | OPEN |
| Scientific physical CDR/gross accounting | Only exact-variable reporting presence established. No exhaustive nonoverlapping carbon partition or independent I3 review. | REVIEW_PENDING; I3_VERIFIED=0 |
| Cross-repository empirical contract | Receiver is implemented and synthetic tests exist; actual local empirical JSON has not yet been accepted by PathwaysHub in a reported transcript | OPEN |
| Public permission and attribution | Aggregates are distinct from original AR6 rows; required attribution and source license citation documented below. Exact final public artifact, categories with small counts, and rights still merit human review | REVIEW_REQUIRED |

## Source fingerprints — locally reported, not official publisher checksums

- World v1.1 CSV: `4cf39b6b0d968e25ed389318acb1674f92146f977e9db4bfb7970f048ff73977` (361,767,203 bytes).
- Author's original-named metadata XLSX: `fd1bc32db8463769e18f0560ced603a49598c12e1abfa06787ff763c55f06716`.
- Earlier third-party metadata XLSX: `7d22453bdda52e95cea4df46d362018951dd7114e62f01f5bcea65d6e24a7790`.

The differing workbook hashes and positional counts do **not** imply changed `Model + Scenario` metadata records. The unjoined non-cohort sheets have not been semantically reconciled. This comparison does not prove either workbook's publisher origin.

## Attribution and rights review

The **AR6-specific** [license legal code](https://data.ene.iiasa.ac.at/ar6/static/License/Legal.html) is adapted from CC BY 4.0, **not identical to an unrestricted CC BY 4.0 grant**. It permits adapted material including scientific analyses, tables, and visualizations, but restricts sharing a substantial part of the original database. It requires attribution, identification of changes, a link to original material, and a reference to the actual license; it forbids implying IIASA/IPCC endorsement.

Recommended source citation: **Byers, E., Krey, V., Kriegler, E., Riahi, K., Schaeffer, R., et al. (2022), AR6 Scenarios Database, version 1.1, Integrated Assessment Modeling Consortium and International Institute for Applied Systems Analysis, DOI [10.5281/zenodo.7197970](https://doi.org/10.5281/zenodo.7197970).** The [AR6 About page](https://data.ene.iiasa.ac.at/ar6/static/About.html) gives the recommended detailed author list, version/citation guidance and contributing-model credit.

The author's output is an *independently derived aggregate reporting-presence analysis* (World, exact source variable names, climate-vetted C1–C8 categories, four years), and must not be described as the official database, as an official IIASA/IPCC analysis, as a population probability, or as a physical gross/CDR ledger.

**Before public commit:** inspect the exact outgoing files for original source rows, model/scenario identities, licensing or small-cell disclosure problems; confirm no private logs or restricted source data are staged. MIT applies to original project code, not to upstream AR6 scenario data.

## Empirical cross-repository handoff — pinned candidate test

The PathwaysHub [coverage-only receiver](https://github.com/abhijith-sivaprasadan/pathways-hub/blob/main/src/pathways_hub/coverage_contract.py) requires an **out-of-band expected SHA-256**. Recomputing the expected SHA from the untrusted candidate passed to the receiver checks only self-consistency and is not a provenance check.

From a PathwaysHub Python environment, use the actual candidate file and *separately* pinned, previously recorded candidate digest:

~~~powershell
$source='E:\New folder (2)\MissionJob\residual-pathways\atlas\data\coverage_release.json'
$sidecar="$source.sha256"
$pin='489a07276556fdb63774297fbb79fe78ed04ffec831ce05a22d4a338629168ba'
python -m pathways_hub.coverage_contract --artifact $source --sha-file $sidecar --expected-sha256 $pin --output outputs/coverage-contract/status.json
if ($LASTEXITCODE -ne 0) { throw 'PathwaysHub empirical intake rejected candidate' }
Get-Content outputs/coverage-contract/status.json
~~~

A successful run must report `ACCEPTED_COVERAGE_ONLY_UNREVIEWED`, `NOT_ASSESSED`, 0 verified I3. The out-of-band pin in this example is **author-reported**, not an immutable publisher digest. For a genuine release, the pinned expected hash must come from a reviewed immutable upstream Git tag/release and match the exact artifact bytes.

## Publication go/no-go

**HOLD_PUBLIC_ARTIFACT** until all these are documented: (1) exact aggregate artifact and small-cell/licensing review; (2) AR6 attribution and modification notice present in UI and repository; (3) empirical PathwaysHub acceptance and tamper-rejection output; (4) frozen version/tag with trusted digest; (5) post-deploy public SHA and browser check. Publisher authentication and independent I3 scientific review can remain openly incomplete **only when declared explicitly**, without presenting coverage as physically verified carbon accounting.

The old 2050 public snapshot is a different artifact. Identical four-year presence counts do not imply constant emissions levels; exact model-label balancing is **not** model-family weighting.
