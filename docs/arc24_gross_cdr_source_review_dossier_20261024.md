# ARC24 scientific carbon-flow review dossier — first evidence review, 24 October 2026

**Purpose:** transition from arithmetic source-preflight to model/experiment-specific carbon-flow semantics for ARC24-03 (REMIND-MAgPIE 2.1-4.2, CEMICS_SSP1-1p5C-minCDR) and ARC24-06 (POLES ENGAGE, EN_NPi2020_400f). Scientific grades remain NOT_DETERMINED, verified I3=0. This is a **source-reading and evidence-gaps docket**, not an independent expert sign-off.

## The arithmetic phase has stopped

Author-run World v1.1 selected 24-case results: 19 computable total-EIP-net-AFOLU checks, five exactly equal at reported decimal serialization, 14 nonzero; four POLES ENGAGE pathways account for the four 2050 1–10% case residuals. Across these four model-scenario pairs and five years, all 20 original residuals were nonzero. The separately reported `CO2|Other` series accounts numerically for almost the entire residual: 20/20 signs match, and 20/20 residual-minus-Other differences were below 0.001% of the largest compared reported source term. The detailed ENGAGE-style expanded equation is likewise within 0.001% in 20/20, but zero exact. The detailed Demand+Supply+Industry minus EIP differences are 10 small negative, nine small positive, and one exact, all below 0.001% where nonzero. These are algebraically related checks, not independent physical validation. **Do not create more exploratory aggregation corrections without new primary-source semantics.**

## Primary source discoveries

1. **Study-level CEMICS paper:** Strefler, J., Bauer, N., Humpenöder, F., Klein, D., Popp, A., and Kriegler, E. (2021), *Carbon dioxide removal technologies are not born equal*, Environmental Research Letters 16, 074021, DOI [10.1088/1748-9326/ac0a11](https://doi.org/10.1088/1748-9326/ac0a11). The paper studies several CDR portfolios including a minimum-CDR scenario and distinguishes *gross emissions reduction* from offsets by afforestation/reforestation (AR), enhanced weathering, DACCS and BECCS. The paper includes an SSP2 core set and SSP1 supplementary analyses. **Do not assume a given paper's plotted minimum-CDR SSP2 values are the ARC24-03 SSP1 source scenario.**
2. **Authors' reproducibility archive:** Strefler et al., [Zenodo release version 2, record 5103024](https://zenodo.org/records/5103024), CC BY 4.0. The authors state version 2 does not change results but aligns **scenario names and variable categories** with AR6, and include `CDRoptions.Rmd`, `CDRoptionsAR6_complete.mif` (~30.9 MB), `readme_zenodo.txt` and region mapping. **Critical next source comparison:** check that `CEMICS_SSP1-1p5C-minCDR` is present with exact source model/version and Year=2050; match original study's carbon-flow variables to the v1.1 World submission; document any metadata/name differences. No archive contents or case-specific values have yet been inspected locally in this review.
3. **Model family and coupling:** Baumstark et al. (2021), [REMIND2.1: transformation and innovation dynamics...](https://doi.org/10.5194/gmd-14-6571-2021), describes emissions representation in Sect. 3.4 and afforestation, BECCS, DACCS, enhanced weathering, bioenergy systems and soft coupling to MAgPIE. The paper focuses on REMIND2.1 and reports a 2.1.3 source configuration; **version equivalence with the precise combined 2.1-4.2 submission remains to be checked**.
4. **AR6 land boundary limitation:** Prütz, Fuss and Rogelj (2025), [Earth System Science Data 17, 221–...](https://doi.org/10.5194/essd-17-221-2025) differentiates signed **net AFOLU** from separately reported **gross land sequestration** and documents incomplete/unstandardized land-removal reporting. IPCC AR6 WGIII [Chapter 3](https://www.ipcc.ch/report/ar6/wg3/chapter/chapter-3/) explicitly warns that cumulative AFOLU carbon removals are not precisely comparable across models due to mixed net/gross conventions and baseline choice.
5. **POLES context:** [IAMC POLES emissions documentation](https://www.iamcdocumentation.eu/Emissions_-_POLES) outlines energy/industrial emissions in POLES and AFOLU linkage to GLOBIOM/G4M, while the [ENGAGE Netzero Analysis notebook](https://data.ece.iiasa.ac.at/engage-netzero-analysis/notebooks/1_categorization.html) constructs `Emissions|CO2|Other` as a remainder of Total minus AFOLU and three detailed energy/industrial sectors in a related 2021/2022 data snapshot. Neither document independently certifies original AR6 POLES-ENGAGE submission sector *disjointness*, source rounding precision, nor that `Other` represents a physical emitting branch.

## Preliminary role classification: reporting candidates, not certification

| AR6 variable in original ARC24 private source | Provisionally safe interpretation | What still blocks a gross/removal reconstruction |
| --- | --- | --- |
| `Emissions|CO2` | Net-like reported total CO2 aggregation | No exhaustive independent gross positive emissions or removal split demonstrated |
| `Emissions|CO2|Energy and Industrial Processes` | Reported sector aggregation; can include offsets/capture already embedded | Verify whether scope is net, what emissions processes are counted, whether bioenergy, bunkers and CO2 Other overlap |
| `Emissions|CO2|AFOLU` | **Signed net** land/agriculture/forestry CO2 under AR6 conventions | Cannot treat negative values as the same observable as gross land sequestration, nor add land sequestration to it without source mapping |
| `Carbon Sequestration|Land Use` | Separately reported positive gross land uptake proxy | May overlap pre-netted AFOLU and differ among baselines/natural vs anthropogenic land sink |
| `Carbon Sequestration|CCS|Biomass` | Biomass-origin captured CO2 reported as a sequestration flow | Requires biogenic atmospheric uptake, life-cycle treatment, storage durability and partition overlap checks before crediting atmospheric CDR |
| `Carbon Sequestration|CCS|Fossil` | Fossil-origin captured/stored CO2; an avoided/mitigated fossil release, **not an atmospheric removal** | If already netted from emitted fossil CO2, subtracting it twice creates a false sink |
| `Carbon Sequestration|Direct Air Capture` | Reported gross atmospheric capture technology flow, e.g. ARC24-03 has *source-reported zero* at 2050 | Confirm storage/durability, process emissions and whether same atmospheric removal appears in another branch; zero ≠ globally nonexistent |
| `Emissions|CO2|Other` (not necessarily present in every model) | Additional source-reported residual/accounting category in tested POLES ENGAGE export | May be constructed by postprocessing; do not treat as an independent gross emission category |

These terms are generally not automatically disjoint. Even if `net total = sum reported sectors` matches numerically, it does **not** imply `net = sum exhaustive positive gross emissions − sum true atmospheric removals`.

## Two-case scientific review matrix

| Gate | ARC24-03 REMIND-MAgPIE (CEMICS SSP1 minimum CDR) | ARC24-06 POLES ENGAGE |
| --- | --- | --- |
| Original AR6 World v1.1/source hash and 2050 candidate variables | Source-native, six candidate variables present | Source-native, six candidate variables present |
| AFOLU sign, land sequestration | Signed AFOLU positive, separately positive land sink | Signed AFOLU negative, separately positive land sink |
| EIP + AFOLU vs total | Exact source-decimal equality in 2050 | Nonzero but Other explains almost all 2050/other-years difference |
| Case-/version-specific source model methodology | **Partially identified** 2021 study and AR6-aligned author data archive; exact scenario source crosswalk unverified | **Partially identified** related ENGAGE notebook, but exact source version/mapping unverified |
| Source-stated net/gross land semantics and CDR overlap | **Unknown** | **Unknown** |
| Exclusion of fossil CCS from atmospheric removals | Conceptually required; source export mapping still unverified | Same |
| Source-declared input/output quantization | **Unknown** | **Unknown** |
| Complete disjoint positive gross emissions partition | **Not demonstrated** | **Not demonstrated** |
| Complete disjoint atmospheric removal partition | **Not demonstrated** | **Not demonstrated** |
| Independent reviewed I3 grade | **NOT_DETERMINED** | **NOT_DETERMINED** |

## Next tasks, prioritized for scientific value

1. **ARC24-03:** inspect the primary 2021 Strefler study appendix/associated AR6-aligned Zenodo 5103024 Rmd and MIF metadata to establish an exact `CEMICS_SSP1-1p5C-minCDR` crosswalk; read study definitions for gross CO2, offsets by BECCS/AR/DACCS/EW, fossil CCS and how land-sector flux is netted. Note that main-text results are primarily SSP2; the exact source scenario is SSP1. This is a *source reconciliation* task, not adding speculative emissions corrections.
2. **ARC24-06:** find original ENGAGE submission/source team CO2 hierarchy documentation that establishes whether `Other` is a calculated reporting residual, which detailed streams comprise EIP, how linked land fluxes enter AFOLU, and treatment of biomass carbon/capture. The observable source-near-equality is already recorded; it does not need further repetitive tests.
3. **For both:** establish original release/export quantization (not inferred from number of CSV decimal places), complete positive-emission/true atmospheric removal partitions, mutually exclusive capture/sink pathways and source-prescribed signs/units. Record original reviewer evidence and a second independent reviewer before any I1/I2/I3 assignment.
4. **Only if supported by source mappings**, prepare a closed carbon-flow ledger with physically named process streams and numerical reconciliation in `data/ar6-private`; release no original scenario observations without explicit rights review. Do not promote selected 24-case population frequency or treat four POLES pathways as four independent models.

**Status:** first external model-level source dossier assembled; private source crosswalk, physical completeness and independent review **not done**. The 2021 author archive is a high-value new evidence lead, not a verified ARC24 case mapping.