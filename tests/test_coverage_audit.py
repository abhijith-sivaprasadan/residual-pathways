import csv
import json
import pytest
from pathlib import Path
from residual_pathways.coverage_audit import audit, CoverageError, run_audit


def write(tmp_path, rows, column="2050"):
    path = tmp_path / "mini_ar6.csv"
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(("Model", "Scenario", "Region", "Variable", "Unit", column))
        writer.writerows(rows)
    return path


def test_streamed_coverage_and_denominator(tmp_path):
    p = write(tmp_path, [
        ("A", "S", "World", "Emissions|CO2", "Mt CO2/yr", "100"),
        ("A", "S", "World", "Emissions|CH4", "Mt CH4/yr", ""),
        ("B", "S", "World", "Emissions|CO2", "Mt CO2/yr", ""),
        ("C", "S", "World", "Emissions|CO2", "Mt CO2/yr", "0"),
    ])
    out = audit(p, {"co2": "Emissions|CO2", "ch4": "Emissions|CH4"})
    assert out["world_model_scenario_pairs"] == 3
    assert out["candidate_coverage"]["co2"]["model_scenario_pairs_with_observation"] == 2
    assert out["candidate_coverage"]["ch4"]["model_scenario_pairs_with_observation"] == 0
    assert out["candidate_coverage"]["co2"]["coverage_fraction"] == 2/3
    assert out["research_status"].endswith("SEMANTICS_UNREVIEWED")
    assert len(out["source_sha256"]) == 64


def test_optional_x_year_header(tmp_path):
    p = write(tmp_path, [("A", "S", "World", "Emissions|CO2", "Mt CO2/yr", "2")], column="X2050")
    assert audit(p, {"co2": "Emissions|CO2"})["year"] == 2050


def test_duplicates_block(tmp_path):
    row = ("A", "S", "World", "Emissions|CO2", "Mt CO2/yr", "2")
    p = write(tmp_path, [row, row])
    with pytest.raises(CoverageError, match="Duplicate"):
        audit(p, {"co2": "Emissions|CO2"})


def test_nonfinite_blocks(tmp_path):
    p = write(tmp_path, [("A", "S", "World", "Emissions|CO2", "Mt CO2/yr", "NaN")])
    with pytest.raises(CoverageError, match="Nonfinite"):
        audit(p, {"co2": "Emissions|CO2"})


def test_source_data_never_emitted(tmp_path):
    p = write(tmp_path, [("A", "S", "World", "Emissions|CO2", "Mt CO2/yr", "1234567")])
    mapping = tmp_path / "map.json"
    mapping.write_text(json.dumps({"co2": "Emissions|CO2"}))
    output = tmp_path / "report.json"
    result = run_audit(p, mapping, output)
    assert "1234567" not in output.read_text()
    assert result["csv_series_rows"] == 1
