import json
import sys
import pytest
from residual_pathways.messageix_westeros import (
    UPSTREAM_COMMIT, NOTEBOOKS, WesterosError, preflight,
    model_cells_until_objective, source_url,
    setup_private_ixmp, setup_private_kernel,
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
        {"cell_type": "code", "source": ["first = 1\\n", "scenario.solve()\\n"]},
        {"cell_type": "code", "source": ['scenario.var("OBJ")\\n']},
    ]}
    trimmed = model_cells_until_objective(original, 'scenario.var("OBJ")')
    assert trimmed["cells"][0]["source"] == "first = 1\\nscenario.solve()\\n"
    assert trimmed["cells"][1]["source"] == 'scenario.var("OBJ")\\n'
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
