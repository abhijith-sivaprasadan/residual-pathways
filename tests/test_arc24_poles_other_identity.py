"""Regression checks for private raw-decimal AR6 POLES CO2|Other hypothesis."""
import csv
import json

import pytest

from residual_pathways.arc24_poles_other_identity import (
    compare_other_to_residual, write_other_comparison, OTHER,
)
from residual_pathways.case_audit import TOTAL, SIX, CaseAuditError
from residual_pathways.stratify import sha_file

EIP, AFOLU = SIX[:2]
TRACKED = (6, 9, 12, 21)
YEARS = (2030, 2040, 2050, 2060, 2070)


def fixture(tmp_path, *, mismatch=False, no_other=False, bad_unit=False,
            duplicate=False):
    private = tmp_path / "data" / "ar6-private"
    private.mkdir(parents=True)
    world = private / "AR6_Scenarios_Database_World_v1.1.csv"
    cases = []
    all_rows = []
    for i in range(1, 25):
        model = "POLES ENGAGE" if i in TRACKED else "UNRELATED"
        sc = f"SECRET_SCENARIO_{i:02d}"
        observations = {}
        if i in TRACKED:
            # Nonnumeric zero-traps in alternate fields deliberately avoided.
            series = {
                TOTAL: ["110.00", "108.0", "105", "90", "70"],
                EIP: ["100.00", "100.0", "100", "100", "100"],
                AFOLU: ["5.00", "3.0", "0", "-15", "-35"],
                OTHER: ["5.00", "5.0", "5", "5", "5"],
            }
            if i == 9 and mismatch:
                series[OTHER][1] = "4.9"  # residual 5 != Other 4.9
            if i == 12 and mismatch:
                series[OTHER][4] = "-5"  # residual +5 != Other -5
            for variable, year_values in series.items():
                if variable == OTHER and i == 21 and no_other:
                    continue
                unit = "kg" if bad_unit and variable == OTHER and i == 6 else "Mt CO2/yr"
                all_rows.append([model, sc, "World", variable, unit] + year_values)
                if variable in (TOTAL, EIP, AFOLU):
                    observations[variable] = {
                        "raw": year_values[2], "value": float(year_values[2]),
                        "unit": unit,
                    }
        cases.append({
            "case_id": f"ARC24-{i:02d}",
            "model": model, "scenario": sc,
            "category": f"C{(i-1)//3+1}",
            "source_observations": observations,
        })
    if duplicate:
        all_rows.append(all_rows[0][:])
    with world.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Model", "Scenario", "Region", "Variable", "Unit"] + [str(y) for y in YEARS])
        writer.writerows(all_rows)
    packet = private / "canonical_selected24_packet.json"
    packet.write_text(json.dumps({
        "schema": "residualpathways.ar6_canonical_selected24.private.v1",
        "handling": "LOCAL_ONLY_DO_NOT_PUBLISH",
        "source_sha256": sha_file(world),
        "cases": cases,
    }))
    public = tmp_path / "results" / "poles" / "other_test.json"
    return world, packet, public


def test_exact_other_identity_in_all_20_source_case_years(tmp_path):
    world, packet, public = fixture(tmp_path)
    result = write_other_comparison(world, packet, public)
    assert result["case_year_count"] == 20
    assert result["identity_status_counts"] == {
        "EXACT_REPORTED_DECIMAL_IDENTITY_WITH_OTHER": 20
    }
    assert result["sign_matches"] == 20
    assert result["sign_mismatches"] == 0
    assert result["verified_i3"] == 0
    assert all(r["accounting_grade"] == "NOT_DETERMINED" for r in result["rows"])
    published = public.read_text()
    assert "SECRET_SCENARIO" not in published
    assert "POLES ENGAGE" not in published
    assert "reported_value_raw" not in published
    assert '"110.00"' not in published
    assert all("model" not in row and "scenario" not in row for row in result["rows"])


def test_nonzero_mismatch_descriptive_band_and_sign_difference(tmp_path):
    world, packet, public = fixture(tmp_path, mismatch=True)
    report = compare_other_to_residual(world, packet, public)
    assert report["identity_status_counts"]["NONZERO_REPORTED_DECIMAL_MISMATCH_WITH_OTHER"] == 2
    assert report["sign_matches"] == 19
    assert report["sign_mismatches"] == 1
    indexed = {(r["case_id"], r["year"]): r for r in report["rows"]}
    assert indexed[("ARC24-09", 2040)]["mismatch_band"] == "FROM_0_001_TO_BELOW_0_1_PERCENT"
    assert indexed[("ARC24-12", 2070)]["sign_agreement"] is False


def test_missing_other_series_is_not_converted_to_zero(tmp_path):
    world, packet, public = fixture(tmp_path, no_other=True)
    report = compare_other_to_residual(world, packet, public)
    assert report["identity_status_counts"]["SOURCE_SERIES_NOT_REPORTED"] == 5


def test_incompatible_unit_has_distinct_noncomparable_status(tmp_path):
    world, packet, public = fixture(tmp_path, bad_unit=True)
    report = compare_other_to_residual(world, packet, public)
    assert report["identity_status_counts"]["INCOMPATIBLE_SOURCE_UNITS"] == 5


def test_original_world_sha_mismatch_fails_closed(tmp_path):
    world, packet, public = fixture(tmp_path)
    content = json.loads(packet.read_text())
    content["source_sha256"] = "a" * 64
    packet.write_text(json.dumps(content))
    with pytest.raises(CaseAuditError, match="SHA256 mismatch"):
        write_other_comparison(world, packet, public)
    assert not public.exists()


def test_stored_2050_baseline_disagreement_fails_closed(tmp_path):
    world, packet, public = fixture(tmp_path)
    content = json.loads(packet.read_text())
    content["cases"][5]["source_observations"][TOTAL]["raw"] = "999"
    packet.write_text(json.dumps(content))
    with pytest.raises(CaseAuditError, match="2050 selected"):
        write_other_comparison(world, packet, public)


def test_duplicate_source_data_rejected(tmp_path):
    world, packet, public = fixture(tmp_path, duplicate=True)
    with pytest.raises(CaseAuditError, match="Duplicate"):
        write_other_comparison(world, packet, public)


def test_disallows_public_output_under_private_folder(tmp_path):
    world, packet, public = fixture(tmp_path)
    with pytest.raises(CaseAuditError, match="protected"):
        write_other_comparison(world, packet, packet.parent / "bad.json")
