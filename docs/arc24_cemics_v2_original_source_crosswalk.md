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