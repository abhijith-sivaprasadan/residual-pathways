"""Version-explicit, gas-disaggregated GWP100 conversion.

Never convert an already aggregated CO2e quantity or ambiguous methane origin.
These factors are a reproducibility reference, not an IAM data identity.
"""
from __future__ import annotations
from dataclasses import dataclass
import math


GWP100 = {
    "IPCC_AR6_2021_ORIGINAL": {"CH4_FOSSIL": 29.8, "CH4_NONFOSSIL": 27.0, "N2O": 273.0},
    "IPCC_AR6_2025_ERRATA": {"CH4_FOSSIL": 28.1, "CH4_NONFOSSIL": 25.3, "N2O": 267.0},
}
SOURCE = {
    "IPCC_AR6_2021_ORIGINAL": "https://www.ipcc.ch/report/ar6/wg1/chapter/chapter-7/",
    "IPCC_AR6_2025_ERRATA": "https://www.ipcc.ch/report/ar6/wg1/about/errata/",
}
UNITS = {"CH4_FOSSIL": "Mt CH4/yr", "CH4_NONFOSSIL": "Mt CH4/yr", "N2O": "Mt N2O/yr"}


class GWPScopeError(ValueError):
    pass


@dataclass(frozen=True)
class GWPResult:
    source_gas: str
    methane_origin: str | None
    metric: str
    assessment_version: str
    input_mt_per_year: float
    input_unit: str
    factor: float
    co2e_mt_per_year: float
    output_unit: str
    reference_url: str
    status: str = "CALCULATED_FROM_EXPLICIT_GAS_AND_GWP"


def gas_to_co2e(amount: float, gas: str, unit: str, *,
                metric: str, assessment_version: str,
                methane_origin: str | None = None) -> GWPResult:
    """Require named assessment, gas, source class, metric, and raw-gas mass unit."""
    if metric != "GWP100":
        raise GWPScopeError("Only explicitly specified GWP100 supported; no inferred GWP20 or GTP")
    if assessment_version not in GWP100:
        raise GWPScopeError("Unknown assessment or erratum version")
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount):
        raise GWPScopeError("Nonfinite or nonnumeric emissions")
    if gas not in ("CH4", "N2O"):
        raise GWPScopeError("Gas must be unaggregated CH4 or N2O")
    if gas == "CH4":
        if methane_origin not in ("FOSSIL", "NONFOSSIL"):
            raise GWPScopeError("Methane fossil/non-fossil split required")
        key = f"CH4_{methane_origin}"
    else:
        if methane_origin is not None:
            raise GWPScopeError("Methane origin must not be attached to N2O")
        key = "N2O"
    if gas == "N2O" and unit == "kt N2O/yr":
        mass_mt = float(amount) / 1000.0
    elif unit == UNITS[key]:
        mass_mt = float(amount)
    else:
        raise GWPScopeError(f"Expected unaggregated raw gas mass unit {UNITS[key]} or kt N2O/yr; never convert CO2e twice")
    factor = GWP100[assessment_version][key]
    return GWPResult(gas, methane_origin, metric, assessment_version, mass_mt,
                     unit, factor, mass_mt * factor, "Mt CO2e/yr", SOURCE[assessment_version])
