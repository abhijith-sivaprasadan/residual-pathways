"""Test whether reported CO2|Other equals the total-minus-EIP-minus-AFOLU gap.

Exact Decimal arithmetic uses original locally supplied World CSV text.
This tests a *numerical reporting hypothesis*; never changes source data,
assumes physical partitions or assigns I3.
"""
from __future__ import annotations

from collections import Counter
import csv
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path

from .case_audit import CaseAuditError, SIX, TOTAL, UNIT
from .stratify import sha_file
from .arc24_poles_optional_co2 import TARGETS, YEARS

EIP, AFOLU = SIX[:2]
OTHER = "Emissions|CO2|Other"
VARS = (TOTAL, EIP, AFOLU, OTHER)
LABELS = (
    (Decimal("0.001"), "BELOW_0_001_PERCENT"),
    (Decimal("0.1"), "FROM_0_001_TO_BELOW_0_1_PERCENT"),
    (Decimal("1"), "FROM_0_1_TO_BELOW_1_PERCENT"),
    (Decimal("10"), "FROM_1_TO_BELOW_10_PERCENT"),
)


def _as_decimal(raw):
    if raw is None or not isinstance(raw, str) or not raw.strip():
        return None
    try:
        result = Decimal(raw.strip())
    except InvalidOperation as exc:
        raise CaseAuditError("Malformed original source numeric cell") from exc
    if not result.is_finite():
        raise CaseAuditError("Nonfinite original source numeric cell")
    return result


def _sign(value):
    return "POSITIVE" if value > 0 else "NEGATIVE" if value < 0 else "ZERO"


def _compare(observations):
    if any(v not in observations for v in VARS):
        return {
            "status": "SOURCE_SERIES_NOT_REPORTED",
            "residual_sign": None,
            "other_sign": None,
            "sign_agreement": None,
            "mismatch_band": None,
        }
    if any(observations[v][0] != UNIT for v in VARS):
        return {
            "status": "INCOMPATIBLE_SOURCE_UNITS",
            "residual_sign": None,
            "other_sign": None,
            "sign_agreement": None,
            "mismatch_band": None,
        }
    values = {v: observations[v][1] for v in VARS}
    if any(v is None for v in values.values()):
        return {
            "status": "MISSING_YEAR_VALUE",
            "residual_sign": None,
            "other_sign": None,
            "sign_agreement": None,
            "mismatch_band": None,
        }
    residual = values[TOTAL] - values[EIP] - values[AFOLU]
    other = values[OTHER]
    gap = residual - other
    s_r, s_o = _sign(residual), _sign(other)
    if gap == 0:
        status, band = "EXACT_REPORTED_DECIMAL_IDENTITY_WITH_OTHER", "ZERO"
    else:
        status = "NONZERO_REPORTED_DECIMAL_MISMATCH_WITH_OTHER"
        denominator = max(Decimal("1"), *(abs(v) for v in values.values()))
        mismatch_percent = Decimal("100") * abs(gap) / denominator
        band = next((label for bound, label in LABELS if mismatch_percent < bound),
                    "AT_LEAST_10_PERCENT")
    return {
        "status": status, "residual_sign": s_r, "other_sign": s_o,
        "sign_agreement": s_r == s_o, "mismatch_band": band,
    }


def compare_other_to_residual(world, packet_path, public_path):
    world, packet_path, public_path = (
        Path(p).resolve() for p in (world, packet_path, public_path)
    )
    if (not world.is_file() or not packet_path.is_file() or
            len({world, packet_path, public_path}) != 3 or
            "ar6-private" not in packet_path.parts or
            "ar6-private" in public_path.parts):
        raise CaseAuditError("Original protected source input and output must remain separate")
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if (packet.get("schema") != "residualpathways.ar6_canonical_selected24.private.v1" or
            packet.get("handling") != "LOCAL_ONLY_DO_NOT_PUBLISH" or
            not isinstance(packet.get("cases"), list) or len(packet["cases"]) != 24):
        raise CaseAuditError("Expected original 24-case source-native private packet")
    chosen = [c for c in packet["cases"] if c.get("case_id") in TARGETS]
    if len(chosen) != 4 or len({c["case_id"] for c in chosen}) != 4:
        raise CaseAuditError("Expected exactly four unique POLES cases")
    if any(c.get("model") != "POLES ENGAGE" or not c.get("scenario") for c in chosen):
        raise CaseAuditError("One or more original POLES source model identities are invalid")
    world_sha = sha_file(world)
    if world_sha != packet.get("source_sha256"):
        raise CaseAuditError("World source SHA256 mismatch; cannot compare unlike extracts")
    known = {(c["model"], c["scenario"]): c for c in chosen}
    observed = {c["case_id"]: {} for c in chosen}
    with world.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        if len(header) != len(set(header)) or not {
                "Model", "Scenario", "Region", "Variable", "Unit"
                }.issubset(header):
            raise CaseAuditError("Incompatible source CSV header")
        year_fields = {
            y: (str(y) if str(y) in header else f"X{y}" if f"X{y}" in header else None)
            for y in YEARS
        }
        if not year_fields[2050]:
            raise CaseAuditError("Source CSV has no required 2050 field")
        for i, row in enumerate(reader, 2):
            if None in row or any(x is None for x in row.values()):
                raise CaseAuditError(f"Malformed source CSV at row {i}")
            if row["Region"] != "World" or row["Variable"] not in VARS:
                continue
            case = known.get((row["Model"], row["Scenario"]))
            if case is None:
                continue
            case_values = observed[case["case_id"]]
            variable = row["Variable"]
            if variable in case_values:
                raise CaseAuditError("Duplicate original source Model/Scenario/Variable observation")
            values = {year: (row["Unit"], _as_decimal(row[col]))
                      if col is not None else None
                      for year, col in year_fields.items()}
            case_values[variable] = values
            if variable in (TOTAL, EIP, AFOLU):
                baseline = case.get("source_observations", {}).get(variable)
                if (not isinstance(baseline, dict) or
                        baseline.get("unit") != row["Unit"] or
                        _as_decimal(baseline.get("raw")) != values[2050][1]):
                    raise CaseAuditError("Original 2050 selected case and source CSV do not agree")

    outputs = []
    for case in sorted(chosen, key=lambda x: x["case_id"]):
        found = observed[case["case_id"]]
        if not all(v in found for v in (TOTAL, EIP, AFOLU)):
            raise CaseAuditError("Source did not contain all three baseline CO2 series")
        for year in YEARS:
            if not year_fields[year]:
                result = {
                    "status": "YEAR_COLUMN_ABSENT", "residual_sign": None,
                    "other_sign": None, "sign_agreement": None, "mismatch_band": None,
                }
            else:
                terms = {v: found[v][year] for v in VARS if v in found}
                result = _compare(terms)
            outputs.append({
                "case_id": case["case_id"], "category": case["category"],
                "year": year, **result,
                "accounting_grade": "NOT_DETERMINED",
            })
    statuses = dict(Counter(row["status"] for row in outputs))
    matched_signs = sum(row["sign_agreement"] is True for row in outputs)
    mismatched_signs = sum(row["sign_agreement"] is False for row in outputs)
    return {
        "schema": "residualpathways.arc24.poles_other_residual.v1",
        "status": "REPORTED_DECIMAL_OTHER_HYPOTHESIS_ONLY_NO_I3",
        "source_sha256": world_sha, "case_count": 4,
        "case_year_count": len(outputs),
        "comparison": "Emissions|CO2 - EIP - AFOLU versus Emissions|CO2|Other",
        "identity_status_counts": statuses,
        "sign_matches": matched_signs, "sign_mismatches": mismatched_signs,
        "verified_i3": 0, "rows": outputs,
        "critical_caveat": (
            "Reported-decimal equality could establish a model export aggregate "
            "arithmetic convention for these observations, not independently "
            "authenticate variable disjointness, net/gross physical fluxes, "
            "atmospheric carbon removal or a source-declared rounding precision. "
            "Nonzero values require model-version source review. No original "
            "numerical observations, absolute residuals, model or scenario names "
            "are published."
        ),
    }


def write_other_comparison(world, packet, public):
    result = compare_other_to_residual(world, packet, public)
    output = Path(public).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result
