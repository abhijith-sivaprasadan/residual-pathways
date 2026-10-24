# ARC24-03 scientific carbon-flow semantics: evidence gate after source-verified numerical correspondence

**24 October 2026.** This dossier uses real author-run code outputs (not hypothetical test fixtures) and the author's 2021 paper, but **no independently adjudicated gross/CDR ledger**. Versioned AR6 model label: `REMIND-MAgPIE 2.1-4.2`; original authors' MIF label: `REMIND-MAgPIE`.

## 1. Source provenance resolved at the level of recorded series

Authors' Zenodo v2 `CDRoptionsAR6_complete.mif`, MD5 `efbc4f82b0163da790f370775a37cfe7`, was downloaded by the user and independently checksum-verified against the source manifest. World v1.1 CSV has its original local selection SHA. The user ran `arc24-cemics-alias-fingerprint`; 10/10 regression tests passed, and both intended pairings **exactly matched all 4,653 recorded-decimal observations** across 517 shared variables and nine years, with identical units and no excluded/ambiguous source pairs:

- Original authors' `CEMICS_SSP1-1p5C-fullCDR` ↔ versioned AR6 `CEMICS_SSP1-1p5C-fullCDR` = **4,653 / 4,653** exact.
- Original authors' `CEMICS_SSP1-1p5C-noCDR` ↔ versioned AR6 `CEMICS_SSP1-1p5C-minCDR` (ARC24-03) = **4,653 / 4,653** exact.
- Both crossed comparisons = **1,604 / 4,653** exact, **3,049** unequal. Distinct trajectories are demonstrated numerically.

**Interpretation:** ARC24-03 is now **source-series numerically crosswalked** to the original study's `noCDR` label in the tested World region/variables/years. A written author statement explicitly renaming the exact `noCDR` series to `minCDR` and identifying the model binary/version remains unlocated. The nine repeated years/517 variables are correlated outputs of one model, not 4,653 independent confirmations of physical validity.

## 2. Study-level evidence from primary publication

Strefler, J., Bauer, N., Humpenöder, F., Klein, D., Popp, A., Kriegler, E. (2021), *Carbon dioxide removal technologies are not born equal*, Environmental Research Letters 16, 074021. DOI https://doi.org/10.1088/1748-9326/ac0a11.

The open-access study compares six portfolios: a full set of CDR options, only BECCS, only direct-air CCS, only afforestation/reforestation, only enhanced weathering, and a **minimum-CDR** portfolio. Its minimum-CDR scenario allows a restricted, **nonzero** contribution from policy-promised afforestation and BECCS in industry. Fossil/industrial point-source CCS can also be represented as mitigation. The paper's principal textual quantitative examples describe SSP2; **ARC24-03 is SSP1** and must use its actual source series for numerical estimates. The primary dataset includes a variety of source variables beyond the six initially examined in ARC24.

IPCC AR6 WGIII Chapter 12, https://www.ipcc.ch/report/ar6/wg3/chapter/chapter-12/, establishes the physical definition: anthropogenic removal **from the atmosphere plus durable storage**. Fossil point-source CCS is not CDR; direct capture from ambient air with durable storage, and biomass capture with documented net atmospheric uptake and permanent storage, can be components. Natural unenhanced uptake is not automatically anthropogenic CDR. These are external scientific definitions, **not** automatically satisfied by IAMC variable names.

## 3. Candidate net/gross flows and decision rules for original Rmd review

| Source export concept | What the report currently establishes | Evidence needed to qualify as physically disjoint ledger entry |
| --- | --- | --- |
| `Emissions|CO2` | Reported aggregate total (net-like) source series | Declared physical partition and other/missing sources before calling positive gross |
| `Emissions|CO2|Energy and Industrial Processes` | Reported energy/industry aggregate | Whether biomass CCS or industry sources/capture are already netted, how fossil CCS affects it |
| `Emissions|CO2|AFOLU` | Signed net AFOLU export | Model land-sector gross positive emissions, anthropogenic removal, natural land sink treatment and AFOLU netting equation |
| `Carbon Sequestration|Land Use` | Reported land sequestration uptake, separate from net AFOLU | Its baseline, whether includes only anthropogenic uptake, and overlap with the land net sector |
| `Carbon Sequestration|CCS|Biomass` | Source reports biomass-origin capture | Actual durable storage, upstream supply emissions, whether sector net totals already include offsets and whether industry BECCS allowed |
| `Carbon Sequestration|CCS|Fossil` | Captured fossil-origin stream | **Avoidance/mitigation**, not atmosphere-to-storage removal; check whether fossil emissions are already adjusted |
| `Carbon Sequestration|Direct Air Capture` | Source reported zero at 2050 in ARC24-03 | Does zero correspond to DACCS deployment, raw capture, electricity emissions or another variable boundary? |
| Enhanced weathering | Included in overall study portfolio | Original reported variable, source chemistry, baseline, storage time and double-counting with DAC/AFOLU |

## 4. Highest-value next steps (source-text, not another bulk arithmetic score)

1. Read the **authors' MD5-verified original** `CDRoptions.Rmd` (1,522 lines; original CP1252 byte interpretation) around variable selectors, figure inputs and explicitly computed expressions for `gross`, `BECCS`, `DAC`, `AFOLU`, land and `noCDR`. Print **line numbers and short code-context windows**; avoid treating counts of keyword hits as evidence for the formulas.
2. Cross-reference each code variable selector or Rmd equation to **exact original MIF names** present in the registered `noCDR` World case and AR6 `minCDR` series; use the saved `arc24_cemics_alias_fingerprint_public.json` `predefined_carbon_variable_status_counts` to confirm 2050 candidate series' numeric correspondence. The author MIF includes 517 common names, but that does not guarantee a gross-positive emissions numerator is reported.
3. Identify **exact Model output versus postprocessing**: determine whether land sequestration is netted inside AFOLU; whether BECCS captured biomass carbon appears in sector outputs as negative emissions; whether DACCS is counted as actual atmosphere removal and geological storage; whether enhanced-weathering values are carried in an atmospheric-removal stream; and whether positive gross emissions can be reconstructed without overlap. Do not double-subtract land sequestration or fossil CCS.
4. Where source code/variable documentation does not define physical net-to-gross relationships, state **UNRESOLVED**; do not fill gaps with assumptions. Obtain a model-author source mapping/precision statement and an independent reviewer before I3.

### Simple original-author Rmd inspection (Windows PowerShell)

This is a *source-reading command* and writes nothing. The author file was checked against Zenodo's MD5 separately. It prints a bounded selection of original public analysis-code lines, no private AR6 numerical data:

```powershell
$path = (Resolve-Path 'data\ar6-private\cemics-v2\CDRoptions.Rmd').Path
$lines = [System.IO.File]::ReadAllLines($path, [System.Text.Encoding]::GetEncoding(1252))
$regex = '(?i)(noCDR|min ?CDR|fullCDR|gross|sequestration|negative emissions|emissions\|CO2|carbon sequestration)'
$hits = for ($i = 0; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -match $regex) {
        [pscustomobject]@{ Line=($i+1); SourceCode=$lines[$i].Trim() }
    }
}
$hits | Select-Object -First 80 | Format-Table -Wrap -AutoSize
```

After identifying numbered passages that actually define stream identities and formulas, read narrow surrounding code lines instead of copying all 1,522 lines. Remember Rmd may contain hardcoded output or figure transformations; a plotting variable name is not itself proof of a physical carbon-flow equation.

### Author's source-aligned candidate variable comparison (no confidential numbers)

```powershell
$f = Get-Content 'results\ar6-canonical-gate\arc24_cemics_alias_fingerprint_public.json' -Raw | ConvertFrom-Json
$p = $f.comparisons | Where-Object comparison -eq 'NOCDR_TO_MINCDR_HYPOTHESIS'
$p.predefined_carbon_variable_status_counts | Format-List
```

**Current I3 status**: NOT_DETERMINED. Gross-positive and true atmospheric CDR remain unverified. This dossier is a source-identification success followed by a physical-semantics review, not a scientific grade.

## 5. Actual author R Markdown inspection — first formula-level findings (24 October 2026)

The author executed the bounded PowerShell inspection against the **previously checksum-verified** `CDRoptions.Rmd` using Windows-1252 text decoding. The first attempt containing `for (...) { ... } | Out-Null` produced a PowerShell parser error (pipeline after a `for` block). The corrected `$matchesFound = for (...) { ... }; $matchesFound | ...` command succeeded; this does not change or invalidate the original file or its MD5. Source lines below are those reported by the author from the original Rmd, **not an interpretation generated by a test fixture**.

### 5.1 Original model-output selectors, exactly as used by author analysis

| Rmd line | Authors' code / source series | Provisional source interpretation; constraint |
| --- | --- | --- |
| **150** | `CO2tot <- data[,,"Emissions|CO2 (Mt CO2/yr)"]` | Reported total CO2 in original data, not automatically positive gross emissions |
| **151** | `CDRaff <- -data[,,"Emissions|CO2|Land|Land-use Change|Regrowth (Mt CO2/yr)"]` | Afforestation/regrowth CDR **constructed by negating a signed emission series**. This is NOT proof it equals the distinct aggregate IAMC variable `Carbon Sequestration|Land Use`, nor that it accounts for all land removals |
| **152** | `CDRew <- data[,,"Carbon Sequestration|Enhanced Weathering (Mt CO2/yr)"]` | Author explicitly tracks an EW source series. Requires geological/chemical permanence and accounting boundary review |
| **153** | `CDRbeccs <- data[,,"Carbon Sequestration|CCS|Biomass (Mt CO2/yr)"]` | Author uses biomass-origin CCS capture as a removal-category flow. Captured CO2 is not automatically a verified net atmospheric removal without lifecycle/baseline/storage audit |
| **154** | `CDRdaccs <- data[,,"Carbon Sequestration|Direct Air Capture (Mt CO2/yr)"]` | Author separately tracks direct-air capture. Need distinguish captured volume and durable storage/net emissions |
| **193–194** | `CO2gross2020/2050 <- data["GLO","y2020/y2050","Emissions|CO2|Gross Fossil Fuels and Industry (Mt CO2/yr)"]` | **Directly reported gross fossil fuel + industrial CO2 source metric**. Excludes any other gross source not specified; not independently proven exhaustive economy-wide gross |
| **196** | `CO2redrate <- 100*(1-exp(log(CO2gross2050/CO2gross2020)/30))` | Annualized geometric percentage *reduction* in the study's reported gross fossil/industry CO2 between 2020 and 2050. Mathematically equivalent to `100 × [1-(gross2050/gross2020)^(1/30)]` when both terms are positive; it is **not a gross-minus-net accounting identity** |

**Important correction to earlier ARC24 source candidate list:** The authors' explicit `CDRaff` maps to `Emissions|CO2|Land|Land-use Change|Regrowth`, while the ARC24-selected land candidate was `Carbon Sequestration|Land Use`. Those are **distinct identifiers and cannot be equated without a source mapping**. The separate original `Gross Fossil Fuels and Industry` selector is not among the seven earlier carbon-variable-match status categories; **its source World case/units and exact author-vs-AR6 crosswalk must be checked explicitly** before using its numerical values.

### 5.2 Original study naming evidence, stronger than a lexical coincidence

- **Rmd lines 555–558**: the SSP1/1.5°C gross-CO2-reduction plotting code includes `CEMICS_SSP1-1p5C-noCDR` as the final selected scenario and provides `min CDR` as the final display label in its `scale_x_discrete(labels=...)` call.
- **Rmd lines 599–601**: an additional SSP1 chart likewise lists the archived `noCDR` scenario and the final displayed label `min CDR`.
- **Rmd lines 362, 365–366**: the corresponding SSP2 chart also includes `noCDR` in the scenario selections and `min CDR` in the ordered legend label vectors.

These are direct **author-code presentation-label clues** that the archive's `noCDR` variant is referred to as `min CDR` in the 2021 study. The Rmd excerpts do not print explicit display-scale breaks/factor-level ordering, so an exact one-to-one visual axis mapping should not be asserted solely from list order; however, with the independently observed **4653/4653 source data correspondence** and discriminating crossed controls, the collective evidence for the AR6 `minCDR` crosswalk is now much stronger. A written model-submission rename/version statement remains desirable but is no longer the only source-based support.

### 5.3 Original candidate carbon series correspond over all nine tested years

The user's already executed `arc24-cemics-alias-fingerprint` report, inspected via PowerShell, explicitly shows **nine exact reported-decimal matches each** for `Emissions|CO2`, `Emissions|CO2|AFOLU`, `Emissions|CO2|Energy and Industrial Processes`, `Carbon Sequestration|Land Use`, `Carbon Sequestration|CCS|Biomass`, `Carbon Sequestration|CCS|Fossil`, and `Carbon Sequestration|Direct Air Capture` in the author `noCDR` vs AR6 `minCDR` pairing. It shows no status for `Emissions|CO2|Other` in the preselected comparison—**do not convert blank status into a reported physical zero**.

### 5.4 What is not yet in the shared excerpt

The broad search output shows the authors' selectors and a gross-reduction metric, but **not** the actual defining equations for `CDRtotal`, `CO2tot2`, `redMit`, `redAff`, `redEW`, `redBECCS`, `redDACCS`, or the related sector-netting formulas. The document contains later derived objects and graph components (e.g. 491–495 and 723–799), but those *uses* are not definitions. Do not reverse-engineer an exhaustive four-part identity from variable names and figure captions.

Request only the bounded original-source text windows to determine the exact calculation and avoid another broad keyword dump:

```powershell
$src = (Resolve-Path 'data\ar6-private\cemics-v2\CDRoptions.Rmd').Path
$lines = [System.IO.File]::ReadAllLines($src, [System.Text.Encoding]::GetEncoding(1252))
foreach ($range in @(@(140,215), @(335,355), @(545,561))) {
    Write-Host "--- Original CEMICS Rmd lines $($range[0])–$($range[1]) ---"
    foreach ($n in $range[0]..$range[1]) {
        '{0,4}: {1}' -f $n, $lines[$n - 1]
    }
}
```

This reads publicly released author source code from the user's unchanged local source; it does not print AR6 World emissions observations. Next interpretation target: decide if source `CDRtotal` is a sum of explicitly disjoint source streams and whether the author's `CO2gross` measures have separate sector scopes. **Still no I3: 0 verified physically exhaustive atmospheric removal partitions.**
## 6. Original author source formulas REVEALED by 2026-10-24 user's exact line-level Rmd extract

**Original source evidence:** The author displayed lines **140–215** of the byte-preserved, Zenodo-MD5-verified `CDRoptions.Rmd` using CP1252 in local PowerShell. The full calculation block (source lines 150–156) is:

```r
CO2tot <- data[,,"Emissions|CO2 (Mt CO2/yr)"]
CDRaff <- -data[,,"Emissions|CO2|Land|Land-use Change|Regrowth (Mt CO2/yr)"]
CDRew <- data[,,"Carbon Sequestration|Enhanced Weathering (Mt CO2/yr)"]
CDRbeccs <- data[,,"Carbon Sequestration|CCS|Biomass (Mt CO2/yr)"]
CDRdaccs <- data[,,"Carbon Sequestration|Direct Air Capture (Mt CO2/yr)"]
CDRtotal <- CDRaff + CDRew + CDRbeccs + CDRdaccs
CO2pos <- CO2tot + CDRtotal
```

**This is now an actual author-defined scenario reporting identity, not an inferred additive correction.** For World and 2050 the study's *operational* source-defined removal accounting is `CDRtotal = -Regrowth_emissions + Enhanced_Weathering_sequestration + Biomass_CCS + Direct_Air_Capture`; its **derived** residual positive-side measure is `CO2pos = net_Emissions|CO2 + CDRtotal`. It does NOT include fossil CCS as a CDR contribution. Whether the source model's reported series are physically exhaustive/nonoverlapping anthropogenic atmospheric removal pathways, net of lifecycle/regrowth baselines and storage losses, remains unverified. In particular, **CO2pos is NOT the separately reported original MIF variable `Emissions|CO2|Gross Fossil Fuels and Industry`, and it is NOT automatically the complete economy-wide gross emission stream.**

Other source code that materially constrains interpretation:

- **Line 159:** `CDRcosts <- CO2price*CDRtotal*(-0.001)` — source accounting cost sign convention, *not* a physical mass balance. The unit factor converts study monetary scaling.
- **Line 160:** `CO2rev <- CO2price*CO2pos*0.001` — author's `CO2pos` is used as the positive-emissions-side quantity for price/revenue calculations.
- **Lines 162–168:** author time-step weights integrate `CDRtotal` into cumulative contributions; these are not independent physical removal validations.
- **Lines 193–196:** `CO2gross2020`/`CO2gross2050` directly select `Emissions|CO2|Gross Fossil Fuels and Industry`; `CO2redrate = 100*(1-exp(log(gross2050/gross2020)/30))`. This direct sectoral gross input measures **gross fossil and industry** separately from `CO2pos` and should not be silently substituted for it.
- **Lines 198–202:** `CO2netneg <- CO2tot; CO2netneg[CO2netneg>0] <- 0; CO2netneg <- CO2netneg*(-0.001)` and weighted cumulative net-negative emissions. This operational metric is the negative portion of net total, expressed in Gt rather than Mt; it **does not equal total CDR deployment**, which may offset positive remaining emissions.
- **Line 210:** the author's Fig 1 CDR deployment series is `CDRtotal * 0.001`, i.e. Mt CO2/yr to Gt CO2/yr.

### What was actually verified by source matching

Original author's `noCDR`↔AR6 `minCDR` fingerprint showed **9/9 exact recorded-decimal World source matches each** for total CO2, net AFOLU, combined energy/industry, `Carbon Sequestration|Land Use`, biomass CCS, fossil CCS and direct-air capture. **Not yet specifically demonstrated within this report** are source availability/World-2050 matches for the Rmd's distinct `Emissions|CO2|Land|Land-use Change|Regrowth`, `Carbon Sequestration|Enhanced Weathering`, and `Emissions|CO2|Gross Fossil Fuels and Industry`. Do not mistake these for absent or zero; inspect them directly with source hashes and units.

### Scientific accounting interpretation

An exact algebraic source identity of the form `net CO2 = CO2pos - CDRtotal` is **true by the author's definition** of CO2pos. It is *not independently verified physical closure* of gross emissions versus truly atmospheric removals. To certify that, we need (i) source-defined complete partition of positive sector flows, (ii) non-overlap and anthropogenic additionality for the four removal terms, (iii) durability/storage and lifecycle netting, (iv) consistency with AFOLU's signed-net boundary and biomass-origin accounting, (v) model-specific source precision, and (vi) independent expert review. The source is now well beyond provenance inference, but **I3=0** remains justified.

### Next decisive source-locked test

Directly inspect the original World source with a local checksum-verified code path for the eight named variables: net CO2, signed regrowth land flux, enhanced weathering sequestration, biomass CCS, DAC, gross fossil+industry, signed net AFOLU, and separate `Carbon Sequestration|Land Use`. Report public **presence/unit agreement, original-decimal match status, signed flags and a coarse magnitude band** for the *difference* between author's `CO2pos` and separate gross fossil+industry only as a comparison of **unlike system boundaries**, not an expected zero-balance diagnostic. Keep all source numerical observations and computed totals private. Report absent source variables explicitly, never invent zero. Finish reviewing original author model methods before any I3 classification.

## 7. Original-source 2050 ARC24-03 calculation worksheet — prepared and awaiting real execution

The source MD5- and original AR6 World SHA-locked command `arc24-cemics-author-accounting` now implements the **exact author Rmd** `CDRtotal` and `CO2pos` operational formulas from the publicly released source, without inventing extra ledger terms. Before evaluating it, the code checks all seven original Rmd selector/assignment strings, original MIF/Rmd MD5 fingerprints, AR6 World SHA, and the saved ARC24-03 private original-2050 observations. It compares named MIF and AR6 source records by **unique matching source unit**; duplicate same-unit rows are flagged instead of chosen, and missing fields are not imputed as zero.

Inputs named explicitly: reported net `Emissions|CO2`, signed `Emissions|CO2|Land|Land-use Change|Regrowth`, `Carbon Sequestration|Enhanced Weathering`, `Carbon Sequestration|CCS|Biomass`, `Carbon Sequestration|Direct Air Capture`, and the **distinct** `Emissions|CO2|Gross Fossil Fuels and Industry` plus reported net AFOLU, general Land Use sequestration and captured Fossil CCS for semantic context. Only source terms with exact author/AR6 recorded-decimal equality and required `Mt CO2/yr` unit enter the operational calculation. Gross fossil+industry is a **separate boundary comparison**, never treated as an expected closure target.

The coded public report `results/ar6-canonical-gate/arc24_cemics_author_accounting_public.json` contains only series names, source presence/units, source-decimal match status, signs of verified terms/derived measures and a coarse **magnitude band for difference between derived CO2pos and separately reported gross fossil+industry**, if computable. It publishes **no original scenario numerical CO2 observations**. It explicitly labels this an **author operational equation** but NOT verified economy-wide positive-gross or durable, additional nonoverlapping physical CDR. Tests cover synthetically computed four-branch CDR, missing source terms, source tampering, duplicate source rows, missing net/gross equivalence and data non-publication.

New code, tests and CLI are committed but **NOT YET RUN LOCALLY**. A successful execution will be relevant even if it reports `AR6_SERIES_NOT_REPORTED` for one of the newly identified Rmd source variables; in that case, request a source-author MIF-only source scope review rather than silently carrying over absent AR6 fields.

Windows PowerShell:

```powershell
cd 'E:\New folder (2)\MissionJob\residual-pathways'
git pull --ff-only
& .\.venv-messageix\Scripts\python.exe -m pytest -q tests/test_arc24_cemics_author_accounting.py
if ($LASTEXITCODE -ne 0) { throw 'Author carbon-flow regression tests failed' }
& .\.venv-messageix\Scripts\python.exe -m residual_pathways arc24-cemics-author-accounting
if ($LASTEXITCODE -ne 0) { throw 'Original source worksheet failed' }
$a = Get-Content 'results/ar6-canonical-gate/arc24_cemics_author_accounting_public.json' -Raw | ConvertFrom-Json
$a.individual_source_terms | Select-Object variable,source_comparison_status,source_value_sign | Format-Table -Wrap -AutoSize
$a.operational_study_accounting | Format-List
$a.study_CO2pos_vs_separate_gross_fossil_industry | Format-List
```

**Study method versus physically closed carbon accounting must remain separate.** In particular, `CO2pos = CO2tot + CDRtotal` is an exact *definition* in this research script; writing its residual as zero is tautological, not external validation. The label `Gross Fossil Fuels and Industry` describes an additional narrower gross-sector indicator with a different boundary. Neither source should be used as a drop-in positive economy-wide emissions ledger. Verified I3 remains zero.

## 8. Original author 2050 operational formula real execution: missing source-key mapping, not zero CDR (24 October 2026)

The author executed the newly committed source-MD5/SHA-locked worksheet on the **real CEMICS source archive and AR6 World v1.1**, with **8/8 regression tests passed**. Command outcome: `ORIGINAL_AUTHOR_FORMULA_DIAGNOSTIC_NO_I3`; `NOT_COMPUTABLE_MISSING_OR_UNVERIFIED_SOURCE_TERM` due solely to the exact-name source `Emissions|CO2|Land|Land-use Change|Regrowth`; distinct Gross Fossil Fuels and Industry versus study-derived CO2pos `NOT_COMPARABLE_UNVERIFIED_INPUT`.

| Source-original variable | User-observed 2050 source status | Source-observed sign |
| --- | --- | --- |
| Emissions|CO2 | EXACT_REPORTED_DECIMAL_MATCH | POSITIVE |
| Emissions|CO2|Land|Land-use Change|Regrowth | AUTHOR_SERIES_NOT_REPORTED *under exact raw name* | UNVERIFIED |
| Carbon Sequestration|Enhanced Weathering | EXACT_REPORTED_DECIMAL_MATCH | ZERO |
| Carbon Sequestration|CCS|Biomass | EXACT_REPORTED_DECIMAL_MATCH | POSITIVE |
| Carbon Sequestration|Direct Air Capture | EXACT_REPORTED_DECIMAL_MATCH | ZERO |
| Emissions|CO2|Gross Fossil Fuels and Industry | AR6_SERIES_NOT_REPORTED *under exact AR6 name* (authors' MIF does report it) | UNVERIFIED in two-source comparison |
| Emissions|CO2|AFOLU | EXACT_REPORTED_DECIMAL_MATCH | POSITIVE |
| Carbon Sequestration|Land Use | EXACT_REPORTED_DECIMAL_MATCH | POSITIVE |
| Carbon Sequestration|CCS|Fossil | EXACT_REPORTED_DECIMAL_MATCH | POSITIVE |

**No numeric operational CDRtotal or CO2pos has yet been computed** for this case. An absent exact regrowth source field must not be turned into zero. Separately, source-reported positive `Carbon Sequestration|Land Use` is **not established equivalent to the Rmd regrowth flux**.

### Material new source-preprocessing clue

The very same original R Markdown, **lines 144–145**, does a preprocessing step *before* selecting land regrowth at line 151:

```r
# delete "+" and "++" from variable names
data <- deletePlus(data)
```

Current [PIK MAgPIE reporting documentation](https://pik-piam.r-universe.dev/magpie4/doc/manual.html) lists its regrowth hierarchical variable as `Emissions|CO2|Land|Land-use Change|+|Regrowth`, and classifies it as **negative removals from forest regrowth**, distinct from a signed net land-sector flux. **This public documentation may refer to a later version than the 2021 source MIF**. Therefore it is a *hypothesis* that the authors' original source Regrowth line is stored with an extra `|+|`/`|++|` marker that `deletePlus()` strips before the authors' Rmd formula. The actual raw archive field and original `deletePlus` behaviour still need verification. This explains why prior strict crosswalk could show `AUTHOR_SERIES_NOT_REPORTED` without proving that the dataset lacks an operational regrowth flow.

**Scientific next step:** inspect source names for `Regrowth`, `Gross Fossil Fuels and Industry` and `Land Use` in the **same MD5-locked author scenario**, inspect same names in World v1.1 and Rmd pre-processing lines 95–146. Report original names, units, unique source-record counts and candidate hierarchy-only transformations, **no numeric emissions values**. No arithmetic substitution until a *unique* source field maps through the author's preprocessing. Even then label any source-author-only regrowth as NOT directly crosswalked to AR6 if absent in World. Hold I3=0.
### Targeted, original-source name-lineage test prepared (unrun)

New `arc24-cemics-field-lineage` command is a **source-name-only diagnostic**; it does **not** recompute CDRtotal or make any unverified value substitutions. It verifies the original author MIF and Rmd MD5 fingerprints, AR6 World SHA and registered ARC24-03 source identity, then inventories original MIF-vs-AR6 World `Variable` names and original `Unit` records for:

- `Emissions|CO2|Land|Land-use Change|Regrowth` — exact Rmd postprocessed selector, including candidates with a standalone `|+|` or `|++|` hierarchy marker;
- `Emissions|CO2|Gross Fossil Fuels and Industry` — original author's separately reported sector-gross variable, known not to exist in AR6 under exact name;
- `Carbon Sequestration|Land Use` — distinct earlier ARC24 aggregate land-sequestration term that must **not** be silently substituted for regrowth.

The inventory reports exact raw-name availability, unique potential *syntactic* hierarchy-marker candidates, raw source variable names, units and source-record counts, plus surrounding land/gross field names. It explicitly sets `automatic_variable_rename_accepted=false`, `operational_CDRtotal_computed=false`, `verified_i3=0`. Only after author-Rmd preprocessing behaviour and raw source names are linked unambiguously may a *source-author-only* regrowth study calculation proceed; if AR6 lacks the same original variable, the report must say so rather than claiming the author-to-AR6 series matches.

**Original scientific caveat:** `deletePlus(data)` is visibly in the exact original 2021 Rmd, whereas the PIK MAgPIE source-variable hierarchy documentation searched in 2026 can represent `Regrowth` as `...|Land-use Change|+|Regrowth`. This is a plausible explanation, **not yet checked in the user's actual archived 2021 MIF**. The inventory diagnoses that precise question without using a source-numeric fingerprint to choose a convenient record.

Run locally, no downloads:

```powershell
cd 'E:\New folder (2)\MissionJob\residual-pathways'
git pull --ff-only
& .\.venv-messageix\Scripts\python.exe -m pytest -q tests/test_arc24_cemics_field_lineage.py
if ($LASTEXITCODE -ne 0) { throw 'Source lineage tests failed' }
& .\.venv-messageix\Scripts\python.exe -m residual_pathways arc24-cemics-field-lineage
if ($LASTEXITCODE -ne 0) { throw 'Original CEMICS field lineage failed' }
$l = Get-Content 'results\ar6-canonical-gate\arc24_cemics_field_lineage_public.json' -Raw | ConvertFrom-Json
$l.original_author_fields | Select-Object requested_postprocessed_rmd_name,raw_exact_name_present,marker_candidate_count,hierarchy_marker_candidate_names | Format-List
$l.original_ar6_fields | Select-Object requested_postprocessed_rmd_name,raw_exact_name_present,marker_candidate_count,hierarchy_marker_candidate_names | Format-List
$l.context_name_inventory | Where-Object { $_.original_variable_name -match 'Regrowth|Gross Fossil' } | Format-Table -Wrap -AutoSize
```

To inspect exact Rmd data-loading details also run: `100..146 | % { '{0,4}: {1}' -f $_,$lines[$_-1] }` using the original `$lines` array from prior verified Rmd inspection. The code and tests have been committed but **not yet executed against the user's source**.
## 9. Original Regrowth name mapping resolved, CLI reporting bug identified, and operational worksheet extended (24 October 2026)

**Actual local source evidence from user:** The new `arc24-cemics-field-lineage` run passed **7/7 original synthetic tests** and successfully wrote `results/ar6-canonical-gate/arc24_cemics_field_lineage_public.json`, then raised `KeyError: 'hierarchy_marker_candidate_count'` **only in CLI summary printing**. The report itself records the correct field `marker_candidate_count`. A committed CLI fix aligns the field name; an end-to-end CLI test was added to prevent that particular regression.

The actual original World 2050 name/availability findings (confirmed from saved generated public JSON):

| Source field | Original authors' `noCDR` MIF | AR6 `minCDR` World |
| --- | --- | --- |
| `Emissions|CO2|Land|Land-use Change|Regrowth` (Rmd postprocessed selector) | Not present under that exact raw spelling. **Exactly one** raw hierarchy-marked candidate: `Emissions|CO2|Land|Land-use Change|+|Regrowth` | Neither unmarked nor plus-marked spelling reported |
| `Emissions|CO2|Gross Fossil Fuels and Industry` | **One** raw `Mt CO2/yr` source record with a present 2050 value | Not reported under that exact name |
| `Carbon Sequestration|Land Use` | **One** raw `Mt CO2/yr` source record with a present 2050 value | **One** raw `Mt CO2/yr` source record with a present 2050 value |

**Primary transformation code found, version-appropriate:** The archived Rmd line 145 executes `data <- deletePlus(data)`. The upstream [REMIND 2021 `R/deletePlus.R` implementation](https://rdrr.io/github/pik-piam/remind/src/R/deletePlus.R), documented as of September 2021, applies `gsub('(\\+|\\++)\\|','',getNames(mif))` for MAgPIE objects. This strips plus hierarchy tokens immediately before `|`, mapping precisely the observed original author MIF's `...|Land-use Change|+|Regrowth` to its unmarked Rmd selector. **The 2021 helper provides direct software support for the transform**, beyond the previous purely proposed marker removal. The original raw source series is nonetheless NOT present in AR6 World under those names.

### New source-locked operational accounting computation, pending real local test

The `arc24-cemics-author-accounting` module now accepts the source's uniquely identified +/++-hierarchy **regrowth** field only after confirming original Rmd `deletePlus` and the seven source-formula strings. It refuses duplicate postprocessed names, duplicate same-unit source records, unexpected units and absent year values. It does **not** reinterpret `Carbon Sequestration|Land Use` as regrowth. It separately permits the directly selected, uniquely reported **authors'-archive-only** Gross Fossil Fuels and Industry value for a different-scope comparison, marking both inputs as author-only and **NOT** AR6 matched.

All other CDR operands (`Emissions|CO2`, EW, biomass CCS, DAC) still require exact reported-decimal equality between the locked original author MIF and AR6 World source. The calculated formula remains **exactly**:

`CDRtotal = (-Regrowth_source_emissions) + EW + Biomass_CCS + DAC`; `CO2pos = Net_CO2 + CDRtotal`.

The public file reports **only** source-name/unit/status provenance and signs/broad difference bands; all numeric original source/regrowth/gross values stay private. An exact algebraic CO2pos identity is **not independent physical carbon mass-balance evidence**. Source model/version documentation, CDR physical netness/durability/land additionality and independent I3 review remain open (verified I3=0).

New synthetic tests include author-only plus-marker regrowth, author-only gross, multiple postprocessed-name collisions, duplicate original gross-unit rows, and missing source preprocessing. Tests and the real run of this new patch **are not yet confirmed by the user**.

### Next run

```powershell
cd 'E:\New folder (2)\MissionJob\residual-pathways'
git pull --ff-only
& .\.venv-messageix\Scripts\python.exe -m pytest -q tests/test_arc24_cemics_field_lineage.py tests/test_arc24_cemics_author_accounting.py
if ($LASTEXITCODE -ne 0) { throw 'Source accounting regression tests failed' }
& .\.venv-messageix\Scripts\python.exe -m residual_pathways arc24-cemics-field-lineage
if ($LASTEXITCODE -ne 0) { throw 'Source name-lineage CLI failed' }
& .\.venv-messageix\Scripts\python.exe -m residual_pathways arc24-cemics-author-accounting
if ($LASTEXITCODE -ne 0) { throw 'Original authors accounting computation failed' }
$a = Get-Content 'results/ar6-canonical-gate/arc24_cemics_author_accounting_public.json' -Raw | ConvertFrom-Json
$a.individual_source_terms | Select-Object variable,original_author_raw_variable,source_comparison_status,source_value_sign,provenance | Format-Table -Wrap -AutoSize
$a.operational_study_accounting | Format-List
$a.study_CO2pos_vs_separate_gross_fossil_industry | Format-List
```

**Interpretation criterion:** a successful new run may establish the authors' operational study CDR basket numerically at 2050 while still **not** establishing an exhaustive mutually exclusive physical total-emissions/CDR partition. No I3 promotion is permitted from the arithmetic definition alone.
## 10. REAL original authors' 2050 `CDRtotal` and `CO2pos` successfully computed — 24 October 2026

**Local execution evidence, not synthetic fixture:** user pulled GitHub commit `40e64e3`; **20/20 regression tests passed** across field lineage + operational accounting. Both real source-locked commands finished successfully; the earlier field-lineage reporting-only KeyError is fixed. No original raw source emissions or privately selected 2050 figures were exported.

| Real 2050 source input or derived study measure | Original source provenance | Observed sign or status |
| --- | --- | --- |
| `Emissions|CO2` (`CO2tot`) | **Authors' MD5-verified MIF + AR6 World SHA-verified** original Decimal match | POSITIVE |
| Rmd `CDRaff = -Regrowth` | Unique authors' raw `Emissions|CO2|Land|Land-use Change|+|Regrowth`, transformed by original Rmd `deletePlus` (absent AR6 World) | Raw signed source NEGATIVE; *derived regrowth removal* POSITIVE |
| Enhanced weathering | Source-author and AR6 originally reported series exactly match | ZERO |
| Biomass CCS | Source-author and AR6 originally reported series exactly match | POSITIVE |
| Direct air capture | Source-author and AR6 originally reported series exactly match | ZERO |
| Authors' `CDRtotal` = `-Regrowth+EW+BiomassCCS+DAC` | **All five formula operands now source-backed**; source code lines 150–155; one operand author-only | POSITIVE; `AUTHORS_EXPLICIT_FORMULA_COMPUTABLE_NOT_I3` |
| Authors' `CO2pos` = `CO2tot+CDRtotal` | Original analysis-code line 156; now reproducible | POSITIVE |
| `Emissions|CO2|Gross Fossil Fuels and Industry` | Unique authors' MIF original 2050 record and original Rmd source lines 193–194; **absent in AR6 World** | POSITIVE |
| `Emissions|CO2|AFOLU` | Authors' MIF + AR6 reported-decimal matched | POSITIVE |
| `Carbon Sequestration|Land Use` | Authors' MIF + AR6 matched; **not substituted for regrowth** | POSITIVE |
| `Carbon Sequestration|CCS|Fossil` | Authors' MIF + AR6 matched; **not treated as atmospheric CDR** | POSITIVE |

### High-value, nonzero boundary finding

`study_CO2pos_vs_separate_gross_fossil_industry` status **`DIFFERENT_SCOPES_AUTHOR_GROSS_ONLY_COMPARISON`**; derived authors' `CO2pos` is **greater than** original authors' `Emissions|CO2|Gross Fossil Fuels and Industry` for ARC24-03/World/2050. Reported-decimal **difference is nonzero and at least 10%** of `max(1, abs(CO2pos), abs(gross fossil industry))`. This is a **coarse relative band**, not a share of one named gross component and not a publication of restricted numeric quantities. Both derived positive-side emissions and source Gross Fossil/Industry are positive.

**Scientific reading:** The two metrics have **different declared scopes**, so equality is **not** a source-imposed equation; the ≥10% difference is **not evidence of non-closure, source rounding or a mass-conservation failure**. The boundary difference is large enough to justify an independent source-taxonomy review before ever describing `CO2pos` as physical economy-wide gross. The 2021 REMIND2.1 model description separately includes emissions from energy/industry, land use and other categories, and allows distinct CDR options; see Baumstark et al., *Geosci. Model Dev.* 14, 6571–6603 (2021), https://doi.org/10.5194/gmd-14-6571-2021, §3.4. Gross fossil-industrial CO2 by its name does not exhaust potential positive land-use emissions; however **this specific gap has NOT been decomposed into land/other source components**.

Contemporaneous MAgPIE-related literature, [*Land use change and carbon emissions of a transformation to timber cities*](https://pmc.ncbi.nlm.nih.gov/articles/PMC9427734/), describes signed regrowth fluxes and positive gross land-use-change emissions as distinct components. This supports a **model-family interpretation**, not the exact 2021 CEMICS export-specific source decomposition. For citation-ready model attribution, verify exactly which 2021 land reporting version was used, the AFOLU netting convention and original gross fossil-sector construction from model reporting code. Do not import a later MAgPIE version's exact formulas as if author-run 2021 source semantics were independently proven.

### Clear gates

- **Source-series identity:** verified for the selected matching World records (the previous 4,653/4,653 author-noCDR ↔ AR6-minCDR crosswalk).
- **Original study's operation:** **reproduced numerically** for World 2050 using primary MIF, exact Rmd formula and confirmed source-only regrowth field.
- **Original study `CO2pos` vs independent fossil+industry gross:** numerically compared; **different boundaries, >10% positive gap**, not a required equality.
- **Physical gross/removals closure:** **NOT VERIFIED**; anthropogenic land-regrowth additionality, gross land emissions, lifecycle/storage permanence, overlap with BECCS and carbon from fuels and other sectors require source-definition checks.
- **Independent external I3 review:** **0**, no promotion.

**Stop rule:** Do not rerun the same near-identity or broaden the scope of source-data arithmetic without new independent model/reporting definitions. The next high-ROI work is source-taxonomy investigation of `Emissions|CO2|Gross Fossil Fuels and Industry` and positive land gross fluxes, and how AFOLU net emissions and biomass/land regrowth are combined. A manuscript should report `CO2pos` as **authors' operational positive-side measure**, not certified physical economy-wide gross.
## 11. Land and gross carbon source name audit — original two-name output is NOT a full land inventory (24 October 2026)

**User's actual printed result** from previous `arc24_cemics_field_lineage_public.json`:

```text
Emissions|CO2|Gross Fossil Fuels and Industry        author=True, AR6=False, Mt CO2/yr
Emissions|CO2|Land|Land-use Change|+|Regrowth       author=True, AR6=False, Mt CO2/yr
```

**Scope correction:** This two-line result is **not a finding that the source MIF only has two gross/land components**. The earlier code populated `context_name_inventory` only for names containing *literal* `regrowth`, `gross fossil fuels` or `land-use change`; the user then applied a second `-match 'Land-use Change|Gross Fossil'` filter. Thus other land/forest/AFOLU variables, and gross source fields whose names do not contain those exact phrases, were not screened at all. It would be invalid to claim there are no other positive land emission variables, or to quantify the previously observed `CO2pos − Gross Fossil Fuels and Industry` gap as land use from this two-line output.

### More comprehensive and still privacy-safe scan now implemented (pending local user run)

`arc24-cemics-field-lineage` continues verifying the original Strefler authors' MIF and Rmd MD5s, AR6 World SHA and exact cohort case ID, but now adds an **expanded emissions-family name inventory** with the following overlapping *search buckets*:

- `co2_land_reporting`: all exact original variable names beginning `Emissions|CO2|Land`.
- `gross_co2_reporting`: emission variable names with `Gross` in the CO2 reporting hierarchy.
- `fossil_and_industry_reporting`: CO2 names mentioning fossil fuels/industry or energy and industrial processes.
- `afolu_or_other_reporting`: CO2 AFOLU, Other or land-use change hierarchy.
- `land_sequestration_reporting`: land-use or afforestation sequestration variables.
- `cdr_technology_reporting`: carbon sequestration names of every reported technology.
- `broad_land_emissions_and_cdr`: wider land, forest, deforestation, regrowth and AFOLU-related CO2 and sequestration identifiers.

For each group, the JSON records every source-variable name (max 180 listed per group, with an explicit truncation flag), original author vs AR6 presence, full original reporting unit names, count of same-unit records and 2050 cell presence, **without numeric carbon observations or reconstructed totals**. Buckets can overlap; nested reporting variable names do **not** certify mutually exclusive sector streams or give permission to sum parent/child categories. The old narrow context section is retained for backward compatibility, so readers must inspect `expanded_emissions_family_inventory` rather than mistake `context_name_inventory` for a general inventory. Regression tests now include off-filter land conversion, gross industry, source-only CCS, overlapping name groups and truncation. The new code/tests are **committed but not yet run on the author's real MIF**.

### Independent methodology evidence (not a historical exact export mapping)

The peer-reviewed [REMIND2.1 2021 model description](https://gmd.copernicus.org/articles/14/6571/2021/index.html), §§2.4.1, 3.2.5, 3.4.1–3.4.3, describes energy/industry emissions, exogenous or MAgPIE-coupled land-use emissions, and four CDR options. This is credible reason to inspect the relevant source reporting hierarchy and document gross land emissions separately from fossil industry emissions. A [2020 REMIND-EU reporting code fork](https://rdrr.io/github/Renato-Rodrigues/REMIND-EU_reporting/src/R/reportEmi.R) separately constructs `Emi|CO2|Gross Fossil Fuels and Industry` from energy/industry terms and a `Land-Use Change` category, but **that fork is not proven to be the exact Strefler 2021 CEMICS author reporting implementation**, and its names use a shorter `Emi` namespace. Treat it as a *testable methodological lead*, not a substitute for the original author model code, an exact gross equation or a physical partition proof.

### Local read-only science audit

```powershell
cd 'E:\New folder (2)\MissionJob\residual-pathways'
git pull --ff-only
& .\.venv-messageix\Scripts\python.exe -m pytest -q tests/test_arc24_cemics_field_lineage.py
if ($LASTEXITCODE -ne 0) { throw 'Expanded source hierarchy synthetic tests failed' }
& .\.venv-messageix\Scripts\python.exe -m residual_pathways arc24-cemics-field-lineage
if ($LASTEXITCODE -ne 0) { throw 'Expanded source hierarchy original scan failed' }
$l = Get-Content 'results\ar6-canonical-gate\arc24_cemics_field_lineage_public.json' -Raw | ConvertFrom-Json
$l.expanded_emissions_family_inventory.PSObject.Properties | ForEach-Object {
    $g = $_.Value
    Write-Host "`n=== $($_.Name) === (names: $($g.total_distinct_variable_names), truncated: $($g.names_truncated))"
    $g.reported_fields | Select-Object original_variable_name,author_reported,ar6_reported,author_units | Format-Table -Wrap -AutoSize
}
```

**Interpretation stop rule:** do not recalculate a new gross/land total from a variable family listing. Before such arithmetic, locate source-specific reported positive land-flux formulas, sign conventions, net AFOLU relationships, capture source/storage accounting and disjointness. I3 stays at **0**.