# Research Note 02 — Twenty-four-case forensic preflight of IAMC carbon-accounting reporting

**23 October 2026. Status: source-grounded exploratory methods note; not peer-reviewed. No case-level expert verification yet.**

## Abstract

We implement and execute a reproducible 24-case accounting preflight on a publicly published IIASA-labelled AR6 World *teaching release*, linked to a separately republished climate-vetted metadata workbook. The sample selects low-, median- and high-completeness scenarios in each of eight C1–C8 climate categories, without choosing cases based on reported emissions magnitudes. Each case receives six-variable reporting and unit checks plus a local-only review packet for model-specific documentation. Exactly 24 scenarios were selected; seven co-report all six chosen reporting candidates, and 19 have the three same-unit variables required for a provisional aggregate-minus-EIP-minus-AFOLU arithmetic diagnostic. These are **not** verified accounting identities: no case has undergone scientific semantic review, and zero I3 claims are made. The work exposes the distinction between scenario availability, source-variable coverage and a genuinely reconstructible gross-emissions identity.

## 1. Sources and provenance

The input is the 361,767,203-byte AR6 World teaching-release CSV (Zenodo record 20056332), with source SHA-256 **4cf39b6b0d968e25ed389318acb1674f92146f977e9db4bfb7970f048ff73977**. The metadata input was obtained from a third-party republishing of the named AR6 v1.1 metadata workbook, SHA-256 **7d22453bdda52e95cea4df46d362018951dd7114e62f01f5bcea65d6e24a7790**. Both are separately traceable, but these files have **not been authenticated by direct hash comparison with the original canonical official v1.1 downloads**. Consequently this note is a teaching-source pilot, not a canonical full-v1.1 paper.

The source covers 693,299 IAMC series and 2,298 World-region model–scenario identities. The selected chapter-3-vetted sheet provides 1,202 matched scenarios, with category sample populations: C1=97, C2=133, C3=311, C4=159, C5=212, C6=97, C7=164, C8=29. Failure of climate vetting or absence of climate assessment excludes a scenario from this preflight by design.

## 2. Registered case-selection protocol

For each category, evaluate the number (0–6) of finite 2050 values with exact variable names and matching Mt CO2/yr units across: EIP CO2, AFOLU CO2, land-use carbon sequestration, biomass CCS, fossil CCS and direct-air capture. A reported zero counts as reported; a missing observation never becomes zero. Sort cases by score with fixed SHA-256 tie breaking, then select the category minimum, lower median, and maximum. This produces **three per category and exactly 24 distinct cases**. No emissions magnitudes influence selection, and no reviewers select preferred results after inspection.

This is a *purposive contrast sample*, NOT a random representative sample. Neither seven complete cases out of 24 nor any later case-grade frequency is an estimator of AR6 population reporting or scientific identifiability. The population-level co-reporting measures are reported separately in the preceding source-audit findings.

## 3. Actual findings from automated source inspection

| Vetted climate category | Low completeness | Median completeness | High completeness |
|---|---:|---:|---:|
| C1 | 3/6 | 5/6 | 6/6 |
| C2 | 3/6 | 5/6 | 6/6 |
| C3 | 1/6 | 5/6 | 6/6 |
| C4 | 1/6 | 5/6 | 6/6 |
| C5 | 3/6 | 5/6 | 6/6 |
| C6 | 1/6 | 5/6 | 6/6 |
| C7 | 1/6 | 4/6 | 6/6 |
| C8 | 2/6 | 4/6 | 5/6 |

Results: **24** cases selected, **7** with all six variables in compatible units; **19** have sufficient exact-name, same-unit data for the exploratory three-term arithmetic check. No source-value imputation or forced unit conversion was performed. The missing 2050 terms block the arithmetic comparison in the other five cases. Seven complete cases occur in C1–C7 high-coverage slots; the highest-ranked selected C8 case has only five of the six variables.

Numerical differences for the 19 eligible cases are computed *locally* from the original data, but are not exported or described as physical mass-balance validation. No source rounding/quantization precision or scope-exhaustiveness proof has been established. Specifically, even a zero difference in CO2(total) minus CO2(EIP) minus CO2(AFOLU) would not establish **positive gross emissions** or an atmospheric removal partition.

## 4. Why this does not establish gross-emissions identifiability

IAMC standards explicitly describe variables as semi-hierarchical, rather than guaranteeing all subcategories sum additively. Aggregate emissions, EIP emissions, AFOLU net flux and carbon sequestration may therefore be nested or operate across different physical boundaries. Fossil point-source CCS is avoided fossil-source release, **not** atmospheric CO2 removal. Land-use carbon sequestration, bioenergy with CCS, direct-air capture and enhanced weathering require their own completeness, durability and lifecycle-boundary assessments. A reported variable might be exactly zero or omit another pathway; neither case authorizes treating an unreported physical process as zero.

The current 24-case public register intentionally labels every case **NOT_REVIEWED** and **NOT_DETERMINED** for I0/I1/I2/I3. Zero *verified* I3 claims reflects the unfinished review, not a conclusion that no scenarios could ever support I3.

## 5. Reproducibility and data handling

The source data and metadata are downloaded and verified through GitHub Actions. The run invokes the case-audit CLI and asserts exact source/metadata hashes, exactly 24 unique case IDs, three cases in each category, zero human-reviewed cases, zero verified I3 claims, and the existence of a separate local-only source-value review packet. CI uploads only an anonymized-by-label coded register and aggregate counts, never the original source scenario rows, their identities or private source values.

- [Complete reproducibility and forensic preflight run](https://github.com/abhijith-sivaprasadan/residual-pathways/actions/runs/39970521899)
- [Permanent coded 24-case register](../data/derived/rp24_case_register.csv)
- [Audit algorithm and registered rubric](../docs/case_audit_protocol.md)
- [Existing AR6 teaching-source coverage findings](../docs/ar6_teaching_2050_findings.md)

The local packet is regenerated with the same pinned CSV and metadata sources; it contains the selected Model/Scenario identities, exact source observations, numerical diagnostics and uncompleted source-evidence review templates. It is excluded from repository commits and uploaded artifacts.

## 6. Next scientific tasks

**First, verify the canonical AR6 v1.1 file hashes and licensing.** Second, for all 24 cases, locate and inspect model/version-specific definitions and original source reports, especially EIP and land sectors, BECCS, fossil CCS and alternative removals. Third, document original numerical precision; independently check disjoint/exhaustive accounting components; and only then attempt a fully defined numerical reconciliation. Fourth, report I0–I3 inclusion and exclusion *with evidence per case*, and obtain independent scrutiny before promoting any I3 cases to a manuscript.

Independent science review is not reproducible by asserting boolean fields. The work completed here is source selection, provenance checks, reporting diagnosis and reviewer preparation, **not 24 completed forensic literature reviews**.

## References

1. IIASA, AR6 Scenario Explorer and Database: https://iiasa.ac.at/models-tools-data/ar6-scenario-explorer-and-database
2. IPCC AR6 WGIII Annex III, Scenarios and Modelling Methods: https://www.ipcc.ch/report/ar6/wg3/downloads/report/IPCC_AR6_WGIII_Annex-III.pdf
3. IIASA IAMC reporting standard, semi-hierarchical variables and non-guaranteed additivity: https://docs.ece.iiasa.ac.at/standards/variables.html
4. IIASA emissions reporting conventions: https://data.ene.iiasa.ac.at/database/emissions.html
5. Prütz et al. (2025), CDR reporting and land-related gross/net decomposition: https://doi.org/10.5194/essd-17-221-2025
6. Official AR6 scenario database Zenodo publication: https://zenodo.org/records/7197970
