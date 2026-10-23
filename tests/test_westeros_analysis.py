"""Synthetic fixtures test read-only Westeros analysis; no solver runs in tests."""
from __future__ import annotations
import json
import math
import sys
from types import SimpleNamespace

import pytest

from residual_pathways.messageix_westeros import NOTEBOOKS, UPSTREAM_COMMIT, source_url
from residual_pathways.westeros_analysis import (
    WesterosAnalysisError, analyze_run, compare_snapshots, reduce_metric,
    report_md, scenario_snapshot, svg_chart,
)


def act(tech, year, lvl, vintage=690, *, time="year"):
    return {"node_loc": "Westeros", "technology": tech, "year_vtg": vintage,
            "year_act": year, "mode": "standard", "time": time, "lvl": lvl}


def cap(tech, year, lvl, vintage=690):
    return {"node_loc": "Westeros", "technology": tech,
            "year_vtg": vintage, "year_act": year, "lvl": lvl}


def cap_new(tech, year, lvl):
    return {"node_loc": "Westeros", "technology": tech, "year_vtg": year, "lvl": lvl}


def scenario_data(coal, wind):
    return {
        "OBJ": {"lvl": 159025.828125 if coal == 10 else 191510.796875, "mrg": 0},
        "ACT": [act("coal_ppl", 700, coal / 2, 690), act("coal_ppl", 700, coal / 2, 700),
                act("wind_ppl", 700, wind), act("grid", 700, 9),
                act("bulb", 700, 8)],
        "CAP": [cap("coal_ppl", 700, coal * 2), cap("wind_ppl", 700, wind * 2)],
        "CAP_NEW": [cap_new("coal_ppl", 700, coal / 4), cap_new("wind_ppl", 700, wind / 4)],
    }


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
        "notebooks": [{"stage": stage, "source_url": source_url(filename),
                       "sha256": "a" * 64, "model_cells": 15}
                      for stage, filename, _ in NOTEBOOKS],
        "solved_scenarios": [{"scenario": "baseline", "version": 1,
                             "has_solution": True, "objective_native": 159025.828125},
                            {"scenario": "emission_bound", "version": 1,
                             "has_solution": True, "objective_native": 191510.796875}],
    }


class FakeScenario:
    def __init__(self, platform, model, scenario, version):
        assert model == "Westeros Electrified"
        assert version == 1
        self.version = version
        self.name = scenario
        self.data = scenario_data(10, 2) if scenario == "baseline" else scenario_data(8, 5)

    def has_solution(self):
        return True

    def has_var(self, name):
        return name in self.data or (self.name == "emission_bound" and name == "EMISS")

    def has_par(self, name):
        return self.name == "emission_bound" and name == "bound_emission"

    def has_equ(self, name):
        return self.name == "emission_bound" and name == "EMISSION_CONSTRAINT"

    def var(self, name):
        if name == "EMISS":
            return [{"node": "Westeros", "emission": "CO2", "type_tec": "all",
                     "year": 700, "lvl": 59.2, "mrg": 0.0}]
        return self.data[name]

    def par(self, name):
        return [{"node": "Westeros", "type_emission": "GHG", "type_tec": "all",
                 "type_year": "cumulative", "value": 500.0, "unit": "MtCO2"}]

    def equ(self, name):
        return [{"node": "Westeros", "type_emission": "GHG", "type_tec": "all",
                 "type_year": "cumulative", "lvl": 0.0, "mrg": -4.2}]


def test_reduce_vintage_activity_and_new_capacity():
    out = reduce_metric([act("coal_ppl", 700, 2.5), act("coal_ppl", 700, 7.5, 700)], "ACT")
    assert out[("ACT", "coal_ppl", 700)] == 10
    assert reduce_metric([cap_new("wind_ppl", 700, 1.5)], "CAP_NEW")[("CAP_NEW", "wind_ppl", 700)] == 1.5


@pytest.mark.parametrize("rows", [
    [act("coal_ppl", 700, float("nan"))],
    [act("coal_ppl", 700, 2, time="day")],
    [dict(act("coal_ppl", 700, 2), node_loc="Wrong")],
    [act("unknown", 700, 3)],
    [dict(act("coal_ppl", 700, 2), lvl="2")],
])
def test_bad_activity_rows_fail_closed(rows):
    with pytest.raises(WesterosAnalysisError):
        reduce_metric(rows, "ACT")


def test_snapshot_does_not_convert_emissions_dual_into_shadow_price():
    base_expected = {"version": 1, "objective_native": 159025.828125}
    bound_expected = {"version": 1, "objective_native": 191510.796875}
    fake = object()
    b = scenario_snapshot(FakeScenario(fake, "Westeros Electrified", "baseline", 1),
                          "baseline", base_expected)
    e = scenario_snapshot(FakeScenario(fake, "Westeros Electrified", "emission_bound", 1),
                          "emission_bound", bound_expected)
    result = compare_snapshots({"baseline": b, "emission_bound": e},
                               "20261023T230104Z_e182e730")
    assert result["objective"]["difference_native"] == 32484.96875
    matched = [r for r in result["comparisons"] if r["metric"] == "ACT"
               and r["technology"] == "coal_ppl" and r["year"] == 700]
    assert matched[0]["baseline"] == 10
    assert matched[0]["emission_bound"] == 8
    assert matched[0]["delta"] == -2
    assert result["emissions_bound"]["baseline_emissions"] == "NOT_MODELED_IN_BASELINE"
    assert result["emissions_bound"]["binding_status"] == "NOT_ESTABLISHED"
    assert result["emissions_bound"]["shadow_price_status"] == "NOT_ESTABLISHED"
    assert result["emissions_bound"]["constraint_equation"]["records"][0]["mrg"] == -4.2
    svg = svg_chart(result, "ACT")
    assert svg.startswith("<svg")
    assert "coal_ppl" in svg
    assert "NOT_ESTABLISHED" in report_md(result)


def test_unobserved_tuples_remain_missing_not_zero():
    a = {"scenario": "baseline", "objective_native": 10.0,
         "metrics": {"ACT": {("ACT", "coal_ppl", 700): 3.0},
                     "CAP": {("CAP", "coal_ppl", 700): 2.0},
                     "CAP_NEW": {("CAP_NEW", "wind_ppl", 700): 1.0}}}
    b = {"scenario": "emission_bound", "objective_native": 12.0,
         "metrics": {"ACT": {("ACT", "coal_ppl", 700): 4.0,
                              ("ACT", "wind_ppl", 700): 1.0},
                     "CAP": {("CAP", "coal_ppl", 700): 2.0},
                     "CAP_NEW": {("CAP_NEW", "wind_ppl", 700): 1.0}},
         "EMISS": {"status": "NOT_AVAILABLE", "records": []},
         "bound_emission": {"status": "NOT_AVAILABLE", "records": []},
         "EMISSION_CONSTRAINT": {"status": "NOT_AVAILABLE", "records": []}}
    result = compare_snapshots({"baseline": a, "emission_bound": b}, "dummy")
    wind = next(x for x in result["comparisons"] if x["metric"] == "ACT"
                and x["technology"] == "wind_ppl")
    assert wind["baseline"] is None
    assert wind["delta"] is None
    assert wind["comparison"] == "MISSING_IN_ONE_SCENARIO"


def test_end_to_end_fake_local_ixmp_no_solver(tmp_path, monkeypatch):
    run = tmp_path / "local"
    config = run / "ixmp_config"
    config.mkdir(parents=True)
    (config / "config.json").write_text("{}")
    dbdir = run / "ixmp_database"
    dbdir.mkdir()
    (dbdir / "westeros.script").write_text("SYNTHETIC_TEST_ONLY")
    (run / "manifest.private.json").write_text(json.dumps(fake_private()))
    class Platform:
        closed = False
        def close_db(self):
            self.closed = True
    mp = Platform()
    monkeypatch.setitem(sys.modules, "ixmp", SimpleNamespace(Platform=lambda: mp))
    monkeypatch.setitem(sys.modules, "message_ix", SimpleNamespace(Scenario=FakeScenario))
    outdir = tmp_path / "results"
    summary, index = analyze_run(run / "manifest.private.json", outdir)
    assert mp.closed
    assert summary["status"] == "LOCAL_STORED_IXMP_ANALYSIS"
    assert set(index["files_sha256"]) >= {"summary.json", "technology_comparison.csv",
                                         "report.md", "act_comparison.svg"}
    assert "NOT_ESTABLISHED" in (outdir / "report.md").read_text()
    for name, digest in index["files_sha256"].items():
        import hashlib
        assert hashlib.sha256((outdir / name).read_bytes()).hexdigest() == digest
    assert "ixmp_database" not in (outdir / "summary.json").read_text()
    assert "SYNTHETIC_TEST_ONLY" not in (outdir / "summary.json").read_text()
