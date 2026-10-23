# AR6 v1.1 World data: local analysis route

The official IPCC AR6 WGIII scenario database is hosted by IIASA:
- https://data.ene.iiasa.ac.at/ar6/#/downloads
- https://zenodo.org/records/7197970
- https://iiasa.ac.at/models-tools-data/ar6-scenario-explorer-and-database

The World v1.1 CSV is about 353 MB uncompressed; the metadata indicators XLSX is a separate approximately 3 MB file. Zenodo documents scientific research and science-communication permission but restricts substantial redistribution. Download and use the data from the official explorer under its applicable terms; **do not commit the source dataset to GitHub**.

Once downloaded into data/AR6_Scenarios_Database_World_v1.1.csv, run:

    python -m residual_pathways audit-ar6 --input data/AR6_Scenarios_Database_World_v1.1.csv --candidates config/ar6_variable_candidates.json --output results/ar6/coverage_2050.json --year 2050

The audit runs with the Python standard library and streams rows; it records the file hash and only variable-availability counts. It does not infer I1–I3 status or publish raw source observations. The candidate variable list is a **search dictionary**, not a validated physical partition or claim that every name occurs in the source. Check the metadata for official exact variable names and units, then review definitions and source precision before any gross/CDR decomposition.

After the coverage audit, link scenario climate categories from the separately retrieved metadata. Do not compare mitigation intensity or sector composition without reporting-comparable cohorts. An unreviewed variable appearing in the CSV is not evidence that it can be summed or interpreted as gross or atmospheric removal.

**Status:** This source-specific script has synthetic tests, but no completed AR6 World input has yet been run and no AR6-derived coverage result is asserted.
