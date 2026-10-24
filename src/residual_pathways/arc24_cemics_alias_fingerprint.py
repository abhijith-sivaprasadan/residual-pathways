"""Multi-year source-fingerprint experiment for CEMICS noCDR/minCDR alias.

Compares authors' MD5-pinned v2 MIF with source-SHA-locked AR6 World v1.1.
A shared fullCDR pairing is the positive-control mapping; crossed pairings
provide negative/discrimination controls. Reports *statuses only*, no CO2
observations and NO automatic alias approval or I3 certification.
"""
from __future__ import annotations

from collections import Counter
from decimal import Decimal
import csv
import json
from pathlib import Path

from .arc24_cemics_crosswalk import (
    CASE_ID, MODEL, SCENARIO, EXPECTED_ARCHIVE_MD5, AUTHOR_SUPPORT_MD5,
    _decimal, _digest, _headered_archive, _read_author_text_lines,
)
from .case_audit import CaseAuditError, TOTAL, SIX
from .stratify import sha_file

ARCHIVE_MODEL = "REMIND-MAgPIE"
AUTHOR_NO = "CEMICS_SSP1-1p5C-noCDR"
AUTHOR_FULL = "CEMICS_SSP1-1p5C-fullCDR"
AR6_MIN = SCENARIO
AR6_FULL = AUTHOR_FULL
SOURCE_YEARS = (2020, 2030, 2040, 2050, 2060, 2070, 2080, 2090, 2100)
PAIRINGS = (
    ("FULL_SAME_LABEL_CONTROL", AUTHOR_FULL, AR6_FULL),
    ("NOCDR_TO_MINCDR_HYPOTHESIS", AUTHOR_NO, AR6_MIN),
    ("FULL_TO_MINCDR_NEGATIVE_CONTROL", AUTHOR_FULL, AR6_MIN),
    ("NOCDR_TO_FULL_NEGATIVE_CONTROL", AUTHOR_NO, AR6_FULL),
)
HIGHLIGHT = (TOTAL,) + tuple(SIX) + ("Emissions|CO2|Other",)


def _year_name(year, header):
    return next((k for k in (str(year), "X"+str(year)) if k in header), None)


def _load_ar6(world, pairs):
    result = {k: {} for k in pairs}
    available = set()
    with world.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        if len(header) != len(set(header)) or not {
            "Model", "Scenario", "Region", "Variable", "Unit"
        }.issubset(header):
            raise CaseAuditError("Invalid World v1.1 IAMC header")
        yearcols = {y:_year_name(y, header) for y in SOURCE_YEARS}
        available = {y for y, col in yearcols.items() if col}
        for linenum,row in enumerate(reader, 2):
            if None in row or any(v is None for v in row.values()):
                raise CaseAuditError(f"Malformed World CSV row {linenum}")
            if row["Model"] != MODEL or row["Region"] != "World":
                continue
            target = row["Scenario"]
            if target not in result:
                continue
            var = row["Variable"]
            # Repeated names may differ by source Unit or an extra MIF
            # dimension. Preserve every row; decide comparability later.
            result[target].setdefault(var, []).append((row["Unit"], {
                y:_decimal(row[col]) for y,col in yearcols.items() if col
            }))
    return result, available


def _load_authors(mif, pairs):
    result = {k: {} for k in pairs}
    years_found = set()
    for row in _headered_archive(mif):
        if None in row or any(v is None for v in row.values()):
            raise CaseAuditError("Malformed authors' MIF")
        if row["Model"] != ARCHIVE_MODEL or row["Region"] != "World":
            continue
        target = row["Scenario"]
        if target not in result:
            continue
        var = row["Variable"]
        yearcols = {y:_year_name(y, row) for y in SOURCE_YEARS}
        years_found.update(y for y,col in yearcols.items() if col)
        result[target].setdefault(var, []).append((row["Unit"], {
            y:_decimal(row[col]) for y,col in yearcols.items() if col
        }))
    return result, years_found


def _unique_compatible_pair(author_rows, ar6_rows):
    """Use the one and only jointly reported unit; refuse ambiguous rows.

    With distinct units in the original MIF, comparing the sole matching
    unit is defensible and logged. Multiple records of the *same* unit remain
    ambiguous even when their displayed numbers happen to match.
    """
    units_a = {item[0] for item in author_rows}
    units_b = {item[0] for item in ar6_rows}
    common = units_a & units_b
    if not common:
        return None, "NO_SHARED_UNIT"
    if len(common) != 1:
        return None, "AMBIGUOUS_MULTIPLE_SHARED_UNITS"
    common_unit = next(iter(common))
    a = [row for row in author_rows if row[0] == common_unit]
    b = [row for row in ar6_rows if row[0] == common_unit]
    if len(a) != 1 or len(b) != 1:
        return None, "AMBIGUOUS_DUPLICATE_ROWS_SAME_UNIT"
    return (a[0], b[0]), None


def _outcome(one, other):
    if one[0] != other[0]:
        return "INCOMPATIBLE_UNITS"
    a,b = one[1],other[1]
    if a is None or b is None:
        return "MISSING_VALUE"
    if a == b:
        return "EXACT_REPORTED_DECIMAL_MATCH"
    ratio = (abs(a-b) / max(Decimal(1),abs(a),abs(b)))*Decimal(100)
    if ratio < Decimal("0.001"):
        return "NONZERO_BELOW_0_001_PERCENT"
    if ratio < Decimal("0.1"):
        return "NONZERO_0_001_TO_0_1_PERCENT"
    if ratio < Decimal("1"):
        return "NONZERO_0_1_TO_1_PERCENT"
    if ratio < Decimal("10"):
        return "NONZERO_1_TO_10_PERCENT"
    return "NONZERO_AT_LEAST_10_PERCENT"


def compare_author_aliases(mif_path, world_path, packet_path, public_path,
                           rmd_path=None):
    mif, world, packet_file, public = (Path(p).resolve() for p in
                                     (mif_path, world_path, packet_path, public_path))
    if (len({mif,world,packet_file,public}) != 4 or
            not all(p.is_file() for p in (mif,world,packet_file)) or
            any("ar6-private" not in p.parts for p in (mif,world,packet_file)) or
            "ar6-private" in public.parts):
        raise CaseAuditError("Original authors' MIF and World v1.1 inputs must remain private")
    if _digest(mif) != EXPECTED_ARCHIVE_MD5:
        raise CaseAuditError("Zenodo v2 author MIF MD5 does not match source manifest")
    packet = json.loads(packet_file.read_text(encoding="utf-8"))
    if (packet.get("schema") != "residualpathways.ar6_canonical_selected24.private.v1"
            or packet.get("handling") != "LOCAL_ONLY_DO_NOT_PUBLISH"
            or not isinstance(packet.get("cases"),list) or len(packet["cases"]) != 24):
        raise CaseAuditError("Expected original 24-case private source packet")
    selected = [c for c in packet["cases"] if c.get("case_id") == CASE_ID]
    if len(selected) != 1 or selected[0].get("model") != MODEL or selected[0].get("scenario") != AR6_MIN:
        raise CaseAuditError("ARC24-03 changed relative to registered AR6 cohort")
    if sha_file(world) != packet.get("source_sha256"):
        raise CaseAuditError("World v1.1 source SHA changed")
    author_names = {p[1] for p in PAIRINGS}
    ar6_names = {p[2] for p in PAIRINGS}
    author, author_years = _load_authors(mif, author_names)
    ar6, ar6_years = _load_ar6(world, ar6_names)
    years = sorted(author_years & ar6_years)
    if 2050 not in years:
        raise CaseAuditError("No common 2050 source year")
    # Cross-check source's own 2050 observations for ARC24-03 first.
    baseline = selected[0].get("source_observations")
    if not isinstance(baseline,dict) or not baseline:
        raise CaseAuditError("Selected original AR6 2050 observations absent")
    for name, observation in baseline.items():
        records = ar6[AR6_MIN].get(name, [])
        if (len(records) != 1 or
                records[0][0] != observation.get("unit") or
                records[0][1].get(2050) != _decimal(observation.get("raw"))):
            raise CaseAuditError("Selected ARC24-03 packet 2050 value differs from source World or is ambiguous")
    reports = []
    for code, orig, published in PAIRINGS:
        left, right = author[orig], ar6[published]
        overlapping = sorted(set(left)&set(right))
        counts=Counter()
        by_variable={}
        per_year=Counter()
        ambiguous_variables=[]
        multiple_unit_variables=[]
        for variable in overlapping:
            a_rows, b_rows = left[variable], right[variable]
            if len({row[0] for row in a_rows}) > 1:
                multiple_unit_variables.append(variable)
            pair, reason = _unique_compatible_pair(a_rows, b_rows)
            if reason and reason.startswith("AMBIGUOUS"):
                ambiguous_variables.append(variable)
            for year in years:
                if reason:
                    result = reason
                else:
                    a_unit,a_values = pair[0]
                    b_unit,b_values = pair[1]
                    result = _outcome((a_unit,a_values.get(year)),
                                      (b_unit,b_values.get(year)))
                counts[result]+=1
                per_year[year]+=1
                if variable in HIGHLIGHT:
                    by_variable.setdefault(variable,Counter())[result]+=1
        attempted=sum(counts.values())
        excluded = sum(counts[label] for label in (
            "NO_SHARED_UNIT", "AMBIGUOUS_MULTIPLE_SHARED_UNITS",
            "AMBIGUOUS_DUPLICATE_ROWS_SAME_UNIT", "MISSING_VALUE"))
        compared=attempted-excluded
        exact=counts["EXACT_REPORTED_DECIMAL_MATCH"]
        reports.append({
            "comparison":code, "author_scenario_label":orig,
            "ar6_scenario_label":published,
            "author_model_label":ARCHIVE_MODEL,
            "ar6_model_label":MODEL,
            "author_world_variables":len(left),
            "ar6_world_variables":len(right),
            "shared_variable_names":len(overlapping),
            "years":years,
            "year_variable_attempted":attempted,
            "year_variable_compared":compared,
            "excluded_from_numerical_comparison":excluded,
            "author_multi_unit_variable_count":len(multiple_unit_variables),
            "author_multi_unit_variable_names":multiple_unit_variables[:50],
            "ambiguous_shared_variable_count":len(ambiguous_variables),
            "ambiguous_shared_variable_names":ambiguous_variables[:50],
            "exact_decimal_matches":exact,
            "exact_decimal_match_fraction":round(exact/compared,6) if compared else None,
            "status_counts":dict(counts),
            "per_year_shared_variable_counts":dict(per_year),
            "predefined_carbon_variable_status_counts":{
                var:dict(by_variable.get(var,Counter())) for var in HIGHLIGHT
            },
            "interpretation":"NUMERIC_FINGERPRINT_ONLY_NOT_AUTHOR_APPROVED_ALIAS",
        })
    evidence = None
    if rmd_path:
        path=Path(rmd_path).resolve()
        if not path.is_file() or "ar6-private" not in path.parts:
            raise CaseAuditError("Author R Markdown supporting source must remain private")
        if _digest(path) != AUTHOR_SUPPORT_MD5["authors_rmd"]:
            raise CaseAuditError("Original author R Markdown MD5 mismatch")
        lines,coding=_read_author_text_lines(path)
        terms=("nocdr","mincdr","min cdr","limited cdr","fullcdr","ssP1")
        evidence={
            "source_md5_verified":True,"encoding":coding,
            "keyword_line_counts":{
                term:sum(term.casefold() in line.casefold() for line in lines)
                for term in terms
            },
            "keyword_first_line_numbers":{
                term:[idx+1 for idx,line in enumerate(lines) if term.casefold() in line.casefold()][:15]
                for term in terms
            },
        }
    return {
        "schema":"residualpathways.arc24.cemics_alias_fingerprint.v1",
        "status":"CEMICS_SOURCE_ALIAS_NUMERIC_TEST_NO_PHYSICAL_INFERENCE",
        "source":"https://zenodo.org/records/5103024",
        "duplicate_resolution_policy": (
            "Compare only a uniquely matched Unit row in each source. "
            "Repeated source variable names with distinct Unit labels are "
            "preserved. Two or more rows with same matching Unit (or multiple "
            "shared units) are AMBIGUOUS and excluded from numerical counts. "
            "No source records are discarded, summed or averaged."
        ),
        "source_author_mif_md5":EXPECTED_ARCHIVE_MD5,
        "source_ar6_world_sha256":packet["source_sha256"],
        "selected_case_id":CASE_ID,
        "archive_model_version":"UNVERSIONED_SOURCE_LABEL",
        "registered_ar6_model_version":"2.1-4.2",
        "author_Rmd_source_text_evidence":evidence,
        "comparisons":reports,
        "scientific_source_alias_verified":False,
        "verified_i3":0,
        "caveat":(
            "Even exact reported-decimal equality across source variables/years "
            "is not a documented scenario renaming, does not verify that model "
            "versions are identical, and does not establish physically disjoint "
            "gross positive emissions/atmospheric-removal partitions. Controls "
            "are used to test discrimination, not to grant case provenance. "
            "No source numerical observations were exported."
        ),
    }


def write_author_alias_fingerprints(mif,world,packet,output,rmd=None):
    result=compare_author_aliases(mif,world,packet,output,rmd_path=rmd)
    dest=Path(output).resolve()
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return result
