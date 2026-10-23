from residual_pathways.preflight import inspect_environment, write_preflight


def test_preflight_is_explicitly_not_solve(tmp_path):
    status = write_preflight(tmp_path / "report.json")
    assert status["gams_license_checked"] is False
    assert status["westeros_solved"] is False
    assert status["scientific_status"] == "NOT_A_MESSAGEIX_EXPERIMENT"
    assert "gams-preflight.v1" in (tmp_path / "report.json").read_text()


def test_never_claim_install_is_license():
    d = inspect_environment()
    assert not (d["gams_license_checked"] or d["westeros_solved"])
