"""Original CEMICS field-name trace, *not* a numerical accounting adjustment.

The authors' verified Rmd executes deletePlus(data) before selecting
regrowth. Search the original authors' MIF and AR6 World for exactly reported
raw names and a purely syntactic possible '+/++' hierarchy-marker spelling.
No variables are substituted, inferred equal or set to zero.
"""
from __future__ import annotations

import json
from pathlib import Path

from .arc24_cemics_crosswalk import (
    CASE_ID, MODEL, SCENARIO, EXPECTED_ARCHIVE_MD5,
    AUTHOR_SUPPORT_MD5, _digest, _read_author_text_lines,
)
from .arc24_cemics_alias_fingerprint import (
    AUTHOR_NO, _load_authors, _load_ar6,
)
from .case_audit import CaseAuditError
from .stratify import sha_file

REGROWTH = "Emissions|CO2|Land|Land-use Change|Regrowth"
GROSS = "Emissions|CO2|Gross Fossil Fuels and Industry"
LAND = "Carbon Sequestration|Land Use"
QUESTIONS = (REGROWTH, GROSS, LAND)
MARKERS = frozenset(("+", "++"))


def remove_hierarchy_markers(name):
    """A conservative candidate spelling ONLY, not a source-author mapping."""
    return "|".join(part for part in name.split("|") if part not in MARKERS)


def _matching_units(rows):
    return [
        {
            "unit": unit,
            "source_records": sum(1 for value in rows if value[0] == unit),
            "year2050_cells_present": sum(
                1 for u, years in rows if u == unit and years.get(2050) is not None
            ),
        }
        for unit in sorted({x[0] for x in rows})
    ]


def _source_name_report(target, data):
    exact = data.get(target, [])
    marker_candidates = [
        label for label in sorted(data)
        if label != target and remove_hierarchy_markers(label) == target
    ]
    all_candidates = [target] if exact else []
    all_candidates.extend(marker_candidates)
    return {
        "requested_postprocessed_rmd_name": target,
        "raw_exact_name_present": bool(exact),
        "raw_exact_source_units": _matching_units(exact),
        "hierarchy_marker_candidate_names": marker_candidates,
        "marker_candidate_count": len(marker_candidates),
        "marker_candidate_source_units": [
            {"raw_original_variable_name": label,
             "units": _matching_units(data[label])}
            for label in marker_candidates
        ],
        "unique_marker_candidate_without_exact_match": (
            not bool(exact) and len(marker_candidates) == 1
        ),
        "source_field_identity_certified_by_author_preprocessing": False,
        "source_numeric_values_released": False,
    }


def inventory(mif_path, world_path, packet_path, rmd_path, public_path):
    mif, world, packet_file, rmd, public = (
        Path(x).resolve() for x in
        (mif_path, world_path, packet_path, rmd_path, public_path)
    )
    if (len({mif,world,packet_file,rmd,public}) != 5 or
            not all(p.is_file() for p in (mif,world,packet_file,rmd)) or
            any("ar6-private" not in p.parts for p in
                (mif,world,packet_file,rmd)) or "ar6-private" in public.parts):
        raise CaseAuditError("All original sources must stay under ar6-private and output outside it")
    if _digest(mif) != EXPECTED_ARCHIVE_MD5:
        raise CaseAuditError("Original author MIF MD5 mismatch")
    if _digest(rmd) != AUTHOR_SUPPORT_MD5["authors_rmd"]:
        raise CaseAuditError("Original author Rmd MD5 mismatch")
    packet = json.loads(packet_file.read_text(encoding="utf-8"))
    if (packet.get("schema") != "residualpathways.ar6_canonical_selected24.private.v1"
            or packet.get("handling") != "LOCAL_ONLY_DO_NOT_PUBLISH"
            or not isinstance(packet.get("cases"),list)
            or len(packet["cases"]) != 24):
        raise CaseAuditError("Expected original ARC24 private packet")
    matches = [c for c in packet["cases"] if c.get("case_id") == CASE_ID]
    if (len(matches) != 1 or matches[0].get("model") != MODEL or
            matches[0].get("scenario") != SCENARIO):
        raise CaseAuditError("ARC24-03 source identity changed")
    if sha_file(world) != packet.get("source_sha256"):
        raise CaseAuditError("AR6 World source SHA mismatch")

    rmd_lines, encoding = _read_author_text_lines(rmd)
    # Confirm source-code preprocessor is actually reported in this release.
    required = ('data <- deletePlus(data)',
                'CDRaff <- -data[,,"Emissions|CO2|Land|Land-use Change|Regrowth (Mt CO2/yr)"]')
    stripped = {line.strip() for line in rmd_lines}
    if any(code not in stripped for code in required):
        raise CaseAuditError("Author Rmd deletePlus and/or regrowth selector changed")
    author, years_a = _load_authors(mif, {AUTHOR_NO})
    ar6, years_w = _load_ar6(world, {SCENARIO})
    if 2050 not in (years_a & years_w):
        raise CaseAuditError("No common original 2050 field year")
    authors_fields, ar6_fields = author[AUTHOR_NO], ar6[SCENARIO]

    focus = ("regrowth", "gross fossil fuels", "land-use change")
    candidates = [
        name for name in sorted(set(authors_fields) | set(ar6_fields))
        if any(word in name.casefold() for word in focus)
    ]
    # Names only. No raw values, decimals, private IDs or carbon numbers.
    result = {
        "schema":"residualpathways.arc24.cemics_2050_field_lineage.v1",
        "status":"SOURCE_KEY_PREPROCESSING_DIAGNOSTIC_NOT_NUMERIC_CDR",
        "author_archive":"https://zenodo.org/records/5103024",
        "source_author_mif_md5":EXPECTED_ARCHIVE_MD5,
        "source_author_rmd_md5":AUTHOR_SUPPORT_MD5["authors_rmd"],
        "source_ar6_world_sha256":packet["source_sha256"],
        "case_id":CASE_ID, "year":2050,
        "study_preprocessing_command_found":"data <- deletePlus(data)",
        "study_regrowth_selector_found": True,
        "author_text_encoding":encoding,
        "original_author_fields":[_source_name_report(term,authors_fields)
                                  for term in QUESTIONS],
        "original_ar6_fields":[_source_name_report(term,ar6_fields)
                               for term in QUESTIONS],
        "context_name_inventory":[
            {
                "original_variable_name":name,
                "author_present":name in authors_fields,
                "ar6_present":name in ar6_fields,
                "author_reported_units":sorted({r[0] for r in authors_fields.get(name,[])}),
                "ar6_reported_units":sorted({r[0] for r in ar6_fields.get(name,[])}),
            }
            for name in candidates[:120]
        ],
        "context_candidate_count":len(candidates),
        "no_source_values_in_output":True,
        "automatic_variable_rename_accepted":False,
        "operational_CDRtotal_computed":False,
        "verified_i3":0,
        "warning":(
            "deletePlus is a documented study source preprocessing step, but the "
            "precise transformation of each particular 2021 archive name must "
            "be established. A syntactic removal of hierarchy +/++ is a "
            "candidate field crosswalk only. Do not replace missing land "
            "regrowth with Carbon Sequestration|Land Use, invent zeros, or "
            "treat a source-author-only variable as AR6 World matched."
        ),
    }
    public.parent.mkdir(parents=True,exist_ok=True)
    public.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",
                      encoding="utf-8")
    return result
