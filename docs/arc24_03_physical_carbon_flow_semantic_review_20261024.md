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
