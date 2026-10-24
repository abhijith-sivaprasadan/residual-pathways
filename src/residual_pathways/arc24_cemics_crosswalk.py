"""Verify an original CEMICS research release against the local AR6 World case.

Strict external author-archive file MD5, fixed AR6 World SHA, exact scenario,
model, region and variable names, source units, year and Decimal observations.
DOES NOT prove complete gross emissions, source processing/precision or I3.
No original numerical observations are written to the public report.
"""
from __future__ import annotations

from collections import Counter
import csv
from decimal import Decimal, InvalidOperation
from hashlib import md5
from itertools import chain
import json
from pathlib import Path

from .case_audit import CaseAuditError, SIX, TOTAL, UNIT
from .stratify import sha_file

CASE_ID = "ARC24-03"
MODEL = "REMIND-MAgPIE 2.1-4.2"
SCENARIO = "CEMICS_SSP1-1p5C-minCDR"
EXPECTED_ARCHIVE_MD5 = "efbc4f82b0163da790f370775a37cfe7"
KEYS = ("Model", "Scenario", "Region", "Variable", "Unit")
YEAR = "2050"
CANDIDATES = (TOTAL,) + tuple(SIX) + ("Emissions|CO2|Other",)
YEAR_ALIASES = (YEAR, "X" + YEAR)


def _decimal(raw):
    if raw is None or not str(raw).strip() or str(raw).strip().lower() in (
            "na", "nan", "n/a", "null"):
        return None
    try:
        value = Decimal(str(raw).strip())
    except InvalidOperation as exc:
        raise CaseAuditError("Invalid original numeric source cell") from exc
    if not value.is_finite():
        raise CaseAuditError("Source numeric cell is non-finite")
    return value


def _digest(path, algorithm="md5"):
    from hashlib import new
    h = new(algorithm)
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(2**20), b""):
            h.update(block)
    return h.hexdigest()


def _headered_archive(path):
    """Read semicolon/tab/comma MIF IAMC wide form; skip leading comments.

    Explicitly fails on unfamiliar formats. Never guesses column roles.
    """
    with path.open("r", encoding="utf-8-sig", errors="strict", newline="") as handle:
        skipped = 0
        for line in handle:
            skipped += 1
            if skipped > 2000:
                raise CaseAuditError("Cannot locate source MIF header in first 2000 lines")
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "*", "!")):
                continue
            for delimiter in (";", "\t", ","):
                pieces = next(csv.reader([line], delimiter=delimiter))
                names = [x.strip() for x in pieces]
                if set(KEYS).issubset(names):
                    reader = csv.reader(chain([line], handle), delimiter=delimiter)
                    header = [name.strip() for name in next(reader)]
                    # REMIND MIF spec permits/requires final delimiters; these
                    # produce a terminal empty cell after the last column.
                    if header and header[-1] == "":
                        header.pop()
                    if len(set(header)) != len(header):
                        raise CaseAuditError("Archive MIF header has duplicate names")
                    for fields in reader:
                        if not fields or len(fields) == 1 and not fields[0].strip():
                            continue
                        if len(fields) == len(header) + 1 and fields[-1] == "":
                            fields.pop()
                        if len(fields) != len(header):
                            raise CaseAuditError("Archive MIF row width differs from declared header")
                        yield dict(zip(header, fields))
                    return
        raise CaseAuditError("Unsupported MIF layout: expected wide IAMC header")


def _year_column(header):
    for v in YEAR_ALIASES:
        if v in header:
            return v
    return None


def _loaded_value(data):
    if not isinstance(data, dict):
        raise CaseAuditError("Malformed original source observation")
    return data["unit"], _decimal(data.get("raw"))


def _status(archive, official):
    if archive is None:
        return "ARCHIVE_VARIABLE_NOT_REPORTED", None
    if official is None:
        return "AR6_VARIABLE_NOT_REPORTED", None
    if archive[0] != official[0]:
        return "UNITS_DIFFER", None
    a, b = archive[1], official[1]
    if a is None or b is None:
        return "MISSING_YEAR_VALUE", None
    if a == b:
        return "EXACT_REPORTED_DECIMAL_MATCH", "ZERO"
    difference = abs(a-b)
    norm = max(Decimal("1"), abs(a), abs(b))
    p = difference / norm * Decimal(100)
    boundaries = (
        (Decimal("0.001"), "BELOW_0_001_PERCENT"),
        (Decimal("0.1"), "FROM_0_001_TO_BELOW_0_1_PERCENT"),
        (Decimal("1"), "FROM_0_1_TO_BELOW_1_PERCENT"),
        (Decimal("10"), "FROM_1_TO_BELOW_10_PERCENT"),
    )
    band = next((name for n, name in boundaries if p < n), "AT_LEAST_10_PERCENT")
    return "NONZERO_REPORTED_DECIMAL_DIFFERENCE", band


def crosswalk(mif_path, world_path, packet_path, public_path,
              rmd_path=None, readme_path=None):
    paths = [Path(x).resolve() for x in (mif_path, world_path, packet_path, public_path)]
    mif, world, packet_file, public = paths
    if (not all(p.is_file() for p in (mif, world, packet_file)) or
            len(set(paths)) != 4 or "ar6-private" not in packet_file.parts or
            "ar6-private" not in mif.parts or "ar6-private" not in world.parts or
            "ar6-private" in public.parts):
        raise CaseAuditError("Original author archive and AR6 World must remain in private source directories")
    archive_md5 = _digest(mif)
    if archive_md5 != EXPECTED_ARCHIVE_MD5:
        raise CaseAuditError("Authors' CEMICS v2 MIF MD5 mismatch (Zenodo 5103024)")
    packet = json.loads(packet_file.read_text(encoding="utf-8"))
    if (packet.get("schema") != "residualpathways.ar6_canonical_selected24.private.v1"
            or packet.get("handling") != "LOCAL_ONLY_DO_NOT_PUBLISH"
            or not isinstance(packet.get("cases"), list)
            or len(packet["cases"]) != 24):
        raise CaseAuditError("Expected original private ARC24 selection")
    matched = [c for c in packet["cases"] if c.get("case_id") == CASE_ID]
    if len(matched) != 1 or matched[0].get("model") != MODEL or matched[0].get("scenario") != SCENARIO:
        raise CaseAuditError("ARC24-03 no longer maps to expected REMIND CEMICS model and scenario")
    if sha_file(world) != packet.get("source_sha256"):
        raise CaseAuditError("AR6 World v1.1 source SHA has changed")
    case = matched[0]
    # Only reproduce the original reported 2050 source-record values.
    saved = case.get("source_observations")
    if not isinstance(saved, dict):
        raise CaseAuditError("Original AR6 selected 2050 observation map absent")
    original_ar6 = {}
    ar6_source_year_column = None
    with world.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        if not set(KEYS).issubset(fields) or len(fields) != len(set(fields)):
            raise CaseAuditError("AR6 World header invalid")
        ar6_source_year_column = _year_column(fields)
        if not ar6_source_year_column:
            raise CaseAuditError("AR6 World 2050 year column absent")
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise CaseAuditError("Malformed World CSV row")
            if (row["Model"], row["Scenario"], row["Region"]) != (
                    MODEL, SCENARIO, "World"):
                continue
            key = row["Variable"]
            if key in original_ar6:
                raise CaseAuditError("Duplicate AR6 World scenario-variable row")
            original_ar6[key] = (row["Unit"], _decimal(row[ar6_source_year_column]))
    if not original_ar6:
        raise CaseAuditError("ARC24-03 exact original model/scenario/World source absent")
    for v, payload in saved.items():
        if v not in original_ar6 or _loaded_value(payload) != original_ar6[v]:
            raise CaseAuditError("Original ARC24-03 private 2050 case and source World CSV disagree")

    archive_all_same_scenario, archive_exact_pair, archive_world, seen = 0, 0, {}, set()
    exact_source_regions, archive_model_labels = Counter(), Counter()
    archive_year_col = None
    for row in _headered_archive(mif):
        if None in row or any(v is None for v in row.values()):
            raise CaseAuditError("Malformed author MIF CSV row")
        if row.get("Scenario") != SCENARIO:
            continue
        archive_all_same_scenario += 1
        archive_model_labels[row["Model"]] += 1
        if row.get("Model") != MODEL:
            continue
        archive_exact_pair += 1
        region = row["Region"]
        exact_source_regions[region] += 1
        if region != "World":
            continue
        v = row["Variable"]
        if v in archive_world:
            raise CaseAuditError("Duplicate author MIF exact World scenario-variable row")
        if archive_year_col is None:
            archive_year_col = _year_column(row.keys())
            if not archive_year_col:
                raise CaseAuditError("Author MIF lacks the 2050 source column")
        archive_world[v] = (row["Unit"], _decimal(row[archive_year_col]))
    if archive_exact_pair and archive_year_col is None and not archive_world:
        # Could be a different region naming scheme; don't guess its meaning.
        result_state = "MATCHED_MODEL_SCENARIO_BUT_WORLD_REGION_NOT_FOUND"
    elif archive_world:
        result_state = "EXACT_MODEL_SCENARIO_WORLD_YEAR_FOUND_SOURCE_SEMANTICS_UNVERIFIED"
    elif archive_all_same_scenario:
        result_state = "SCENARIO_NAME_MATCH_ONLY_MODEL_MAPPING_UNVERIFIED"
    else:
        result_state = "SCENARIO_NOT_LOCATED_IN_AUTHOR_MIF"
    all_vars = sorted(set(archive_world) | set(original_ar6))
    candidates = []
    for v in CANDIDATES:
        row = archive_world.get(v)
        ar6 = original_ar6.get(v)
        status, band = _status(row, ar6)
        candidates.append({"variable": v, "archive_present": row is not None,
                           "ar6_present": ar6 is not None,
                           "archive_unit": row[0] if row else None,
                           "ar6_unit": ar6[0] if ar6 else None,
                           "comparison_status": status, "difference_band": band})
    all_pairs = [v for v in all_vars if v in archive_world and v in original_ar6]
    overlap_counts = Counter(_status(archive_world[v], original_ar6[v])[0] for v in all_pairs)
    carbon_names = sorted(v for v in archive_world if any(
        term in v.lower() for term in ("co2", "carbon", "removal", "sequestration")))
    # Names are diagnostic candidates only; never label them verified gross or removals.
    external_code = {}
    for kind, path in (("authors_rmd", rmd_path), ("authors_readme", readme_path)):
        if path is None:
            continue
        path = Path(path).resolve()
        if not path.is_file() or "ar6-private" not in path.parts:
            raise CaseAuditError("Supporting author methodology source not private or missing")
        expected = {
            "authors_rmd": "66923e9fbbeec5113849e2566d486c29",
            "authors_readme": "e0d133b76db3fd3ccb95f06279197ff0",
        }[kind]
        if _digest(path) != expected:
            raise CaseAuditError("Zenodo-listed MD5 mismatch in author supporting source")
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        keys = ("gross", "emissions", "BECCS", "DAC", "land", "remov", "SSP1",
                "CEMICS_SSP1-1p5C-minCDR")
        external_code[kind] = {
            "source_md5_verified": True, "line_count": len(lines),
            "keyword_line_counts": {
                k: sum(k.lower() in line.lower() for line in lines) for k in keys
            },
            "exact_scenario_line_numbers": [
                i+1 for i, line in enumerate(lines)
                if SCENARIO.lower() in line.lower()
            ][:25],
        }
    public_out = {
        "schema": "residualpathways.arc24.cemics_source_crosswalk.v1",
        "status": result_state, "case_id": CASE_ID, "year": 2050,
        "author_source": "https://zenodo.org/records/5103024",
        "archive_md5": archive_md5, "ar6_world_sha256": packet["source_sha256"],
        "archive_scenario_name_row_count": archive_all_same_scenario,
        "archive_exact_model_scenario_row_count": archive_exact_pair,
        "archive_exact_world_variable_count": len(archive_world),
        "ar6_exact_world_variable_count": len(original_ar6),
        "archive_region_name_counts_exact_pair": dict(exact_source_regions),
        "same_scenario_distinct_model_label_count":
            sum(m != MODEL for m in archive_model_labels),
        "overlapping_variable_names": len(all_pairs),
        "overlap_status_counts": dict(overlap_counts),
        "selected_variable_comparisons": candidates,
        "archive_carbon_related_variable_name_count": len(carbon_names),
        "archive_carbon_related_variable_names": carbon_names,
        "author_methodology_code_presence": external_code,
        "scientific_grade": "NOT_DETERMINED", "verified_i3": False,
        "limitations": [
            "Matching source Model/Scenario/Region/Variable/Unit/Year is source attribution, not a certified emissions/removals physical partition.",
            "Differences are source-reported decimal differences; original quantization and AR6 transformations are not established.",
            "Same Scenario with a changed Model identifier is not automatically the same physical model version.",
            "Carbon-related variable names are candidates only, never inferred disjoint gross or atmospheric-removal components.",
            "No restricted original AR6 numerical emissions or archive observations published.",
        ],
    }
    public.parent.mkdir(parents=True, exist_ok=True)
    public.write_text(json.dumps(public_out, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return public_out
