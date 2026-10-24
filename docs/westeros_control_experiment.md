# Controlled third Westeros scenario: emissions accounting, no cap

**Goal:** distinguish effects of *adding CO2 bookkeeping* from effects of *imposing the CO2 cap*. The already-solved reference pair is:
- `baseline`: no CO2 emission factor/cap; saved objective 159025.828125.
- `emission_bound`: coal CO2 emission factor and 500 MtCO2 average-annual bound; saved objective 191510.796875.

This experiment uses only ONE additional licensed GAMS solve: it **clones the emissions-bound scenario into a completely different private HSQLDB platform**, retains the emissions factor and every other model input, removes exactly the `bound_emission` parameter values, then solves `emissions_accounting_no_cap`.

The script checks that 13 known input parameters (including demand, output/input efficiencies, investment/operating costs, technical lifetime, capacity factors, histories, and emission factors) match the source. It also verifies the two original objectives and their saved versions, and requires numerical agreement between the original baseline and the new emissions-accounting-only objective before concluding the difference with the bounded case can be attributed to the cap. The new private database and all results are gitignored; **no original source scenario is modified**.

## Execute (Windows PowerShell)

```powershell
cd 'E:\New folder (2)\MissionJob\residual-pathways'
git pull --ff-only

& .\.venv-messageix\Scripts\python.exe -m pytest -q tests/test_westeros_no_cap.py

$env:IXMP_GAMS_PATH = 'C:\GAMS\54'
$env:Path = "C:\GAMS\54\apifiles\Java\api;C:\GAMS\54;$env:Path"

& .\.venv-messageix\Scripts\python.exe -m residual_pathways westeros-no-cap-control `
  --manifest 'results/messageix_private/20261023T230104Z_e182e730/manifest.private.json' `
  --output 'results/westeros_control_private'
```

The runner creates a unique directory under `results/westeros_control_private/` containing:

- `manifest.private.json`: source pin, three-case status, copied-input checks, control objective and reporting digest (no licence contents).
- `ixmp_database/`: NEW source-isolated HSQLDB, containing the one new control scenario.
- `three_case_comparison.json` and `three_case_comparison.csv`: three objectives and ACT/CAP/CAP_NEW by technology and year, with control-minus-baseline and bound-minus-control columns.

The script **does not rerun the two original optimizations**. If the new solver cannot solve, or if the model input parity fails, it raises and records a private failure status instead of producing a success claim. If the new control *does* solve but its objective differs materially from the original baseline, the private result persists as `CONTROL_SOLVED_BUT_BASELINE_OBJECTIVE_MISMATCH` and the runner raises; this is a scientific diagnostic, not a passing causal result.

## Analysis claim gates

**Passing state:** `ACTUAL_MESSAGEIX_GAMS_CONTROL_SOLVED`, with `baseline_vs_control.numerically_equivalent == true`. Then, with only `bound_emission` changed between the two emissions-enabled cases, the objective difference `bounded - no_cap` can be attributed to the bound in this **small educational example**.

Keep the actual result private until `three_case_comparison.json` is inspected. A passing result is not a carbon shadow price, global IAM result, independent reproduction or source-authenticated scientific publication.

Docs: [ixmp clone across platforms](https://docs.messageix.org/projects/ixmp/en/stable/api.html) and [MESSAGEix model core](https://docs.messageix.org/en/v3.11.1/model/MESSAGE/model_core.html).

## ixmp 3.11.1 cross-platform clone compatibility (2026-10-24)

The first real control attempt **failed before GAMS execution** with:

```text
NotImplementedError: Cross-platform clone of message_ix.Scenario with `keep_solution=False`
```

This is an explicit ixmp JDBC backend limitation. The runner is now fixed to perform `clone(..., platform=dst, keep_solution=True)`, call `clone.remove_solution()` **on the isolated destination**, assert the saved solution was actually cleared, and only then `check_out()`. It also calls `remove_par("bound_emission", existing_rows)` to remove **parameter rows only**. Passing no rows (`remove_par("bound_emission")`) would delete the parameter definition and is unsafe for MESSAGEix.

The regression fixture now models the JDBC rejection of `keep_solution=False` and tests the copy-clear-edit ordering. **The corrected cross-platform path subsequently passed a real local GAMS attempt on 2026-10-24 (documented below)**. The earlier failed attempt has `FAILED_NOT_VERIFIED` status in its own timestamped private folder; do not interpret it as a solver failure. Each retry creates a different timestamped directory, leaving original scenarios untouched.

## Second local attempt: weak-reference identity guard (2026-10-24)

The second real Windows attempt passed the updated four mock tests, but the runner stopped **after the cross-platform clone call**, before clearing the copied solution or starting the new GAMS solve. The now-obsolete check `clone.platform is dst` failed: ixmp 3.11.1's `TimeSeries.__init__` deliberately stores `platform` as `weakref.proxy(mp)`, which is a proxy object, not the original Python `Platform`. That `is` comparison cannot authenticate database identity.

The implementation now checks `clone.platform._backend is dst._backend` **and** `clone.platform._backend is not src._backend`. Tests now mirror ixmp's weak-reference behavior, explicitly reject clones on the wrong backend, and ensure no control solve starts when that guard fails. The first two attempted runs remain isolated in fresh private directories. The corrected version was subsequently executed successfully against the actual locally saved source scenarios, as recorded below.

## Successful real control execution (2026-10-24 02:24 local)

The author supplied the actual third-attempt Windows PowerShell execution transcript after pulling commit `8dd9c9c`:

- `pytest -q tests/test_westeros_no_cap.py`: **5 passed**.
- Local source scenario/database opened correctly; cross-platform clone and destination solution removal proceeded past both earlier API limitations.
- GAMS **54.6.0** + CPLEX reported **LP status optimal**, `Optimal solution found`, and **normal completion**; console objective: **159025.830480** (native units).
- Runner finished with **`ACTUAL_MESSAGEIX_GAMS_CONTROL_SOLVED`**, `Baseline and control numerically equivalent: True`, and `Isolated cap objective effect (native units): 32484.96875`.
- New, separate private destination: `results/westeros_control_private/20261024T002431Z_f8428b42`.

The original stored baseline is **159025.828125**, while the capped result is **191510.796875**. Because the runner reports the difference between capped and saved control objectives as **32484.96875**, the saved control objective is **arithmetically implied** to be **159025.828125** at the printed precision. That is consistent with the solver's higher-precision console objective, 159025.830480. The author has not supplied the three-case comparison JSON itself, so exact control values for `ACT`, `CAP`, and `CAP_NEW` remain to be inspected before describing their parity as observed.

**Conclusion:** The emissions-accounting-only control model, based on the emissions-constrained model with solely `bound_emission` values removed, has the same saved objective as the original baseline to solver/reporting precision. The higher objective in the capped case is therefore attributable to imposing the emissions constraint in this controlled educational example. This is a single, author-run GAMS experiment, not independent scientific replication or a carbon-price calculation.

The GAMS importer again logged that optional variables `I` and `C` were not found in GDX; despite this, the run reached normal completion, the expected solution was saved, and the runner's numerical gates passed. These messages warrant separate completeness review before any claim about the full output variable set.

**Privacy:** The original terminal transcript contains personal GAMS licence/account identifiers and user filesystem paths. Do **not** publish the raw log, source HSQLDB, GDX, or executed notebooks. For publication, inspect and separately export only approved derived evidence.
