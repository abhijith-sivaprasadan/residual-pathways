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