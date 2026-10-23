"""Mock data only: this audit does not execute or independently verify GAMS."""
import json
import math
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest

from residual_pathways.westeros_cap_audit import reconcile_cap, audit_saved_run
from residual_pathways.westeros_analysis import WesterosAnalysisError
from residual_pathways.messageix_westeros import NOTEBOOKS, UPSTREAM_COMMIT, source_url


def example():
    vals = [350.5697571642012, 568.5098361190279, 580.9204067167708]
    return {
        "year_set": [690, 700, 710, 720],
        "cat_year": [{"type_year": "cumulative", "year": str(y)}
                     for y in (700, 710, 720)],
        "cat_emission": [{"type_emission": "GHG", "emission": "CO2"}],
        "duration_period": [],
        "emission_scaling": [],
        "historical_emission": [],
        "bound_emission": [{"node": "Westeros", "type_emission": "GHG", "type_tec": "all",
                            "type_year": "cumulative", "value": 500.0, "unit": "MtCO2"}],
        "EMISS": [{"node": node, "emission": "CO2", "type_tec": "all",
                   "year": year, "lvl": val, "mrg": 0.0}
                  for node in ("World", "Westeros")
                  for year, val in zip((700, 710, 720), vals)],
    }


def test_stored_emissions_saturate_exact_bound_with_pinned_year_durations():
    result = reconcile_cap(example())
    assert result["status"] == "NUMERICALLY_SATURATED"
    assert math.isclose(result["computed_average_annual"], 500.0, abs_tol=1e-10)
    assert math.isclose(result["slack"], 0, abs_tol=1e-10)
    assert result["period_durations"] == {"700": 10, "710": 10, "720": 10}
    assert result["duration_source"] == "DERIVED_FROM_PINNED_YEAR_SET"
    assert result["scaling_source"] == "PINNED_GAMS_DATA_LOAD_DEFAULT_ONE"
    assert result["shadow_price_status"] == "NOT_ESTABLISHED"


def test_world_aggregation_would_be_wrong():
    data = example()
    data["EMISS"] = [r for r in data["EMISS"] if r["node"] == "World"]
    assert reconcile_cap(data)["status"] == "NOT_ESTABLISHED"


def test_explicit_unequal_weights_override_year_difference():
    data = example()
    data["duration_period"] = [{"year": y, "value": d, "unit": "y"}
                                for y, d in zip((700, 710, 720), (5, 10, 20))]
    result = reconcile_cap(data)
    assert result["duration_source"] == "SAVED_SCENARIO_PARAMETER"
    assert result["computed_average_annual"] != pytest.approx(500.0)
    assert result["status"] == "WITHIN_BOUND_WITH_SLACK" or result["status"] == "APPARENT_BOUND_VIOLATION"


def test_missing_mapping_or_wrong_bound_stays_not_established():
    for field in ("cat_year", "cat_emission", "EMISS", "bound_emission"):
        data = example()
        data[field] = []
        assert reconcile_cap(data)["status"] == "NOT_ESTABLISHED"


def test_no_carbon_price_inference_even_if_optional_dual_available():
    result = reconcile_cap(example())
    assert result["shadow_price_status"] == "NOT_ESTABLISHED"
    assert result["status"] == "NUMERICALLY_SATURATED"


def test_historical_emissions_are_not_discarded():
    data = example()
    data["historical_emission"] = [{"node": "Westeros", "emission": "CO2",
                                    "type_tec": "all", "year": 700, "value": 100.0}]
    r = reconcile_cap(data)
    assert r["status"] == "APPARENT_BOUND_VIOLATION"
    assert r["computed_average_annual"] == pytest.approx(533.3333333333333)


def test_malformed_duplicates_fail_closed():
    data = example()
    data["EMISS"].append(dict(data["EMISS"][-1]))
    assert reconcile_cap(data)["status"] == "NOT_ESTABLISHED"


def fake_private():
    return {
        "schema": "local-westeros-execution.v1",
        "run_id": "20261023T230104Z_e182e730",
        "status": "ACTUAL_MESSAGEIX_GAMS_SOLVED",
        "model": "Westeros Electrified",
        "upstream_commit": UPSTREAM_COMMIT,
        "upstream_release": "v3.11.1",
        "evidence_scope": "EDUCATIONAL_MESSAGEIX_GAMS_NOT_AR6",
        "license_content_stored": False,
        "environment": {
            "actual_solve_performed": True, "message_ix_version": "3.11.1",
            "ixmp_version": "3.11.1", "upstream_commit": UPSTREAM_COMMIT,
        },
        "notebooks": [
            {"stage": stage, "source_url": source_url(filename),
             "sha256": "a" * 64, "model_cells": 10}
            for stage, filename, _ in NOTEBOOKS
        ],
        "solved_scenarios": [
            {"scenario": "baseline", "version": 1, "has_solution": True,
             "objective_native": 159025.828125},
            {"scenario": "emission_bound", "version": 1, "has_solution": True,
             "objective_native": 191510.796875},
        ],
    }


def test_local_readonly_cap_diagnostic_with_mock_ixmp(tmp_path, monkeypatch):
    run = tmp_path / "private"
    (run / "ixmp_config").mkdir(parents=True)
    (run / "ixmp_config" / "config.json").write_text("{}")
    (run / "ixmp_database").mkdir()
    (run / "ixmp_database" / "westeros.script").write_text("SYNTHETIC_TEST_ONLY")
    (run / "manifest.private.json").write_text(json.dumps(fake_private()))
    d = example()
    class FakeScenario:
        def __init__(self, p, model, scenario, version):
            assert model == "Westeros Electrified" and scenario == "emission_bound" and version == 1
            self.version = version
        def has_solution(self):
            return True
        def set(self, name):
            return d["year_set"] if name == "year" else d[name]
        def par(self, name):
            return d[name]
        def var(self, name):
            return {"lvl": 191510.796875, "mrg": 0.0} if name == "OBJ" else d[name]
    class FakePlatform:
        closed = False
        def close_db(self):
            self.closed = True
    p = FakePlatform()
    monkeypatch.setitem(sys.modules, "ixmp", SimpleNamespace(Platform=lambda: p))
    monkeypatch.setitem(sys.modules, "message_ix", SimpleNamespace(Scenario=FakeScenario))
    out = tmp_path / "derived"
    r = audit_saved_run(run / "manifest.private.json", out)
    assert p.closed
    assert r["status"] == "NUMERICALLY_SATURATED"
    assert (out / "cap_reconciliation.json").exists()
    import hashlib
    assert (out / "cap_reconciliation.sha256").read_text().strip() == hashlib.sha256(
        (out / "cap_reconciliation.json").read_bytes()).hexdigest()
    assert "ixmp_config" not in (out / "cap_reconciliation.json").read_text()
