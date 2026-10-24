"""Does POLES ENGAGE report AR6 optional non-AFOLU CO2 categories?

Only redacted presence, sign, units and missingness across four source-locked
scenarios and five years. No unverified reconciliation, fill or double counting.
"""
from __future__ import annotations

from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
import csv
import json

from .case_audit import CaseAuditError, UNIT
from .stratify import sha_file

TARGETS = ("ARC24-06", "ARC24-09", "ARC24-12", "ARC24-21")
YEARS = (2030, 2040, 2050, 2060, 2070)
OPTIONAL = (
    "Emissions|CO2|Other",
    "Emissions|CO2|Waste",
    "Emissions|CO2|Other Capture and Removal",
    "Emissions|CO2|Product Use",
)


def _state(raw, unit):
    if unit != UNIT:
        return "INCOMPATIBLE_UNIT"
    if raw is None or not raw.strip():
        return "MISSING_YEAR_VALUE"
    try:
        val = Decimal(raw.strip())
    except InvalidOperation as exc:
        raise CaseAuditError("Invalid optional CO2 source number") from exc
    if not val.is_finite():
        raise CaseAuditError("Nonfinite optional CO2 source number")
    return "POSITIVE" if val > 0 else "NEGATIVE" if val < 0 else "REPORTED_ZERO"


def optional_sector_presence(world, packet_file, public_output):
    world, packet_file, public_output = (
        Path(x).resolve() for x in (world, packet_file, public_output)
    )
    if (not world.is_file() or not packet_file.is_file() or
            len({world, packet_file, public_output}) != 3 or
            "ar6-private" not in packet_file.parts or
            "ar6-private" in public_output.parts):
        raise CaseAuditError("Keep protected AR6 inputs private and public diagnostics separate")
    packet = json.loads(packet_file.read_text(encoding="utf-8"))
    if (packet.get("schema") != "residualpathways.ar6_canonical_selected24.private.v1" or
            packet.get("handling") != "LOCAL_ONLY_DO_NOT_PUBLISH" or
            not isinstance(packet.get("cases"), list) or len(packet["cases"]) != 24):
        raise CaseAuditError("Expected original canonical selected-24 private packet")
    chosen = [c for c in packet["cases"] if c.get("case_id") in TARGETS]
    if len(chosen) != 4 or len({c["case_id"] for c in chosen}) != 4:
        raise CaseAuditError("Four unique selected POLES cases required")
    for c in chosen:
        if c.get("model") != "POLES ENGAGE" or not c.get("scenario"):
            raise CaseAuditError("Selected case is not the known POLES model")
    fingerprint = sha_file(world)
    if fingerprint != packet.get("source_sha256"):
        raise CaseAuditError("Original World CSV fingerprint differs from selected cohort")
    keyed = {(c["model"], c["scenario"]): c for c in chosen}
    found = {c["case_id"]: {} for c in chosen}
    with world.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames or []
        if len(set(headers)) != len(headers) or not {
                "Model", "Scenario", "Region", "Variable", "Unit"
                }.issubset(headers):
            raise CaseAuditError("Malformed original World IAMC CSV header")
        cols = {y: (str(y) if str(y) in headers else
                    f"X{y}" if f"X{y}" in headers else None) for y in YEARS}
        for i, row in enumerate(reader, start=2):
            if None in row or any(val is None for val in row.values()):
                raise CaseAuditError(f"Invalid World CSV row {i}")
            if row["Region"] != "World" or row["Variable"] not in OPTIONAL:
                continue
            case = keyed.get((row["Model"], row["Scenario"]))
            if case is None:
                continue
            case_rows = found[case["case_id"]]
            variable = row["Variable"]
            if variable in case_rows:
                raise CaseAuditError("Duplicate optional series for selected scenario")
            case_rows[variable] = {
                y: ("YEAR_COLUMN_ABSENT" if not col else
                    _state(row[col], row["Unit"]))
                for y, col in cols.items()
            }
    output = []
    for c in sorted(chosen, key=lambda case: case["case_id"]):
        for year in YEARS:
            found_vars = found[c["case_id"]]
            states = {key: found_vars[key][year] if key in found_vars
                      else "SERIES_NOT_REPORTED" for key in OPTIONAL}
            output.append({
                "case_id": c["case_id"],
                "category": c["category"],
                "year": year,
                "optional_sector_states": states,
                "physical_scope_review": "NOT_PERFORMED",
            })
    counts = {var: dict(Counter(r["optional_sector_states"][var] for r in output))
              for var in OPTIONAL}
    return {
        "schema": "residualpathways.arc24.poles_optional_co2.v1",
        "status": "ORIGINAL_SOURCE_PRESENCE_ONLY_NO_ADJUSTED_ACCOUNTING",
        "source_sha256": fingerprint,
        "num_cases": 4,
        "num_case_years": 20,
        "years": list(YEARS),
        "optional_variables": list(OPTIONAL),
        "status_by_optional_variable": counts,
        "observations": output,
        "verified_i3": 0,
        "method_source": "https://climate-assessment.readthedocs.io/en/latest/general.html",
        "scope_warning": (
            "The AR6 climate-assessment workflow may reclassify Other, Waste, "
            "Other Capture and Removal and Product Use to EIP in an alternate input "
            "route. This is NOT an official explanation for raw POLES ENGAGE "
            "total-EIP-AFOLU discrepancies. Presence does not establish that a "
            "variable is additive or disjoint; absence is not a physical zero. "
            "No source numerical values have been published."
        ),
    }


def write_optional_sectors(world, packet_file, public_output):
    result = optional_sector_presence(world, packet_file, public_output)
    path = Path(public_output).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
