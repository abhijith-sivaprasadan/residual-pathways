"""Synthetic canonical-source fixtures; never treats toy files as IIASA authentic."""
from hashlib import sha256
import csv
import json

import pytest
from openpyxl import Workbook

from residual_pathways.ar6_canonical_gate import source_gate, select_canonical_24
from residual_pathways.case_audit import CaseAuditError, SIX, TOTAL, UNIT


def inputs(tmp_path, *, modify=None, metadata_change=False):
    private = tmp_path / "data" / "ar6-private"
    private.mkdir(parents=True)
    p = private / "case_audit_review_packet.json"
    cases = []
    names = ["Model", "Scenario", "Region", "Variable", "Unit", "2050"]
    rows = []
    for i in range(1, 25):
        model = f"MODEL_{i:02d}"
        scenario = f"SCENARIO_{i:02d}"
        cat = f"C{(i-1)//3+1}"
        v = {TOTAL: {"value": 10.0, "raw": "10", "unit": UNIT},
             SIX[0]: {"value": 10.0, "raw": "10", "unit": UNIT}}
        cases.append({
            "case_id": f"RP24-{i:02d}", "year": 2050, "category": cat,
            "slot": ("LOW", "MEDIAN", "HIGH")[(i-1) % 3],
            "model": model, "scenario": scenario, "source_observations": v,
        })
        for name in (TOTAL, SIX[0]):
            raw = "10"
            if modify == "numeric" and i == 1 and name == TOTAL:
                raw = "11"
            if modify == "format" and i == 1 and name == TOTAL:
                raw = "10.0"
            if modify == "unit" and i == 1 and name == TOTAL:
                unit = "kg" 
            else:
                unit = UNIT
            if modify == "missing" and i == 1 and name == TOTAL:
                continue
            rows.append([model, scenario, "World", name, unit, raw])
    p.write_text(json.dumps({"cases": cases, "handling": "LOCAL_ONLY_DO_NOT_COMMIT"}))
    canonical = tmp_path / "data" / "AR6_Scenarios_Database_World_v1.1.csv"
    with canonical.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(names)
        w.writerows(rows)
    meta = tmp_path / "data" / "AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "meta_Ch3vetted_withclimate"
    ws.append(["Model", "Scenario", "Category"])
    for i in range(1, 25):
        category = f"C{(i-1)//3+1}"
        if metadata_change and i == 1:
            category = "C8"
        ws.append([f"MODEL_{i:02d}", f"SCENARIO_{i:02d}", category])
    wb.save(meta)
    return canonical, meta, p


def run(tmp_path, **kwargs):
    canonical, meta, packet = inputs(tmp_path, **kwargs)
    public = tmp_path / "results" / "ar6-canonical-gate" / "summary_public.json"
    private = tmp_path / "data" / "ar6-private" / "canonical_rp24_review.json"
    result = source_gate(canonical, meta, packet, public, private)
    return result, json.loads(private.read_text()), public.read_text()


def test_matches_24_without_false_source_authentication(tmp_path):
    report, details, serialized = run(tmp_path)
    assert report["status"] == "LOCAL_FILE_HASHED_ORIGIN_NOT_AUTHENTICATED"
    assert report["source_matched_rp24_cases"] == 24
    assert report["metadata_matched_rp24_cases"] == 24
    assert report["observation_status_counts"]["EXACT_TEXT_AND_UNIT"] == 48
    assert report["verified_i3_cases"] == 0
    assert all(c["identity_status"] == "IDENTITY_AND_CATEGORY_MATCH"
               for c in report["cases"])
    assert len(details["case_reviews"]) == 24
    assert len(details["observations"]) == 48
    assert "MODEL_01" not in serialized
    assert "SCENARIO_01" not in serialized
    assert "canonical_observation" not in serialized


@pytest.mark.parametrize("mod,expected", [
    ("numeric", "NUMERICAL_DIFFERENCE"),
    ("unit", "UNIT_DIFFERENCE"),
    ("missing", "ABSENT_IN_CANONICAL_FILE"),
    ("format", "EQUIVALENT_NUMBER_AND_UNIT"),
])
def test_relevant_source_mismatches_reported_without_publishing_values(tmp_path, mod, expected):
    report, private, serialized = run(tmp_path, modify=mod)
    assert report["observation_status_counts"][expected] == 1
    assert report["verified_i3_cases"] == 0
    assert any(r["status"] == expected for r in private["observations"])
    assert "MODEL_01" not in serialized


def test_category_changed_gates_review_not_false_i3(tmp_path):
    report, _, _ = run(tmp_path, metadata_change=True)
    assert report["cases"][0]["identity_status"] == "VETTED_CATEGORY_CHANGED"
    assert report["reviewed_rp24_cases"] == 0


def test_renamed_teaching_source_is_not_canonical(tmp_path):
    world, meta, p = inputs(tmp_path)
    invalid = world.with_name("AR6-demo-data.csv")
    invalid.write_bytes(world.read_bytes())
    with pytest.raises(CaseAuditError, match="filenames"):
        source_gate(invalid, meta, p, tmp_path/"results"/"summary.json",
                    tmp_path/"data"/"ar6-private"/"private.json")


def test_nonprivate_output_path_rejected(tmp_path):
    world, meta, p = inputs(tmp_path)
    with pytest.raises(CaseAuditError, match="Private"):
        source_gate(world, meta, p, tmp_path/"results"/"public.json",
                    tmp_path/"results"/"private.json")


def test_source_duplicate_selection_record_fails_closed(tmp_path):
    world, meta, p = inputs(tmp_path)
    with world.open("a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow(["MODEL_01", "SCENARIO_01", "World", TOTAL, UNIT, "10"])
    with pytest.raises(CaseAuditError, match="Duplicate selected"):
        source_gate(world, meta, p, tmp_path/"results"/"public.json",
                    tmp_path/"data"/"ar6-private"/"private.json")


def test_canonical_select_without_teaching_packet(tmp_path):
    world, metadata, packet = inputs(tmp_path)
    packet.unlink()
    public_file = tmp_path / "results" / "canonical" / "selected24_public.json"
    private_file = tmp_path / "data" / "ar6-private" / "canonical_selected24_packet.json"
    summary = select_canonical_24(world, metadata, public_file, private_file)
    assert summary["status"] == "CANONICAL_NAMED_LOCAL_COHORT_SELECTED_ORIGIN_UNVERIFIED"
    assert summary["origin_authentication"] == "NOT_ESTABLISHED_FILENAME_AND_HASH_NOT_PROOF"
    assert len(summary["cases"]) == 24
    assert len({r["case_id"] for r in summary["cases"]}) == 24
    assert sum(r["category"] == "C1" for r in summary["cases"]) == 3
    assert summary["reviewed_cases"] == 0
    assert summary["verified_i3_cases"] == 0
    assert summary["six_variable_complete_cases"] == 0
    assert summary["source_matched_cohort_count"] == 24
    assert summary["source_rows_scanned"] == 48
    assert "MODEL_01" not in public_file.read_text()
    assert "SCENARIO_01" not in public_file.read_text()
    assert "10.0" not in public_file.read_text()
    data = json.loads(private_file.read_text())
    assert len(data["cases"]) == 24
    assert any(c["model"] == "MODEL_01" for c in data["cases"])
    assert all(c["review"]["conclusion"] == "NOT_DETERMINED" for c in data["cases"])
    assert all(c["review"]["reviewer"] is None for c in data["cases"])


def test_canonical_select_rejects_unsafe_output_without_writing(tmp_path):
    world, metadata, _ = inputs(tmp_path)
    forbidden = tmp_path / "results" / "private_review.json"
    with pytest.raises(CaseAuditError, match="Private"):
        select_canonical_24(world, metadata,
                            tmp_path / "results" / "public.json", forbidden)
    assert not forbidden.exists()


def test_canonical_select_rejects_teaching_file_renamed_wrongly(tmp_path):
    world, metadata, _ = inputs(tmp_path)
    renamed = world.with_name("AR6-demo-data.csv")
    renamed.write_bytes(world.read_bytes())
    with pytest.raises(CaseAuditError, match="official filenames"):
        select_canonical_24(renamed, metadata,
                            tmp_path / "results" / "public.json",
                            tmp_path / "data" / "ar6-private" / "private.json")
