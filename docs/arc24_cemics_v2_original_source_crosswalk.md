# ARC24-03 original CEMICS v2 source crosswalk — evidence-led review

**Research date:** 2026-10-24. **Status:** primary study archive, checksum manifest and external scenario identification verified; strict local source-file comparison **implemented but not yet executed** against the author's downloaded archive. This note does not assign gross-emissions/CDR physical partition status or I3.

## 1. Provenance and scenario identification already established

- **Peer-reviewed originating paper:** Strefler et al. (2021), *Carbon dioxide removal technologies are not born equal*, Environmental Research Letters 16, 074021, DOI https://doi.org/10.1088/1748-9326/ac0a11. Studies how alternative CDR portfolios (BECCS, DACCS, afforestation/reforestation and enhanced weathering) affect emission reductions, pathways, deployment and impacts. The main-text quantitative analysis is largely SSP2; ARC24-03 is the **SSP1** variant and must not borrow the paper's SSP2 2050 numeric statements.
- **Original author research files:** Strefler et al., Zenodo **v2**, record https://zenodo.org/records/5103024, DOI 10.5281/zenodo.5103024, distributed CC BY 4.0. Authors state this release **updates names and variable categories to those submitted to the IPCC AR6 database without changing results**. The files listed on Zenodo are below.
- **Independent exact scenario reference:** Climate Analytics global pathway methodology https://1p5ndc-pathways.climateanalytics.org/methodology lists the pair **REMIND-MAgPIE 2.1-4.2**, **CEMICS_SSP1-1p5C-minCDR**. That exact pair was independently observed in the user's World v1.1 local selected ARC24-03 packet.
- **MIF file specification:** The PIK/IAMC MIF format is a semicolon-delimited IAMC-wide file with `Model`, `Scenario`, `Region`, `Variable`, `Unit` and year columns. Each line conventionally terminates in a **trailing semicolon** (https://pik-piam.r-universe.dev/mip/doc/mif.html and https://rdrr.io/github/pik-piam/rmndt/man/readMIF.html). The parser specifically handles this terminal empty token. No names or source numbers are guessed if an unfamiliar format appears.

| Original Zenodo v2 file | Archive-listed MD5 | Purpose |
| --- | --- | --- |
| `CDRoptionsAR6_complete.mif` | `efbc4f82b0163da790f370775a37cfe7` | Main author-released IAMC-wide source results (~30.9 MB) |
| `CDRoptions.Rmd` | `66923e9fbbeec5113849e2566d486c29` | Original article/appendix plotting and processing code (~100 kB) |
| `readme_zenodo.txt` | `e0d133b76db3fd3ccb95f06279197ff0` | Original authors' interpretation notes |
| `regionmappingH12.csv` | `9d59c73f814f6a0fcea89a3bbe591c0a` | Original authors' regional labels/crosswalk |

**What these findings do not establish:** The authors' archive has not yet been opened within the local project; the exact pair and global-year observation have not yet been found in its contents, and no variable-level numeric comparison between source archive and AR6 World has yet been run.

## 2. Implemented reproducible source crosswalk, without reproducing original observations

A new Windows PowerShell downloader, `scripts/fetch_cemics_v2.ps1`, fetches the four files directly from Zenodo to **data/ar6-private/cemics-v2**, validates each **publisher-listed MD5**, refuses to overwrite a pre-existing file with the wrong checksum and deletes partial downloads on failure. This path is already protected by the repository `.gitignore`.

The new `arc24-cemics-crosswalk` CLI then validates:

1. the **authors' v2 MIF checksum** and supplementary R Markdown/README checksums;
2. the already recorded SHA-256 of the original user's AR6 World v1.1 CSV and that the original ARC24-03 private packet's 2050 observations still match the source World CSV exactly;
3. exact **Model**, **Scenario**, **World** region, 2050, variable names and source units in the author MIF; a scenario-name-only match with a different model label is explicitly **not** promoted to equivalence;
4. which candidate variable names are shared, absent or unit-incompatible in the author dataset versus the AR6 release;
5. reported-decimal exact matches versus nonzero differences in coarse **relative difference bands** (not claimed source export precision), without exposing any numerical original emissions;
6. carbon-related source variable-name inventory and whether the author Rmd/README mention key concepts; these are **research leads**, not a reviewed semantic disjointness finding.

The source check is intentionally fail-closed for unfamiliar MIF layouts or mismatched source hashes. The original source data are **never committed to GitHub** and the public report contains only source fingerprints, anonymous case ID, source-variable names, units, status labels, keyword counts and coarse mismatch bands. It explicitly leaves scientific I3 false.

### Run in Windows PowerShell

    cd 'E:\New folder (2)\MissionJob\residual-pathways'
    git pull --ff-only
    & .\scripts\fetch_cemics_v2.ps1
    & .\.venv-messageix\Scripts\python.exe -m pytest -q tests/test_arc24_cemics_crosswalk.py
    & .\.venv-messageix\Scripts\python.exe -m residual_pathways arc24-cemics-crosswalk
    $x = Get-Content 'results/ar6-canonical-gate/arc24_cemics_source_crosswalk_public.json' -Raw | ConvertFrom-Json
    $x.status
    $x.archive_exact_model_scenario_row_count
    $x.archive_exact_world_variable_count
    $x.overlapping_variable_names
    $x.overlap_status_counts
    $x.selected_variable_comparisons | Select-Object variable,archive_present,archive_unit,ar6_unit,comparison_status,difference_band | Format-Table -Wrap -AutoSize

**Still pending**: actual local test results, author file download, the exact CEMICS MIF scenario record and full original model-methodology reading. DO NOT present the above as a completed source reconciliation.

## 3. Accounted and unaccounted carbon flows — the review questions

| Carbon-flow concept | Available evidence now | Specific source work needed before a physical accounting claim |
| --- | --- | --- |
| Source climate scenario identity | 2021 authors' AR6-name-aligned release and independent exact label reference | Strict archive MIF Model+Scenario+Region+Year crosswalk; compare source-name transformations and per-variable consistency |
| Gross positive CO2 emissions | 2021 paper distinguishes gross-emissions reduction from CDR offsets | Identify authors' specific reported or computed **gross** emission streams and formula, separating positive fossil/industrial, land gross and any other sources, without silently treating a net aggregate as positive gross |
| Land removals | Original AR6 ARC24-03 reports positive land sequestration and positive signed net AFOLU in 2050 | Determine gross land sequestration versus signed net AFOLU identity and whether background natural sink or baseline reference is included; do not double count sinks |
| Biomass CCS / BECCS | Paper analyses BECCS as a CDR option, and ARC24-03 has positive biomass CCS reported | Establish biomass uptake and permanent storage flow and whether land sink/accounting offsets appear elsewhere; captured CO2 amount alone cannot establish net atmospheric removal |
| Fossil CCS | Original ARC24-03 includes positive fossil CCS | Distinguish avoided emissions from true removal and confirm how capture is netted in reported fossil sector emissions |
| DACCS | The paper analyses DACCS; ARC24-03 reports a **zero** DAC source value at 2050 | Confirm scenario/year-specific deployment and whether DAC reporting maps to durable atmospheric removal, not infer that the model lacks DAC generally |
| Enhanced weathering | Included among paper's CDR portfolio alternatives | Look for original source variable/report mapping and ensure missing AR6 candidate variables are not silently counted as physical zeros |
| Precision and numerical reconciliation | Original private World CSV SHA, 2050 exact aggregate arithmetic checked | Original author export quantization, nonoverlapping gross/emission partitions, source/version mappings and an independent reviewer; source filename/decimal formatting alone is insufficient |

## 4. Go/no-go rule for physical source review

After the real crosswalk, confirm exact study data match and independently read relevant Rmd variable formulas and original model-paper definitions. **If either exact scenario crosswalk or complete nonoverlapping positive/removal sector taxonomy is unavailable, report the corresponding concrete blocker** rather than imputing gross emissions. Only source-authorized physical components, a quantization-bound balance test and independent reviewer can justify subsequent I1/I2/I3 assignment. The selected sample is purposive, not representative of the full AR6 ensemble.

Sources: Strefler et al. (2021) https://doi.org/10.1088/1748-9326/ac0a11 ; original author's dataset https://zenodo.org/records/5103024 ; Climate Analytics methodology https://1p5ndc-pathways.climateanalytics.org/methodology ; PIK MIF data format https://pik-piam.r-universe.dev/mip/doc/mif.html .
## 5. Actual author file acquisition succeeded; text encoding blocker corrected in code (24 October 2026)

The author's Windows PowerShell run downloaded **all four Zenodo v2 files** and verified **every publisher-listed MD5 checksum**. The original archive is available at `data/ar6-private/cemics-v2` (gitignored). The first synthetic crosswalk suite passed **12/12 tests**. The first actual `arc24-cemics-crosswalk` run then raised `UnicodeDecodeError` at the Rmd/README supporting-source `path.read_text(encoding='utf-8-sig')`. Because the public result file is written only after completing this section, no crosswalk report was created.

Crucially, the exception occurred **after** author MIF MD5 verification, AR6 World source SHA-256 verification, private packet 2050 source checks, and initial MIF/World candidate comparison. Reaching this code point **does not demonstrate** that the exact scenario was present in the author MIF; its outcome was calculated internally but **not emitted** due to the later exception.

### Correction

The source reader now attempts lossless **strict** `utf-8-sig` decoding first, then legacy `cp1252` and `latin-1` only if the preceding decoding failed. Both raw archive files and their MD5 checks remain unchanged. Every supporting-file report records `decoded_as`, `utf8_strict_success`, and `encoding_certainty`, explicitly flagging a legacy byte interpretation as **not certified by the authors**. NUL-containing files or unexpected replacement characters are rejected, rather than silently replacing corrupt data.

New synthetic tests reproduce a non-UTF-8 `0xc2` byte and validate full Rmd/README flow with original bytes and MD5 constraints, UTF-8 behaviour, Latin-1 fallback, binary guard and tampered-MD5 rejection. **These new tests and the corrected real-source command are committed but not yet rerun by the author.**

PowerShell after pull:

    git pull --ff-only
    & .\.venv-messageix\Scripts\python.exe -m pytest -q tests/test_arc24_cemics_crosswalk.py
    & .\.venv-messageix\Scripts\python.exe -m residual_pathways arc24-cemics-crosswalk
    if ($LASTEXITCODE -ne 0) { throw 'CEMICS source crosswalk failed; do not read stale/missing report' }
    $x = Get-Content 'results/ar6-canonical-gate/arc24_cemics_source_crosswalk_public.json' -Raw | ConvertFrom-Json
    $x.status
    $x.archive_exact_model_scenario_row_count
    $x.archive_exact_world_variable_count
    $x.overlapping_variable_names
    $x.overlap_status_counts
    $x.author_methodology_code_presence | Format-List

No original archive re-download is needed; all four already exist and passed the publisher's checksums. If the corrected run instead reveals scenario absence, different model naming or variable-level discrepancies, report those scientific blockers directly rather than assuming source equivalence or assigning I3.

## 6. Real ARC24-03 crosswalk result: archive exact scenario ABSENT (24 October 2026)

The author successfully reran the fixed crosswalk using original MD5-verified Strefler/Zenodo v2 files and local World v1.1 data; **18/18 synthetic tests passed**. Unlike the earlier Unicode error, this run finished and created the coded report. Actual result:

| Original-source identity/field diagnostic | Observed result |
| --- | --- |
| CLI status | `SCENARIO_NOT_LOCATED_IN_AUTHOR_MIF` |
| Author MIF rows with exact `Scenario = CEMICS_SSP1-1p5C-minCDR` | **0** |
| Author MIF rows with both exact model/scenario | **0** |
| Exact source World/2050 variables in that author MIF scenario | **0** |
| Shared source variable names eligible for numerical comparison | **0** |
| Eight nominated CO2/CCS/land candidate variables | **All eight `ARCHIVE_VARIABLE_NOT_REPORTED` under the exact model/scenario key** |
| Author R Markdown exact string occurrences | **0** |
| Author R Markdown source text decoding | `cp1252`; legacy single-byte interpretation, not independently certified |
| Author README source text decoding | `cp1252`; legacy single-byte interpretation, not independently certified |
| Scientific I3 verification | **0** |

The R Markdown contains substantial keyword hits (BECCS 168 lines, DAC 175, SSP1 35 and gross 10), but those are literal string occurrences **not** source-variable identities, scenario mapping or quantified CDR evidence. The author's MIF file and supporting documents remain verified unmodified by their original MD5 checksums.

**Interpretation correction:** The authors' Zenodo v2 statement about *aligning scenario and variable categories with AR6* does **not** establish that the archive contains every AR6 scenario later associated with CEMICS, or that this exact SSP1 run is included. An exact-name miss is not a reason to inject guessed alternative labels or to declare that the entire published study lacks SSP1 results. The exact ARC24-03 link to the archived source remains **UNVERIFIED**, which blocks numerical crosswalk and any I3 claim via this route.

### Next targeted source-name investigation

A read-only source-locked CLI `arc24-cemics-names` inventories only the **authors' MIF Model/Scenario identifiers** (not original numerical emissions values). It reports unique source model/scenario counts, exact/normalized matches, semantically *unverified* similarly named candidates, and Rmd keyword line numbers. Similarity scores are lexical and **cannot** establish identical runs or physical accounting scopes. Nothing changes the original ARC24-03 selection or original data.

Run:

    git pull --ff-only
    & .\.venv-messageix\Scripts\python.exe -m pytest -q tests/test_arc24_cemics_name_inventory.py
    & .\.venv-messageix\Scripts\python.exe -m residual_pathways arc24-cemics-names
    $n = Get-Content 'results/ar6-canonical-gate/arc24_cemics_name_inventory_public.json' -Raw | ConvertFrom-Json
    $n.distinct_models; $n.distinct_scenarios; $n.distinct_model_scenario_pairs
    $n.model_labels_and_counts | Format-Table -AutoSize
    $n.normalized_scenario_matches | Format-Table -AutoSize
    $n.cemics_ssp1_cdr_candidates | Select-Object -First 30 | Format-Table -AutoSize
    $n.nearest_scenario_labels | Format-Table -AutoSize

The command is **committed but has not been executed against the author's original MIF**. If there is no source-labelled/semantically supported candidate, conclude that exact case-source linkage is presently unavailable and use the peer-reviewed study only for **model-family methodological context**. Independently review original AR6 dataset definitions/metadata, or a different primary scenario submission, rather than substituting similar source runs. Do not pursue near-equality searches across unrelated source scenarios as proof of identity.

### Scientific interpretation and software correction to the initial field statuses

The user-observed initial candidate-variable rows each read `ARCHIVE_VARIABLE_NOT_REPORTED`, but **this was a consequence of an absent exact scenario key**, not proof that the authors' entire MIF did not report total CO2, CCS, DAC or AFOLU variables in other scenarios. Crosswalk code has been amended: a missing scenario now yields `CASE_SCENARIO_ABSENT_FIELDS_NOT_ASSESSED`; a matching scenario with unverified model yields `EXACT_MODEL_UNVERIFIED_FIELDS_NOT_ASSESSED`; and absent World region yields `WORLD_REGION_ABSENT_FIELDS_NOT_ASSESSED`. The existing `ARCHIVE_VARIABLE_NOT_REPORTED` status remains valid only after an exact Model/Scenario/World source record was found and a particular variable is missing.

Author-source model/scenario name inventory implementation added with synthetic tests and separate checksums for both MIF and R Markdown source. **These newest code changes are not yet confirmed by a real local rerun.** The actual completed earlier run still definitively establishes the zero exact-scenario-labelled rows.

## 7. Original authors' 20-scenario MIF inventory; no minCDR direct label (local execution 24 October 2026)

Author-ran source-name inventory **24/24 synthetic tests passed** and processed the checksum-verified original MIF. Actual original author file contains **147,534 rows, one author model label `REMIND-MAgPIE`, 20 distinct scenarios and 20 unique model×scenario pairs**. The registered AR6 ARC24-03 uses the *versioned* model label `REMIND-MAgPIE 2.1-4.2`, scenario `CEMICS_SSP1-1p5C-minCDR`. There are **no exact or punctuation-normalized matches** for minCDR among the 20 author scenario labels. The observed SSP1/1.5°C author scenarios and rows:

| Author source scenario | Number of original author rows |
| --- | ---: |
| `CEMICS_SSP1-1p5C-noCDR` | 7,391 |
| `CEMICS_SSP1-1p5C-fullCDR` | 7,391 |
| `CEMICS_SSP1-1p5C-AR-only` | 7,391 |
| `CEMICS_SSP1-1p5C-EW-only` | 7,391 |
| `CEMICS_SSP1-1p5C-DAC-only` | 7,391 |
| `CEMICS_SSP1-1p5C-BECCS-only` | 7,391 |

**Do not infer that `noCDR` and `minCDR` mean the same scenario** from their similar names (the string similarity of the author's noCDR name to minCDR is 0.923; it has *no physical or statistical meaning*). The original Strefler paper explicitly refers to a 'min CDR' experiment (see 2021 Environmental Research Letters paper), while the author MIF calls its minimum-looking branch noCDR. A later AR6 pathway paper refers to a scenario minCDR with the versioned 2.1-4.2 label; this is a plausible naming-transformation question, not yet a verified equivalence.

References include the [Strefler paper](https://doi.org/10.1088/1748-9326/ac0a11), [author's Zenodo v2](https://zenodo.org/records/5103024), [Climate Analytics selected AR6 scenarios](https://1p5ndc-pathways.climateanalytics.org/methodology), and [Ganti et al. (2025) illustrative minCDR scenario choices](https://doi.org/10.1080/14693062.2025.2481138). An IPCC WGIII Second Order Draft annex also used a `limCDR` label in early CEMICS scenario lists, but that draft must not be treated as the final mapping or final approved emissions protocol.

### Controlled multi-year, multi-variable source fingerprint — now implemented, **pending local execution**

New CLI `arc24-cemics-alias-fingerprint` compares **four explicitly registered pairings** across shared original World source variables and shared 2020–2100 year columns:

1. **Full same-label positive control**: author's `CEMICS_SSP1-1p5C-fullCDR` versus AR6 `CEMICS_SSP1-1p5C-fullCDR`. Although author Model lacks the 2.1-4.2 version suffix, this is the closest legitimate candidate for validating whether data snapshots match across these exact scenario labels.
2. **Source alias hypothesis**: author's `CEMICS_SSP1-1p5C-noCDR` versus AR6 `CEMICS_SSP1-1p5C-minCDR` (ARC24-03).
3. **Crossed negative/control comparison**: author's `fullCDR` versus AR6 `minCDR`.
4. **Crossed negative/control comparison**: author's `noCDR` versus AR6 `fullCDR`.

The script verifies original author MIF MD5, original World v1.1 source SHA-256, saved ARC24-03 2050 values, original units and author Rmd MD5. It compares exact source Decimal values by *matching original variable names, years and source units*, and reports status counts for each pairing and pre-registered CO2/CCS/land fields **without emitting original emission observations**. It separately indexes Rmd mentions of `noCDR`, `minCDR`, `min CDR`, limited CDR and SSP1. Crucially, even 100% numeric equality cannot by itself establish an **author-approved rename** or model-version identity, and automatic I3 promotion is prohibited.

Windows PowerShell:

    git pull --ff-only
    & .\.venv-messageix\Scripts\python.exe -m pytest -q tests/test_arc24_cemics_alias_fingerprint.py
    & .\.venv-messageix\Scripts\python.exe -m residual_pathways arc24-cemics-alias-fingerprint
    $f = Get-Content 'results/ar6-canonical-gate/arc24_cemics_alias_fingerprint_public.json' -Raw | ConvertFrom-Json
    $f.comparisons | Select-Object comparison,shared_variable_names,year_variable_compared,exact_decimal_matches,exact_decimal_match_fraction | Format-Table -AutoSize
    $f.comparisons | ForEach-Object { $_.comparison; $_.status_counts | Format-List }
    $f.author_Rmd_source_text_evidence.keyword_line_counts | Format-List

**Go/no-go:** If the full-label positive control matches across many independent original variable/year cells and the noCDR-to-minCDR fingerprint also matches substantially better than the two crossed negative controls, record this as *strong evidence for numerical series correspondence*, but **not** official model alias confirmation or carbon-flow disjointness. If fingerprints diverge materially, close this author's v2 archive as an unsuitable numerical provenance source for ARC24-03. Preserve the paper solely for its model-family physical methods and seek the actual AR6 original scenario submission/documentation elsewhere. All grades remain NOT_DETERMINED, I3=0.

### Primary-paper nuance: min CDR does not literally mean zero carbon removal

The [open-access 2021 Strefler et al. article at IOPscience](https://doi.org/10.1088/1748-9326/ac0a11), main text, explicitly defines a **minimum-CDR** experiment as permitting residual carbon-removal contributions associated with then-current policies and **industry BECCS** while excluding unrestricted deployment of the full CDR portfolio. This is important: **min CDR cannot be safely interpreted as literally zero carbon removal**, and conversely an archive scenario *labelled* `noCDR` need not mathematically have no CDR. The paper's main-text configuration is SSP2; SSP1 is covered in supplementary material, so main-text SSP2 quantities cannot be carried over to ARC24-03's SSP1 output.

This supports a semantic reason to investigate `noCDR` versus AR6 `minCDR` without assuming equivalence. The study author's original Rmd and the independent controlled source fingerprint must be reconciled first; **the literature does not itself attest that the two strings name the identical released model run**. Fossil and industrial CCS are also allowed in the study designs; fossil CO2 capture therefore must not be counted as atmospheric removals.
