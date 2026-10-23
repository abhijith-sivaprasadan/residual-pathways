"""Export allowlisted author-reported local Westeros results for PathwaysHub.

Reads a successful private manifest only. Neither GAMS nor the private ixmp
database is accessed; no raw solver logs, executed notebooks or licence data
are copied. Integrity is not independent attestation of solver execution.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import math
import re

from .messageix_westeros import MODEL, NOTEBOOKS, UPSTREAM_COMMIT, UPSTREAM_RELEASE, source_url

EVIDENCE_SCHEMA = "residualpathways.westeros.evidence.v1"
BUNDLE_SCHEMA = "pathways-handoff.westeros.v1"
ATTESTATION = "AUTHOR_REPORTED_LOCAL_EXECUTION_NOT_INDEPENDENTLY_VERIFIED"
HASH_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
RUN_PATTERN = re.compile(r"[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}\Z")


class WesterosExportError(ValueError):
    """Private manifest did not meet the limited publication gate."""


def _require(condition, message):
    if not condition:
        raise WesterosExportError(message)


def _finite_number(value):
    _require(type(value) in (float, int), "Objective must be a JSON number (not bool/string)")
    _require(math.isfinite(value), "Objective must be finite")
    return value


def evidence_from_private_manifest(private):
    """Construct a fresh, strict allowlist; never serialize private input verbatim."""
    _require(isinstance(private, dict), "Expected a private manifest JSON object")
    _require(private.get("schema") == "local-westeros-execution.v1", "Unexpected private manifest schema")
    _require(private.get("status") == "ACTUAL_MESSAGEIX_GAMS_SOLVED", "Source run was not verified as solved")
    _require(private.get("model") == MODEL, "Unexpected model")
    _require(private.get("upstream_commit") == UPSTREAM_COMMIT, "Unexpected pinned upstream commit")
    _require(private.get("upstream_release") == UPSTREAM_RELEASE, "Unexpected upstream release")
    _require(private.get("evidence_scope") == "EDUCATIONAL_MESSAGEIX_GAMS_NOT_AR6", "Unexpected evidence scope")
    _require(private.get("license_content_stored") is False, "Private manifest does not certify licence content excluded")

    run_id = private.get("run_id")
    _require(isinstance(run_id, str) and RUN_PATTERN.fullmatch(run_id), "Invalid source run identifier")
    env = private.get("environment")
    _require(isinstance(env, dict), "Missing source environment")
    _require(env.get("actual_solve_performed") is True, "No recorded completed local solve")
    _require(env.get("message_ix_version") == "3.11.1", "Incorrect MESSAGEix version")
    _require(env.get("ixmp_version") == "3.11.1", "Incorrect ixmp version")
    _require(env.get("upstream_commit") == UPSTREAM_COMMIT, "Environment upstream pin differs")

    raw_notebooks = private.get("notebooks")
    raw_solutions = private.get("solved_scenarios")
    _require(isinstance(raw_notebooks, list) and len(raw_notebooks) == 2,
             "Exactly two pinned notebooks are required")
    _require(isinstance(raw_solutions, list) and len(raw_solutions) == 2,
             "Exactly two solved scenarios are required")
    expected = {stage: filename for stage, filename, _ in NOTEBOOKS}
    notebook_by_stage = {}
    solution_by_stage = {}
    for note in raw_notebooks:
        _require(isinstance(note, dict), "Malformed notebook record")
        stage = note.get("stage")
        _require(stage in expected and stage not in notebook_by_stage, "Unexpected/duplicate notebook")
        _require(note.get("source_url") == source_url(expected[stage]), "Unexpected notebook source URL")
        digest = note.get("sha256")
        _require(isinstance(digest, str) and HASH_PATTERN.fullmatch(digest), "Invalid notebook source SHA-256")
        _require(type(note.get("model_cells")) is int and note["model_cells"] > 0, "Missing notebook execution cells")
        notebook_by_stage[stage] = digest
    for solved in raw_solutions:
        _require(isinstance(solved, dict), "Malformed solved scenario record")
        stage = solved.get("scenario")
        _require(stage in expected and stage not in solution_by_stage, "Unexpected/duplicate solved scenario")
        _require(solved.get("has_solution") is True, "Source scenario has no persisted solution")
        version = solved.get("version")
        _require(type(version) is int and version >= 1, "Invalid saved scenario version")
        solution_by_stage[stage] = {
            "scenario": stage,
            "version": version,
            "has_solution": True,
            "objective_native": _finite_number(solved.get("objective_native")),
            "notebook_source_sha256": notebook_by_stage[stage],
        }
    _require(set(notebook_by_stage) == set(expected) == set(solution_by_stage), "Scenario or notebook missing")

    return {
        "schema_version": EVIDENCE_SCHEMA,
        "provenance": ATTESTATION,
        "source_project": "residual-pathways",
        "source_run_id": run_id,
        "source_run_status": "ACTUAL_MESSAGEIX_GAMS_SOLVED",
        "scientific_scope": "EDUCATIONAL_MESSAGEIX_GAMS_NOT_AR6",
        "model": MODEL,
        "upstream_commit": UPSTREAM_COMMIT,
        "upstream_release": UPSTREAM_RELEASE,
        "message_ix_version": "3.11.1",
        "ixmp_version": "3.11.1",
        "scenarios": [solution_by_stage[stage] for stage, _, _ in NOTEBOOKS],
    }


def export_westeros_evidence(source_manifest, output_dir):
    """Emit only a sanitized JSON artifact and a byte-hash sidecar manifest."""
    source_manifest = Path(source_manifest).resolve()
    output_dir = Path(output_dir).resolve()
    _require(source_manifest.is_file(), "Private manifest not found")
    _require(source_manifest.stat().st_size <= 1_000_000, "Private manifest is unexpectedly large")
    try:
        private = json.loads(source_manifest.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise WesterosExportError("Invalid private manifest JSON") from exc

    evidence = evidence_from_private_manifest(private)
    artifact_name = "westeros_evidence.json"
    raw = (json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
    index = {
        "schema_version": BUNDLE_SCHEMA,
        "artifact_name": artifact_name,
        "artifact_sha256": sha256(raw).hexdigest(),
        "artifact_bytes": len(raw),
        "publication_scope": "SANITIZED_DERIVED_METADATA_ONLY",
        "attestation": ATTESTATION,
    }
    _require(output_dir != source_manifest.parent, "Do not overwrite the private run directory")
    _require(not (output_dir / artifact_name).resolve() == source_manifest, "Export cannot overwrite source")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / artifact_name).write_bytes(raw)
    (output_dir / "westeros_evidence.manifest.json").write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return index
