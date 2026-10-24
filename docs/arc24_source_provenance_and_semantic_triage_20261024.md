# ARC24 source provenance and model-specific semantic triage — 24 October 2026

**Status:** real local AR6-named v1.1 World/metadata analysis succeeded as author reported; source bytes and 24-case selection validated by checksum and output diagnostics. This is an initial **model-documentation triage**, **not** a completed scientific accounting review. I1/I2/I3 classifications remain **NOT_DETERMINED**.

## 1. Source fingerprint comparison

| Input | Actual locally computed SHA-256 | Interpretation |
|---|---|---|
| World v1.1 CSV (361,767,203 bytes) | `4cf39b6b0d968e25ed389318acb1674f92146f977e9db4bfb7970f048ff73977` | **Exactly matches** the previously used public Zenodo teaching-labelled `AR6-demo-data.csv` bytes, as reported by author. Both names refer to byte-identical data in these two downloads; calling the earlier analysis an unrepresentative numeric *subset* is misleading on this evidence. |
| Metadata indicators v1.1 XLSX (2,769,289 bytes) | `fd1bc32db8463769e18f0560ced603a49598c12e1abfa06787ff763c55f06716` | **Differs from** prior third-party republished metadata workbook (`7d22453bdda52e95cea4df46d362018951dd7114e62f01f5bcea65d6e24a7790`). Different zipped XLSX bytes do not by themselves establish that cell values or classification changed. |

The AR6 World source has therefore passed a **two-route byte-concordance check** (official-named local download versus teaching-labelled public copy), but a matching checksum cannot authenticate the IIASA portal transaction without an acquisition receipt. The metadata file has a different SHA and should receive a **sheet/content-level semantic diff** if the prior XLSX is available. Do not infer differing category definitions or class membership solely from binary inequality.

Source: official v1.1 [Zenodo dataset record](https://zenodo.org/records/7197970), [IIASA explorer](https://data.ene.iiasa.ac.at/ar6/#/downloads), and [2026 teaching-labelled release](https://zenodo.org/records/20056332). Zenodo labels the 2026 upload a teaching subset, but the author's actual SHA-256 check shows **the downloadable CSV files are byte-identical**. The user reports accessing the two new files from IIASA; an independent signed publisher-side checksum has not been found.

## 2. ARC24 selection and diversity caveat

Source-native selection: 1,202 metadata-vetted Model×Scenario pairs matched in the World file; a deterministic purposive three-per-class C1–C8 sample yielded 24 ARC24 cases. Seven show all six nominated variable names in the required unit; 19 can support a **three-term arithmetic preflight only**. Zero cases qualify as independently verified I3.

The seven six-variable-complete cases represent **four exact model/version labels**: **four POLES ENGAGE**, one REMIND-MAgPIE 2.1-4.2, one COFFEE 1.1, one WITCH 5.0. This is **not seven independent model frameworks**. For statistical comparison, count exact model labels separately from cases and later check parent modelling families and selection weighting. The sample intentionally selects extremes of variable availability; it cannot estimate ensemble-wide I3 frequencies.

Do **not** publish the private packet's individual numeric observations or use case IDs to imply independent reviewed scenarios. Exact model/scenario names and observations remain locally available in `data/ar6-private/canonical_selected24_packet.json`.

## 3. Source-backed general model documentation: preliminary risk inventory

| Model group and ARC24 case IDs | What sources actually establish | Necessary source-specific decisions still unverified | Source |
|---|---|---|---|
| REMIND-MAgPIE 2.1-4.2: ARC24-03 | REMIND energy-economy and MAgPIE land-use/agriculture models may be iteratively **soft coupled**; bioenergy supply and land-use emissions influence the energy optimization. The CEMICS scenario belongs to a CDR-availability study. | Match documentation to **2.1-4.2 and the exact CEMICS minCDR scenario**; establish signed AFOLU, biomass growth versus land sequestration, BECCS physical flows, negative-emissions and DAC representation, and whether total CO₂/EIP/AFOLU form a scope-compatible, disjoint accounting identity. | [IAMC framework description](https://www.iamcdocumentation.eu/Model_Documentation_-_REMIND-MAgPIE), [scenario cross-reference](https://1p5ndc-pathways.climateanalytics.org/methodology), [2026 CDR-scenario discussion](https://publications.pik-potsdam.de/pubman/item/item_33843_1/component/file_33844/Fair%2Bcarbon%2Bremoval%2Bobligations%2Bunder%2Bclimate%2Bresponse%2Buncertainty.pdf) |
| POLES ENGAGE: ARC24-06, 09, 12, 21 | Available POLES documentation derives fossil energy CO₂ from its energy balance and combines agriculture/LULUCF information supplied via **GLOBIOM/G4M** lookup/linkage. POLES is a sectoral simulation framework, not four independent model families in our selected data. | **Version caution:** general POLES/JRC and archived IAMC documentation does not certify the exact **POLES ENGAGE** scenario implementation. For each scenario check EIP versus energy-industrial scopes, AFOLU sign/netting, land sequestration imported from GLOBIOM, CCS accounting, storage vs removal, reference year and reporting precision. | [IAMC POLES emissions](https://www.iamcdocumentation.eu/Emissions_-_POLES), [European Commission JRC POLES model](https://joint-research-centre.ec.europa.eu/what-we-do/scientific-tools-and-databases/poles/model_en), [ENGAGE project](https://engage-climate.org/explorer-tools/scenario-explorer/) |
| COFFEE 1.1: ARC24-15 | Related COFFEE-TEA documentation describes a linear-programming COFFEE energy system and reports CCS capture, transport and geological storage routes. | Whether the published **COFFEE 1.1** results use the same accounting and model configuration as COFFEE-TEA reference material is **not confirmed**. In particular, CO₂ capture or saline-aquifer storage cannot automatically be counted as atmospheric CDR, and land emissions may be already net. | [IAMC COFFEE-TEA CO₂ removal and CCS methods](https://www.iamcdocumentation.eu/Carbon_dioxide_removal_%28CDR%29_options_-_COFFEE-TEA), [COFFEE emissions documentation](https://www.iamcdocumentation.eu/Emissions_-_COFFEE-TEA) |
| WITCH 5.0: ARC24-18 | WITCH links economic/energy modelling and **GLOBIOM** land-use responses, and official model documentation details emissions and CDR options. | Validate the **WITCH 5.0 scenario** configuration, overlap between land removals and BECCS/DAC reporting, actual storage flow and source-precision convention; present-day WITCH documentation may post-date the 2022 AR6 submission. | [WITCH 5.0 model reference](https://www.iamcdocumentation.eu/Reference_card_-_WITCH), [WITCH model-scope docs](https://doc.witchmodel.org/model-scope.html) |

These are **model-family facts and research flags**, not evidence that specific exported variable identities or sector partitions have passed scientific review. The model docs often describe more recent implementations than the exact 2021/2022 submissions; extrapolation across versions is forbidden without a specific citation or developer confirmation.

## 4. First in-depth scientific review order

1. **ARC24-03 / REMIND-MAgPIE 2.1-4.2:** establish the scenario-specific CEMICS minCDR study, signed AFOLU source and relationship between net energy, gross positive sectoral emissions, BECCS and DAC. Check whether land sequestration is already netted in another branch.
2. **ARC24-06 / POLES ENGAGE:** establish the ENGAGE-specific submission protocol and model-paper version, mapping from GLOBIOM land fluxes to IAMC AFOLU and sequestration variables. Compare with ARC24-09/12/21 only **within** the same framework, not as independent model families.
3. **ARC24-15 / COFFEE 1.1 and ARC24-18 / WITCH 5.0:** repeat source/precision/semantic review with distinct model documentation. Include ARC24-24 (C8) as a deliberate missing-variable negative/control case.

Before any I3 upgrade, record: exact primary source and version, gas/geography/year, sector disjointness, sign/land accounting, fossil CCS versus atmospheric removal, source stated numeric precision, complete positive and removal partitions, full net identity residual, reviewer and review date. A mathematically zero residual does **not** replace semantic evidence. Use `docs/accounting_protocol.md` for provisional tolerance criteria and explicitly retain unknown original export precision.

## 5. Further checks needed

- Run a worksheet/content-level diff of the local official XLSX against the older redistributed XLSX, checking `meta_Ch3vetted_withclimate` row identity and every category/critical column, not just the workbook's ZIP-level SHA.
- Save source acquisition provenance privately (IIASA portal download record and date; do not publish account identifiers). Record the locally observed World and metadata hashes.
- When model-specific evidence supports it, run a private 2050 field-by-field extraction for two chosen cases and document allowed semantic mappings; **do not invent source-derived gross/net/removal figures**.
- Keep ARC24 grade `NOT_DETERMINED`, and PathwaysHub RP-18 `NEEDS_EXTERNAL_REVIEW` until evidence and review are complete.
