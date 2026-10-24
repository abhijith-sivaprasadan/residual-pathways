"""Local-only candidate publication preflight; never authorizes publication.

Checks an OUT-OF-BAND author-reported SHA pin, scientific scope and aggregate
privacy-sensitive small cells before a human considers committing a public JSON.
No raw AR6 rows, model/scenario identities or original values are read.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import re

from .coverage_release import CATEGORIES, FIELDS as INPUT_FIELDS, SCHEMA, YEARS

PUBLIC_FIELDS = {
    "category", "year", "variable", "denominator", "reporting",
    "model_labels", "scenario_fraction", "model_label_balanced_fraction", "units",
}
TOP_FIELDS = {
    "schema", "version", "scope", "evidence", "science_review_state",
    "i3_verified", "physical_accounting", "source_authentication",
    "metadata_concordance_status", "sha256", "metadata_sheet", "years",
    "categories", "variables", "cohort_size", "weighting", "records", "limitations",
}
WORLD_SHA = "4cf39b6b0d968e25ed389318acb1674f92146f977e9db4bfb7970f048ff73977"
META_SHA = "fd1bc32db8463769e18f0560ced603a49598c12e1abfa06787ff763c55f06716"
AUTHOR_REPORTED_CANDIDATE_SHA = "489a07276556fdb63774297fbb79fe78ed04ffec831ce05a22d4a338629168ba"


class PublicationPreflightError(ValueError):
    pass


def _object_no_duplicates(pairs):
    out = {}
    for name, value in pairs:
        if name in out:
            raise PublicationPreflightError("Duplicate JSON key")
        out[name] = value
    return out


def review_bytes(raw: bytes, sidecar: str, *, expected_sha256: str,
                 small_cell_threshold: int = 5) -> dict:
    """Validate aggregate-only scope and flag small cells for human review.

    A passed structural check never grants publisher authentication, scientific
    I3 status, public dissemination rights or human sign-off.
    """
    if not isinstance(raw, bytes) or not 0 < len(raw) <= 524288:
        raise PublicationPreflightError("Unexpected source artifact byte size")
    if (not isinstance(expected_sha256, str) or
            re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None):
        raise PublicationPreflightError("Explicit SHA-256 pin required")
    actual = sha256(raw).hexdigest()
    parts = sidecar.strip().split() if isinstance(sidecar, str) else []
    if (len(parts) != 2 or parts[0] != expected_sha256 or
            parts[1] != "coverage_release.json" or actual != expected_sha256):
        raise PublicationPreflightError("Source artifact, sidecar and pinned digest differ")
    if type(small_cell_threshold) is not int or not 2 <= small_cell_threshold <= 100:
        raise PublicationPreflightError("Invalid reviewer screening threshold")
    try:
        doc = json.loads(raw.decode("utf-8"), object_pairs_hook=_object_no_duplicates)
    except (ValueError, UnicodeError) as exc:
        raise PublicationPreflightError("Invalid JSON source artifact") from exc
    if not isinstance(doc, dict) or set(doc) != TOP_FIELDS:
        raise PublicationPreflightError("Unexpected release top-level fields")
    if (doc["schema"] != SCHEMA or doc["version"] != "0.1.0-candidate" or
            doc["years"] != YEARS or doc["categories"] != CATEGORIES or
            doc["scope"] != "World / climate-vetted C1-C8 / four years" or
            doc["metadata_sheet"] != "meta_Ch3vetted_withclimate" or
            doc["source_authentication"] !=
            "LOCAL_FINGERPRINT_ONLY_PUBLISHER_RECEIPT_NOT_INDEPENDENTLY_VERIFIED" or
            doc["metadata_concordance_status"] != "DIFFERENCES_RECORDED"):
        raise PublicationPreflightError("Incorrect version, category, year or provenance")
    if (doc["evidence"] != "EXACT_VARIABLE_REPORTING_PRESENCE_ONLY" or
            doc["science_review_state"] != "REVIEW_PENDING" or
            type(doc["i3_verified"]) is not int or doc["i3_verified"] != 0 or
            doc["physical_accounting"] != "NOT_ESTABLISHED"):
        raise PublicationPreflightError("Scientific claims exceed reporting-presence evidence")
    if (doc["sha256"] != {"world_csv": WORLD_SHA, "metadata_xlsx": META_SHA} or
            type(doc["cohort_size"]) is not int or doc["cohort_size"] != 1202):
        raise PublicationPreflightError("Source hashes or cohort size differ from local evidence")
    variables = doc["variables"]
    if (not isinstance(variables, list) or len(variables) != 11 or
            any(not isinstance(x, str) or not x for x in variables) or
            len(set(variables)) != len(variables)):
        raise PublicationPreflightError("Unexpected variable inventory")
    if (not isinstance(doc["weighting"], dict) or
            set(doc["weighting"]) != {"scenario", "model_label_balanced"} or
            "NOT a model-family estimate" not in doc["weighting"]["model_label_balanced"] or
            not isinstance(doc["limitations"], list) or not doc["limitations"]):
        raise PublicationPreflightError("Missing model-label or source-data limitations")
    rows = doc["records"]
    if not isinstance(rows, list) or len(rows) != 352:
        raise PublicationPreflightError("Coverage matrix must have 352 records")
    expected = {(cat, year, name) for cat in CATEGORIES for year in YEARS for name in variables}
    observed = set()
    category_denominators = {}
    small = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != PUBLIC_FIELDS:
            raise PublicationPreflightError("Unexpected row fields: possible source disclosure")
        cat, year, variable = row["category"], row["year"], row["variable"]
        try:
            key = (cat, year, variable)
            if key not in expected or key in observed:
                raise PublicationPreflightError("Unrecognized or repeated coverage record")
            observed.add(key)
            den, reporting, models = (row["denominator"], row["reporting"], row["model_labels"])
            if (any(type(v) is not int for v in (den, reporting, models)) or
                    den < 1 or not 0 <= reporting <= den or not 1 <= models <= den):
                raise PublicationPreflightError("Invalid source denominator or counts")
            if (not isinstance(row["units"], list) or
                    not all(isinstance(u, str) for u in row["units"])):
                raise PublicationPreflightError("Unsupported units data")
            for frac in ("scenario_fraction", "model_label_balanced_fraction"):
                f = row[frac]
                if type(f) not in (float, int) or not math.isfinite(f) or not 0 <= f <= 1:
                    raise PublicationPreflightError("Invalid reporting fraction")
            if abs(row["scenario_fraction"] - reporting / den) > 1e-9:
                raise PublicationPreflightError("Reporting fraction does not match counts")
            dkey = (cat, year)
            if dkey in category_denominators and category_denominators[dkey] != (den, models):
                raise PublicationPreflightError("Inconsistent category denominators")
            category_denominators[dkey] = (den, models)
            unreported = den - reporting
            reasons = []
            if den < small_cell_threshold:
                reasons.append("SMALL_CATEGORY_DENOMINATOR")
            if 0 < reporting < small_cell_threshold:
                reasons.append("SMALL_NONZERO_REPORTING_CELL")
            if 0 < unreported < small_cell_threshold:
                reasons.append("SMALL_NONZERO_MISSING_CELL")
            if reasons:
                small.append({
                    "category": cat, "year": year, "variable": variable,
                    "denominator": den, "reporting": reporting,
                    "not_reporting": unreported, "reasons": reasons,
                })
        except TypeError as exc:
            raise PublicationPreflightError("Malformed aggregate record") from exc
    if observed != expected:
        raise PublicationPreflightError("Incomplete category/year/variable cross-product")
    totals = {
        year: sum(category_denominators[cat, year][0] for cat in CATEGORIES)
        for year in YEARS
    }
    if any(n != 1202 for n in totals.values()):
        raise PublicationPreflightError("Category totals do not reconcile")
    return {
        "status": "HUMAN_DISCLOSURE_AND_LICENSE_REVIEW_REQUIRED",
        "release_candidate_sha256": actual,
        "pin_origin": "AUTHOR_REPORTED_PRIOR_LOCAL_TRANSCRIPT_NOT_IMMUTABLE_PUBLIC_RELEASE",
        "source_file_scope": "AGGREGATE_COUNTS_ONLY_SCHEMA_CHECKED",
        "records": len(rows),
        "matched_scenarios": 1202,
        "reporting_coverage_only": True,
        "science_review_state": "REVIEW_PENDING",
        "verified_i3": 0,
        "automated_structural_checks": "PASS",
        "small_cell_screen": {
            "threshold": small_cell_threshold,
            "policy": "CONSERVATIVE_SCREENING_HEURISTIC_NOT_AR6_LICENSE_REQUIREMENT",
            "flagged_count": len(small),
            "flagged": small,
        },
        "human_approval": False,
        "publisher_authentication": "NOT_INDEPENDENTLY_VERIFIED",
        "disclaimer": (
            "Screening is not a grant of redistribution rights. Review exact rows, "
            "low-count categories, license, source attribution and provenance "
            "before a tag or publication. Never distribute original AR6 rows."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--sha-file", type=Path, required=True)
    parser.add_argument("--expected-sha256", default=AUTHOR_REPORTED_CANDIDATE_SHA)
    parser.add_argument("--output", type=Path,
                        default=Path("results/ar6-canonical-gate/publication_preflight_local.json"))
    args = parser.parse_args()
    report = review_bytes(args.artifact.read_bytes(), args.sha_file.read_text(encoding="ascii"),
                          expected_sha256=args.expected_sha256)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(report["status"])
    print("Aggregate structural validation:", report["automated_structural_checks"])
    print("Review small cells:", report["small_cell_screen"]["flagged_count"])
    print("Reviewer approval: still required; no publication performed.")


if __name__ == "__main__":
    main()
