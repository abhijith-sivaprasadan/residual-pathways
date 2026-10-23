"""Streaming coverage audit for locally authorized AR6-format World IAMC CSV files.

Does not export source data or infer the physical meaning of variable names.
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path


class CoverageError(ValueError):
    pass


def audit(path, variable_candidates, year=2050):
    """Count reported observations by exact variable name; I3 is never inferred from availability."""
    path = Path(path)
    source_hash = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            source_hash.update(block)
    names = list(variable_candidates.values())
    if not names or len(set(names)) != len(names):
        raise CoverageError("Candidate variable mappings must be unique; not a source-reviewed dictionary")
    cohorts = set()
    matched = {label: set() for label in variable_candidates}
    seen_units = {label: set() for label in variable_candidates}
    observed_records = Counter()
    rows_total = 0
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        if len(set(headers)) != len(headers) or not {"Model", "Scenario", "Region", "Variable", "Unit"} <= set(headers):
            raise CoverageError("Missing/duplicated IAMC dimension headers")
        year_field = str(year) if str(year) in headers else f"X{year}"
        if year_field not in headers:
            raise CoverageError(f"Year {year} is not present; no interpolation permitted")
        for i, row in enumerate(reader, start=2):
            rows_total += 1
            if None in row:
                raise CoverageError(f"Extra CSV fields on line {i}")
            if row["Region"] != "World":
                continue
            if not all(row.get(k) for k in ("Model", "Scenario", "Variable", "Unit")):
                raise CoverageError(f"Missing required IAMC dimension on line {i}")
            pair = (row["Model"], row["Scenario"])
            cohorts.add(pair)
            name = row["Variable"]
            if name not in names:
                continue
            raw = (row.get(year_field) or "").strip()
            if not raw:
                continue
            try:
                val = float(raw)
            except ValueError as e:
                raise CoverageError(f"Non-numeric {year} on line {i}") from e
            if not math.isfinite(val):
                raise CoverageError(f"Nonfinite {year} on line {i}")
            label = next(l for l, n in variable_candidates.items() if n == name)
            if pair in matched[label]:
                raise CoverageError(f"Duplicate year/variable observations for {pair} / {name}")
            matched[label].add(pair)
            seen_units[label].add(row["Unit"])
            observed_records[label] += 1
    return {
        "audit_version": "1.0.0",
        "research_status": "VARIABLE_PRESENCE_ONLY_SEMANTICS_UNREVIEWED",
        "source_filename": path.name,
        "source_sha256": source_hash.hexdigest(),
        "year": year,
        "region": "World",
        "csv_series_rows": rows_total,
        "world_model_scenario_pairs": len(cohorts),
        "candidate_coverage": {
            label: {"exact_variable": source_name,
                    "model_scenario_pairs_with_observation": len(matched[label]),
                    "model_scenario_denominator": len(cohorts),
                    "units_seen": sorted(seen_units[label]),
                    "coverage_fraction": len(matched[label]) / len(cohorts) if cohorts else None}
            for label, source_name in variable_candidates.items()},
        "unresolved": [
            "Candidate variable names are not source-reviewed accounting identities",
            "No statement about positive gross, net, CDR, BECCS, DACCS or fossil CCS identifiability is made",
            "Model categories, sector completeness, overlaps and source quantization remain unverified",
            "I3 eligibility is not evaluated by this audit",
        ],
    }


def run_audit(input_path, candidates_path, output_path, year=2050):
    candidates = json.loads(Path(candidates_path).read_text(encoding="utf-8"))
    result = audit(input_path, candidates, year=year)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
