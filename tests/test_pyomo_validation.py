import pytest
from residual_pathways.pyomo_validation import solve_pyomo,verify_all
from residual_pathways.stylized_model import Assumptions,SCENARIOS
from dataclasses import replace

def test_pyomo_baseline():
    r=solve_pyomo(Assumptions(),"baseline")
    assert r["status"]=="OPTIMAL"
    assert r["objective_million_usd"]==pytest.approx(5544)
    assert r["renewable_twh"]==pytest.approx(60)
    assert r["fossil_ccs_mt"]==pytest.approx(13)

def test_pyomo_infeasible():
    p=replace(Assumptions(),**SCENARIOS["combined_severe_constraints"])
    r=solve_pyomo(p,"severe")
    assert r["status"]=="INFEASIBLE_OR_UNSOLVED"

def test_all_scenarios_match_scipy(tmp_path):
    d=verify_all(tmp_path/"pyomo_crosscheck.json")
    assert len(d["cases"])==6
    assert all(x["agreement"] for x in d["cases"])
    assert "NOT_MESSAGEIX" in d["scientific_status"]
