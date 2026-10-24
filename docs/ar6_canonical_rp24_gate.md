# AR6 canonical v1.1 and RP24 source gate

**Research status, 24 October 2026:** official acquisition route identified; original canonical files **not yet** downloaded, authenticated, hashed or checked in the author's local environment. No model-specific RP24 accounting reviews or I3 classifications have been completed.

## Official source and legal boundary

IIASA's authoritative AR6 v1.1 entry is https://data.ene.iiasa.ac.at/ar6/#/downloads . The release is documented at https://zenodo.org/records/7197970 . Its Zenodo archive restricts the original file downloads and directs users to the IIASA explorer. Required World-region files:

- AR6_Scenarios_Database_World_v1.1.csv
- AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx

The previously audited public data at https://zenodo.org/records/20056332 are expressly a **teaching subset** and do not automatically authenticate the canonical release. Scientific analysis of the official dataset is permitted subject to attribution, but substantial source-data redistribution is restricted. Neither source files, GAMS logs, private case packets nor download credentials may be committed to Git.

The official explorer uses JavaScript. When necessary, use its guest login and email-delivered download process where offered. A matching filename or local SHA256 can check integrity, **not certify original provenance**. Record the direct download route and release privately.

## Recommended: canonical-native selection (does not need old teaching packet)

The newly added **ar6-canonical-select** command creates a *new* deterministic, purposive 24-case sample directly from the locally obtained canonical-named v1.1 World and climate-vetted metadata files (three each from C1-C8, low/median/high by six-variable reporting availability). It uses the official-name files as its sole data inputs and **does not require** the old teaching-source case_audit_review_packet.json file.

PowerShell from the repository after downloading the two original IIASA files:

    git pull --ff-only
    & .\.venv-messageix\Scripts\python.exe -m pytest -q tests/test_ar6_canonical_gate.py
    & .\.venv-messageix\Scripts\python.exe -m residual_pathways ar6-canonical-select --world 'data/ar6-private/AR6_Scenarios_Database_World_v1.1.csv' --metadata 'data/ar6-private/AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx'

Default derived outputs:

- Public, coded selection register: results/ar6-canonical-gate/selected24_public.json
- **Private** review packet with Model/Scenario identities, source observations and blank documentation fields: data/ar6-private/canonical_selected24_packet.json

Expected status: CANONICAL_NAMED_LOCAL_COHORT_SELECTED_ORIGIN_UNVERIFIED. This denotes checked local file structure and selection **only**, not provenance authentication, human review, a verified gross/CDR accounting partition or I3. Record the direct portal download route privately.

The pre-existing **ar6-canonical-gate** command further down is now **optional**: use it to compare a recreated teaching-derived RP24 cohort against this locally downloaded release if both earlier teaching input and metadata are available. Do not substitute a teaching source for the official World file or treat the two samplings as statistically identical.

## Execute the prepared gate

In Windows PowerShell, first update and test:

    cd 'E:\New folder (2)\MissionJob\residual-pathways'
    git pull --ff-only
    & .\.venv-messageix\Scripts\python.exe -m pytest -q tests/test_ar6_canonical_gate.py

Download both *unmodified official v1.1 files* from the IIASA explorer into the gitignored data/ar6-private folder. **Never rename AR6-demo-data.csv to mimic the official filename.**

The pre-existing teaching-source RP24 reviewer packet is:

    data/ar6-private/case_audit_review_packet.json

If it is missing, regenerate the earlier teaching-source 24-case packet using docs/case_audit_protocol.md; original teaching-source data are also local-only.

Run the canonical comparison:

    & .\.venv-messageix\Scripts\python.exe -m residual_pathways ar6-canonical-gate --world 'data/ar6-private/AR6_Scenarios_Database_World_v1.1.csv' --metadata 'data/ar6-private/AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx' --packet 'data/ar6-private/case_audit_review_packet.json' --public-output 'results/ar6-canonical-gate/summary_public.json' --private-output 'data/ar6-private/canonical_rp24_review.json'

The tool streams the large World CSV and selects the climate-vetted metadata sheet. It writes byte lengths, SHA-256 hashes, canonical-name source counts, exact original model-scenario matches, category concordance and per-variable source differences. Public output uses coded RP24 IDs and aggregate counts only; original identities and all scenario values are kept in the **private** review report. The script does not fetch IIASA files, connect to the official server, grant source permission, assign an I3 grade or certify acquisition authenticity.

Its expected evidence status is LOCAL_FILE_HASHED_ORIGIN_NOT_AUTHENTICATED, even when the 24 identities and every selected observation agree. This means local file integrity and concordance, not scientifically reviewed emissions.

## Review queue and next scientific gate

The first seven review targets are the six-variable-complete *teaching-source* cases RP24-03, RP24-06, RP24-09, RP24-12, RP24-15, RP24-18 and RP24-21. Their completeness is only the **presence of six candidate fields**, not a verified exhaustive net/gross/removal accounting identity. C8's high-coverage RP24-24 reports five such fields; it should be reviewed for coverage exclusions.

For every case, document and source-verify:
1. Whether CO2 aggregate and AFOLU sector series are gross versus signed net and whether energy/industry subterms are disjoint.
2. Units, year, regional and activity scopes; how carbon capture, storage, fossil CCS, biomass CCS, land sinks and direct-air capture are actually measured.
3. Whether a true, exhaustive, nonoverlapping partition exists, rather than merely the existence of nested IAMC variable names.
4. Primary model/version documentation for definitions and original export precision, not display-derived precision.
5. Numerical source quantization and materiality reconciliation only after the semantic gates pass; preserve all failures and unknown terms as unavailable.
6. Human reviewer decisions with dated source references; never auto-promote I3 because tests or arithmetic happen to agree.

The purposive 24-case sample is not statistically representative. The canonical release may change the candidate scores and should receive a *new preregistered sampling comparison* after direct file inspection.

## Gate status

- Official source/acquisition route: verified through public IIASA and Zenodo pages.
- Actual canonical v1.1 file origin and hashes: **pending local download**.
- RP24 teaching-data preflight: **complete**, 24 cases; seven with all six reported candidates.
- Canonical comparison implementation and regression fixtures: **committed**, not yet exercised against the actual canonical files.
- Semantic and source-precision reviews: **not started**, zero verified I3.

Do not mark RP-03 or RP-18 completed while canonical provenance or scientific review is pending.

References: https://iiasa.ac.at/models-tools-data/ar6-scenario-explorer-and-database ; https://zenodo.org/records/7197970 ; https://docs.ece.iiasa.ac.at/standards/variables.html
