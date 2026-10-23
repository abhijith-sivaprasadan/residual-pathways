import csv
import json
from pathlib import Path

import pytest

from residual_pathways.core import (DataError, read_iamc, coverage, compare,
    identifiability, reconcile, build_results, write_outputs)


def make_csv(tmp_path, records):
    p = tmp_path / "input.csv"
    with p.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Model", "Scenario", "Region", "Variable", "Unit", "2030", "2050", "2100"])
        w.writerows(records)
    return p


def test_parse_missing_is_not_zero(tmp_path):
    p = make_csv(tmp_path, [["A", "S", "World", "Emissions|CO2", "Mt CO2/yr", "2", "", "1"]])
    rows, meta = read_iamc(p)
    assert rows[0]["values"] == {"2030": 2.0, "2100": 1.0}
    assert meta["missing_cells"] == 1
    assert len(meta["sha256"]) == 64


def test_duplicate_rejected(tmp_path):
    row = ["A", "S", "World", "Emissions|CO2", "Mt CO2/yr", "2", "3", "4"]
    with pytest.raises(DataError, match="duplicate"):
        read_iamc(make_csv(tmp_path, [row, row]))


@pytest.mark.parametrize("invalid", ["NaN", "inf", "abc"])
def test_invalid_numeric_rejected(tmp_path, invalid):
    p = make_csv(tmp_path, [["A", "S", "World", "Emissions|CO2", "Mt CO2/yr", invalid, "1", "1"]])
    with pytest.raises(DataError):
        read_iamc(p)


def test_comparison_fail_closed_when_model_missing(tmp_path):
    p = make_csv(tmp_path, [["IMAGE 3.0.1", "S", "World", "Emissions|CO2", "Mt CO2/yr", "1", "2", "3"]])
    rows, _ = read_iamc(p)
    assert compare(rows) == []


def test_comparison_exact_matching(tmp_path):
    models = ["IMAGE 3.0.1", "REMIND-MAgPIE 1.7-3.0", "MESSAGEix-GLOBIOM 1.0"]
    p = make_csv(tmp_path, [[m, "S", "World", "Emissions|CO2", "Mt CO2/yr", "1", str(i + 4), "8"] for i, m in enumerate(models)])
    rows, meta = read_iamc(p)
    comparison = compare(rows)
    assert len(comparison) == 3
    assert {r["value"] for r in comparison} == {4., 5., 6.}
    assert coverage(rows)["world_co2_2050_count"] == 3
    out = tmp_path / "out"
    write_outputs(build_results(rows, meta), out)
    assert json.loads((out / "release/manifest.json").read_text())["identifiability_level"] == "I0"


def test_accounting_unknown_precision_cannot_be_i3():
    r = reconcile(0., 20., 20., quantization_steps=None,
                  semantics_verified=True, partition_exhaustive=True, nonoverlapping=True)
    assert r["status"] == "PRECISION_UNRESOLVED"
    assert identifiability({"net_co2", "gross_positive_co2", "atmospheric_removals"},
                           reviewed_semantics=True, exhaustive=True, nonoverlap=True, reconciliation=r)[0] == "I2"


def test_accounting_near_zero_passes_only_with_precision():
    r = reconcile(0., 20., 20., quantization_steps=(0.01, 0.01, 0.01),
                  semantics_verified=True, partition_exhaustive=True, nonoverlapping=True)
    assert r["status"] == "PASS"
    assert identifiability({"net_co2", "gross_positive_co2", "atmospheric_removals"},
                           reviewed_semantics=True, exhaustive=True, nonoverlap=True, reconciliation=r)[0] == "I3"


def test_accounting_semantic_failure_not_ignored():
    r = reconcile(4., 10., 6., quantization_steps=(0.01,) * 3,
                  semantics_verified=True, partition_exhaustive=False, nonoverlapping=True)
    assert r["status"] == "BLOCKED_SEMANTICS"


def test_accounting_nonzero_error_materiality_fails():
    r = reconcile(0., 20., 19., quantization_steps=(0.01,) * 3,
                  semantics_verified=True, partition_exhaustive=True, nonoverlapping=True)
    assert r["status"] == "FAIL"
