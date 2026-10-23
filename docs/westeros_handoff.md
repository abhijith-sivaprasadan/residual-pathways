# Sanitized local Westeros evidence → PathwaysHub (contract v1)

This handoff **does not run GAMS again**. It reads the original local `manifest.private.json` that the two-notebook `messageix_westeros` runner created after a completed solve. It exports only an explicit allowlist of scalar objectives, model/scenario IDs, pinned tutorial source hashes, versions and author-reported execution state.

The v1 export is for the **two-scenario notebook runner** (baseline + emissions bound), not the independent three-scenario `westeros-validate` workflow. It never contains local paths, access codes, licence files, logs, GDX, database dumps, credentials, hardware identity, personal email, or executed notebooks.

## Commands — Windows PowerShell

From your real residual-pathways checkout:

```powershell
cd 'E:\New folder (2)\MissionJob\residual-pathways'
git pull --ff-only

# Uses the existing successful local run; no license and no new solve required.
& .\.venv-messageix\Scripts\python.exe -m residual_pathways westeros-export `
  --input 'results/messageix_private/20261023T230104Z_e182e730/manifest.private.json' `
  --output 'results/westeros_handoff'
```

The exporter refuses incomplete/failed runs, unknown notebook sources, missing scenarios, invalid objective numbers, or a manifest that does not report both persisted ixmp solutions. Its output directory is gitignored:

- `results/westeros_handoff/westeros_evidence.json` — sanitized, versioned result.
- `results/westeros_handoff/westeros_evidence.manifest.json` — SHA-256 of the exact evidence JSON bytes plus its length and narrowly declared evidence level.

The exporter does **not** independently authenticate the author's local manifest; an author can modify both a JSON artifact and its SHA sidecar. A matching hash checks pairwise byte integrity, **not** real solver execution, trust in the author, or proof that the upstream notebooks were actually downloaded.

To consume in PathwaysHub:

```powershell
cd 'E:\New folder (2)\MissionJob\pathways-hub'
git pull --ff-only
& .\.venv\Scripts\python.exe -m pathways_hub consume-westeros `
  --manifest '..\residual-pathways\results\westeros_handoff\westeros_evidence.manifest.json' `
  --artifact '..\residual-pathways\results\westeros_handoff\westeros_evidence.json' `
  --output 'outputs/westeros_contract'
```

Inspect `outputs/westeros_contract/decision.json`; a valid handoff reports **ACCEPTED_AUTHOR_REPORTED_LOCAL**, not independently reproduced or scientifically approved. Passing `--expected-sha256` with a digest obtained from a trusted *separate* channel can additionally pin the artifact bytes.

## Publication gate

Review both generated files before publishing. Only share the sanitized bundle if comfortable releasing this narrowly scoped metadata. **Never publish** `results/messageix_private/`, raw logs, executed notebooks or licence identifiers.

The purpose is an auditable research-operations boundary: PathwaysHub verifies a digest and a semantic schema for an *author-attested tutorial result*. It is not a numerical reproduction, an AR6 source audit, an I3 carbon-accounting certificate, or independent research peer review. GitHub Actions may exercise this contract with **synthetic fixtures only**, and must never report that as actual GAMS execution.

## First author-reported real local handoff (2026-10-24)

The author supplied terminal output confirming that this exporter ran against the previously solved private run `20261023T230104Z_e182e730` and that the resulting allowlisted artifact was accepted by the *local* PathwaysHub `consume-westeros` command:

- Consumer status: `ACCEPTED_AUTHOR_REPORTED_LOCAL`
- Integrity: `BYTE_HASH_MATCH_AND_SCHEMA_CHECKED`
- Reported evidence artifact SHA-256: `f8da4d0ddacc35758e48b1c1396b89867cc9ed0e7e55ed8a1abba708a3dc3fe1`
- Persisted ixmp objectives: baseline **159025.828125**, emissions bound **191510.796875**, change **20.427479694974863%**

This is **not a published handoff bundle, independent hash recomputation, or independently executed model**. Original private manifest and licence-bearing GAMS logs remain on the author's Windows system. See [PathwaysHub evidence note](https://github.com/abhijith-sivaprasadan/pathways-hub/blob/main/docs/messageix_local_run.md).
