"""Source audit tests with synthetic fixtures. Actual 24-case CI uses published source data."""
import csv
import json
import pytest
from residual_pathways.case_audit import (
    CATEGORIES, SIX, TOTAL, CaseAuditError, audit_cases,
    run_case_audit, arithmetic_diagnostic,
)


def fixture(tmp_path):
    meta = tmp_path / "metadata.csv"
    src = tmp_path / "source.csv"
    with meta.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Model", "Scenario", "Category"])
        for category in CATEGORIES:
            for i in range(5):
                w.writerow([f"Model-{category}", f"Scenario-{i}", category])
    with src.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Model", "Scenario", "Region", "Variable", "Unit", "2050"])
        for category in CATEGORIES:
            for i in range(5):
                for name in (TOTAL,) + SIX[:i+1]:
                    w.writerow([f"Model-{category}", f"Scenario-{i}",
                                "World", name, "Mt CO2/yr", str(i+10)])
    names = {"aggregate": TOTAL, **{str(i): var for i, var in enumerate(SIX)}}
    namefile = tmp_path / "names.json"
    namefile.write_text(json.dumps(names))
    return src, meta, names, namefile


def test_select_24_reproducible_each_category_three(tmp_path):
    source, metadata, names, _ = fixture(tmp_path)
    x, px = audit_cases(source, metadata, list(names.values()))
    y, py = audit_cases(source, metadata, list(names.values()))
    assert x == y and px == py
    assert x["summary"]["case_count"] == 24
    assert x["summary"]["per_category"] == {c: 3 for c in CATEGORIES}
    assert len({(item["model"], item["scenario"]) for item in px["cases"]}) == 24
    assert x["summary"]["verified_i3_cases"] == 0
    assert all(c["human_review"] == "NOT_REVIEWED" for c in x["cases"])
    assert all(c["accounting_grade"] == "NOT_DETERMINED" for c in x["cases"])


def test_public_contains_no_source_names_or_exact_values(tmp_path):
    source, metadata, names, file = fixture(tmp_path)
    public = tmp_path / "out" / "public.json"
    private = tmp_path / "private" / "review.json"
    result = run_case_audit(source, metadata, file, public, private)
    assert result["summary"]["case_count"] == 24
    p = public.read_text()
    assert "Model-C1" not in p and "Scenario-0" not in p
    assert "source_observations" not in p
    assert "source_observations" in private.read_text()
    assert result["selection"]["probability_sample"] is False


def test_arithmetic_diagnostic_never_claims_reconciliation():
    rec = {TOTAL: {"value": 12., "unit": "Mt CO2/yr"},
           SIX[0]: {"value": 8., "unit": "Mt CO2/yr"},
           SIX[1]: {"value": 4., "unit": "Mt CO2/yr"}}
    x = arithmetic_diagnostic(rec)
    assert x["difference_mt"] == 0
    assert x["status"] == "ARITHMETIC_ONLY_NOT_PHYSICAL_RECONCILIATION"
    rec[SIX[1]]["unit"] = "Gt CO2/yr"
    assert arithmetic_diagnostic(rec)["status"] == "NOT_COMPUTABLE_UNITS"
    del rec[SIX[0]]
    assert arithmetic_diagnostic(rec)["status"] == "NOT_COMPUTABLE_MISSING"


def test_reject_duplicate_and_nonfinite_source(tmp_path):
    source, metadata, names, _ = fixture(tmp_path)
    raw = source.read_text()
    row = raw.splitlines()[1]
    source.write_text(raw + row + "\n")
    with pytest.raises(CaseAuditError, match="Duplicate"):
        audit_cases(source, metadata, list(names.values()))
    source.write_text(raw.replace(",10\n", ",NaN\n", 1))
    with pytest.raises(CaseAuditError, match="Nonfinite"):
        audit_cases(source, metadata, list(names.values()))


def test_category_with_fewer_than_three_cannot_be_invented(tmp_path):
    source, metadata, names, _ = fixture(tmp_path)
    rows = metadata.read_text().splitlines()
    metadata.write_text("\n".join(r for r in rows if "Model-C8" not in r or "Scenario-0" in r) + "\n")
    with pytest.raises(CaseAuditError, match="Too few"):
        audit_cases(source, metadata, list(names.values()))


def test_never_write_private_packet_into_public_folder(tmp_path):
    source, meta, names, f = fixture(tmp_path)
    with pytest.raises(CaseAuditError, match="must differ"):
        run_case_audit(source, meta, f, tmp_path/"same", tmp_path/"same")


def test_missing_required_candidate_name_fails(tmp_path):
    src, meta, names, _ = fixture(tmp_path)
    with pytest.raises(CaseAuditError, match="Exact required"):
        audit_cases(src, meta, [TOTAL])
