# Licensed MESSAGEix Westeros: GitHub-first Windows setup

**Author-reported local execution succeeded on 2026-10-24.** The author supplied Windows terminal output showing both pinned MESSAGEix 3.11.1 Westeros notebook scenarios solved to optimality using GAMS 54.6.0/CPLEX. The local runner reported `ACTUAL_MESSAGEIX_GAMS_SOLVED` after reading saved objectives from ixmp: baseline 159025.830480, emissions-bound 191510.804279 (native objective units). The private manifest and raw logs have **not** been published or independently re-executed by CI. See the [PathwaysHub evidence-scope note](https://github.com/abhijith-sivaprasadan/pathways-hub/blob/main/docs/messageix_local_run.md). Source-controlled code does not require a local checkout; executing licensed GAMS on your computer does.

## 1. Clone the GitHub repositories

In Windows PowerShell, from a directory where you want the projects:

    mkdir "$HOME\Documents\MissionJob" -Force
    cd "$HOME\Documents\MissionJob"
    git clone https://github.com/abhijith-sivaprasadan/residual-pathways.git
    git clone https://github.com/abhijith-sivaprasadan/pathways-hub.git
    cd residual-pathways

Only residual-pathways is needed for the Westeros solve. Clone pathways-hub now or later.

## 2. Check the system prerequisites

MESSAGEix 3.11.1 requires Python and a Java runtime when using pip, plus an installed GAMS executable with a usable license. Install GAMS from https://www.gams.com/latest/ and activate your license using the official installer. Its advanced installation can add the executable to PATH; reopen PowerShell after installation.

To check executable discovery:

    Get-Command gams
    Get-Command java
    py -3.11 --version

These commands do not prove that a particular solver license is valid. Do not paste license contents or access codes into GitHub, ChatGPT, issue comments or CI logs. The runner does not inspect license files.

Official installation instructions: https://docs.messageix.org/en/v3.11.1/install.html and https://www.gams.com/latest/docs/UG_WIN_INSTALL.html.

## 3. Create the separate MESSAGEix environment

From the residual-pathways checkout:

    .\scripts\setup_westeros_windows.ps1

The script creates a separate local Python 3.11 virtual environment, installs the exact MESSAGEix 3.11.1 matching the upstream tutorials, and executes a safe dependency preflight. If PowerShell blocks script execution, run the equivalent commands individually:

    py -3.11 -m venv .venv-messageix
    & .\.venv-messageix\Scripts\python.exe -m pip install -e . -r requirements-messageix.txt
    & .\.venv-messageix\Scripts\python.exe -m residual_pathways.messageix_westeros --preflight

## 4. Execute the official baseline and emissions-bound scenarios

    & .\.venv-messageix\Scripts\python.exe -m residual_pathways.messageix_westeros

The runner downloads the official v3.11.1 baseline and emissions-bound Westeros notebooks at immutable MESSAGEix Git commit 2d521407a430a08de997a771e7b38d88f7e7d2b6. It SHA-256 fingerprints the downloaded source notebooks and executes the original model-building, commit, solve and objective-check cells. Optional reporting/plotting cells after the first objective check are omitted; no GAMS or MESSAGEix model-building instructions are changed.

The runner creates a fresh private HSQLDB database using IXMP_DATA for each run, and its own private Jupyter kernel tied to your active virtual environment. It records the actual two solved scenario objective values and versions only after both source notebooks finish and ixmp reports saved solutions.

All data, private executed notebooks, a fresh local database and run manifests live under results/messageix_private/ (ignored by Git). A successful local manifest has status ACTUAL_MESSAGEIX_GAMS_SOLVED. GitHub CI cannot claim this status without an actual local licensed solve.

To verify downloading only, without solving:

    & .\.venv-messageix\Scripts\python.exe -m residual_pathways.messageix_westeros --download-only

## 5. If execution fails

The local manifest will record FAILED_NOT_VERIFIED and a failure exception type, never a fake objective or successful solve. An executed notebook may contain local environment paths or solver errors; do not publish it without inspection and redaction. Share a redacted traceback or error category instead of a license file, personal paths or activation credentials.

Upstream tutorial source: https://docs.messageix.org/en/v3.11.1/tutorials.html

## 6. Scope of scientific evidence

These runs establish real experience using the small educational MESSAGEix/GAMS Westeros model only. They do not establish that the user has run a global MESSAGEix-GLOBIOM integrated assessment model, reproduced IIASA AR6 World data or resolved the model-specific I3 gross-net-CDR partition. After confirming both scenarios, a further controlled and source-documented sensitivity can be executed in this exact model.
