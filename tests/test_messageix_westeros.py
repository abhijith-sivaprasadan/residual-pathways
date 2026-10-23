import json
import sys
from types import SimpleNamespace
import pytest
from residual_pathways.messageix_westeros import (
    UPSTREAM_COMMIT, NOTEBOOKS, WesterosError, preflight,
    model_cells_until_objective, source_url, objective_level,
    read_gams_solutions, setup_private_ixmp, setup_private_kernel,
)


def test_upstream_commit_is_immutable_identifier():
    assert len(UPSTREAM_COMMIT) == 40
    assert all(c in "0123456789abcdef" for c in UPSTREAM_COMMIT)
    assert all(UPSTREAM_COMMIT in source_url(name) for _, name, _ in NOTEBOOKS)


def test_truncate_after_actual_model_solve_but_before_plotting():
    original = {"cells": [
        {"cell_type": "markdown", "source": ["Intro"]},
        {"cell_type": "code", "source": ["scenario.solve()"]},
        {"cell_type": "code", "source": ['scenario.var("OBJ")["lvl"]']},
        {"cell_type": "code", "source": ["only_plot_afterward()"]},
    ]}
    trimmed = model_cells_until_objective(original, 'scenario.var("OBJ")')
    assert len(trimmed["cells"]) == 3
    assert len(original["cells"]) == 4
    assert all(isinstance(cell["source"], str) for cell in trimmed["cells"])
    assert [cell["source"] for cell in trimmed["cells"]] == [
        "Intro", "scenario.solve()", 'scenario.var("OBJ")["lvl"]',
    ]
    # The original upstream notebook and any cells beyond OBJ remain untouched.
    assert isinstance(original["cells"][0]["source"], list)
    assert original["cells"][3]["source"] == ["only_plot_afterward()"]


def test_normalizes_multiline_sources_without_losing_line_breaks():
    original = {"cells": [
        {"cell_type": "code", "source": ["first = 1\n", "scenario.solve()\n"]},
        {"cell_type": "code", "source": ['scenario.var("OBJ")\n']},
    ]}
    trimmed = model_cells_until_objective(original, 'scenario.var("OBJ")')
    assert trimmed["cells"][0]["source"] == "first = 1\nscenario.solve()\n"
    assert trimmed["cells"][1]["source"] == 'scenario.var("OBJ")\n'
    assert isinstance(original["cells"][0]["source"], list)


def test_fail_if_no_solve_or_malformed():
    with pytest.raises(WesterosError, match="precedes actual solve"):
        model_cells_until_objective(
            {"cells": [{"cell_type": "code", "source": ['scenario.var("OBJ")']}]},
            'scenario.var("OBJ")'
        )
    with pytest.raises(WesterosError, match="Malformed"):
        model_cells_until_objective({"cells": "wrong"}, 'scenario.var("OBJ")')


def test_ixmp_config_is_project_private(tmp_path):
    dest = setup_private_ixmp(tmp_path)
    conf = json.loads((dest / "config.json").read_text())
    assert conf["platform"]["default"] == "local"
    assert str(tmp_path).replace("\\", "/") in conf["platform"]["local"]["path"]
    assert "license" not in json.dumps(conf).lower()


def test_kernel_uses_active_python_environment(tmp_path):
    root = setup_private_kernel(tmp_path)
    kernel = json.loads((root / "kernels/rp-messageix/kernel.json").read_text())
    assert kernel["argv"][0] == sys.executable


def test_preflight_never_claims_success():
    d = preflight()
    assert d["actual_solve_performed"] is False
    assert d["license_checked"] is False
    assert d["evidence"] == "ENVIRONMENT_ONLY_NOT_A_GAMS_SOLVE"


def test_scalar_objective_from_ixmp_dict_and_indexed_dataframe():
    # ixmp returns a dict, not a DataFrame, for scalar variables like OBJ.
    assert objective_level({"lvl": 159025.830480, "mrg": 0.0}, "baseline") == 159025.830480
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame({"lvl": [191510.804279], "mrg": [0.0]})
    assert objective_level(df, "emission_bound") == 191510.804279


@pytest.mark.parametrize("bad", [
    {}, {"mrg": 0.0}, {"lvl": None}, {"lvl": float("nan")},
    {"lvl": float("inf")}, {"lvl": [1.0, 2.0]}, "invalid",
])
def test_invalid_scalar_objective_rejected(bad):
    with pytest.raises(WesterosError):
        objective_level(bad, "baseline")


def test_invalid_indexed_objective_rejected():
    pd = pytest.importorskip("pandas")
    for df in (pd.DataFrame(), pd.DataFrame({"lvl": []}),
               pd.DataFrame({"lvl": [1.0, 2.0]}),
               pd.DataFrame({"mrg": [0.0]})):
        with pytest.raises(WesterosError):
            objective_level(df, "baseline")


def test_read_gams_solutions_checks_both_solved_scenarios(monkeypatch):
    class Platform:
        closed = False
        def close_db(self):
            self.closed = True

    platform = Platform()
    monkeypatch.setitem(sys.modules, "ixmp", SimpleNamespace(Platform=lambda: platform))
    class Scenario:
        def __init__(self, platform_arg, model, scenario):
            assert platform_arg is platform and model == "Westeros Electrified"
            self.scenario = scenario
            self.version = 1
        def has_solution(self):
            return True
        def var(self, name):
            assert name == "OBJ"
            return {"lvl": {"baseline": 159025.830480,
                            "emission_bound": 191510.804279}[self.scenario],
                    "mrg": 0.0}
    monkeypatch.setitem(sys.modules, "message_ix", SimpleNamespace(Scenario=Scenario))
    values = read_gams_solutions()
    assert [v["scenario"] for v in values] == ["baseline", "emission_bound"]
    assert [v["objective_native"] for v in values] == [159025.830480, 191510.804279]
    assert all(v["has_solution"] is True and v["version"] == 1 for v in values)
    assert platform.closed is True
