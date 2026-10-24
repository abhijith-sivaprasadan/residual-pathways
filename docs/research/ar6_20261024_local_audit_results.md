# AR6 research: first local audit outcomes and model-specific evidence interpretation

**Date:** 24 October 2026. **Evidence basis:** author's Windows PowerShell transcript from the real v1.1 World/metadata files, synthetic code tests, the immutable published reporting-coverage bundle, and cited public model documentation. Original World rows, model/scenario observations, private worksheets and original private reviewer packet are not published.

## 1. Completed reproducible results build

- All **12 newly introduced** research tests passed locally; same research paper/figure tests also passed in [GitHub Actions](https://github.com/abhijith-sivaprasadan/residual-pathways/actions/workflows/ar6-research-findings.yml).
- Real frozen 1,202-scenario / 352-record source-pinned manuscript and table generated locally:
  `docs/research/coverage_20261024/ar6_reporting_coverage_results.md`,
  `docs/research/coverage_20261024/ar6_presence_table.csv`, and three SVG figures under `figures/`. CI also produced these as a workflow artifact.
- Authors' observed outputs here are **derived reporting-presence statistics, not positive gross CO₂ or verified negative emissions**. The manuscript and figures were generated on the author's machine but were **not automatically committed to Git** by the generator. Human review of the five derived text/figure files should precede committing them, with no source rows.

## 2. New local metadata reconciliation result

The author's run of `residual_pathways.metadata_sheet_review` reports:

| Sheet | Positional differing normalized cells | Normalized content or identity result | Remaining blocker |
| --- | ---: | --- | --- |
| `meta` | 106,388 | **IDENTITY_JOIN_IDENTICAL_POSITIONAL_DIFFERENCES_ONLY**; same `Model + Scenario` records, no changed joined values | None identified for original per-scenario metadata values |
| `meta_Ch3vetted_withclimate` | 88,784 | **IDENTITY_JOIN_IDENTICAL_POSITIONAL_DIFFERENCES_ONLY**; same 1,202-row climate-vetted joined values | None identified for original cohort fields |
| `categories_indicators_doc` | 0 | **IDENTICAL_NORMALIZED_CELL_COORDINATES** | None |
| `Illustrative_Pathways` | 39 | **SAME_NORMALIZED_ROWS_POSITIONAL_DIFFERENCES_ONLY** | No changed normalized row content detected |
| `README` | 1 | **NON_IDENTITY_SHEET_CONTENT_DIFFERENCE_UNRESOLVED**; one normalized row differs | Inspect sole changed cell locally for documentation/license/version meaning |

The earlier `metadata_concordance_public.json` reported 2,304 shared `meta` and 1,202 shared climate-vetted `Model + Scenario` records, and **zero changed identity-joined records**. The new review independently confirms that sorted normalized row content also agrees, including the previously suspicious illustrative sheet. These findings do not establish authentic publisher acquisition or source-file authorship; they narrow the original-vs-redistributed workbook **substantive data** differences to a README note.

### Close the one remaining cell locally

The `residual_pathways.metadata_readme_private` tool takes both already-registered XLSX files, checks their exact SHA-256 digests, and writes **full original and earlier text exclusively to ignored `data/ar6-private/metadata_readme_diff_private.json`**. It prints only the changed coordinate and count. The author should read it **privately**, decide whether this is copyright/attribution, substantive version notice, typographical/formatting change, or unresolved. No cell text needs to be copied into public issue comments; no origin claims should be upgraded from this result.

~~~powershell
$py = '.\.venv-messageix\Scripts\python.exe'
& $py -m residual_pathways.metadata_readme_private `
  --official 'data/ar6-private/AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx' `
  --earlier 'data/ar6-private/earlier_thirdparty_metadata.xlsx' `
  --output 'data/ar6-private/metadata_readme_diff_private.json'
if ($LASTEXITCODE -ne 0) { throw 'README difference check failed' }
~~~

This is the **only** worksheet-level content question that the two checked workbook copies still require. Any publisher-side errata or file version updates published later must be investigated separately; workbook-to-workbook agreement is not a statement that no future errata exist.

## 3. Publisher provenance remains an independent question

The local `source_provenance_receipt` produced `publisher_origin_authentication=NOT_ESTABLISHED`, `file_download_receipt_status=NOT_PROVIDED`. Official [AR6 v1.1 Zenodo record](https://zenodo.org/records/7197970) explicitly lists the two source file names and directs source download to the IIASA AR6 Explorer; it does **not** provide an independently verified publisher content digest for the author's locally held files. A Scenario Services account-confirmation email, **if separately available**, would show account registration only and not a specific dataset download. No private account correspondence is reproduced here. The source hashes identify the actual local inputs; a saved HTTP response/browser download entry with server URL and delivery timestamp is stronger acquisition evidence but does not by itself constitute a publisher cryptographic signature.

The project can responsibly describe the source as **locally hash-checked, v1.1-named AR6 World and metadata data, with joined metadata concordance and an unverified publisher download receipt**. Leave source-authentication status open pending a corroborated portal transaction.

## 4. Scientifically grounded ARC24 review: two actionable negative gates

**Model-scenario grades remain `NOT_DETERMINED`; none is automatically I0, I1, I2 or I3.** The author's local private docket contains 24 cases, eight priority cases, and zero independently reviewed classifications.

### ARC24-03: REMIND–MAgPIE 2.1-4.2 / CEMICS SSP1 minimum-CDR

- The exact pairing appears in a separate [Climate Analytics pathway cross-reference](https://1p5ndc-pathways.climateanalytics.org/methodology), independently supporting the scenario label/model association.
- The earlier author-run four-file [Strefler et al. (2021) original archive](https://zenodo.org/records/5103024) crosswalk found **zero exact matching MIF scenario rows** and no exact case label in the original Rmd. This archive **cannot be used as a verified numerical provenance** for ARC24-03, even though the study offers relevant model-family methodology. Do not silently substitute a different SSP2 minimum-CDR case.
- The author's source sign screen reports positive signed net AFOLU and positive reported land sequestration and BECCS, with **explicitly reported zero DAC** at 2050. This does not establish a net carbon removal amount or disjoint positive-emission/removal ledger. The first task is exact SSP1 case crosswalk to a primary submission or model/team variable specification.

### ARC24-06: POLES ENGAGE / EN_NPi2020_400f

- The related, source-authored [ENGAGE netzero-analysis notebook](https://data.ece.iiasa.ac.at/engage-netzero-analysis/notebooks/1_categorization.html) explicitly **constructs CO₂ Other as a residual** of total minus AFOLU, Energy Demand, Energy Supply and Industrial Processes; a second Other branch is constructed within demand, also algebraically. The authors explicitly describe doing so to close the hierarchy.
- Therefore a close algebraic remainder in this **related ENGAGE processed dataset** is not independent physical evidence of a real positive-emitting category. It does **not** prove that the actual ARC24-06 AR6 `Emissions|CO2|Other` export used the identical transform—this mapping still needs an exact dataset/version and calculation-history comparison.
- The author's prior private AR6 evaluation found that 20/20 POLES ENGAGE year/scenario residual signs match reported Other, and all residual-minus-Other differences were below 0.001% of the largest source term; this is reproducible numerical proximity, **not** independent proof of an exhaustive physical partition.
- [IAMC variable naming guidance](https://docs.ece.iiasa.ac.at/standards/variables.html) explicitly states its pipe hierarchy is semi-hierarchical and not necessarily additive. [IAMC POLES model documentation](https://www.iamcdocumentation.eu/Emissions_-_POLES) indicates soft-linked land emissions through GLOBIOM/G4M rather than a standalone POLES land-process measurement. Exact versions and mapping are essential.

**Immediate scientific decision for both cases:** source-specific completeness/disjointness, positive gross emissions, land netting, biological capture vs durable sequestration, fossil CCS exclusion, numerical source precision and independent review are **not established**. Continue at the primary-model-documentation level, **not** by inventing balancing terms or applying arbitrary rounding tolerances.

## 5. Next accountable deliverable

1. **Project author:** privately classify the single README cell; update public provenance status **only if warranted**.
2. **Project author:** capture an authentic download-history/HTTP-response receipt if still available; keep all signed URLs and account data in `data/ar6-private`.
3. **Model evidence reviewer:** contact the relevant authors or locate version-specific original export metadata for ARC24-03 and ARC24-06. A primary document should explicitly state which processes enter each source variable, not simply repeat an IAMC label.
4. **Independent scientific reviewer:** verify physical exhaustiveness, source quantization and nonoverlap for any proposed I3 classification before scientific grading.
5. **Publication:** manually review and version the already generated manuscript/CSV/SVG outputs. They are **derived descriptive findings**, not an independently peer-reviewed research paper.

Current scientific status: `REVIEW_PENDING`, `I3_VERIFIED=0`, `PHYSICAL_ACCOUNTING=NOT_ESTABLISHED`.
