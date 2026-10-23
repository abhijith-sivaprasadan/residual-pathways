from dataclasses import replace
import pytest
from residual_pathways.stylized_model import Assumptions, SCENARIOS, solve, run_experiments


def test_real_highs_baseline_solution():
    x = solve(Assumptions(), "baseline")
    assert x["status"] == "OPTIMAL"
    assert x["renewable_generation_twh"] == pytest.approx(60)
    assert x["fossil_generation_twh"] == pytest.approx(40)
    assert x["fossil_ccs_captured_mt"] == pytest.approx(13)
    assert x["atmospheric_removal_dac_mt"] == pytest.approx(0)
    assert x["net_atmospheric_emissions_mt"] == pytest.approx(25)
    assert x["objective_million_usd"] == pytest.approx(5544)
    assert x["identity_residual_mt"] < 1e-9


def test_controlled_counterfactuals():
    a = solve(replace(Assumptions(), renewable_limit_twh=30), "renewables_slow")
    b = solve(replace(Assumptions(), fossil_ccs_limit_mt=10), "storage_slow")
    assert a["fossil_ccs_captured_mt"] == pytest.approx(30)
    assert a["atmospheric_removal_dac_mt"] == pytest.approx(5.5)
    assert a["objective_million_usd"] == pytest.approx(6442.5)
    assert b["atmospheric_removal_dac_mt"] == pytest.approx(3)
    assert b["objective_million_usd"] == pytest.approx(5805)


def test_severe_combined_limit_is_not_silently_relaxed():
    x = solve(replace(Assumptions(), **SCENARIOS["combined_severe_constraints"]), "infeasible")
    assert x["status"] == "INFEASIBLE_OR_UNSOLVED"


@pytest.mark.parametrize("kwargs", [
    {"demand_twh": 0}, {"renewable_limit_twh": -5}, {"capture_fraction_limit": 2},
    {"atmospheric_cdr_limit_mt": -1}, {"fossil_emissions_mt_per_twh": float("nan")},
])
def test_bad_assumptions_rejected(kwargs):
    with pytest.raises(ValueError):
        solve(replace(Assumptions(), **kwargs), "invalid")


def test_synthetic_disclosure_and_outputs(tmp_path):
    report = run_experiments(tmp_path)
    assert len(report["results"]) == 6
    assert all(x["provenance_type"] == "SYNTHETIC_TEST_ONLY" for x in report["results"])
    assert "NOT MESSAGEix" in (tmp_path / "experiment_report.md").read_text()
