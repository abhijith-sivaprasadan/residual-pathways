"""Source-sign diagnostics for the author-held ARC24 private review packet.

Keeps source model names, scenario names and numerical observations local;
publishes only coded case IDs, variable signs, exact units and method warnings.
A sign classification is NOT an I1-I3 scientific review.
"""
from __future__ import annotations

import json
from collections import Counter
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path

from .case_audit import SIX, TOTAL, UNIT, CaseAuditError

VARIABLES = (TOTAL, SIX[0], SIX[1], SIX[2], SIX[3], SIX[4], SIX[5])
AFOLU = "Emissions|CO2|AFOLU"
LAND = "Carbon Sequestration|Land Use"
FOSSIL_CCS = "Carbon Sequestration|CCS|Fossil"
DAC = "Carbon Sequestration|Direct Air Capture"


def sign(value):
    if value is None or isinstance(value, bool):
        raise CaseAuditError("Missing or invalid observed value; do not treat it as zero")
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise CaseAuditError("Invalid source observation") from exc
    if not decimal.is_finite():
        raise CaseAuditError("Nonfinite source observation")
    return "POSITIVE" if decimal > 0 else "NEGATIVE" if decimal < 0 else "ZERO"


def sign_report(packet):
    if not isinstance(packet, dict) or packet.get("handling") != "LOCAL_ONLY_DO_NOT_PUBLISH":
        raise CaseAuditError("Expected original private ARC24 selected source packet")
    cases = packet.get("cases")
    if not isinstance(cases, list) or len(cases) != 24:
        raise CaseAuditError("Expected exactly 24 original ARC24 cases")
    if len({c.get("case_id") for c in cases if isinstance(c, dict)}) != 24:
        raise CaseAuditError("Duplicate/malformed coded ARC24 cases")
    public_cases = []
    for c in cases:
        case_id = c.get("case_id")
        if not isinstance(case_id, str) or not case_id.startswith("ARC24-"):
            raise CaseAuditError("Case must use anonymized ARC24 identifier")
        obs = c.get("source_observations")
        if not isinstance(obs, dict):
            raise CaseAuditError("Missing observations map")
        states = {}
        units = {}
        for name in VARIABLES:
            datum = obs.get(name)
            if datum is None:
                states[name] = "MISSING"
                units[name] = None
                continue
            if not isinstance(datum, dict) or not isinstance(datum.get("unit"), str):
                raise CaseAuditError("Malformed observation/unit")
            unit = datum["unit"]
            units[name] = unit
            states[name] = sign(datum.get("value")) if unit == UNIT else "INCOMPATIBLE_UNIT"
        notes = []
        if states[AFOLU] == "NEGATIVE":
            notes.append("NEGATIVE_NET_AFOLU_CO2_NOT_GROSS_LAND_CDR")
        if states[LAND] == "POSITIVE" and states[AFOLU] in {"NEGATIVE", "POSITIVE"}:
            notes.append("LAND_SEQUESTRATION_AND_NET_AFOLU_COEXIST_DO_NOT_DOUBLE_COUNT")
        if states[FOSSIL_CCS] in {"ZERO", "POSITIVE", "NEGATIVE"}:
            notes.append("FOSSIL_CCS_IS_NOT_ATMOSPHERIC_REMOVAL")
        if states[DAC] == "ZERO":
            notes.append("DAC_REPORTED_ZERO_NOT_MISSING")
        public_cases.append({
            "case_id": case_id, "category": c.get("category"),
            "variable_signs": states, "units": units,
            "diagnostic_flags": notes,
            "scientific_accounting_grade": "NOT_DETERMINED",
        })
    public_cases.sort(key=lambda item: item["case_id"])
    negative = sum(c["variable_signs"][AFOLU] == "NEGATIVE" for c in public_cases)
    absent = sum(c["variable_signs"][LAND] == "MISSING" for c in public_cases)
    return {
        "schema": "residualpathways.arc24.sign_screen.v1",
        "status": "SOURCE_SIGN_SCREEN_ONLY_NO_I3",
        "source_sha256": packet.get("source_sha256"),
        "metadata_sha256": packet.get("metadata_sha256"),
        "number_of_cases": 24,
        "negative_afolu_cases": negative,
        "missing_land_sequestration_cases": absent,
        "reviewed_cases": 0,
        "verified_i3_cases": 0,
        "external_semantics_reference": "https://doi.org/10.5194/essd-17-221-2025",
        "warning": "AR6 AFOLU reports net signed CO2; land sequestration is a separately reported gross land sink. Sign and variable availability do not establish a complete disjoint positive-emissions/removals identity. Fossil CCS is not CDR.",
        "cases": public_cases,
    }


def write_sign_report(input_path, output_path):
    inp, out = Path(input_path).resolve(), Path(output_path).resolve()
    if not inp.is_file() or inp.stat().st_size > 30_000_000:
        raise CaseAuditError("Private source packet absent or unexpectedly large")
    if inp == out or "ar6-private" in out.parts:
        raise CaseAuditError("Public output must not overwrite or reside under ar6-private")
    packet = json.loads(inp.read_text(encoding="utf-8"))
    report = sign_report(packet)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
