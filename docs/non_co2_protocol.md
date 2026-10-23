# CH4 and N2O reporting: source-defined metrics and error prevention

## Purpose

Integrated assessment datasets may contain native mass CH4, N2O, CO2, and already aggregated CO2e. These are not interchangeable. The new gwp.py module converts only a clearly gas-specific, annual raw mass of CH4 or N2O in Mt gas/year into Mt CO2-equivalent/year with named GWP100 assessment and methane origin. The function refuses ambiguous CH4 provenance, wrong time horizons, CO2e inputs and implicit assessment choices. This is a pure arithmetic/reference feature; **no AR6 gas-scenario analysis has yet been executed**.

## Assessment version conflict

The original 2021 IPCC AR6 WGI Chapter 7 Table 7.15 GWP100 values reported CH4 fossil 29.8, CH4 non-fossil 27.0 and N2O 273. The IPCC errata dated 7 October 2025 corrected the values to 28.1, 25.3 and 267 respectively. Both versions are explicitly selectable; an old assessment output must not be silently updated to the corrected reference, and a current analysis must document its selected basis.

Primary material:
- https://www.ipcc.ch/report/ar6/wg1/chapter/chapter-7/
- https://www.ipcc.ch/report/ar6/wg1/about/errata/

These are **GWP100** rather than GTP or alternative horizon metrics. Aggregation is valid only when quantities refer to the same region, date, gas boundaries and model/scenario and are free of pre-aggregated CO2e double counting. No function here asserts that a scenario database reports fossil versus non-fossil methane separately.

## Deferred questions

1. AR6 World dataset gas variable coverage by model and climate category; do not infer complete reporting from a single variable.
2. Which GWP assessment is used in each reported aggregate? The official database metadata and reporting conventions must answer this before reconciling gases.
3. Whether non-CO2 reporting boundaries match the reviewed CO2 gross/net/CDR accounting definition.
4. Uncertainty in the reported GWP assessment values and separation of emissions uncertainty versus metric uncertainty.

The existence of a conversion function is not evidence of a verified emissions-accounting partition.
