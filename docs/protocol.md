# Research protocol (initial implemented subset)

## Question and estimand

This pilot asks how many published World-region IAMC CO2 observations share exact model/scenario/year/variable/unit definitions and can therefore be compared descriptively. The source is the official pyam tutorial_data.csv (CD-LINKS historical examples).

This is **not a gross residual-emissions estimate**. Reported "Emissions|CO2" cannot automatically be interpreted as net, positive gross, or emissions remaining after a named technology intervention. No causal attribution is attempted.

## Formal quality gates

1. Input: retain upstream source Git revision, SHA-256, exact row count, year coverage and missingness.
2. IAMC: reject duplicate series and non-finite numeric values; do not zero-fill absent year values.
3. Comparability: exact join by Scenario, Region=World, Variable=Emissions|CO2, Unit=Mt CO2/yr, Year=2050, and selected three historical model versions. Do not extrapolate or convert undocumented units.
4. Accounting levels: I0 indicates no verified usable net/gross/remove partition; I1 requires reviewed net; I2 partial component information; I3 an exhaustive, nonoverlapping compatible positive-emissions/removal partition *and* reviewed source precision and dual numerical/materiality reconciliation.
5. I3 numerical tests: provisional source-quantization sum and strict materiality test; no source precision => blocked. No p-hacking tolerances after seeing attractive figures.
6. Output: source-linked results, coverage counts, CSV, report and versioned release manifest. The digest is computed from the emitted results JSON.

## Interpretation

The tutorial cohort cannot identify residual gross emissions. Its legitimate outcome is an audited coverage and comparability exercise. The research question for full AR6 is different and conditional on a variable-level source audit.

### Initial version limitations

- Does not inspect AR6 model/scenario metadata or climate-category compatibility.
- Does not derive CO2 removal, CCS or sectoral gross emissions.
- Does not solve MESSAGEix/GAMS models.
- The I3 validator is a *research-protocol implementation tested with synthetic examples*, not evidence that any IAMC model-scenario satisfies I3.
- Cross-model scenario names are shared; structural differences remain uncontrolled.

See the complete v3 research plan maintained alongside the development notes; treat the present code as an implemented subset, not a completed protocol.
