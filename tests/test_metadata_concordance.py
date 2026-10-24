"""Synthetic metadata comparison tests; not an authentication of IIASA data."""
import json
import pytest
from openpyxl import Workbook

from residual_pathways.metadata_concordance import compare, ConcordanceError


def workbook(path, *, data, extra=None):
    wb = Workbook()
    ws = wb.active
    ws.title = "meta_Ch3vetted_withclimate"
    ws.append(["Model", "Scenario", "Category", "Score"])
    for row in data:
        ws.append(row)
    if extra is not None:
        wb.create_sheet("README").append(["description", extra])
    wb.save(path)


def test_byte_distinct_but_normalized_cell_equivalence(tmp_path):
    a, b = tmp_path / "official.xlsx", tmp_path / "earlier.xlsx"
    workbook(a, data=[["M", "S", "C1", 1]])
    workbook(b, data=[["M", "S", "C1", 1.0]])
    result = compare(a, b)
    assert result["status"] == "EQUIVALENT_NORMALIZED_CELLS"
    assert result["sheets"][0]["identity_join"]["shared_model_scenarios"] == 1
    assert "M" not in json.dumps(result)
    assert "C1" not in json.dumps(result)


def test_reordered_rows_differ_by_cells_not_identity(tmp_path):
    a, b = tmp_path / "official.xlsx", tmp_path / "earlier.xlsx"
    workbook(a, data=[["M1", "S1", "C1", 1], ["M2", "S2", "C2", 2]])
    workbook(b, data=[["M2", "S2", "C2", 2], ["M1", "S1", "C1", 1]])
    sheet = compare(a, b)["sheets"][0]
    assert sheet["normalized_cell_differences"] > 0
    assert sheet["identity_join"]["shared_records_with_differences"] == 0


def test_changed_value_and_added_identity_reported_without_values(tmp_path):
    a, b = tmp_path / "official.xlsx", tmp_path / "earlier.xlsx"
    workbook(a, data=[["M1", "S1", "C1", 1], ["M2", "S2", "C2", 2]])
    workbook(b, data=[["M1", "S1", "C3", 1], ["M3", "S3", "C2", 2]])
    x = compare(a, b)
    j = x["sheets"][0]["identity_join"]
    assert (j["shared_model_scenarios"], j["official_only"], j["earlier_only"]) == (1, 1, 1)
    assert j["changed_column_counts"] == {"Category": 1}
    assert "M1" not in json.dumps(x)
    assert "S1" not in json.dumps(x)


def test_duplicate_identity_rejected(tmp_path):
    a, b = tmp_path / "official.xlsx", tmp_path / "earlier.xlsx"
    workbook(a, data=[["M", "S", "C1", 1], ["M", "S", "C1", 2]])
    workbook(b, data=[["M", "S", "C1", 1]])
    with pytest.raises(ConcordanceError, match="Duplicate"):
        compare(a, b)
