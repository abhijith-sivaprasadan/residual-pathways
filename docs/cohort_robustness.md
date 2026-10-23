# AR6 teaching-source scenario reporting robustness

The robustness CLI computes exact-name World reporting presence in 2030, 2050, 2070 and 2100 separately for C1–C8, with explicit model/scenario denominators and missing values preserved. It does not read emissions magnitudes into an output dataset or infer the sign of anything not reported.

Two deliberately different sample summaries are emitted for each category-year-variable: (1) fraction of Model×Scenario pairs reporting the exact-name value; (2) average within-model-label reporting fraction giving equal weight to each distinct exact Model label. Neither is a probability. Model labels should not be equated to independent scientific model families without externally reviewed mapping.

This controls sample-selection diagnostics, not model structure or causality. The input remains the independently published AR6 teaching release and third-party redistributed named v1.1 metadata, not authenticated canonical-v1.1 files. Derived category/variable aggregates only are released.

Run: python -m residual_pathways cohort-robustness --input data/ar6-private/AR6-demo-data.csv --metadata data/ar6-private/AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx --candidates config/ar6_variable_candidates.json --output results/ar6-teaching-pilot/robustness_4years.json
