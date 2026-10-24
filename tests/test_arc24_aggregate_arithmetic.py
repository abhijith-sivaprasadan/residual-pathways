"""Synthetic ARC24 decimal arithmetic validation; no real-world AR6 case assumed I3."""
from copy import deepcopy
from decimal import Decimal
import json

import pytest

from residual_pathways.arc24_aggregate_arithmetic import (
    audit_aggregate, write_aggregate_screen,
)
from residual_pathways.case_audit import (
    CaseAuditError, TOTAL, SIX, UNIT,
)


def record(raw, unit=UNIT):
    return {"raw": raw, "value": float(raw), "unit": unit}


def synthetic_packet():
    cases = []
    for i in range(1, 25):
        obs = {
            TOTAL: record("0.30"),
            SIX[0]: record("0.20"),
            SIX[1]: record("0.10"),
        }
        cases.append({
            "case_id": f"ARC24-{i:02d}", "category": f"C{(i-1)//3+1}",
            "model": f"SECRET_MODEL_{i:02d}",
            "scenario": f"SECRET_SCENARIO_{i:02d}",
            "year": 2050,
            "source_observations": obs,
            "arithmetic_diagnostic": {
                "status": "ARITHMETIC_ONLY_NOT_PHYSICAL_RECONCILIATION",
                "difference_mt": 0.30 - 0.20 - 0.10,
            },
        })
    return {
        "schema": "residualpathways.ar6_canonical_selected24.private.v1",
        "handling": "LOCAL_ONLY_DO_NOT_PUBLISH",
        "source_sha256": "a" * 64,
        "metadata_sha256": "b" * 64,
        "cases": cases,
    }


def test_exact_decimal_math_is_not_scientific_i3():
    result, private = audit_aggregate(synthetic_packet())
    assert result["num_cases"] == 24
    assert result["status_counts"]["EXACT_REPORTED_DECIMAL_CLOSURE"] == 24
    assert result["reviewed_i3_cases"] == 0
    assert all(c["semantic_partition_status"] == "NOT_REVIEWED" for c in result["cases"])
    assert private["cases"][0]["source_reported_decimal_residual_mtCO2_per_year"] == "0.00"
    assert all("model" not in c and "scenario" not in c for c in result["cases"])


def test_nonzero_diagnostic_and_private_math():
    p = synthetic_packet()
    c = p["cases"][0]
    c["source_observations"][TOTAL] = record("0.31")
    c["arithmetic_diagnostic"]["difference_mt"] = 0.31 - 0.20 - 0.10
    result, private = audit_aggregate(p)
    assert result["status_counts"]["NONZERO_REPORTED_DECIMAL_RESIDUAL"] == 1
    assert result["status_counts"]["EXACT_REPORTED_DECIMAL_CLOSURE"] == 23
    assert private["cases"][0]["source_reported_decimal_residual_mtCO2_per_year"] == "0.01"


def test_missing_not_zero_and_incompatible_units():
    p = synthetic_packet()
    del p["cases"][0]["source_observations"][TOTAL]
    p["cases"][1]["source_observations"][TOTAL]["unit"] = "kg"
    r, private = audit_aggregate(p)
    assert r["status_counts"]["NOT_COMPUTABLE_MISSING"] == 1
    assert r["status_counts"]["NOT_COMPUTABLE_UNITS"] == 1
    assert private["cases"][0]["source_reported_decimal_residual_mtCO2_per_year"] is None
    assert private["cases"][1]["source_reported_decimal_residual_mtCO2_per_year"] is None
    assert r["status_counts"]["EXACT_REPORTED_DECIMAL_CLOSURE"] == 22


@pytest.mark.parametrize("raw", ["NaN", "inf", "bad", "", "1e9999"])
def test_nonfinite_invalid_or_overflow_source_rejected(raw):
    p = synthetic_packet()
    p["cases"][0]["source_observations"][TOTAL]["raw"] = raw
    with pytest.raises(CaseAuditError):
        audit_aggregate(p)


def test_tampered_prior_floating_diagnostic_is_rejected():
    p = synthetic_packet()
    p["cases"][0]["arithmetic_diagnostic"]["difference_mt"] = 3.0
    with pytest.raises(CaseAuditError, match="does not match"):
        audit_aggregate(p)


def test_tampered_raw_float_mismatch_is_rejected():
    p = synthetic_packet()
    p["cases"][0]["source_observations"][TOTAL]["value"] = 100.0
    with pytest.raises(CaseAuditError, match="disagree"):
        audit_aggregate(p)


def test_private_and_public_material_are_separated(tmp_path):
    packet = synthetic_packet()
    private_folder = tmp_path / "data" / "ar6-private"
    private_folder.mkdir(parents=True)
    src = private_folder / "canonical_selected24_packet.json"
    src.write_text(json.dumps(packet))
    dest = tmp_path / "results" / "ar6" / "arithmetic_public.json"
    details = private_folder / "arithmetic_private.json"
    output = write_aggregate_screen(src, dest, details)
    assert output["status"] == "ARITHMETIC_SCREEN_ONLY_NO_I3"
    pub_txt = dest.read_text()
    assert "SECRET_MODEL_" not in pub_txt
    assert "SECRET_SCENARIO_" not in pub_txt
    assert "reported_value_raw" not in pub_txt
    assert "source_reported_decimal_residual_mtCO2_per_year" not in pub_txt
    assert "SECRET_MODEL_01" in details.read_text()
    assert output["private_packet_sha256"]
    assert details.read_text() != pub_txt


def test_public_source_output_cannot_share_private_folder(tmp_path):
    packet = synthetic_packet()
    pdir = tmp_path / "data" / "ar6-private"
    pdir.mkdir(parents=True)
    src = pdir / "packet.json"
    src.write_text(json.dumps(packet))
    with pytest.raises(CaseAuditError, match="Private packet"):
        write_aggregate_screen(src, pdir / "leak.json", pdir / "review.json")


def test_duplicate_case_ids_rejected():
    p = synthetic_packet()
    p["cases"][0]["case_id"] = p["cases"][1]["case_id"]
    with pytest.raises(CaseAuditError):
        audit_aggregate(p)
