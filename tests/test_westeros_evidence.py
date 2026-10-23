"""Synthetic unit fixtures: these tests never run GAMS or attest a solve."""
import json
from hashlib import sha256
from pathlib import Path

import pytest

from residual_pathways.messageix_westeros import NOTEBOOKS, UPSTREAM_COMMIT, source_url
from residual_pathways.westeros_evidence import (
    WesterosExportError, evidence_from_private_manifest, export_westeros_evidence,
)


def simulated_private_manifest():
    return {
        "schema": "local-westeros-execution.v1",
        "run_id": "20261023T230104Z_e182e730",
        "status": "ACTUAL_MESSAGEIX_GAMS_SOLVED",
        "model": "Westeros Electrified",
        "upstream_commit": UPSTREAM_COMMIT,
        "upstream_release": "v3.11.1",
        "evidence_scope": "EDUCATIONAL_MESSAGEIX_GAMS_NOT_AR6",
        "license_content_stored": False,
        "private_notes": r"C:\Users\secret\gamslice.dat",
        "environment": {
            "actual_solve_performed": True,
            "message_ix_version": "3.11.1",
            "ixmp_version": "3.11.1",
            "upstream_commit": UPSTREAM_COMMIT,
            "other_sensitive_string": "DO_NOT_PUBLISH",
        },
        "notebooks": [
            {"stage": stage, "source_url": source_url(filename),
             "sha256": ("a" if stage == "baseline" else "b") * 64,
             "model_cells": 30}
            for stage, filename, _ in NOTEBOOKS
        ],
        "solved_scenarios": [
            {"scenario": "baseline", "has_solution": True,
             "version": 1, "objective_native": 159025.830480},
            {"scenario": "emission_bound", "has_solution": True,
             "version": 1, "objective_native": 191510.804279},
        ],
    }


def test_export_minimal_allowlist_and_byte_hash(tmp_path):
    private = simulated_private_manifest()
    raw_path = tmp_path / "private" / "manifest.private.json"
    raw_path.parent.mkdir()
    raw_path.write_text(json.dumps(private))
    output = tmp_path / "publishable"
    index = export_westeros_evidence(raw_path, output)
    raw = (output / "westeros_evidence.json").read_bytes()
    evidence = json.loads(raw)
    assert index["artifact_sha256"] == sha256(raw).hexdigest()
    assert index["artifact_bytes"] == len(raw)
    assert json.loads((output / "westeros_evidence.manifest.json").read_text()) == index
    assert evidence["provenance"] == "AUTHOR_REPORTED_LOCAL_EXECUTION_NOT_INDEPENDENTLY_VERIFIED"
    assert len(evidence["scenarios"]) == 2
    assert "DO_NOT_PUBLISH" not in raw.decode()
    assert "gamslice" not in raw.decode().lower()
    assert "secret" not in raw.decode().lower()
    assert "license" not in raw.decode().lower()
    assert "Users" not in raw.decode()
    assert "manifest.private.json" not in raw.decode()


@pytest.mark.parametrize("mutate", [
    lambda d: d.update(status="FAILED_NOT_VERIFIED"),
    lambda d: d.update(license_content_stored=True),
    lambda d: d["environment"].update(actual_solve_performed=False),
    lambda d: d["environment"].update(message_ix_version="0.0"),
    lambda d: d["solved_scenarios"][0].update(has_solution=False),
    lambda d: d["solved_scenarios"][0].update(objective_native=float("nan")),
    lambda d: d["solved_scenarios"].append(dict(d["solved_scenarios"][0])),
    lambda d: d["notebooks"][0].update(sha256="invalid"),
    lambda d: d["notebooks"][0].update(source_url="https://example.com/untrusted.ipynb"),
    lambda d: d.update(upstream_commit="0" * 40),
])
def test_export_rejects_invalid_solve_claims(mutate):
    d = simulated_private_manifest()
    mutate(d)
    with pytest.raises(WesterosExportError):
        evidence_from_private_manifest(d)


def test_export_does_not_touch_original(tmp_path):
    private = simulated_private_manifest()
    p = tmp_path / "manifest.private.json"
    p.write_text(json.dumps(private))
    before = p.read_bytes()
    export_westeros_evidence(p, tmp_path / "exports")
    assert p.read_bytes() == before
