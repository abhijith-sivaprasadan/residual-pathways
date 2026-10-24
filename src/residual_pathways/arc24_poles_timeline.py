"""Targeted multi-year test of four POLES AR6 arithmetic discrepancies.

Computes redacted *descriptive* signed residual bands for only the four
previously selected POLES cases. No physical emissions partition inferred.
Author-controlled full source CSV stays local and its SHA is checked.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import csv
import json
from pathlib import Path

from .case_audit import CaseAuditError, SIX, TOTAL
from .stratify import sha_file

COMPONENTS = (TOTAL, SIX[0], SIX[1])
TARGET_IDS = ("ARC24-06", "ARC24-09", "ARC24-12", "ARC24-21")
YEARS = (2030, 2040, 2050, 2060, 2070)
UNIT = "Mt CO2/yr"
BANDS = (
    (Decimal("0.001"), "BELOW_0_001_PERCENT"),
    (Decimal("0.1"), "FROM_0_001_TO_BELOW_0_1_PERCENT"),
    (Decimal("1"), "FROM_0_1_TO_BELOW_1_PERCENT"),
    (Decimal("10"), "FROM_1_TO_BELOW_10_PERCENT"),
)


def _decimal(raw):
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        value = Decimal(raw.strip())
    except InvalidOperation as exc:
        raise CaseAuditError("Malformed source numeric text") from exc
    if not value.is_finite():
        raise CaseAuditError("Nonfinite source numeric text")
    return value


def _describe(values):
    if values is None or any(v is None for v in values):
        return {"arithmetic_status": "MISSING", "signed_residual_band": None}
    total, eip, afolu = values
    delta = total - eip - afolu
    if delta == 0:
        return {"arithmetic_status": "EXACT_DECIMAL_EQUALITY", "signed_residual_band": "ZERO"}
    base = max(Decimal(1), *(abs(v) for v in values))
    percent = Decimal(100) * abs(delta) / base
    band = next((label for threshold, label in BANDS if percent < threshold),
                "AT_LEAST_10_PERCENT")
    sign = "POSITIVE" if delta > 0 else "NEGATIVE"
    return {"arithmetic_status": "NONZERO_DECIMAL_RESIDUAL",
            "signed_residual_band": sign + "__" + band}


def investigate(csv_path, private_packet, public_output):
    csv_path, private_packet, public_output = (
        Path(p).resolve() for p in (csv_path, private_packet, public_output)
    )
    if len({csv_path, private_packet, public_output}) != 3 or (
            "ar6-private" not in private_packet.parts or
            "ar6-private" in public_output.parts or
            public_output in (csv_path, private_packet)):
        raise CaseAuditError("Private source and review packet cannot be a public output")
    packet = json.loads(private_packet.read_text(encoding="utf-8"))
    if packet.get("schema") != "residualpathways.ar6_canonical_selected24.private.v1" or packet.get("handling") != "LOCAL_ONLY_DO_NOT_PUBLISH":
        raise CaseAuditError("Expected private source-native 24-case packet")
    cases = packet.get("cases")
    if not isinstance(cases, list) or len(cases) != 24:
        raise CaseAuditError("24-case private ARC24 packet required")
    target_cases = [c for c in cases if c.get("case_id") in TARGET_IDS]
    if len(target_cases) != len(TARGET_IDS) or len({c["case_id"] for c in target_cases}) != len(TARGET_IDS):
        raise CaseAuditError("Four coded POLES cases not uniquely identified")
    for c in target_cases:
        if c.get("model") != "POLES ENGAGE" or not c.get("scenario"):
            raise CaseAuditError("Target case is not identified as expected POLES ENGAGE model")
    source_sha = sha_file(csv_path)
    if source_sha != packet.get("source_sha256"):
        raise CaseAuditError("World source CSV changed relative to private selected packet")

    by_pair = {(c["model"], c["scenario"]): c for c in target_cases}
    values = {c["case_id"]: {} for c in target_cases}
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        required = {"Model", "Scenario", "Region", "Variable", "Unit"}
        if not required.issubset(header) or len(header) != len(set(header)):
            raise CaseAuditError("World source CSV header incompatible")
        year_fields = {y: (str(y) if str(y) in header else f"X{y}"
                           if f"X{y}" in header else None) for y in YEARS}
        if not year_fields[2050]:
            raise CaseAuditError("Original source missing mandatory 2050 year")
        for line, row in enumerate(reader, start=2):
            if None in row:
                raise CaseAuditError(f"Malformed CSV field count, line {line}")
            if row["Region"] != "World":
                continue
            c = by_pair.get((row["Model"], row["Scenario"]))
            if not c or row["Variable"] not in COMPONENTS:
                continue
            if row["Unit"] != UNIT:
                raise CaseAuditError("Unit mismatch for tracked POLES variable")
            vname = row["Variable"]
            key = c["case_id"]
            if vname in values[key]:
                raise CaseAuditError("Duplicate tracked scenario-variable row")
            values[key][vname] = {y: _decimal(row[field]) if field else None
                                  for y, field in year_fields.items()}
            original = c["source_observations"].get(vname)
            if not isinstance(original, dict) or original.get("unit") != UNIT:
                raise CaseAuditError("Selected source 2050 component missing or incompatible")
            if values[key][vname][2050] != _decimal(original.get("raw")):
                raise CaseAuditError("2050 selected packet and original World CSV disagree")

    rows = []
    for c in sorted(target_cases, key=lambda x: x["case_id"]):
        obs = values[c["case_id"]]
        if len(obs) != len(COMPONENTS):
            raise CaseAuditError("Tracked model/scenario not complete in original CSV")
        for year in YEARS:
            if year_fields[year] is None:
                diagnostics = {"arithmetic_status": "YEAR_COLUMN_ABSENT",
                               "signed_residual_band": None}
            else:
                diagnostics = _describe([obs[v][year] for v in COMPONENTS])
            rows.append({
                "case_id": c["case_id"], "category": c["category"], "year": year,
                **diagnostics,
                "semantic_grade": "NOT_DETERMINED",
            })
    return {
        "schema": "residualpathways.arc24.poles_timeline.v1",
        "status": "MODEL_SPECIFIC_TIMELINE_ARITHMETIC_ONLY",
        "source_sha256": source_sha,
        "cases": len(target_cases), "year_grid": list(YEARS),
        "reviewed_i3_cases": 0,
        "warning": (
            "Coded signed bands are relative to max(1, abs(total), abs(EIP), abs(net AFOLU)). "
            "This is NOT source-reported precision, model accounting error, or a gross-removal balance. "
            "Do not infer causation, atmospheric removals or physical partition completeness."
        ),
        "observations": rows,
    }


def write_timeline(csv_path, private_packet, public_output):
    result = investigate(csv_path, private_packet, public_output)
    dest = Path(public_output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result
