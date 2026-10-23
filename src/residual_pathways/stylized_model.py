"""Synthetic electricity-system experiment solved by SciPy/HiGHS. NOT MESSAGEix."""
from __future__ import annotations
from dataclasses import dataclass, asdict, replace
from pathlib import Path
import json
import math


@dataclass(frozen=True)
class Assumptions:
    demand_twh: float = 100.0
    renewable_limit_twh: float = 60.0
    fossil_emissions_mt_per_twh: float = 0.75
    process_emissions_mt: float = 8.0
    fossil_ccs_limit_mt: float = 30.0
    capture_fraction_limit: float = 0.85
    atmospheric_cdr_limit_mt: float = 8.0
    net_cap_mt: float = 25.0
    renewable_cost_usd_per_mwh: float = 58.0
    fossil_cost_usd_per_mwh: float = 36.0
    fossil_ccs_cost_usd_per_t: float = 48.0
    cdr_cost_usd_per_t: float = 135.0

    def validate(self):
        d = asdict(self)
        if not all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in d.values()):
            raise ValueError("Every input must be a finite number")
        if any(x < 0 for k, x in d.items() if k != "net_cap_mt"):
            raise ValueError("No negative capacities, costs or emissions factors")
        if not 0 <= self.capture_fraction_limit <= 1:
            raise ValueError("Capture fraction must be between zero and one")
        if self.demand_twh <= 0 or self.fossil_emissions_mt_per_twh <= 0:
            raise ValueError("Demand and fossil emissions intensity must be positive")
        return self


SCENARIOS = {
    "baseline": {},
    "renewable_deployment_limited": {"renewable_limit_twh": 30.0},
    "co2_storage_limited": {"fossil_ccs_limit_mt": 10.0},
    "no_atmospheric_removal": {"atmospheric_cdr_limit_mt": 0.0},
    "more_stringent_net_cap": {"net_cap_mt": 18.0},
    "combined_severe_constraints": {"renewable_limit_twh": 20.0, "fossil_ccs_limit_mt": 10.0},
}


def solve(parameters: Assumptions, name: str) -> dict:
    """Variables: renewable TWh, fossil TWh, fossil CCS Mt, atmospheric DAC Mt.

    Positive atmospheric CO2 = fossil before capture - captured fossil CO2 + process.
    Net atmospheric CO2 = positive atmospheric CO2 - true atmospheric DAC.
    Fossil CCS is avoided emissions, not atmospheric removals.
    Costs are million USD; TWh*USD/MWh and Mt*USD/t each equal million USD.
    """
    from scipy.optimize import linprog
    import scipy
    parameters.validate()
    c = [parameters.renewable_cost_usd_per_mwh, parameters.fossil_cost_usd_per_mwh,
         parameters.fossil_ccs_cost_usd_per_t, parameters.cdr_cost_usd_per_t]
    e = parameters.fossil_emissions_mt_per_twh
    constraints = [[-1, -1, 0, 0],
                   [0, -e * parameters.capture_fraction_limit, 1, 0],
                   [0, e, -1, -1]]
    upper = [-parameters.demand_twh, 0, parameters.net_cap_mt - parameters.process_emissions_mt]
    bounds = [(0, parameters.renewable_limit_twh), (0, None),
              (0, parameters.fossil_ccs_limit_mt), (0, parameters.atmospheric_cdr_limit_mt)]
    result = linprog(c, A_ub=constraints, b_ub=upper, bounds=bounds, method="highs")
    row = {"scenario": name, "provenance_type": "SYNTHETIC_TEST_ONLY",
           "model": "one-period-electricity-LP-not-MESSAGEix", "solver": "SciPy/HiGHS",
           "scipy_version": scipy.__version__, "assumptions": asdict(parameters),
           "solver_status": int(result.status)}
    if not result.success:
        row.update(status="INFEASIBLE_OR_UNSOLVED", failure_reason=str(result.message))
        return row
    renew, fossil, ccs, dac = map(float, result.x)
    positive = fossil * e - ccs + parameters.process_emissions_mt
    net = positive - dac
    tolerance = 1e-6
    if not (renew + fossil + tolerance >= parameters.demand_twh
            and ccs <= parameters.capture_fraction_limit * fossil * e + tolerance
            and ccs <= parameters.fossil_ccs_limit_mt + tolerance
            and renew <= parameters.renewable_limit_twh + tolerance
            and dac <= parameters.atmospheric_cdr_limit_mt + tolerance
            and net <= parameters.net_cap_mt + tolerance
            and positive >= -tolerance):
        raise RuntimeError("Numerical feasibility checks failed")
    row.update(status="OPTIMAL", renewable_generation_twh=renew,
               fossil_generation_twh=fossil, fossil_ccs_captured_mt=ccs,
               atmospheric_removal_dac_mt=dac, positive_atmospheric_emissions_mt=positive,
               net_atmospheric_emissions_mt=net, objective_million_usd=float(result.fun),
               identity_residual_mt=abs(net - (positive - dac)),
               gross_definition="positive to atmosphere after fossil CCS, plus processes")
    return row


def run_experiments(output_directory):
    base = Assumptions()
    observations = [solve(replace(base, **changes), name) for name, changes in SCENARIOS.items()]
    assert observations[0]["status"] == "OPTIMAL"
    results = {"schema_version": "synthetic-lp.v1", "data_type": "SYNTHETIC_TEST_ONLY",
               "scientific_status": "educational comparative statics, NOT MESSAGEix or AR6 evidence",
               "solver": "SciPy/HiGHS", "results": observations}
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    (output / "experiment_results.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    report = ["# Synthetic controlled electricity and CO2 experiments", "",
              "NOT MESSAGEix and NOT an AR6 result. Parameters are hypothetical, not calibrated.", "",
              "| Scenario | Status | Renewables TWh | Fossil CCS Mt | DAC Mt | Net Mt | Cost million USD |",
              "|---|---|---:|---:|---:|---:|---:|"]
    def value(item, key):
        return f"{item[key]:.3f}" if item["status"] == "OPTIMAL" else "n/a"
    for x in observations:
        report.append(f"| {x['scenario']} | {x['status']} | {value(x, 'renewable_generation_twh')} | "
                      f"{value(x, 'fossil_ccs_captured_mt')} | {value(x, 'atmospheric_removal_dac_mt')} | "
                      f"{value(x, 'net_atmospheric_emissions_mt')} | {value(x, 'objective_million_usd')} |")
    report += ["", "Fossil CCS decreases positive emissions at source and is not atmospheric CDR. "
               "The comparison is a controlled synthetic exercise only, with no estimates "
               "of real-world abatement costs, IAM effects or technology deployment.", ""]
    (output / "experiment_report.md").write_text("\n".join(report))
    return results
