"""Exact decimal *arithmetic* screen for source-reported AR6 aggregate CO2.

No claim of complete gross emissions, physical removal partition, source
quantization precision or independent scientific accounting validation.
"""
from __future__ import annotations

from collections import Counter
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import math
from pathlib import Path

from .case_audit import CaseAuditError, TOTAL, SIX, UNIT

COMPONENTS = (TOTAL, SIX[0], SIX[1])
RESULT_TYPES = (
    "EXACT_REPORTED_DECIMAL_CLOSURE",
    "NONZERO_REPORTED_DECIMAL_RESIDUAL",
    "NOT_COMPUTABLE_MISSING",
    "NOT_COMPUTABLE_UNITS",
)
SCHEMA = "residualpathways.arc24.aggregate_arithmetic.v1"


def _value(datum, var):
    if not isinstance(datum, dict):
        raise CaseAuditError(f"Malformed source datum for {var}")
    raw, value = datum.get("raw"), datum.get("value")
    if not isinstance(raw, str) or not raw.strip() or value is None or isinstance(value, bool):
        raise CaseAuditError(f"Missing source numeric string or float for {var}")
    try:
        exact = Decimal(raw.strip())
        saved = float(value)
        reconstructed = float(exact)
    except (InvalidOperation, ValueError, OverflowError, TypeError) as exc:
        raise CaseAuditError(f"Invalid source numeric format for {var}") from exc
    if not exact.is_finite() or not math.isfinite(saved) or not math.isfinite(reconstructed):
        raise CaseAuditError(f"Nonfinite source value for {var}")
    if not math.isclose(reconstructed, saved, rel_tol=1e-14, abs_tol=1e-12):
        raise CaseAuditError(f"Raw source text and saved numerical value disagree for {var}")
    return exact


def audit_aggregate(packet):
    if not isinstance(packet, dict) or packet.get("schema") != "residualpathways.ar6_canonical_selected24.private.v1" or packet.get("handling") != "LOCAL_ONLY_DO_NOT_PUBLISH":
        raise CaseAuditError("Expected original private ARC24 canonical selected packet")
    cases = packet.get("cases")
    expected_ids = [f"ARC24-{i:02d}" for i in range(1, 25)]
    if not isinstance(cases, list) or len(cases) != 24 or sorted(
            c.get("case_id") for c in cases if isinstance(c, dict)) != expected_ids:
        raise CaseAuditError("Expected 24 exact ARC24 IDs, once each")
    for field in ("source_sha256", "metadata_sha256"):
        value = packet.get(field)
        if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value.lower()):
            raise CaseAuditError(f"Invalid source fingerprint {field}")

    public_rows, private_rows = [], []
    for c in sorted(cases, key=lambda item: item["case_id"]):
        observations = c.get("source_observations")
        if not isinstance(observations, dict):
            raise CaseAuditError("Missing source observations")
        absent = [v for v in COMPONENTS if v not in observations]
        wrong = [v for v in COMPONENTS if v in observations and
                 (not isinstance(observations[v], dict) or observations[v].get("unit") != UNIT)]
        decoded = {}
        if absent:
            status = "NOT_COMPUTABLE_MISSING"
        elif wrong:
            status = "NOT_COMPUTABLE_UNITS"
        else:
            decoded = {v: _value(observations[v], v) for v in COMPONENTS}
            residual = decoded[TOTAL] - decoded[SIX[0]] - decoded[SIX[1]]
            status = ("EXACT_REPORTED_DECIMAL_CLOSURE" if residual == 0 else
                      "NONZERO_REPORTED_DECIMAL_RESIDUAL")
            # Cross-check the floating diagnostic already computed during
            # source-native ARC24 selection; do not silently replace it.
            prior = c.get("arithmetic_diagnostic")
            if not isinstance(prior, dict) or prior.get("status") != "ARITHMETIC_ONLY_NOT_PHYSICAL_RECONCILIATION":
                raise CaseAuditError("Original ARC24 arithmetic diagnostic missing or incompatible")
            v = prior.get("difference_mt")
            try:
                prior_value = float(v)
            except (ValueError, TypeError, OverflowError) as exc:
                raise CaseAuditError("Original ARC24 numeric diagnostic invalid") from exc
            if not math.isfinite(prior_value) or not math.isclose(
                    float(residual), prior_value, rel_tol=1e-10, abs_tol=1e-7):
                raise CaseAuditError("Existing source-derived diagnostic does not match exact-decimal arithmetic")

        afolu = observations.get(SIX[1])
        afolu_sign = "MISSING"
        if afolu is not None:
            if not isinstance(afolu, dict):
                raise CaseAuditError("Malformed AFOLU observation")
            if afolu.get("unit") != UNIT:
                afolu_sign = "INCOMPATIBLE_UNIT"
            else:
                n = _value(afolu, SIX[1])
                afolu_sign = "NEGATIVE" if n < 0 else "POSITIVE" if n > 0 else "ZERO"

        public_rows.append({
            "case_id": c["case_id"], "category": c.get("category"),
            "arithmetic_status": status, "afolu_sign": afolu_sign,
            "missing_component_count": len(absent),
            "incompatible_unit_component_count": len(wrong),
            "precision_status": "NOT_SOURCE_VERIFIED",
            "semantic_partition_status": "NOT_REVIEWED",
            "gross_removal_identifiability": "NOT_DETERMINED",
        })
        private_rows.append({
            "case_id": c["case_id"], "model": c.get("model"), "scenario": c.get("scenario"),
            "year": c.get("year"), "category": c.get("category"),
            "arithmetic_status": status, "missing_variables": absent,
            "incompatible_unit_variables": wrong,
            "source_terms": [
                {"variable": v, "unit": observations.get(v, {}).get("unit"),
                 "reported_value_raw": observations.get(v, {}).get("raw")}
                for v in COMPONENTS
            ],
            "source_reported_decimal_residual_mtCO2_per_year": (
                str(decoded[TOTAL] - decoded[SIX[0]] - decoded[SIX[1]]) if decoded else None
            ),
            "source_export_quantization": "NOT_ESTABLISHED",
            "physical_partition_review": "PENDING_MODEL_SPECIFIC_EVIDENCE",
        })
    counts = Counter(row["arithmetic_status"] for row in public_rows)
    public = {
        "schema": SCHEMA, "status": "ARITHMETIC_SCREEN_ONLY_NO_I3",
        "source_sha256": packet["source_sha256"],
        "metadata_sha256": packet["metadata_sha256"],
        "num_cases": 24,
        "status_counts": {k: counts[k] for k in RESULT_TYPES},
        "cases": public_rows,
        "reviewed_i3_cases": 0,
        "disclaimer": (
            "The residual is total reported CO2 minus reported EIP CO2 minus "
            "reported signed net AFOLU CO2. Exact decimal equality is not "
            "semantic closure, source-rounding validation, or reconstructible "
            "gross positive emissions/atmospheric removals. "
            "Never double subtract land sequestration or treat fossil CCS as CDR. "
            "A nonzero reported residual may reflect source export rounding."
        ),
    }
    private = {
        "schema": SCHEMA + ".private",
        "handling": "LOCAL_ONLY_DO_NOT_PUBLISH",
        "source_sha256": packet["source_sha256"],
        "metadata_sha256": packet["metadata_sha256"],
        "cases": private_rows,
    }
    return public, private


def write_aggregate_screen(input_path, public_path, private_path):
    inp, pub, priv = (Path(p).resolve() for p in (input_path, public_path, private_path))
    if not inp.is_file() or inp.stat().st_size > 30_000_000:
        raise CaseAuditError("Original private 24-case packet missing or unexpectedly large")
    if len({inp, pub, priv}) != 3 or (
            "ar6-private" not in inp.parts or "ar6-private" not in priv.parts or
            "ar6-private" in pub.parts or pub.parent == priv.parent):
        raise CaseAuditError("Private packet and private output must stay in ar6-private, and public output elsewhere")
    packet = json.loads(inp.read_text(encoding="utf-8"))
    summary, detail = audit_aggregate(packet)
    summary["private_packet_sha256"] = sha256(inp.read_bytes()).hexdigest()
    pub.parent.mkdir(parents=True, exist_ok=True)
    priv.parent.mkdir(parents=True, exist_ok=True)
    pub.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    priv.write_text(json.dumps(detail, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary
