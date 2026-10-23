# QA-001 — Year-column offset caught by independent reference comparison

**Error:** A separately recorded expected-values file selected CSV column index 8 and labelled it 2050. In the actual upstream IAMC header, zero-based column 8 is 2040; 2050 is column 9.

**Detection:** The project's GitHub Actions numerical parity step failed, after unit tests, real upstream fetch and pyam-parity checks all passed. Failure was in the independent 18-observation source reference, not the main Python analyzer, which uses named year fields.

**Correction:** Regenerated all 18 expected values and the descriptive table using the header-derived 2050 column; added this transparent record. The comparison gate remains in CI.

**Impact:** Only the initially recorded 2050 reference JSON and README-style empirical note were wrong. No gross-emissions inference, manuscript, or peer-reviewed result depends on the affected data. Actual 2050 results must be taken from the corrected artifact after CI passes.

**Prevention:** Keep source-header lookup rather than manual numeric positional extraction; preserve the independent source-reference versus pipeline comparison in CI. Future source mappings must be reviewed semantically, not only structurally.
