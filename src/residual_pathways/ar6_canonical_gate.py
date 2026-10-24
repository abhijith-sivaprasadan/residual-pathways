"""Local-only canonical AR6 source-to-RP24 review gate.

Requires the user-obtained official World v1.1 CSV and metadata workbook.
Checks hashes, CSV structure, exact source identities, category membership and
previous teaching-release observations. Does NOT certify the file's origin,
individual model semantics, source precision or I1-I3 accounting.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import csv
import json
import math

from .case_audit import CATEGORIES, CaseAuditError, SIX, TOTAL, UNIT
from .stratify import metadata_rows, sha_file

WORLD_FILE = "AR6_Scenarios_Database_World_v1.1.csv"
META_FILE = "AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx"
SOURCE_HOME = "https://data.ene.iiasa.ac.at/ar6/#/downloads"
REVIEW_SHEET = "meta_Ch3vetted_withclimate"
STATUS = ("EXACT_TEXT_AND_UNIT", "EQUIVALENT_NUMBER_AND_UNIT", "NUMERICAL_DIFFERENCE",
          "UNIT_DIFFERENCE", "ABSENT_IN_CANONICAL_FILE", "NEW_IN_CANONICAL_FILE")


def _json(path, max_size=5_000_000):
    path = Path(path).resolve()
    if not path.is_file() or path.stat().st_size > max_size:
        raise CaseAuditError("Missing or unexpectedly large RP24 local review packet")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise CaseAuditError("Expected review packet object")
    return obj, path


def _matches(pair, expected):
    return isinstance(pair, (list, tuple)) and tuple(pair) == tuple(expected)


def _num(raw):
    try:
        v = float(raw)
        if math.isfinite(v):
            return v
    except (ValueError, TypeError):
        pass
    raise CaseAuditError("Nonfinite or invalid official-source observation")


def _candidate_values(source_path, wanted, selected_names, year):
    values = {case: {} for case in wanted}
    source_pairs = set()
    rows_read = 0
    with Path(source_path).open("r", encoding="utf-8-sig", newline="") as h:
        reader = csv.DictReader(h)
        headers = reader.fieldnames or []
        y = str(year) if str(year) in headers else "X" + str(year)
        required = {"Model", "Scenario", "Region", "Variable", "Unit", y}
        if len(set(headers)) != len(headers) or not required.issubset(headers):
            raise CaseAuditError("Official-source CSV header malformed or missing exact year")
        for row in reader:
            rows_read += 1
            if None in row or None in row.values():
                raise CaseAuditError("Malformed official-source CSV row")
            if row["Region"] != "World":
                continue
            pair = (row["Model"], row["Scenario"])
            if pair not in wanted:
                continue
            source_pairs.add(pair)
            name = row["Variable"]
            if name not in selected_names or not row[y].strip():
                continue
            if name in values[pair]:
                raise CaseAuditError("Duplicate selected official-source model/scenario/year/variable")
            values[pair][name] = {"unit": row["Unit"], "raw": row[y].strip(),
                                  "value": _num(row[y])}
    return values, source_pairs, rows_read


def _compare(previous, canonical):
    a, b = previous["unit"], canonical["unit"]
    if a != b:
        return "UNIT_DIFFERENCE"
    if previous["raw"] == canonical["raw"]:
        return "EXACT_TEXT_AND_UNIT"
    if math.isclose(float(previous["value"]), canonical["value"], rel_tol=1e-12,
                    abs_tol=1e-12):
        return "EQUIVALENT_NUMBER_AND_UNIT"
    return "NUMERICAL_DIFFERENCE"


def source_gate(world, metadata, private_packet, public_output, private_output, *,
                year=2050, sheet=REVIEW_SHEET):
    world, metadata = Path(world).resolve(), Path(metadata).resolve()
    if world.name != WORLD_FILE or metadata.name != META_FILE:
        raise CaseAuditError("Official filenames required; renamed teaching files are not accepted")
    if not world.is_file() or not metadata.is_file():
        raise CaseAuditError("Official World and metadata files must exist locally")
    if year != 2050 or sheet != REVIEW_SHEET:
        raise CaseAuditError("RP24 reference gate requires exact 2050 and climate-vetted sheet")
    packet, packet_file = _json(private_packet)
    cases = packet.get("cases")
    if not isinstance(cases, list) or len(cases) != 24:
        raise CaseAuditError("Expected original private 24-case review packet")
    ids = [c.get("case_id") for c in cases]
    if len(set(ids)) != 24 or sorted(ids) != [f"RP24-{i:02d}" for i in range(1,25)]:
        raise CaseAuditError("RP24 case IDs not complete and unique")
    by_pair = {}
    for c in cases:
        if c.get("year") != year or c.get("category") not in CATEGORIES:
            raise CaseAuditError("Inconsistent local case year/category")
        pair = (c.get("model"), c.get("scenario"))
        if not all(isinstance(s, str) and s for s in pair) or pair in by_pair:
            raise CaseAuditError("Duplicate/invalid local source scenario identity")
        if not isinstance(c.get("source_observations"), dict):
            raise CaseAuditError("Missing teaching-source observations")
        by_pair[pair] = c

    cohort = {}
    for idx, record in enumerate(metadata_rows(metadata, sheet_name=sheet), start=2):
        pair = (str(record.get("Model") or "").strip(),
                str(record.get("Scenario") or "").strip())
        cat = str(record.get("Category") or "").strip()
        if pair == ("", ""):
            continue
        if not all(pair) or pair in cohort:
            raise CaseAuditError(f"Malformed/duplicate canonical metadata row {idx}")
        cohort[pair] = cat
    if not cohort:
        raise CaseAuditError("Canonical climate-vetted metadata sheet is empty")

    source_values, source_pairs, rows = _candidate_values(
        world, by_pair, {*SIX, TOTAL}, year)
    statuses = Counter()
    case_outcomes = []
    private_rows = []
    for pair, case in sorted(by_pair.items(), key=lambda x: x[1]["case_id"]):
        observations = case["source_observations"]
        canonical = source_values[pair]
        observed = {}
        for key in sorted(set(observations) | set(canonical)):
            a = observations.get(key)
            b = canonical.get(key)
            status = (_compare(a, b) if a is not None and b is not None else
                      "NEW_IN_CANONICAL_FILE" if a is None else
                      "ABSENT_IN_CANONICAL_FILE")
            statuses[status] += 1
            observed[key] = status
            private_rows.append({
                "case_id": case["case_id"], "variable": key,
                "status": status, "teaching_observation": a,
                "canonical_observation": b,
            })
        canonical_category = cohort.get(pair)
        identity_status = (
            "SCENARIO_NOT_IN_WORLD_FILE" if pair not in source_pairs
            else "SCENARIO_NOT_IN_VETTED_METADATA" if canonical_category is None
            else "VETTED_CATEGORY_CHANGED" if canonical_category != case["category"]
            else "IDENTITY_AND_CATEGORY_MATCH"
        )
        case_outcomes.append({
            "case_id": case["case_id"], "category_teaching": case["category"],
            "identity_status": identity_status,
            "observations_compared": len(observed),
            "changed_values_or_units": sum(v in ("NUMERICAL_DIFFERENCE",
                "UNIT_DIFFERENCE", "ABSENT_IN_CANONICAL_FILE") for v in observed.values()),
            "scientific_review": "PENDING_MODEL_SPECIFIC_SEMANTICS_AND_PRECISION",
            "accounting_grade": "NOT_DETERMINED",
        })
    world_hash = sha_file(world)
    metadata_hash = sha_file(metadata)
    source_origin = "USER_SUPPLIED_LOCAL_FILES_ORIGIN_NOT_INDEPENDENTLY_VERIFIED"
    public = {
        "schema": "residualpathways.ar6_canonical_rp24_gate.v1",
        "status": "LOCAL_FILE_HASHED_ORIGIN_NOT_AUTHENTICATED",
        "source_origin": source_origin,
        "canonical_expected_file_names": [WORLD_FILE, META_FILE],
        "source_home": SOURCE_HOME,
        "world_sha256": world_hash,
        "metadata_sha256": metadata_hash,
        "world_bytes": world.stat().st_size,
        "metadata_bytes": metadata.stat().st_size,
        "source_rows_read": rows,
        "metadata_vetted_rows_read": len(cohort),
        "source_matched_rp24_cases": sum(p in source_pairs for p in by_pair),
        "metadata_matched_rp24_cases": sum(p in cohort for p in by_pair),
        "reviewed_rp24_cases": 0,
        "verified_i3_cases": 0,
        "observation_status_counts": {k: statuses[k] for k in STATUS},
        "cases": case_outcomes,
        "limits": [
            "Filename and SHA-256 cannot prove a local file came from IIASA",
            "A match to the public teaching release does not validate scientific scope",
            "These 24 were selected on teaching data; official-release sampling may differ",
            "No gross/net/CDR partition validated; no I1-I3 classification issued",
            "Original scenario names and all source values remain private",
        ],
    }
    private = {
        "handling": "LOCAL_ONLY_DO_NOT_COMMIT",
        "schema": "residualpathways.ar6_canonical_rp24_gate.private.v1",
        "world_sha256": world_hash, "metadata_sha256": metadata_hash,
        "case_reviews": [{"case_id": c["case_id"], "model": c["model"],
                          "scenario": c["scenario"], "teaching_category": c["category"],
                          "canonical_category": cohort.get((c["model"], c["scenario"])),
                          "reviewer_decision": "NOT_REVIEWED",
                          "source_model_documentation_url": None,
                          "positive_partition_complete": None,
                          "atmospheric_removal_nonoverlap": None,
                          "source_precision_documented": None,
                          "notes": None}
                         for c in cases],
        "observations": private_rows,
    }
    public_output, private_output = Path(public_output).resolve(), Path(private_output).resolve()
    if (public_output == private_output or
            "ar6-private" not in private_output.parts or
            "ar6-private" in public_output.parts):
        raise CaseAuditError("Private review path must be separate under data/ar6-private")
    if private_output.parent == public_output.parent:
        raise CaseAuditError("Public and private review reports must use different folders")
    public_output.parent.mkdir(parents=True, exist_ok=True)
    private_output.parent.mkdir(parents=True, exist_ok=True)
    public_output.write_text(json.dumps(public, indent=2, sort_keys=True)+"\n",
                             encoding="utf-8")
    private_output.write_text(json.dumps(private, indent=2, sort_keys=True)+"\n",
                              encoding="utf-8")
    return public
