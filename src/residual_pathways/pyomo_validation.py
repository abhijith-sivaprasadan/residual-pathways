"""Independently formulated Pyomo/HiGHS cross-check of synthetic SciPy LP.

This does NOT use MESSAGEix or IPCC AR6 data, and does not establish external
validation. It is an independently encoded small linear-program check.
"""
from __future__ import annotations
from dataclasses import replace
from pathlib import Path
import json
from .stylized_model import Assumptions, SCENARIOS, solve as solve_scipy


def solve_pyomo(params, case):
    import pyomo.environ as pyo
    params.validate()
    m=pyo.ConcreteModel()
    m.renew=pyo.Var(bounds=(0,params.renewable_limit_twh))
    m.fossil=pyo.Var(domain=pyo.NonNegativeReals)
    m.ccs=pyo.Var(bounds=(0,params.fossil_ccs_limit_mt))
    m.dac=pyo.Var(bounds=(0,params.atmospheric_cdr_limit_mt))
    m.supply=pyo.Constraint(expr=m.renew+m.fossil>=params.demand_twh)
    m.capture=pyo.Constraint(expr=m.ccs<=params.capture_fraction_limit*params.fossil_emissions_mt_per_twh*m.fossil)
    m.net=pyo.Constraint(expr=(params.fossil_emissions_mt_per_twh*m.fossil-m.ccs+params.process_emissions_mt-m.dac)<=params.net_cap_mt)
    m.objective=pyo.Objective(expr=params.renewable_cost_usd_per_mwh*m.renew+
        params.fossil_cost_usd_per_mwh*m.fossil+
        params.fossil_ccs_cost_usd_per_t*m.ccs+
        params.cdr_cost_usd_per_t*m.dac,sense=pyo.minimize)
    solver=pyo.SolverFactory("highs")
    if not solver.available(exception_flag=False):
        raise RuntimeError("Pyomo highspy solver not available")
    res=solver.solve(m,load_solutions=False)
    optimal=res.solver.termination_condition==pyo.TerminationCondition.optimal
    if not optimal:
        return {"case":case,"status":"INFEASIBLE_OR_UNSOLVED","termination":str(res.solver.termination_condition),
                "solver":"Pyomo/HiGHS","source":"SYNTHETIC_TEST_ONLY_NOT_MESSAGEix"}
    m.solutions.load_from(res)
    r,f,c,d=(float(pyo.value(x)) for x in (m.renew,m.fossil,m.ccs,m.dac))
    net=params.fossil_emissions_mt_per_twh*f-c+params.process_emissions_mt-d
    if not (r+f>=params.demand_twh-1e-6 and
            c<=params.capture_fraction_limit*params.fossil_emissions_mt_per_twh*f+1e-6 and
            net<=params.net_cap_mt+1e-6):
        raise RuntimeError("Independent Pyomo model primal feasibility failed")
    return {"case":case,"status":"OPTIMAL","objective_million_usd":float(pyo.value(m.objective)),
            "renewable_twh":r,"fossil_twh":f,"fossil_ccs_mt":c,"dac_mt":d,
            "net_co2_mt":net,"termination":str(res.solver.termination_condition),
            "solver":"Pyomo/HiGHS","source":"SYNTHETIC_TEST_ONLY_NOT_MESSAGEix"}


def verify_all(destination):
    runs=[]
    for name,changes in SCENARIOS.items():
        p=replace(Assumptions(),**changes)
        py=solve_pyomo(p,name)
        scipy=solve_scipy(p,name)
        consistent=py["status"]==scipy["status"]
        if consistent and py["status"]=="OPTIMAL":
            consistent=abs(py["objective_million_usd"]-scipy["objective_million_usd"])<=1e-5
            consistent=consistent and abs(py["net_co2_mt"]-scipy["net_atmospheric_emissions_mt"])<=1e-5
        if not consistent:
            raise RuntimeError("Independent formulations disagree for "+name)
        runs.append({"case":name,"pyomo":py,"scipy_status":scipy["status"],
                     "scipy_objective_million_usd":scipy.get("objective_million_usd"),
                     "agreement":True})
    report={"schema_version":"independent-synthetic-lp-check.v1",
            "explanation":"Independent algebraic Pyomo LP vs SciPy linear-program formulation; same HiGHS family, hence not an independent solver algorithm.",
            "scientific_status":"SYNTHETIC_ONLY_NOT_MESSAGEIX_OR_AR6",
            "cases":runs}
    p=Path(destination);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    return report
