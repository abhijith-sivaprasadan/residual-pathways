# When Do Integrated Assessment Scenarios Identify Residual Positive CO₂ Emissions? A Reproducible Reporting-Coverage and Accounting-Readiness Pilot

**Independent working-paper draft — 23 October 2026 — UNREVIEWED. Not submitted to a journal.**

**Authorship:** Abhijith Sivaprasadan (independent project; no IIASA affiliation or collaboration is claimed)

## Abstract

Integrated assessment model (IAM) scenario data are frequently used to compare net-zero pathways and carbon dioxide removal (CDR) requirements. Yet a reported net emissions variable is not necessarily a complete partition of positive atmospheric emissions, negative atmospheric carbon flows and avoided emissions due to fossil carbon capture and storage (CCS). This exploratory methods paper tests whether reporting coverage can be reproducibly audited *before* attempting a positive-gross emissions decomposition. We analyse a publicly published, IIASA-labelled World-region AR6 **teaching subset**, together with an independently redistributed climate-vetted v1.1-named metadata workbook; the source hashes and provenance are retained, but the inputs have not been authenticated against the restricted canonical World v1.1 assessment download. The World subset contains 693,299 IAMC series and 2,298 distinct Model×Scenario pairs. Of 1,202 climate-vetted pairs, 422 report a direct air capture variable for 2050; 330 simultaneously report an initial six exact-name carbon accounting candidates, and 261 co-report a stricter candidate set including energy-industrial CO₂, net AFOLU, land-use sequestration, biomass CCS, fossil CCS and direct air capture. Co-reporting alone is not scientific identifiability. A deterministic nonprobability 24-case selection spans eight climate categories and three reporting-completeness levels; seven selected cases report the six specified candidate variables and 19 permit a three-term arithmetic diagnostic, but no case has been validated as an exhaustive positive-gross partition. Separate four-year coverage tests generate 352 category-year-variable records, while a controlled N₂O mass/GWP100 methodological comparison demonstrates a 2.20% change in calculated CO₂-equivalent arising solely from the correction of the assessment metric. A hypothetical optimisation exercise is solved and cross-checked with two independent algebraic formulations using HiGHS, but is unrelated to real IAM trajectories. The defensible contribution is an auditable, fail-closed reporting and scientific-readiness workflow, not a gross emissions estimate or causal technology ranking.

**Keywords:** integrated assessment models, IAMC, mitigation pathways, reporting completeness, identifiability, positive gross CO₂, negative emissions, carbon dioxide removal, scenario selection.

## 1. Introduction and research questions

Net-zero ambitions require distinctions between residual positive atmospheric CO₂ flows and separately sourced atmospheric carbon removal. An aggregate reported emissions pathway can be negative when a physical system simultaneously emits positive CO₂ and sequesters carbon. It is incorrect to treat the positive part of an aggregate net series as gross positive emissions. Likewise, avoiding a fossil-point-source stack emission through CCS is not the same operation as removing existing atmospheric CO₂. These distinctions are established in IPCC AR6 WGIII Chapters 3 and 12 and its terminology for CDR.

The practical problem is one of **identifiability**, not chart production. When modelling groups submit variables under the IAMC semihierarchical naming system, matching variable paths do not automatically guarantee additive physical boundaries. Parent and child variables may be netted, overlapping, model-specific or inconsistently reported. Missing values cannot be substituted with physical zeros.

This pilot asks: (A1) What exact-variable 2050 reporting coverage exists in climate-vetted pathways? (A2) How many scenarios co-report particular carbon-accounting candidates, and how does this differ by category? (A3) How robust are reporting conclusions across years and exact model-label weighting? (A4) Can an explicit, preregistered 24-case forensic sample be prepared without inventing scientific source reviews? (A5) Which N₂O comparisons can be made under a documented GWP convention while avoiding guessed methane-origin splits? Separately, it tests small synthetic optimisation and an evidence-constrained research-operations handoff.

## 2. Evidence sources, rights and limitations

The large real-source input is the published **AR6 World data teaching release** at Zenodo record 20056332 (DOI 10.5281/zenodo.20056332), with source SHA-256 4cf39b6b0d968e25ed389318acb1674f92146f977e9db4bfb7970f048ff73977. It is described by the depositor as a subset made available for teaching and measures 361,767,203 bytes in our reproducible pipeline. A separately redistributed workbook named AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx has SHA-256 7d22453bdda52e95cea4df46d362018951dd7114e62f01f5bcea65d6e24a7790. The two datasets have not been matched against original canonical IIASA file hashes and are not used to assert official full-database assessment reproducibility.

The original official AR6 v1.1 World and metadata exports are routed through the IIASA Scenario Explorer; reuse for scientific analysis is permitted under restrictions on substantial rehosting. Accordingly, raw source scenario rows, local reviewer packets and restricted source files are not published from this codebase. Only aggregate counts, method code, anonymised coded cases and provenance notes are released. The project is independently authored, without collaboration or endorsement from IIASA, IPCC, IAM developers or any Real Zero consortium.

## 3. Methods

### 3.1 Exact identity, year and metadata joins

The source parser requires Model, Scenario, Region, Variable, Unit and year. It preserves explicit numeric zero and absence separately, rejects nonfinite source observations and duplicate year-specific selected variable keys, and does not interpolate. Model×Scenario names are joined **exactly** with metadata. The climate-vetted population comes from the metadata workbook sheet named meta_Ch3vetted_withclimate. It must not be mixed with the workbook's broader meta sheet; the latter also includes failed-vetting and non-assessed records.

The four-year robustness method repeats reporting presence analysis for 2030, 2050, 2070 and 2100, retaining category-year-variable denominators. Its scenario-weighted presence fraction is the number of reporting scenarios divided by source-matched eligible scenarios in that category. A separate exact-model-label-balanced statistic averages within-label reporting fractions equally across distinct exact Model names. The latter is explicitly not independent model-family weighting: versions and related model implementations may share underlying frameworks.

### 3.2 Carbon-accounting candidate sets

The initial candidate set comprises reported aggregate CO₂, Energy CO₂, net AFOLU CO₂, fossil CCS, biomass CCS and direct air capture. The extended set used for the stricter result comprises Energy and Industrial Processes CO₂, AFOLU CO₂, Land Use sequestration, biomass CCS, fossil CCS and DAC. The extended set fixes neither process completeness nor net land accounting: nested/sectoral net values and sequestration pathways may overlap or remain incomplete. Its count therefore measures **co-reporting**, not the number of identifiable gross emissions pathways.

The intended physical accounting identity is net = gross positive atmospheric emissions − atmospheric removal, but only for a reviewed complete, non-overlapping same-gas/same-region/same-year/same-sector process partition. No empirical I3 identity is asserted.

### 3.3 Twenty-four-case purposive preflight

Before viewing individual source magnitudes, each climate category C1–C8 was ordered by the number of simultaneously reported, same-unit candidate variables (0–6). Stable SHA-256 ties determined the order. The minimum, lower median and maximum were selected, three distinct Model×Scenario cases per category, 24 cases total. This is deliberately a **purposive extremes/median selection**, not a probability sample. It can reveal failure modes but cannot estimate the I3 prevalence among 1,202 scenarios.

The automated local packet enumerates selected source observations, incompatible or missing units, and an exploratory reported-total minus reported EIP minus reported AFOLU difference. That difference is a numerical diagnostic only. The public coded register removes original model/scenario names and source values. All cases are explicitly NOT_REVIEWED and their accounting grade is NOT_DETERMINED.

### 3.4 Quantization, materiality and scientific release gates

The implemented provisional gate compares an eventual source-reviewed net N against non-overlapping positive gross G and atmospheric removal R, calculating the absolute residual |N − (G − R)|. It separately requires documented semantics, source original reporting quantization for every input, a numerical tolerance half the sum of source quantization quanta plus a floating-point floor, a materiality criterion based on net magnitude and source traceability. A balanced equation cannot bypass a missing or overlapping sector. No arbitrary source decimal display precision is presumed.

The method is *provisional*: the v3 plan's numerical thresholds have **not** been frozen after real precision review. Passing a synthetic test fixture or a user-declared review flag never constitutes a real external scientist's signoff. Six mandatory synthetic counterexamples cover exact identity, near-zero cancellation, deliberate inconsistency, sector overlap, missing land sector and unresolved quantization.

### 3.5 Gas-specific source and GWP convention pilot

The data report N₂O as kt N₂O/year; converting mass to Mt N₂O/year requires division by 1,000. The project compares the original IPCC AR6 WGI GWP100 for N₂O of 273 to the 7 October 2025 correction of 267 on **identical, source-reported N₂O mass values**. Results are an arithmetic change in the assessment convention, not a physical emissions response. Methane remains source-origin-ambiguous for these reported aggregates; direct conversion with either fossil or nonfossil methane GWP is forbidden without an independently established split. An existing CO₂e aggregate is not converted again.

### 3.6 Distinct synthetic control and operations test

A one-period 100 TWh electricity linear programme contains renewables, fossil generation, fossil point-source CCS, a positive atmospheric emissions balance and a separate direct-air removal decision. Costs, resource bounds and emissions intensities are hypothetical. Six cases are solved in SciPy/HiGHS and an **independently encoded Pyomo/HiGHS formulation**, with optimum/feasibility comparison and an intentional infeasible extreme. Neither is MESSAGEix or an observed energy-system model. PathwaysHub separately validates author-authored fictional partner submissions, failures, revisions and evidence-labelled briefings without inventing interpersonal coordination.

## 4. Results

### 4.1 Cohort coverage and co-reporting funnel

The World teaching source contains 693,299 IAMC series and 2,298 distinct World-region Model×Scenario identities. The climate-vetted metadata cohort yields 1,202 matched cases. At 2050, 422 climate-vetted cases have a finite DAC reported value; 330 co-report the initial six candidates. When the stricter extended set includes net EIP and Land Use sequestration alongside AFOLU, biomass CCS, DAC and fossil CCS, 261 cases co-report all six required exact-name variables (21.7% of vetted scenarios).

| Climate category | Matched vetted cases | DAC variable reported | Stricter six-variable co-reporting |
|---|---:|---:|---:|
| C1 | 97 | 38 | 19 |
| C2 | 133 | 32 | 13 |
| C3 | 311 | 127 | 66 |
| C4 | 159 | 57 | 50 |
| C5 | 212 | 87 | 66 |
| C6 | 97 | 42 | 30 |
| C7 | 164 | 32 | 17 |
| C8 | 29 | 7 | 0 |
| **Total** | **1,202** | **422** | **261** |

Neither 261 nor 330 is an estimate of the number of scenarios genuinely reconstructible at I3. This is **variable presence**, inclusive of reported zero, with possible overlapping/nested definitions and unreported alternative removals. Population composition matters: all 1,202 cases are climate-vetted, while the broader metadata/source join also includes 587 failed-vetting and 509 not climate-assessed source identities. Numerator and denominator selection must be disclosed for any cross-model comparison.

### 4.2 Case-selection diagnostic

The registered preflight selected 24 distinct cases in all eight C1–C8 categories. Seven have all six specified reporting candidates with compatible 2050 units, and 19 have a computable three-term exploratory arithmetic diagnostic. In the C8 category even the highest-ranked selected case reports five of the six candidates. These numbers are features of a **nonprobability purposive sample**, not sample estimates of population I3.

No model/version-specific source accounting or original export precision has yet been reviewed. Accordingly no actual case has been admitted to I1, I2 or I3 by reviewer decision. The observed presence results do not reveal whether the reported net and constituent processes form any exact physical partition.

### 4.3 Four-year reporting robustness

The four-year World metadata-stratified audit computed 352 category×year×variable reporting records (8 categories × 4 years × 11 variables) and the two alternative reporting denominators for each. The source-derived machine-readable category/year table is available as the GitHub Actions aggregate-only research artifact. Comparisons reveal what a chosen cohort reports, not independently distributed future uncertainty or an innovation's causal effect.

### 4.4 N₂O conversion sensitivity

All 1,202 climate-vetted source scenarios report N₂O in 2050. The published category-level table in Research Note 03 gives original and corrected mean N₂O CO₂e per reporting scenario; for any fixed mass the corrected GWP100 factor changes the numerical CO₂-equivalent by (267/273 − 1) = **−2.20%**. This difference is a reporting/assessment-method effect, not a mitigation effect and not a total scenario ensemble emissions value.

### 4.5 Synthetic optimisation

The synthetic SciPy reference baseline has renewable generation 60 TWh, fossil generation 40 TWh, captured fossil source CO₂ 13 Mt, atmospheric DAC 0 Mt, and net atmospheric CO₂ 25 Mt, with a hypothetical objective of 5,544 million USD. A renewable cap of 30 TWh, a storage cap of 10 Mt and a stricter net emissions cap yield distinguishable optimum responses; an intentionally severe joint capacity constraint is correctly infeasible. The independent Pyomo algebra reproduces all six SciPy cases to tolerance, but shares the HiGHS solver family. It cannot validate IAM assumptions or establish MESSAGEix/GAMS competence.

## 5. Discussion: scientific interpretation and threats to validity

This study demonstrates that reporting completeness is a measurable methodological bottleneck prior to emissions decomposition. It provides reproducible denominators, source-provenance assertions and negative tests against common failure modes (missing observations, nested sector names, false fossil CCS-as-CDR, phantom quantization, near-zero cancellation). However the headline co-reporting rates should not be interpreted as a measured level of technical mitigation feasibility or as an actual I3 fraction.

Selection bias matters in at least four ways. First, the teaching subset has not been authenticated against the licensed canonical assessment file; not every assessed IAM pathway need occur in this extract. Second, the climate-vetted sheet is not the same population as all scenario submissions. Third, complete-case selection is associated with models that report a more detailed set of variables and may shift the effective model/scenario composition. Fourth, identical names do not guarantee independent model families, and climate categories arise from assessment outcomes rather than random assignment. Different scenario outputs are observational, not controlled experiments.

No source-reviewed exhaustive positive-emissions/removal partition, permanence boundary, biological sink decomposition, fossil CCS subtraction identity or report-specific numeric quantum has been validated for a real selected case. The current software cannot infer any of those from a close arithmetic result. Such review is a scientific prerequisite, not an implementation detail that should be bypassed.

The N₂O exercise is useful precisely because it does not conflate a physical emissions change with a metric change. A methodology that changes GWP values without citing the assessment version can show apparent emissions differences even when raw mass is unchanged. Other gases need comparable raw source decompositions and explicit conventions; a reported Kyoto Gases aggregate cannot be reverse-engineered from a handful of component series.

## 6. Open gates and future research

Before a claim about positive gross CO₂ can be made, obtain and authenticate the licensed canonical AR6 World v1.1 and metadata, perform the source-specific 24-case scientific review, establish an exhaustive mapping and original precision for every candidate, and publish provenance-linked acceptance/exclusion reasons. Sensitivity to rounding, materiality and model/version definitions must be analysed after the source requirements are met.

Before claiming MESSAGEix experimental experience, obtain the real GAMS installation/license, execute the official version-pinned Westeros baseline, retain solver logs and run matched controlled variants. The current Pyomo experiments are a separate valid *synthetic* fallback. Before claiming external coordination, recruit and record consenting non-author submitter/reviewer participants; the current PathwaysHub test is simulation-only.

An independent historical emissions benchmark, harmonised for gas/region/source-sector boundaries, would improve external consistency analysis but has not been performed. A full systematic literature novelty review and independent scientific scrutiny also remain outstanding. No field trial, original model publication, peer review or actual stakeholder sign-off is implied.

## 7. Conclusion

The empirical contribution is a reproducible, source-traceable workflow measuring reporting coverage and documenting why reported net CO₂ should not be mistaken for positive residual gross emissions. A useful and reproducible **identifiability-preflight** can be completed without pretending that the model submissions provide a scientifically proven exhaustive partition. The present study does **not** yet estimate residual positive gross CO₂, the relative causal importance of technologies, or policy impacts. Research Note 01, Research Note 02 and Research Note 03 provide separate machine-checkable layers behind this working-paper draft.

## References

1. IIASA and IAMC. IPCC AR6 scenario ensemble v1.1. Zenodo: https://zenodo.org/records/7197970.
2. IIASA. Public teaching release of AR6 World data, v1 (2026). https://zenodo.org/records/20056332.
3. IPCC AR6 WGIII. Chapter 3, Mitigation Pathways Compatible with Long-term Goals. https://www.ipcc.ch/report/ar6/wg3/chapter/chapter-3/.
4. IPCC AR6 WGIII. Chapter 12, Cross-sectoral Perspectives and Carbon Dioxide Removal. https://www.ipcc.ch/report/ar6/wg3/chapter/chapter-12/.
5. IPCC AR6 WGIII. Annex III, Scenarios and Modelling Methods. https://www.ipcc.ch/report/ar6/wg3/.
6. IAMC/IIASA. Semi-hierarchical scenario-variable nomenclature and reporting guidance. https://docs.ece.iiasa.ac.at/standards/variables.html.
7. Prütz et al. (2025). Land-use carbon flux reporting and CDR interpretation. Earth System Science Data. https://doi.org/10.5194/essd-17-221-2025.
8. IPCC AR6 WGI. Chapter 7 climate-system energy budget and published October 2025 errata. https://www.ipcc.ch/report/ar6/wg1/about/errata/.
9. MESSAGEix. Versioned Westeros tutorial and documentation. https://docs.messageix.org/en/stable/tutorials.html.

---

**Reproducibility package:** ResidualPathways, Research Notes 01–03, v3 scientific accounting protocol, the source-hashed public AR6 teaching-release CI, synthetic Pyomo/SciPy tests, aggregate-only coded source outputs and companion PathwaysHub source-to-briefing integration. No licensed bulk scenario data are republished. This text is an unreviewed working-paper draft, not an official assessment.
