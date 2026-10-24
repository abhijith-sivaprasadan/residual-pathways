"""Source-locked test of ENGAGE detailed CO2 closure versus combined EIP.

The published ENGAGE notebook defines CO2|Other from Total, AFOLU,
Energy|Demand, Energy|Supply and Industrial Processes. This utility tests
that explicit source arithmetic separately from EIP versus its putative
detailed constituents. Source data stay local; only coded status is saved.
No model physics, official precision, or I1/I2/I3 grade is certified.
"""
from __future__ import annotations

from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
import csv
import json

from .arc24_poles_optional_co2 import TARGETS, YEARS
from .case_audit import CaseAuditError, SIX, TOTAL, UNIT
from .stratify import sha_file

EIP, AFOLU = SIX[:2]
DEMAND = "Emissions|CO2|Energy|Demand"
SUPPLY = "Emissions|CO2|Energy|Supply"
INDUSTRY = "Emissions|CO2|Industrial Processes"
OTHER = "Emissions|CO2|Other"
NEEDED = (TOTAL, EIP, AFOLU, DEMAND, SUPPLY, INDUSTRY, OTHER)


def _number(cell):
    if cell is None or not isinstance(cell, str) or not cell.strip():
        return None
    try:
        value = Decimal(cell.strip())
    except InvalidOperation as exc:
        raise CaseAuditError("Invalid source decimal") from exc
    if not value.is_finite():
        raise CaseAuditError("Nonfinite source decimal")
    return value


def _band(residual, values):
    if residual == 0:
        return "EXACT_REPORTED_DECIMAL_EQUALITY", "ZERO"
    scale = max(Decimal(1), *(abs(x) for x in values))
    percent = Decimal(100) * abs(residual) / scale
    bins = (
        (Decimal("0.001"), "BELOW_0_001_PERCENT"),
        (Decimal("0.1"), "FROM_0_001_TO_BELOW_0_1_PERCENT"),
        (Decimal("1"), "FROM_0_1_TO_BELOW_1_PERCENT"),
        (Decimal("10"), "FROM_1_TO_BELOW_10_PERCENT"),
    )
    category = next((name for bound, name in bins if percent < bound),
                    "AT_LEAST_10_PERCENT")
    direction = "POSITIVE" if residual > 0 else "NEGATIVE"
    return "NONZERO_REPORTED_DECIMAL_RESIDUAL", direction + "__" + category


def _screen(data):
    if len(data) < len(NEEDED):
        return {
            "status": "SOURCE_SERIES_NOT_REPORTED", "expanded_closure": None,
            "eip_detail": None, "unreported_variables": [v for v in NEEDED if v not in data],
        }
    if any(data[v][0] != UNIT for v in NEEDED):
        return {"status": "INCOMPATIBLE_UNITS", "expanded_closure": None,
                "eip_detail": None, "unreported_variables": []}
    vals = {v: data[v][1] for v in NEEDED}
    if any(v is None for v in vals.values()):
        return {"status": "MISSING_YEAR_VALUE", "expanded_closure": None,
                "eip_detail": None, "unreported_variables": []}
    # Test source equations *separately*. The notebook uses the detailed
    # sectors, whereas the AR6 aggregate comparison used combined EIP.
    detailed = vals[DEMAND] + vals[SUPPLY] + vals[INDUSTRY]
    expanded_gap = vals[TOTAL] - vals[AFOLU] - detailed - vals[OTHER]
    detail_minus_eip = detailed - vals[EIP]
    expanded_status, expanded_band = _band(expanded_gap, list(vals.values()))
    detail_status, detail_band = _band(detail_minus_eip, list(vals.values()))
    return {
        "status": "COMPUTABLE_REPORTED_DECIMAL_ONLY",
        "expanded_closure": expanded_status, "expanded_gap_band": expanded_band,
        "eip_detail": detail_status, "eip_gap_band": detail_band,
        "unreported_variables": [],
    }


def investigate_eip_mapping(world, packet_path, public_path):
    world, packet_path, public_path = (Path(x).resolve() for x in
                                       (world, packet_path, public_path))
    if (not world.is_file() or not packet_path.is_file() or
            len({world, packet_path, public_path}) != 3 or
            "ar6-private" not in packet_path.parts or
            "ar6-private" in public_path.parts):
        raise CaseAuditError("Original AR6 World and selection packet must remain private")
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if (packet.get("schema") != "residualpathways.ar6_canonical_selected24.private.v1"
            or packet.get("handling") != "LOCAL_ONLY_DO_NOT_PUBLISH"
            or not isinstance(packet.get("cases"), list) or len(packet["cases"]) != 24):
        raise CaseAuditError("Expected original private ARC24 source selection")
    cases = [c for c in packet["cases"] if c.get("case_id") in TARGETS]
    if len(cases) != 4 or len({c["case_id"] for c in cases}) != 4 or any(
            c.get("model") != "POLES ENGAGE" or not c.get("scenario")
            for c in cases):
        raise CaseAuditError("Expected four unique source-matched POLES cases")
    if sha_file(world) != packet.get("source_sha256"):
        raise CaseAuditError("World v1.1 SHA mismatch against selected private packet")
    source_sha = packet["source_sha256"]
    pair_to_case = {(c["model"], c["scenario"]): c for c in cases}
    data = {c["case_id"]: {} for c in cases}
    with world.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        if (len(fields) != len(set(fields)) or not {
                "Model", "Scenario", "Region", "Variable", "Unit"}.issubset(fields)):
            raise CaseAuditError("Original IAMC World CSV header invalid")
        cols = {year: (str(year) if str(year) in fields else
                       f"X{year}" if f"X{year}" in fields else None) for year in YEARS}
        if not cols[2050]:
            raise CaseAuditError("Mandatory year 2050 absent")
        for line, row in enumerate(reader, 2):
            if None in row or any(v is None for v in row.values()):
                raise CaseAuditError(f"Malformed World CSV row {line}")
            if row["Region"] != "World" or row["Variable"] not in NEEDED:
                continue
            c = pair_to_case.get((row["Model"], row["Scenario"]))
            if c is None:
                continue
            observations = data[c["case_id"]]
            variable = row["Variable"]
            if variable in observations:
                raise CaseAuditError("Duplicate source scenario-variable series")
            observations[variable] = {
                year: (row["Unit"], _number(row[col])) if col else None
                for year, col in cols.items()
            }
            if variable in (TOTAL, EIP, AFOLU):
                saved = c.get("source_observations", {}).get(variable)
                if (not isinstance(saved, dict) or
                        saved.get("unit") != row["Unit"] or
                        _number(saved.get("raw")) != observations[variable][2050][1]):
                    raise CaseAuditError("Selected 2050 source values do not match original CSV")
    output = []
    for c in sorted(cases, key=lambda item: item["case_id"]):
        obs = data[c["case_id"]]
        for year in YEARS:
            vals = {var: obs[var][year] for var in NEEDED
                    if var in obs and cols[year]}
            comparison = _screen(vals) if cols[year] else {
                "status": "YEAR_COLUMN_ABSENT", "expanded_closure": None,
                "eip_detail": None, "unreported_variables": []}
            output.append({
                "case_id": c["case_id"], "category": c["category"],
                "year": year, **comparison,
                "source_export_precision": "UNVERIFIED",
                "physical_partition_grade": "NOT_DETERMINED",
            })
    return {
        "schema": "residualpathways.arc24.poles_eip_mapping.v1",
        "status": "DETAILED_SOURCE_CO2_HIERARCHY_ARITHMETIC_ONLY_NO_I3",
        "source_sha256": source_sha, "case_years": 20,
        "expanded_status_counts": dict(Counter(x["expanded_closure"] for x in output)),
        "eip_detail_status_counts": dict(Counter(x["eip_detail"] for x in output)),
        "availability_counts": dict(Counter(x["status"] for x in output)),
        "verified_i3": 0, "rows": output,
        "evidence": "https://data.ece.iiasa.ac.at/engage-netzero-analysis/notebooks/1_categorization.html",
        "warning": (
            "ENGAGE Netzero Analysis uses total minus AFOLU, energy demand, energy supply, "
            "industrial processes to construct Other. This separately checks the original "
            "World source's EIP aggregate against those detailed categories. Even exact source "
            "arithmetic does not prove source precision, physically disjoint emissions, "
            "gross CO2 fluxes, atmospheric removals or I3 review. No source numbers released."
        ),
    }


def write_eip_mapping(world, packet, public):
    output = investigate_eip_mapping(world, packet, public)
    dest = Path(public).resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(output, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return output
