import json
import pytest
from residual_pathways.westeros import (
    WesterosError, blob_sha, verify_notebook, baseline_cell,
    preflight, validate_environment, TAG, NOTEBOOKS,
)


def test_git_blob_identity():
    assert blob_sha(b"hello\n") == "ce013625030ba8dba906f756967f9e9ca394464a"
    assert blob_sha(b"hello") != blob_sha(b"hello\n")


def test_unpinned_official_notebook_rejected():
    with pytest.raises(WesterosError, match="SHA mismatch"):
        verify_notebook(json.dumps({"nbformat": 4, "cells": []}).encode(), "baseline")


def test_baseline_uses_isolated_platform_and_only_skips_plot():
    nb = {"cells": [{"source": []} for _ in range(70)]}
    nb["cells"][6]["source"] = ["import ixmp\n", "mp = ixmp.Platform()"]
    nb["cells"][18]["source"] = ["gdp_profile = None\n",
                                   'gdp_profile.plot(title="GDP profile")']
    nb["cells"][69]["source"] = ["scenario.solve()"]
    assert "jdbc:hsqldb:mem:rp_westeros" in baseline_cell(nb, 6)
    assert "gdp_profile.plot" not in baseline_cell(nb, 18)
    assert "model_dir" in baseline_cell(nb, 69)


def test_environment_gate():
    with pytest.raises(WesterosError, match="GAMS executable"):
        validate_environment({"gams_available": False,
                              "message_ix_version": "3.11.1"})
    with pytest.raises(WesterosError, match="3.11.1"):
        validate_environment({"gams_available": True,
                              "message_ix_version": "0.1"})


def test_static_metadata_never_fakes_solves():
    assert TAG == "v3.11.1"
    assert len(NOTEBOOKS) == 2
    assert all(len(record[1]) == 40 for record in NOTEBOOKS.values())
    assert preflight()["solve_executed"] is False
