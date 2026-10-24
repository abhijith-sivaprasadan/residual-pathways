"""Synthetic validation of detailed ENGAGE CO2 hierarchy versus combined EIP."""
import csv
import json

import pytest

from residual_pathways.arc24_poles_eip_mapping import (
    investigate_eip_mapping, write_eip_mapping, TOTAL, EIP, AFOLU,
    DEMAND, SUPPLY, INDUSTRY, OTHER,
)
from residual_pathways.case_audit import CaseAuditError
from residual_pathways.stratify import sha_file

TARGETS = (6, 9, 12, 21)
YEARS = (2030, 2040, 2050, 2060, 2070)


def fixture(tmp_path, *, mismatch=False, missing=False, bad_units=False):
    private = tmp_path / "data" / "ar6-private"
    private.mkdir(parents=True)
    src = private / "AR6_Scenarios_Database_World_v1.1.csv"
    cases, rows = [], []
    for i in range(1, 25):
        sc = f"SECRET_{i}"
        model = "POLES ENGAGE" if i in TARGETS else "ANOTHER_MODEL"
        saved = {}
        if i in TARGETS:
            data = {
                TOTAL: ["110.00001"] * 5,
                EIP: ["100.00000"] * 5,
                AFOLU: ["5.00000"] * 5,
                DEMAND: ["80.00000"] * 5,
                SUPPLY: ["19.00000"] * 5,
                INDUSTRY: ["1.00001"] * 5,
                OTHER: ["5.00000"] * 5,
            }
            # Detailed sector sum = 100.00001 versus EIP = 100.00000.
            # Expanded identity is exact, four-term simple identity is not.
            if i == 9 and mismatch:
                data[TOTAL][3] = "110.02001"
            if i == 12 and missing:
                del data[SUPPLY]
            for variable, vals in data.items():
                unit = "kg" if bad_units and i == 6 and variable == SUPPLY else "Mt CO2/yr"
                rows.append([model, sc, "World", variable, unit] + vals)
                if variable in (TOTAL, EIP, AFOLU):
                    saved[variable] = {
                        "raw": vals[2], "value": float(vals[2]), "unit": unit,
                    }
        cases.append({
            "case_id": f"ARC24-{i:02d}", "model": model, "scenario": sc,
            "category": f"C{(i-1)//3+1}", "source_observations": saved,
        })
    with src.open("w", newline="", encoding="utf-8") as stream:
        out = csv.writer(stream)
        out.writerow(["Model", "Scenario", "Region", "Variable", "Unit"] + [str(y) for y in YEARS])
        out.writerows(rows)
    packet = private / "canonical_selected24_packet.json"
    packet.write_text(json.dumps({
        "schema": "residualpathways.ar6_canonical_selected24.private.v1",
        "handling": "LOCAL_ONLY_DO_NOT_PUBLISH", "source_sha256": sha_file(src),
        "cases": cases,
    }))
    dest = tmp_path / "results" / "eip_mapping.json"
    return src, packet, dest


def test_expanded_identity_exact_while_combined_eip_differs(tmp_path):
    src, packet, dest = fixture(tmp_path)
    result = write_eip_mapping(src, packet, dest)
    assert result["case_years"] == 20
    assert result["expanded_status_counts"]["EXACT_REPORTED_DECIMAL_EQUALITY"] == 20
    assert result["eip_detail_status_counts"]["NONZERO_REPORTED_DECIMAL_RESIDUAL"] == 20
    assert all(r["eip_gap_band"] == "POSITIVE__BELOW_0_001_PERCENT" for r in result["rows"])
    assert result["verified_i3"] == 0
    body = dest.read_text()
    assert "SECRET_" not in body
    assert "POLES ENGAGE" not in body
    assert "110.00001" not in body
    assert "model" not in result["rows"][0]
    assert "scenario" not in result["rows"][0]


def test_detects_nonzero_expanded_closure(tmp_path):
    src, packet, dest = fixture(tmp_path, mismatch=True)
    result = investigate_eip_mapping(src, packet, dest)
    assert result["expanded_status_counts"]["NONZERO_REPORTED_DECIMAL_RESIDUAL"] == 1
    assert result["expanded_status_counts"]["EXACT_REPORTED_DECIMAL_EQUALITY"] == 19


def test_missing_detailed_variable_distinct(tmp_path):
    src, packet, dest = fixture(tmp_path, missing=True)
    result = investigate_eip_mapping(src, packet, dest)
    assert result["availability_counts"]["SOURCE_SERIES_NOT_REPORTED"] == 5
    assert "Emissions|CO2|Energy|Supply" in result["rows"][10]["unreported_variables"]


def test_unit_mismatch_cannot_infer_identity(tmp_path):
    src, packet, dest = fixture(tmp_path, bad_units=True)
    result = investigate_eip_mapping(src, packet, dest)
    assert result["availability_counts"]["INCOMPATIBLE_UNITS"] == 5


def test_source_checksum_mismatch_rejected(tmp_path):
    src, packet, dest = fixture(tmp_path)
    j = json.loads(packet.read_text())
    j["source_sha256"] = "wrong"
    packet.write_text(json.dumps(j))
    with pytest.raises(CaseAuditError, match="SHA mismatch"):
        write_eip_mapping(src, packet, dest)
    assert not dest.exists()


def test_private_destination_rejected(tmp_path):
    src, packet, dest = fixture(tmp_path)
    with pytest.raises(CaseAuditError, match="remain private"):
        write_eip_mapping(src, packet, packet.parent / "unsafe.json")


def test_source_2050_identity_tampering_rejected(tmp_path):
    src, packet, dest = fixture(tmp_path)
    p = json.loads(packet.read_text())
    p["cases"][5]["source_observations"][TOTAL]["raw"] = "110.00002"
    packet.write_text(json.dumps(p))
    with pytest.raises(CaseAuditError, match="2050 source values"):
        write_eip_mapping(src, packet, dest)
