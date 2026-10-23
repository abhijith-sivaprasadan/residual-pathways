# Climate-category stratification of AR6 World reporting

The stratified-audit code links the locally authorized AR6 World scenario CSV to the separately downloaded metadata indicators spreadsheet by exact (Model, Scenario). It requires the researcher to name the actual classification column, rather than guessing scenario categories, and preserves the raw category label as given in the metadata. It reports exact-year, exact-variable counts and denominators separately for each class. It never exports scenario values or infers gross accounting from the presence of net-CO2-like variable names.

Install the optional spreadsheet reader: python -m pip install -e ".[metadata]"

Usage: python -m residual_pathways audit-ar6-strata --input data/AR6_Scenarios_Database_World_v1.1.csv --metadata data/AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx --category-column "CHOSEN_ACTUAL_METADATA_HEADER" --output results/ar6/stratified_2050.json

The exact spreadsheet header has deliberately not been hardcoded because the official metadata file has not yet been inspected locally. Inspect its real header before execution. Distinguish eligible fully assessed climate scenarios, policy-category samples, model coverage and source variable definitions when interpreting the result.

Warning: exact presence of CO2, CH4 or N2O variable does not prove gas-origin breakdown, consistent GWP, an exhaustive positive emissions partition, or atmospheric removal permanence.

Source:
- https://iiasa.ac.at/models-tools-data/ar6-scenario-explorer-and-database
- https://zenodo.org/records/7197970

The official AR6 dataset retains upstream access and redistribution terms. The repository does not contain raw AR6 scenario or metadata files. **No claim of running on the actual AR6 ensemble is made.**
