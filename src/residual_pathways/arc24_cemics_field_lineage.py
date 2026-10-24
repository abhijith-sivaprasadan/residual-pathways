"""Original CEMICS field-name trace, *not* a numerical accounting adjustment.

The authors' verified Rmd executes deletePlus(data) before selecting
regrowth. Search the original authors' MIF and AR6 World for exactly reported
raw names and a purely syntactic possible '+/++' hierarchy-marker spelling.
No variables are substituted, inferred equal or set to zero.
"""
from __future__ import annotations

import json
from pathlib import Path
from collections import Counter

from .arc24_cemics_crosswalk import (
    CASE_ID, MODEL, SCENARIO, EXPECTED_ARCHIVE_MD5,
    AUTHOR_SUPPORT_MD5, _digest, _read_author_text_lines,
)
from .arc24_cemics_alias_fingerprint import (
    AUTHOR_NO, _load_authors, _load_ar6, _outcome,
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


# These buckets are *search filters*, not additive model sectors. A row may
# appear in more than one group; a nested variable is not assumed a child
# contribution for a physical emissions sum.
FAMILY_GROUPS = (
    "co2_land_reporting",
    "gross_co2_reporting",
    "fossil_and_industry_reporting",
    "afolu_or_other_reporting",
    "land_sequestration_reporting",
    "cdr_technology_reporting",
    "broad_land_emissions_and_cdr",
)
MAX_NAMES_PER_GROUP = 180


def _within_group(name, group):
    n = name.casefold()
    if group == "co2_land_reporting":
        return n.startswith("emissions|co2|land")
    if group == "gross_co2_reporting":
        return n.startswith("emissions|co2") and (
            "|gross" in n or "gross fossil" in n
        )
    if group == "fossil_and_industry_reporting":
        return (n.startswith("emissions|co2") and
                ("fossil fuels and industry" in n or
                 "energy and industrial processes" in n or
                 "|industry" in n))
    if group == "afolu_or_other_reporting":
        return (n.startswith("emissions|co2|afolu")
                or n.startswith("emissions|co2|other")
                or n.startswith("emissions|co2|land-use change"))
    if group == "land_sequestration_reporting":
        return (n.startswith("carbon sequestration|land")
                or n.startswith("carbon sequestration|afforestation"))
    if group == "cdr_technology_reporting":
        return n.startswith("carbon sequestration|")
    if group == "broad_land_emissions_and_cdr":
        return (n.startswith(("emissions|co2", "carbon sequestration"))
                and any(token in n for token in
                        ("land", "afolu", "regrowth", "forest",
                         "afforestation", "deforestation")))
    raise CaseAuditError("Unknown emissions variable-family filter")


def _family_inventory(author, ar6):
    names = sorted(set(author) | set(ar6))
    groups = {}
    for group in FAMILY_GROUPS:
        selected = [name for name in names if _within_group(name,group)]
        groups[group] = {
            "total_distinct_variable_names":len(selected),
            "shown_name_limit":MAX_NAMES_PER_GROUP,
            "names_truncated":len(selected)>MAX_NAMES_PER_GROUP,
            "reported_fields":[{
                "original_variable_name":name,
                "author_reported":name in author,
                "ar6_reported":name in ar6,
                "author_units":_matching_units(author.get(name,[])),
                "ar6_units":_matching_units(ar6.get(name,[])),
                "source_2050_value_reported":(
                    any(item["year2050_cells_present"] for item in
                        _matching_units(author.get(name,[])))
                    or any(item["year2050_cells_present"] for item in
                        _matching_units(ar6.get(name,[])))
                ),
            } for name in selected[:MAX_NAMES_PER_GROUP]],
        }
    return groups


AFFORESTATION = "Carbon Sequestration|Land Use|Afforestation"
LAND_YEARS = (2020,2030,2040,2050,2060,2070,2080,2090,2100)
REQUIRED_LAND_UNIT = "Mt CO2/yr"


def _only_author_unit_record(source, name):
    rows = [r for r in source.get(name, []) if r[0] == REQUIRED_LAND_UNIT]
    return rows[0][1] if len(rows) == 1 else None


def _land_relationship_fingerprint(author, ar6, *, rmd_deleteplus):
    """Numerical source correspondence, never a physical carbon-flow identity.

    Signed regrowth is inverted solely because the original authors' Rmd
    explicitly does so. Treat duplicate names that deletePlus would collapse
    as ambiguous. AR6 matches for published land aggregate/afforestation are
    reported separately; the author-only regrowth is never marked AR6-matched.
    """
    aliases = [
        name for name in author
        if name != REGROWTH and remove_hierarchy_markers(name) == REGROWTH
    ]
    if (rmd_deleteplus and REGROWTH not in author and len(aliases) == 1):
        regrowth_raw = aliases[0]
    elif REGROWTH in author and not aliases:
        regrowth_raw = REGROWTH
    else:
        regrowth_raw = None
    source_names = {"rmd_regrowth_removal":regrowth_raw,
                    "land_use_afforestation":AFFORESTATION,
                    "land_use_aggregate":LAND}
    verified = {}
    term_records = []
    for code,name in source_names.items():
        record = (_only_author_unit_record(author,name) if name else None)
        value2050 = None if record is None else record.get(2050)
        status = ("AMBIGUOUS_OR_ABSENT_AUTHOR_SOURCE" if record is None
                  else "AUTHOR_2050_VALUE_MISSING" if value2050 is None
                  else "AUTHOR_SOURCE_AVAILABLE")
        if record is not None and value2050 is not None:
            verified[code] = ({
                year:(-value if code == "rmd_regrowth_removal" and value is not None
                      else value)
                for year,value in record.items()
            })
        cross = "AR6_NOT_REPORTED_UNDER_SOURCE_NAME"
        if name in ar6 and record is not None:
            other = _only_author_unit_record(ar6,name)
            if other is None:
                cross = "AR6_AMBIGUOUS_OR_UNEXPECTED_UNIT"
            else:
                match2050 = _outcome(
                    (REQUIRED_LAND_UNIT, value2050),
                    (REQUIRED_LAND_UNIT, other.get(2050))
                )
                cross = match2050
        sign = "UNVERIFIED"
        if code in verified:
            a = verified[code].get(2050)
            sign = ("ZERO" if a == 0 else "POSITIVE" if a > 0
                    else "NEGATIVE") if a is not None else "UNVERIFIED"
        term_records.append({
            "operational_source_term":code,
            "original_author_source_variable":name,
            "year2050_source_status":status,
            "year2050_source_sign":sign,
            "year2050_ar6_crosswalk_status":cross,
        })
    pairs = (
        ("NEGATED_REGROWTH_VS_REPORTED_AFFORESTATION",
         "rmd_regrowth_removal","land_use_afforestation"),
        ("NEGATED_REGROWTH_VS_LAND_USE_AGGREGATE",
         "rmd_regrowth_removal","land_use_aggregate"),
        ("AFFORESTATION_VS_LAND_USE_AGGREGATE",
         "land_use_afforestation","land_use_aggregate"),
    )
    checks = []
    for label,a,b in pairs:
        counts = Counter()
        if a in verified and b in verified:
            for year in LAND_YEARS:
                x,y = verified[a].get(year),verified[b].get(year)
                if x is None or y is None:
                    counts["MISSING_SHARED_SOURCE_YEAR_VALUE"] += 1
                else:
                    counts[_outcome((REQUIRED_LAND_UNIT,x),
                                    (REQUIRED_LAND_UNIT,y))] += 1
        else:
            counts["UNVERIFIED_SOURCE_COMPONENT"] = len(LAND_YEARS)
        checks.append({
            "comparison":label,
            "original_author_world_years_checked":len(LAND_YEARS),
            "source_comparison_status_counts":dict(counts),
            "observations_compared":sum(
                n for k,n in counts.items() if k not in
                ("UNVERIFIED_SOURCE_COMPONENT",
                 "MISSING_SHARED_SOURCE_YEAR_VALUE")
            ),
            "source_data_interpretation":"EMPIRICAL_RELATIONSHIP_ONLY_NOT_FLOW_EQUIVALENCE",
        })
    return {
        "status":"ORIGINAL_AUTHOR_LAND_SERIES_RELATIONSHIP_NO_I3",
        "author_rmd_deleteplus_verified":bool(rmd_deleteplus),
        "regrowth_author_only":(
            regrowth_raw is not None and regrowth_raw not in ar6
        ),
        "original_source_terms":term_records,
        "nine_year_comparisons":checks,
        "authors_regrowth_is_not_AR6_world_export":(
            regrowth_raw is not None and regrowth_raw not in ar6
        ),
        "raw_carbon_observations_exported":False,
        "disjoint_removal_partition_certified":False,
        "verified_i3":0,
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
        "expanded_emissions_family_inventory":_family_inventory(
            authors_fields, ar6_fields
        ),
        "source_land_relationship_fingerprint":_land_relationship_fingerprint(
            authors_fields, ar6_fields,
            rmd_deleteplus="data <- deletePlus(data)" in stripped
        ),
        "family_inventory_warning": (
            "Overlapping source-name search buckets only, NOT physically "
            "independent additive emissions sectors, source-defined gross "
            "taxonomy, exhaustive model export or source net/gross identity. "
            "Name-level absence in these buckets is not proof a model lacks "
            "an unreported quantity. Never add parent and nested IAMC "
            "categories automatically."
        ),
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
