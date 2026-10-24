"""Source-defined CEMICS ARC24-03 accounting worksheet, no inferred gross/CDR grade.

The original checksum-verified Rmd defines:
  CDRtotal = -Regrowth_emissions + Enhanced_Weathering + Biomass_CCS + DAC
  CO2pos   = Emissions|CO2 + CDRtotal
It separately reports gross fossil+industry CO2; this is NOT assumed equal
to CO2pos. Publish only named source-variable statuses and sign/magnitude
bands, NEVER original author or AR6 scenario numerical observations.
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import json

from .arc24_cemics_crosswalk import (
    CASE_ID, MODEL, AUTHOR_SUPPORT_MD5, EXPECTED_ARCHIVE_MD5,
    _digest, _decimal, _read_author_text_lines,
)
from .arc24_cemics_alias_fingerprint import (
    AUTHOR_NO, AR6_MIN, _load_authors, _load_ar6,
    _unique_compatible_pair, _outcome,
)
from .case_audit import CaseAuditError, TOTAL, SIX, UNIT
from .arc24_cemics_field_lineage import remove_hierarchy_markers
from .stratify import sha_file

REGROWTH = "Emissions|CO2|Land|Land-use Change|Regrowth"
EW = "Carbon Sequestration|Enhanced Weathering"
BECCS = "Carbon Sequestration|CCS|Biomass"
DAC = "Carbon Sequestration|Direct Air Capture"
GROSS_FI = "Emissions|CO2|Gross Fossil Fuels and Industry"
AFOLU = SIX[1]
LAND = "Carbon Sequestration|Land Use"
FOSSIL_CCS = "Carbon Sequestration|CCS|Fossil"
TERMS = (TOTAL, REGROWTH, EW, BECCS, DAC, GROSS_FI, AFOLU, LAND, FOSSIL_CCS)
YEAR = 2050
EXACT_FORMULAS = (
    'CO2tot <- data[,,"Emissions|CO2 (Mt CO2/yr)"]',
    'CDRaff <- -data[,,"Emissions|CO2|Land|Land-use Change|Regrowth (Mt CO2/yr)"]',
    'CDRew <- data[,,"Carbon Sequestration|Enhanced Weathering (Mt CO2/yr)"]',
    'CDRbeccs <- data[,,"Carbon Sequestration|CCS|Biomass (Mt CO2/yr)"]',
    'CDRdaccs <- data[,,"Carbon Sequestration|Direct Air Capture (Mt CO2/yr)"]',
    "CDRtotal <- CDRaff + CDRew + CDRbeccs + CDRdaccs",
    "CO2pos <- CO2tot + CDRtotal",
)

def _sign(n):
    if n is None:
        return "UNAVAILABLE"
    return "POSITIVE" if n > 0 else "NEGATIVE" if n < 0 else "ZERO"

def _difference_band(first, second):
    gap = first - second
    if gap == 0:
        return "EXACT_REPORTED_DECIMAL_EQUALITY", "ZERO", "ZERO"
    frac = Decimal(100) * abs(gap) / max(Decimal(1), abs(first), abs(second))
    if frac < Decimal("0.001"):
        band = "BELOW_0_001_PERCENT"
    elif frac < Decimal("0.1"):
        band = "FROM_0_001_TO_BELOW_0_1_PERCENT"
    elif frac < Decimal("1"):
        band = "FROM_0_1_TO_BELOW_1_PERCENT"
    elif frac < Decimal("10"):
        band = "FROM_1_TO_BELOW_10_PERCENT"
    else:
        band = "AT_LEAST_10_PERCENT"
    return "NONZERO_REPORTED_DECIMAL_DIFFERENCE", _sign(gap), band

def derive_source_worksheet(mif_path, world_path, packet_path, rmd_path,
                            public_path):
    paths = tuple(Path(p).resolve() for p in
                  (mif_path, world_path, packet_path, rmd_path, public_path))
    mif, world, packet_file, rmd, public = paths
    if (len(set(paths)) != len(paths)
            or not all(p.is_file() for p in (mif, world, packet_file, rmd))
            or any("ar6-private" not in p.parts for p in paths[:-1])
            or "ar6-private" in public.parts):
        raise CaseAuditError("Original AR6/author source files must remain private")
    if _digest(mif) != EXPECTED_ARCHIVE_MD5:
        raise CaseAuditError("CEMICS authors' original MIF MD5 changed")
    if _digest(rmd) != AUTHOR_SUPPORT_MD5["authors_rmd"]:
        raise CaseAuditError("CEMICS original author Rmd MD5 changed")
    lines, encoding = _read_author_text_lines(rmd)
    stripped = [line.strip() for line in lines]
    if any(formula not in stripped for formula in EXACT_FORMULAS):
        raise CaseAuditError("Original authors' seven CDR/positive CO2 equations absent")
    packet = json.loads(packet_file.read_text(encoding="utf-8"))
    if (packet.get("schema") != "residualpathways.ar6_canonical_selected24.private.v1"
            or packet.get("handling") != "LOCAL_ONLY_DO_NOT_PUBLISH"
            or not isinstance(packet.get("cases"), list)
            or len(packet["cases"]) != 24):
        raise CaseAuditError("Expected original 24-case private ARC24 selection")
    case = [c for c in packet["cases"] if c.get("case_id") == CASE_ID]
    if (len(case) != 1 or case[0].get("model") != MODEL
            or case[0].get("scenario") != AR6_MIN):
        raise CaseAuditError("Original ARC24-03 source identifier mismatch")
    if sha_file(world) != packet.get("source_sha256"):
        raise CaseAuditError("Original AR6 World v1.1 SHA changed")
    source_ar6, years_ar6 = _load_ar6(world, {AR6_MIN})
    source_author, years_author = _load_authors(mif, {AUTHOR_NO})
    if YEAR not in (years_ar6 & years_author):
        raise CaseAuditError("Original source year 2050 not shared")
    ar6 = source_ar6[AR6_MIN]
    author = source_author[AUTHOR_NO]

    # Reconfirm every original 2050 packet value, rather than trusting a
    # prior broad numerical crosswalk or mutable public report.
    baseline = case[0].get("source_observations")
    if not isinstance(baseline, dict) or not baseline:
        raise CaseAuditError("Private ARC24-03 original observations absent")
    for name, original in baseline.items():
        records = ar6.get(name, [])
        if (len(records) != 1 or records[0][0] != original.get("unit")
                or records[0][1].get(YEAR) != _decimal(original.get("raw"))):
            raise CaseAuditError("Original ARC24-03 source packet differs from AR6 World 2050")

    report_rows = []
    author_values = {}
    provenance = {}
    for name in TERMS:
        author_rows, ar6_rows = author.get(name, []), ar6.get(name, [])
        raw_author_key = name
        raw_marker_candidates = []
        if name == REGROWTH:
            raw_marker_candidates = [
                v for v in author
                if v != REGROWTH and remove_hierarchy_markers(v) == REGROWTH
            ]
            # The Rmd calls deletePlus() before looking up REGROWTH.
            # If several source keys would collapse to the same name, the
            # transformed selector is ambiguous, even if records look equal.
            if raw_marker_candidates and "data <- deletePlus(data)" not in stripped:
                raise CaseAuditError("Original author Rmd lacks source deletePlus preprocessing")
            if not author_rows and len(raw_marker_candidates) == 1:
                raw_author_key = raw_marker_candidates[0]
                author_rows = author[raw_author_key]
        row = {
            "variable": name,
            "original_author_raw_variable": raw_author_key,
            "raw_author_regrowth_hierarchy_candidate_count": (
                len(raw_marker_candidates) if name == REGROWTH else 0
            ),
            "author_source_present": bool(author_rows),
            "ar6_source_present": bool(ar6_rows),
            "expected_unit": UNIT,
            "author_units_reported": sorted({r[0] for r in author_rows}),
            "ar6_units_reported": sorted({r[0] for r in ar6_rows}),
            "provenance": "NOT_VERIFIED",
        }
        alias_ambiguous = (
            name == REGROWTH and bool(raw_marker_candidates)
            and (len(raw_marker_candidates) > 1 or raw_author_key == name)
        )
        if alias_ambiguous:
            status = "AMBIGUOUS_AFTER_AUTHOR_DELETEPLUS"
        elif not author_rows:
            status = "AUTHOR_SERIES_NOT_REPORTED"
        elif not ar6_rows and name in (REGROWTH, GROSS_FI):
            # These two streams are expressly selected in the original Rmd
            # but not published as comparable World variables in the
            # registered AR6 source. We may reproduce the *authors'* study
            # formula, never claim the missing AR6 value is equal or zero.
            unit_rows = [record for record in author_rows if record[0] == UNIT]
            if len(unit_rows) != 1:
                status = "AUTHOR_ONLY_UNIQUE_EXPECTED_UNIT_NOT_FOUND"
            else:
                a = unit_rows[0][1].get(YEAR)
                if a is None:
                    status = "AUTHOR_ONLY_MISSING_YEAR_VALUE"
                else:
                    author_values[name] = a
                    if name == REGROWTH:
                        status = "AUTHOR_ONLY_REGROWTH_AFTER_DELETEPLUS_AR6_ABSENT"
                        row["provenance"] = "AUTHOR_MIF_RMD_DELETEPLUS_ONLY"
                    else:
                        status = "AUTHOR_ONLY_GROSS_FOSSIL_INDUSTRY_AR6_ABSENT"
                        row["provenance"] = "AUTHOR_MIF_RMD_DIRECT_SELECTOR_ONLY"
                    provenance[name] = row["provenance"]
        elif not ar6_rows:
            status = "AR6_SERIES_NOT_REPORTED"
        else:
            pair, problem = _unique_compatible_pair(author_rows, ar6_rows)
            if problem:
                status = problem
            elif pair[0][0] != UNIT:
                status = "UNEXPECTED_COMPARISON_UNIT"
            else:
                a, b = pair[0][1].get(YEAR), pair[1][1].get(YEAR)
                if a is None or b is None:
                    status = "MISSING_YEAR_VALUE"
                else:
                    status = _outcome((UNIT, a), (UNIT, b))
                    if status == "EXACT_REPORTED_DECIMAL_MATCH":
                        author_values[name] = a
                        row["provenance"] = (
                            "AUTHOR_PREPROCESSED_RMD_AND_AR6_EXACT_MATCH"
                            if name == REGROWTH and raw_author_key != name
                            else "AUTHOR_AR6_EXACT_REPORTED_DECIMAL_MATCH"
                        )
                        provenance[name] = row["provenance"]
        row["source_comparison_status"] = status
        row["source_value_sign"] = (
            _sign(author_values[name]) if name in author_values else "UNVERIFIED"
        )
        report_rows.append(row)

    requisite = (TOTAL, REGROWTH, EW, BECCS, DAC)
    missing = [name for name in requisite if name not in author_values]
    operational = {
        "status": "NOT_COMPUTABLE_MISSING_OR_UNVERIFIED_SOURCE_TERM" if missing
                  else "AUTHORS_EXPLICIT_FORMULA_COMPUTABLE_NOT_I3",
        "missing_or_unverified_operational_terms": missing,
        "operational_term_provenance": {name: provenance.get(name, "NOT_VERIFIED")
                                         for name in requisite},
        "regrowth_ar6_independently_reported": bool(ar6.get(REGROWTH)),
        "source_author_preprocessing_confirmed": (
            "data <- deletePlus(data)" in stripped
        ),
        "formula_verified_in_original_Rmd": True,
        "formula_total_CDR": "(-regrowth_emissions)+enhanced_weathering+biomass_CCS+DAC",
        "formula_positive_side": "net_CO2 + operational_CDRtotal",
        "physical_gross_positive_emissions_certified": False,
        "atmospheric_removal_net_durable_disjoint_certified": False,
    }
    comparison = {
        "status": "NOT_COMPARABLE_UNVERIFIED_INPUT",
        "comparison_is_a_expected_closure_equation": False,
        "warning": (
            "The authors' derived CO2pos includes their selected CDR basket "
            "readded to net total; their separately reported Gross Fossil Fuels "
            "and Industry has a narrower sectoral label. Equality is not an "
            "author-required conservation identity."
        ),
    }
    if not missing:
        removal = (-author_values[REGROWTH] + author_values[EW]
                   + author_values[BECCS] + author_values[DAC])
        positive = author_values[TOTAL] + removal
        operational.update({
            "operational_CDRtotal_sign": _sign(removal),
            "operational_CO2pos_sign": _sign(positive),
            "net_total_CO2_sign": _sign(author_values[TOTAL]),
            "regrowth_CDR_sign": _sign(-author_values[REGROWTH]),
            "enhanced_weathering_sign": _sign(author_values[EW]),
            "biomass_CCS_sign": _sign(author_values[BECCS]),
            "DAC_sign": _sign(author_values[DAC]),
        })
        if GROSS_FI in author_values:
            relation, sign, band = _difference_band(
                positive, author_values[GROSS_FI])
            comparison.update({
                "status": (
                    "DIFFERENT_SCOPES_AUTHOR_GROSS_ONLY_COMPARISON"
                    if provenance.get(GROSS_FI) == "AUTHOR_MIF_RMD_DIRECT_SELECTOR_ONLY"
                    else "DIFFERENT_SCOPES_NUMERIC_COMPARISON_ONLY"
                ),
                "gross_fossil_industry_source_provenance": provenance.get(GROSS_FI),
                "source_decimal_relation": relation,
                "CO2pos_minus_gross_fossil_industry_sign": sign,
                "absolute_gap_relative_band": band,
                "separate_gross_fossil_industry_sign": _sign(author_values[GROSS_FI]),
            })
    result = {
        "schema": "residualpathways.arc24.cemics_author_accounting_worksheet.v1",
        "status": "ORIGINAL_AUTHOR_FORMULA_DIAGNOSTIC_NO_I3",
        "case_id": CASE_ID, "year": YEAR,
        "author_source_url": "https://zenodo.org/records/5103024",
        "source_author_mif_md5": EXPECTED_ARCHIVE_MD5,
        "source_author_rmd_md5": AUTHOR_SUPPORT_MD5["authors_rmd"],
        "source_ar6_world_sha256": packet["source_sha256"],
        "original_rmd_encoding_interpretation": encoding,
        "individual_source_terms": report_rows,
        "operational_study_accounting": operational,
        "study_CO2pos_vs_separate_gross_fossil_industry": comparison,
        "important_distinction": (
            "The author-derived CO2pos equation is algebraically true by "
            "definition. Its equality does not prove physically exhaustive "
            "positive gross emissions nor net durable and nonoverlapping CDR. "
            "The author-only plus-marked Regrowth and gross fossil/industry "
            "series are not present under those source variable names in AR6 World. "
            "Regrowth emissions and Carbon Sequestration|Land Use are distinct "
            "reported variables. Fossil CCS is not included in the author's "
            "four CDR source terms. No original numeric observations released."
        ),
        "verified_i3": 0,
    }
    public.parent.mkdir(parents=True, exist_ok=True)
    public.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    return result
