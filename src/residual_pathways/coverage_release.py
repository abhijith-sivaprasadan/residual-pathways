"""Freeze a permission-safe, four-year AR6 reporting-coverage release.

Input is the locally derived cohort-robustness JSON, NOT an original World CSV.
No scenario identities or emissions values may enter this export. This is a
reporting-availability release, not an independently verified I3 partition.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import re

SCHEMA = "residualpathways.coverage-only.v1"
YEARS = [2030, 2050, 2070, 2100]
CATEGORIES = [f"C{i}" for i in range(1, 9)]
FIELDS = {"category", "year", "variable", "eligible_scenarios",
          "unique_model_labels", "reporting_scenarios",
          "scenario_weighted_fraction", "model_label_balanced_fraction", "units_seen"}


class ReleaseError(ValueError):
    pass


def _digest(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ReleaseError("Expected a 64-character lowercase SHA-256 digest")
    return value


def assemble(robustness, *, expected_world, expected_metadata, concordance):
    world = _digest(expected_world)
    metadata = _digest(expected_metadata)
    if robustness.get("schema_version") != "reported-presence-robustness.v1":
        raise ReleaseError("Incorrect input schema")
    if robustness.get("source_sha256") != world or robustness.get("metadata_sha256") != metadata:
        raise ReleaseError("Local input SHA-256 does not match explicit expected source fingerprints")
    if robustness.get("region") != "World" or robustness.get("years") != YEARS:
        raise ReleaseError("Expected prespecified World / four-year scope")
    if robustness.get("metadata_sheet") != "meta_Ch3vetted_withclimate":
        raise ReleaseError("Coverage must use the climate-vetted sheet")
    if (concordance.get("schema_version") != "ar6-metadata-concordance-public.v1"
            or concordance["official_named"]["sha256"] != metadata):
        raise ReleaseError("Missing or mismatched metadata comparison")
    variables = robustness.get("variable_names")
    if not isinstance(variables, list) or not variables or len(variables) != len(set(variables)):
        raise ReleaseError("Unusable exact-source variable inventory")
    rows = robustness.get("records")
    if not isinstance(rows, list):
        raise ReleaseError("Missing coverage records")
    records, seen = [], set()
    denoms = {}
    for row in rows:
        if set(row) != FIELDS:
            raise ReleaseError("Unknown/omitted field; refusing to export possible source identity")
        cat, year, var = row["category"], row["year"], row["variable"]
        if cat not in CATEGORIES or year not in YEARS or var not in variables:
            raise ReleaseError("Unknown category/year/variable")
        key = (cat, year, var)
        if key in seen:
            raise ReleaseError("Duplicate category/year/variable aggregate")
        seen.add(key)
        eligible = row["eligible_scenarios"]
        found = row["reporting_scenarios"]
        labels = row["unique_model_labels"]
        if any(type(n) is not int for n in (eligible, found, labels)):
            raise ReleaseError("Counts must be integers")
        if eligible <= 0 or found < 0 or found > eligible or labels < 1 or labels > eligible:
            raise ReleaseError("Inconsistent denominators or reporting count")
        dkey = (cat, year)
        if dkey in denoms and denoms[dkey] != (eligible, labels):
            raise ReleaseError("Contradictory denominators within category and year")
        denoms[dkey] = (eligible, labels)
        sw, mw = row["scenario_weighted_fraction"], row["model_label_balanced_fraction"]
        if (not isinstance(sw, (int, float)) or not isinstance(mw, (int, float))
                or not math.isfinite(sw) or not math.isfinite(mw)
                or not 0 <= sw <= 1 or not 0 <= mw <= 1
                or abs(sw - found / eligible) > 1e-9):
            raise ReleaseError("Inconsistent fractions")
        units = row["units_seen"]
        if not isinstance(units, list) or not all(isinstance(u, str) for u in units):
            raise ReleaseError("Malformed unit labels")
        records.append({
            "category": cat, "year": year, "variable": var, "denominator": eligible,
            "reporting": found, "model_labels": labels,
            "scenario_fraction": sw, "model_label_balanced_fraction": mw,
            "units": units,
        })
    target = {(c, y, v) for c in CATEGORIES for y in YEARS for v in variables}
    if seen != target:
        raise ReleaseError(f"Incomplete cross-product of prespecified reporting dimensions: {len(target-seen)} missing")
    populations = {y: sum(denoms[(cat, y)][0] for cat in CATEGORIES) for y in YEARS}
    if len(set(populations.values())) != 1 or populations[2050] != robustness["matched_source_scenarios"]:
        raise ReleaseError("Category denominators do not reconcile to the matched source cohort")
    records.sort(key=lambda x: (x["year"], int(x["category"][1:]), variables.index(x["variable"])))
    return {
        "schema": SCHEMA, "version": "0.1.0-candidate", "scope": "World / climate-vetted C1-C8 / four years",
        "evidence": "EXACT_VARIABLE_REPORTING_PRESENCE_ONLY",
        "science_review_state": "REVIEW_PENDING",
        "i3_verified": 0,
        "physical_accounting": "NOT_ESTABLISHED",
        "source_authentication": "LOCAL_FINGERPRINT_ONLY_PUBLISHER_RECEIPT_NOT_INDEPENDENTLY_VERIFIED",
        "metadata_concordance_status": concordance["status"],
        "sha256": {"world_csv": world, "metadata_xlsx": metadata},
        "metadata_sheet": "meta_Ch3vetted_withclimate",
        "years": YEARS, "categories": CATEGORIES,
        "variables": variables,
        "cohort_size": populations[2050],
        "weighting": {
            "scenario": "Share of model-scenario records in the selected climate category",
            "model_label_balanced": "Mean of within-exact-model-label reporting fractions. NOT a model-family estimate.",
        },
        "records": records,
        "limitations": [
            "Reporting availability is not a complete disjoint gross/negative carbon ledger",
            "Zero independently verified I3 cases does not mean zero scientifically eligible cases",
            "No IPCC/IIASA official authentication inferred from matching file digests",
            "Unreviewed reporting coverage must not be renamed I0 without a source-based insufficiency determination",
            "Underlying source rows and named Model/Scenario identities excluded from this artifact",
        ],
    }


def freeze(source, concordance, output, *, expected_world, expected_metadata):
    input_data = json.loads(Path(source).read_text(encoding="utf-8"))
    comparison = json.loads(Path(concordance).read_text(encoding="utf-8"))
    result = assemble(input_data, expected_world=expected_world,
                      expected_metadata=expected_metadata, concordance=comparison)
    output = Path(output)
    raw = (json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    digest = sha256(raw).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(digest + "  " + output.name + "\n", encoding="ascii")
    return digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--robustness", required=True, type=Path)
    parser.add_argument("--concordance", required=True, type=Path)
    parser.add_argument("--expected-world-sha256", required=True)
    parser.add_argument("--expected-metadata-sha256", required=True)
    parser.add_argument("--output", type=Path, default=Path("atlas/data/coverage_release.json"))
    a = parser.parse_args()
    digest = freeze(a.robustness, a.concordance, a.output,
                    expected_world=a.expected_world_sha256,
                    expected_metadata=a.expected_metadata_sha256)
    print("PROVISIONAL COVERAGE-ONLY BUNDLE:", a.output, "SHA256:", digest)
    print("Source provenance and physical I3 scientific review remain open.")


if __name__ == "__main__":
    main()
