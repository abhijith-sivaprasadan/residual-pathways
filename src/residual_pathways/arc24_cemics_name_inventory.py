"""Read-only author-archive scenario-name inventory for ARC24-03 source tracing.

No numeric source observations are emitted. Identifiers from the CC BY 4.0
authors' MIF are for diagnostic inspection, NEVER automatically mapped to
AR6 scenarios. The original author MIF MD5 must match Zenodo record 5103024.
"""
from __future__ import annotations
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
import json
import re

from .arc24_cemics_crosswalk import (
    CASE_ID, MODEL, SCENARIO, EXPECTED_ARCHIVE_MD5,
    _digest, _headered_archive, _read_author_text_lines,
)
from .case_audit import CaseAuditError

def normal_name(s):
    return re.sub(r"[^a-z0-9]", "", s.casefold())

def inspect_source_names(mif_path, output_path, *, rmd_path=None):
    source, public = Path(mif_path).resolve(), Path(output_path).resolve()
    if (not source.is_file() or source == public or
            "ar6-private" not in source.parts or "ar6-private" in public.parts):
        raise CaseAuditError("Original authors' MIF must stay private")
    if _digest(source) != EXPECTED_ARCHIVE_MD5:
        raise CaseAuditError("Original Zenodo v2 MIF MD5 mismatch")
    by_pair = Counter()
    models, scenarios = Counter(), Counter()
    for row in _headered_archive(source):
        if None in row or any(value is None for value in row.values()):
            raise CaseAuditError("Malformed original MIF row")
        model, scenario = row["Model"].strip(), row["Scenario"].strip()
        if not model or not scenario:
            raise CaseAuditError("Blank Model or Scenario in author archive")
        by_pair[(model, scenario)] += 1
        models[model] += 1
        scenarios[scenario] += 1
    if not by_pair:
        raise CaseAuditError("Verified authors' MIF did not yield any rows")
    target = normal_name(SCENARIO)
    matching_norm = [
        {"model": model, "scenario": scenario, "row_count": n}
        for (model, scenario), n in by_pair.items()
        if normal_name(scenario) == target
    ]
    # This is a search aide only, not an automated scenario equivalence.
    candidate_pairs = [
        (model, scenario, n) for (model, scenario), n in by_pair.items()
        if any(token in normal_name(scenario)
               for token in ("cemics", "ssp1", "mincdr", "fullcdr"))
    ]
    def order_key(triple):
        model, scenario, _ = triple
        a = SequenceMatcher(None, target, normal_name(scenario)).ratio()
        return (-a, scenario.casefold(), model.casefold())
    candidate_pairs.sort(key=order_key)
    nearest = sorted(by_pair, key=lambda pair: (
        -SequenceMatcher(None, target, normal_name(pair[1])).ratio(),
        pair[1].casefold(), pair[0].casefold()))
    rmd = None
    if rmd_path is not None:
        rmd_path = Path(rmd_path).resolve()
        if not rmd_path.is_file() or "ar6-private" not in rmd_path.parts:
            raise CaseAuditError("Rmd original source must stay private")
        lines, coding = _read_author_text_lines(rmd_path)
        hits = {}
        for name in ("cemics", "ssp1", "mincdr", "fullcdr", "gross", "beccs",
                     "afolu", "carbon sequestration", "industrial"):
            hits[name] = [i for i, line in enumerate(lines, 1)
                          if name in line.casefold()][:80]
        rmd = {"encoding_interpretation": coding,
               "total_lines": len(lines), "matching_line_numbers": hits}
    # The printed identifiers are public author's model/scenario labels from
    # the CC BY archive; no World CSV values or author numeric cells.
    results = {
        "schema": "residualpathways.arc24.cemics_authors_name_inventory.v1",
        "status": "ORIGINAL_AUTHORS_MIF_IDENTITY_INVENTORY_ONLY",
        "source": "https://zenodo.org/records/5103024",
        "source_md5": EXPECTED_ARCHIVE_MD5,
        "case_id": CASE_ID,
        "target_model": MODEL, "target_scenario": SCENARIO,
        "total_source_rows": sum(by_pair.values()),
        "distinct_models": len(models),
        "distinct_scenarios": len(scenarios),
        "distinct_model_scenario_pairs": len(by_pair),
        "model_labels_and_counts": [
            {"model": name, "rows": count}
            for name, count in sorted(models.items())
        ][:100],
        "exact_original_model_scenario_label": (
            (MODEL, SCENARIO) in by_pair
        ),
        "normalized_scenario_matches": matching_norm[:30],
        "cemics_ssp1_cdr_candidate_pair_count": len(candidate_pairs),
        "cemics_ssp1_cdr_candidates": [
            {"model": model, "scenario": sc, "rows": count,
             "label_similarity": round(SequenceMatcher(
                None, target, normal_name(sc)).ratio(), 3)}
            for model, sc, count in candidate_pairs[:60]
        ],
        "nearest_scenario_labels": [
            {"model": model, "scenario": sc,
             "label_similarity": round(SequenceMatcher(
                None, target, normal_name(sc)).ratio(), 3)}
            for model, sc in nearest[:12]
        ],
        "rmd_keyword_index": rmd,
        "accounting_grade": "NOT_DETERMINED",
        "verified_i3": 0,
        "warning": (
            "Similarity is text-based, not a model-run equivalence or data "
            "concordance test. The authors' Rmd may use aliases or scripts to "
            "rename output before AR6 ingestion. Do not equate any similarly "
            "named run to ARC24-03 without original model-specific crosswalk."
        ),
    }
    public.parent.mkdir(parents=True, exist_ok=True)
    public.write_text(json.dumps(results, sort_keys=True, indent=2)+"\n",
                      encoding="utf-8")
    return results
