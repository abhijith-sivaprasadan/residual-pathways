"""No real GAMS run: synthetic mocks exercise isolated three-case control logic."""
import copy
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from weakref import proxy

import pytest

from residual_pathways.messageix_westeros import MODEL, NOTEBOOKS, UPSTREAM_COMMIT, source_url
from residual_pathways.westeros_no_cap import (
    CONTROL_NAME, PARITY_PARS, build_three_case_comparison,
    run_control, verify_clone_inputs,
)
from residual_pathways.westeros_analysis import WesterosAnalysisError


def original_manifest():
    return {
        "schema": "local-westeros-execution.v1",
        "run_id": "20261023T230104Z_e182e730",
        "status": "ACTUAL_MESSAGEIX_GAMS_SOLVED",
        "model": MODEL,
        "upstream_commit": UPSTREAM_COMMIT,
        "upstream_release": "v3.11.1",
        "evidence_scope": "EDUCATIONAL_MESSAGEIX_GAMS_NOT_AR6",
        "license_content_stored": False,
        "environment": {
            "message_ix_version": "3.11.1", "ixmp_version": "3.11.1",
            "upstream_commit": UPSTREAM_COMMIT, "actual_solve_performed": True,
        },
        "notebooks": [
            {"stage": stage, "source_url": source_url(filename),
             "sha256": "f" * 64, "model_cells": 30}
            for stage, filename, _ in NOTEBOOKS
        ],
        "solved_scenarios": [
            {"scenario": "baseline", "version": 1, "objective_native": 159025.828125,
             "has_solution": True},
            {"scenario": "emission_bound", "version": 1,
             "objective_native": 191510.796875, "has_solution": True},
        ],
    }


def indices():
    for tech in ("coal_ppl", "wind_ppl", "grid", "bulb"):
        for year in (700, 710, 720):
            yield tech, year


def mock_metric(metric, multiplier):
    out = []
    for tech, year in indices():
        row = {"technology": tech, "node_loc": "Westeros", "lvl": multiplier * 10}
        if metric == "ACT":
            row.update(year_vtg=year, year_act=year, time="year", mode="standard")
        elif metric == "CAP":
            row.update(year_vtg=year, year_act=year)
        else:
            row.update(year_vtg=year)
        out.append(row)
    return out


class FakePlatform:
    def __init__(self, kind):
        self.kind = kind
        self.closed = False
        self._backend = object()  # Distinct backend per platform, like real ixmp.

    def close_db(self):
        self.closed = True


class FakeScenario:
    solve_count = 0
    copied_solution_clear_count = 0
    no_cap_level = 159025.828125
    bad_parameter = False
    source_mutations = 0
    def __init__(self, platform, model, scenario, version=None):
        assert model == MODEL
        # Mirror ixmp.TimeSeries.__init__: this is a weakref proxy, not mp.
        self.platform = proxy(platform)
        self.name = scenario
        self.version = version or 1
        self.solved = scenario in ("baseline", "emission_bound")
        self.parameters = {p: [{"node": "Westeros", "value": 1.0}] for p in PARITY_PARS}
        self.parameters["emission_factor"] = [{
            "node_loc": "Westeros", "technology": "coal_ppl",
            "emission": "CO2", "value": 7.4,
        }]
        self.parameters["bound_emission"] = ([{"node": "Westeros",
                                                "value": 500.0,
                                                "type_emission": "GHG"}]
                                               if scenario == "emission_bound" else [])
        self.data = {"ACT": mock_metric("ACT", 1),
                     "CAP": mock_metric("CAP", 2),
                     "CAP_NEW": mock_metric("CAP_NEW", 3)}

    def has_solution(self):
        return self.solved

    def var(self, name):
        if name == "OBJ":
            return {"lvl": 191510.796875 if self.name == "emission_bound" else
                    self.no_cap_level if self.name == CONTROL_NAME else 159025.828125,
                    "mrg": 0.0}
        return self.data[name]

    def par(self, name):
        return self.parameters[name]

    def clone(self, *, model, scenario, annotation, keep_solution, platform):
        assert self.name == "emission_bound"
        if platform.kind == "isolated" and keep_solution is False:
            # Mirror JDBCBackend.clone() v3.11.1's documented guard.
            raise NotImplementedError(
                "Cross-platform clone of message_ix.Scenario with `keep_solution=False`"
            )
        assert platform.kind == "isolated" and keep_solution is True
        s = FakeScenario(platform, model, scenario, version=1)
        s.parameters = copy.deepcopy(self.parameters)
        s.solved = True
        return s

    def remove_solution(self):
        assert self.name == CONTROL_NAME and self.platform.kind == "isolated"
        assert self.solved, "Cannot clear a non-existent solution"
        FakeScenario.copied_solution_clear_count += 1
        self.solved = False

    def check_out(self):
        assert not self.solved, "Must remove copied solution before checkout"
        self.checked_out = True

    def remove_par(self, name, key=None):
        assert self.name == CONTROL_NAME and name == "bound_emission"
        assert getattr(self, "checked_out", False), "Must check out before editing"
        assert key is not None, "Calling remove_par without key DELETES the parameter definition"
        assert len(key) == 1 and key == self.parameters[name]
        self.parameters[name] = []

    def commit(self, comment):
        assert "Remove CO2" in comment

    def set_as_default(self):
        pass

    def solve(self):
        assert self.name == CONTROL_NAME
        FakeScenario.solve_count += 1
        self.solved = True


def create_private(tmp_path):
    root = tmp_path / "saved"
    (root / "ixmp_config").mkdir(parents=True)
    (root / "ixmp_config" / "config.json").write_text("{}")
    (root / "ixmp_database").mkdir()
    (root / "ixmp_database" / "westeros.script").write_text("PRIVATE")
    p = root / "manifest.private.json"
    p.write_text(json.dumps(original_manifest()))
    return p


@pytest.fixture
def mock_platforms(monkeypatch):
    platforms = []
    def open_platform(*args, **kwargs):
        p = FakePlatform("isolated" if kwargs.get("backend") == "jdbc" else "original")
        platforms.append(p)
        return p
    FakeScenario.solve_count = 0
    FakeScenario.copied_solution_clear_count = 0
    FakeScenario.no_cap_level = 159025.828125
    monkeypatch.setitem(sys.modules, "ixmp", SimpleNamespace(Platform=open_platform))
    monkeypatch.setitem(sys.modules, "message_ix", SimpleNamespace(Scenario=FakeScenario))
    return platforms


def journal_cloned_solution_method(directory):
    return json.loads((directory / "manifest.private.json").read_text())["clone_method"]


def test_isolated_control_solves_only_one_scenario(tmp_path, mock_platforms):
    p = create_private(tmp_path)
    original_bytes = p.read_bytes()
    comparison, out = run_control(p, tmp_path / "output")
    assert comparison["status"] == "ACTUAL_MESSAGEIX_GAMS_CONTROL_SOLVED"
    assert comparison["baseline_vs_control"]["numerically_equivalent"] is True
    assert comparison["cap_effect"]["attributable_to_bound_only"] is True
    assert comparison["cap_effect"]["difference_native"] == 32484.96875
    assert len(comparison["comparisons"]) == 36
    assert all(r["complete"] for r in comparison["comparisons"])
    assert all(platform.closed for platform in mock_platforms)
    assert FakeScenario.solve_count == 1
    assert FakeScenario.copied_solution_clear_count == 1
    assert p.read_bytes() == original_bytes
    # The real ixmp API uses a weak proxy; identity with the Platform fails,
    # but the underlying destination backend identity must match exactly.
    assert mock_platforms[0]._backend is not mock_platforms[1]._backend
    assert journal_cloned_solution_method(out) == "CROSS_PLATFORM_KEEP_SOLUTION_THEN_REMOVE_SOLUTION"
    assert (out / "three_case_comparison.json").is_file()
    journal = json.loads((out / "manifest.private.json").read_text())
    assert journal["licensed_gams_solve_performed"] is True
    assert journal["status"] == "ACTUAL_MESSAGEIX_GAMS_CONTROL_SOLVED"
    assert not (tmp_path / "saved" / "three_case_comparison.json").exists()


def test_intended_parameter_deletion_preserves_emissions_factors():
    platform = FakePlatform("source")
    destination = FakePlatform("isolated")
    bounded = FakeScenario(platform, MODEL, "emission_bound")
    with pytest.raises(NotImplementedError, match="Cross-platform clone"):
        bounded.clone(model=MODEL, scenario=CONTROL_NAME, annotation="unsupported",
                      keep_solution=False, platform=destination)
    c = bounded.clone(model=MODEL, scenario=CONTROL_NAME, annotation="controlled",
                      keep_solution=True, platform=destination)
    assert c.has_solution()
    assert c.platform is not destination, "ixmp returns a proxy, not the same Platform object"
    assert c.platform._backend is destination._backend
    assert c.platform._backend is not platform._backend
    with pytest.raises(AssertionError, match="Must remove copied solution"):
        c.check_out()
    c.remove_solution()
    assert not c.has_solution()
    c.check_out()
    with pytest.raises(AssertionError, match="DELETES the parameter"):
        c.remove_par("bound_emission")
    c.remove_par("bound_emission", c.par("bound_emission"))
    assert bounded.par("bound_emission"), "Source bound must stay unchanged"
    parity = verify_clone_inputs(bounded, c)
    assert parity["control_cap_rows"] == 0
    assert parity["source_cap_rows"] == 1
    assert parity["parameter_rows_verified"]["emission_factor"] == 1
    c.parameters["inv_cost"][0]["value"] = 1000.0
    with pytest.raises(WesterosAnalysisError, match="inv_cost"):
        verify_clone_inputs(bounded, c)


def test_objective_mismatch_not_silently_classified_as_cap_effect(tmp_path, mock_platforms):
    original = create_private(tmp_path)
    FakeScenario.no_cap_level = 160000.0
    with pytest.raises(RuntimeError, match="differs from baseline"):
        run_control(original, tmp_path / "output")
    assert FakeScenario.solve_count == 1
    journal = json.loads(next((tmp_path / "output").glob("*/manifest.private.json")).read_text())
    assert journal["status"] == "CONTROL_SOLVED_BUT_BASELINE_OBJECTIVE_MISMATCH"
    assert journal["licensed_gams_solve_performed"] is True


def test_three_case_comparison_refuses_missing_scenario():
    with pytest.raises(WesterosAnalysisError, match="incomplete"):
        build_three_case_comparison({}, "example", 1, {})

def test_reject_clone_bound_to_source_backend_before_any_changes(
    tmp_path, mock_platforms, monkeypatch
):
    source_manifest = create_private(tmp_path)

    def wrongly_attached_clone(self, *, model, scenario, annotation,
                               keep_solution, platform):
        # Simulate a faulty backend that returns a wrapper attached to the
        # SOURCE instead of the destination; verify fail-closed handling.
        assert keep_solution is True
        bad = FakeScenario(self.platform, model, scenario, version=1)
        bad.solved = True
        return bad

    monkeypatch.setattr(FakeScenario, "clone", wrongly_attached_clone)
    with pytest.raises(WesterosAnalysisError, match="isolated destination backend"):
        run_control(source_manifest, tmp_path / "output")
    assert FakeScenario.solve_count == 0
    assert FakeScenario.copied_solution_clear_count == 0
    assert all(p.closed for p in mock_platforms)
    journal = json.loads(next((tmp_path / "output").glob("*/manifest.private.json")).read_text())
    assert journal["status"] == "FAILED_NOT_VERIFIED"
    assert journal["licensed_gams_solve_performed"] is False
