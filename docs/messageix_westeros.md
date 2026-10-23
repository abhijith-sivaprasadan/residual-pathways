# Actual MESSAGEix Westeros / GAMS execution gate

**Current status: runner coded and unit-tested; no licensed GAMS solve yet reported.** This is not a claim that possession of a GAMS license suffices to run the model.

The runner fetches and validates the official Westeros Electrified baseline and emissions-bound notebook sources from iiasa/message_ix **tag v3.11.1**. It checks their exact Git blob SHA-1 IDs, then runs the corresponding official data-building cells with only two deliberate changes: the ixmp Platform is an isolated in-memory HSQLDB database, and optional visual plotting is skipped. It then runs the official GAMS-backed MESSAGEix baseline.

Two separate clones are solved using the exact same model and assumed data except their documented interventions: (1) a one-factor wind capital cost change from 1500 to 750 USD/kW, (2) the official emissions-bound tutorial's 500 MtCO2 cumulative CO2 bound with coal source factor 7.4 tCO2/kWa. All three cases must have a finite solved OBJ scalar or the run fails. The project labels these STYLIZED Westeros exercises, not AR6/global integrated assessment output or residual emissions reconstruction.

## Run on Windows with your licensed GAMS

1. Install a GAMS build supported by your licence; activate it in **GAMS Studio > Help > GAMS Licensing**. GAMS and Python must run on the same machine. Do not send the license/access code to this chat or store it in Git.
2. Start a fresh PowerShell session. Check **where.exe gams** and **java -version**. If either executable is missing, complete installation / PATH setup first.
3. Clone or update the ResidualPathways repository, navigate to its root, and create a dedicated Python environment. This avoids breaking the existing project dependencies.

    py -3.11 -m venv .venv-messageix
    .\.venv-messageix\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -e ".[messageix]"
    python -m residual_pathways gams-preflight --output results/gams_preflight_local.json
    python -m residual_pathways westeros-validate --output results/messageix_westeros

4. Successful execution creates **results/messageix_westeros/solved_manifest.json** containing three records with status SOLVED_MESSAGEIX_GAMS_STYLIZED_WESTEROS, has_solution=true and finite objective values. A failed solve creates failed_manifest.json and must not be reported as successful.

Outputs are in results/, which is gitignored. They include source notebooks, a private local GAMS model copy and GAMS intermediate/listing files. **Never push raw GDX, solver listing files, passwords, keys or gamslice.txt.**

The loader deliberately requires message_ix==3.11.1 to match the notebook's tagged API. If ixmp reports Java runtime errors, install a compatible JDK and set JAVA_HOME. If the model fails because your GAMS licence lacks a supported LP solver, consult GAMS Studio licensing or your administrator; simply having a licence does not guarantee the needed solver entitlement.

Docs: https://docs.messageix.org/en/stable/tutorials.html and https://docs.messageix.org/en/stable/install.html ; GAMS licence: https://www.gams.com/latest/docs/UG_License.html

## Scope and remaining work

Passing this run would close the technical Westeros baseline/perturbation gate. The canonical AR6 World source-authentication gate and the RP24 source-specific emissions-accounting reviews remain separate. Local GAMS execution cannot authenticate a scientific accounting partition or a real IIASA collaboration.
