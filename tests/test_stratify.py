import csv
import pytest
from residual_pathways.stratify import audit_strata, StrataError


def writer(path, headings, rows):
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(headings)
        w.writerows(rows)
    return path


def test_scenario_category_join_and_missing_reporting(tmp_path):
    metadata = writer(tmp_path/"meta.csv", ["Model", "Scenario", "Category"], [
        ["A", "S", "C1"], ["B", "S", "C2"], ["C", "S", ""], ["D", "S", "C1"]
    ])
    data = writer(tmp_path/"input.csv", ["Model","Scenario","Region","Variable","Unit","2050"], [
        ["A", "S", "World", "Emissions|CO2", "Mt CO2/yr", "0"],
        ["A", "S", "World", "Emissions|CH4", "Mt CH4/yr", ""],
        ["B", "S", "World", "Emissions|CO2", "Mt CO2/yr", "-5"],
        ["C", "S", "World", "Emissions|CO2", "Mt CO2/yr", "30"],
        ["Z", "S", "World", "Emissions|CO2", "Mt CO2/yr", "10"],
    ])
    d = audit_strata(data, metadata)
    assert d["matched_model_scenarios"] == 3
    assert d["unmatched_metadata_model_scenarios_count"] == 1
    assert d["unmatched_source_model_scenarios_count"] == 1
    assert d["strata"]["C1"]["variable_coverage"]["Emissions|CO2"]["coverage_fraction"] == 1
    assert d["strata"]["C1"]["variable_coverage"]["Emissions|CH4"]["coverage_fraction"] == 0
    assert "MISSING_CATEGORY" in d["strata"]
    assert d["scientific_status"] == "PRESENCE_ONLY_NO_ACCOUNTING_IDENTIFIABILITY"


def test_duplicate_source_variable_rejected(tmp_path):
    md = writer(tmp_path/"meta.csv", ["Model","Scenario","Category"], [["A","S","C1"]])
    row = ["A","S","World","Emissions|CO2","Mt CO2/yr","1"]
    src = writer(tmp_path/"input.csv", ["Model","Scenario","Region","Variable","Unit","2050"], [row,row])
    with pytest.raises(StrataError, match="Multiple"):
        audit_strata(src,md)


def test_duplicate_metadata_key_rejected(tmp_path):
    md = writer(tmp_path/"meta.csv",["Model","Scenario","Category"],[["A","S","C1"],["A","S","C2"]])
    src = writer(tmp_path/"input.csv",["Model","Scenario","Region","Variable","Unit","2050"],[
        ["A","S","World","Emissions|CO2","Mt CO2/yr","1"]])
    with pytest.raises(StrataError, match="Duplicate model"):
        audit_strata(src,md)
