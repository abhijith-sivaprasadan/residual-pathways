"""AR6-format source/metadata category coverage audit: source observations not rehosted."""
from __future__ import annotations
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
import csv
import json
import math


class StrataError(ValueError):
    pass


def sha_file(filename):
    digest = sha256()
    with Path(filename).open("rb") as fd:
        for chunk in iter(lambda: fd.read(1048576), b""):
            digest.update(chunk)
    return digest.hexdigest()


def metadata_rows(path):
    path = Path(path)
    if path.suffix.lower() in (".xlsx", ".xlsm"):
        try:
            from openpyxl import load_workbook
        except ImportError as e:
            raise StrataError("Install the metadata optional extra for XLSX inputs") from e
        wb = load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        iterator = ws.values
        headers = [str(x) if x is not None else "" for x in next(iterator)]
        if len(headers) != len(set(headers)):
            raise StrataError("Duplicate XLSX metadata headers")
        for data in iterator:
            yield dict(zip(headers, ("" if x is None else str(x) for x in data)))
    elif path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as fd:
            reader = csv.DictReader(fd)
            headers = reader.fieldnames or []
            if len(headers) != len(set(headers)):
                raise StrataError("Duplicate CSV metadata headers")
            yield from reader
    else:
        raise StrataError("Metadata must be .csv or .xlsx")


def audit_strata(source_csv, metadata_path, *,
                 year=2050, category_column="Category",
                 variable_names=None):
    """Exact Model+Scenario join to source-defined metadata class; no class inferred."""
    if variable_names is None:
        variable_names = ("Emissions|CO2", "Emissions|CH4", "Emissions|N2O")
    if len(set(variable_names)) != len(variable_names) or not variable_names:
        raise StrataError("Explicit unique variables required")
    md = {}
    for i, rec in enumerate(metadata_rows(metadata_path), 2):
        if not {"Model", "Scenario", category_column} <= rec.keys():
            raise StrataError("Metadata must have Model/Scenario plus explicitly named category")
        key = (rec["Model"].strip(), rec["Scenario"].strip())
        if not all(key):
            raise StrataError(f"Missing metadata identity at row {i}")
        if key in md:
            raise StrataError(f"Duplicate model/scenario metadata at row {i}")
        cat = (rec[category_column] or "").strip()
        md[key] = cat if cat else "MISSING_CATEGORY"
    if not md:
        raise StrataError("No metadata identities")

    matched_source = set()
    sources_without_metadata = set()
    observed = defaultdict(set)
    unit_register = defaultdict(set)
    source_series_count = 0
    duplicate_obs = set()
    with Path(source_csv).open(encoding="utf-8-sig", newline="") as fd:
        reader = csv.DictReader(fd)
        headers = reader.fieldnames or []
        year_key = str(year) if str(year) in headers else f"X{year}"
        if len(headers) != len(set(headers)) or not {"Model", "Scenario", "Region", "Variable", "Unit", year_key} <= set(headers):
            raise StrataError("Source has missing/duplicate columns or absent requested year")
        for line, row in enumerate(reader, 2):
            source_series_count += 1
            if None in row:
                raise StrataError(f"Extra source fields line {line}")
            if row["Region"] != "World":
                continue
            key = (row["Model"], row["Scenario"])
            if key not in md:
                sources_without_metadata.add(key)
                continue
            matched_source.add(key)
            var = row["Variable"]
            if var not in variable_names:
                continue
            raw = (row.get(year_key) or "").strip()
            if not raw:
                continue
            try:
                value = float(raw)
            except ValueError as e:
                raise StrataError(f"Invalid numeric World value at line {line}") from e
            if not math.isfinite(value):
                raise StrataError(f"Non-finite World value at line {line}")
            obs_id = (key, var)
            if obs_id in duplicate_obs:
                raise StrataError("Multiple source records for same model/scenario/variable/year; units not silently mixed")
            duplicate_obs.add(obs_id)
            observed[var].add(key)
            unit_register[var].add(row["Unit"])
    by_category = Counter(md[key] for key in matched_source)
    result = {}
    for category, denominator in sorted(by_category.items()):
        result[category] = {
            "model_scenarios_in_source_and_metadata": denominator,
            "variable_coverage": {
                name: {"observed_model_scenarios": len(set(observed[name]) & {key for key in matched_source if md[key] == category}),
                       "units_seen": sorted(unit_register[name])}
                for name in variable_names},
        }
        for var in variable_names:
            n = result[category]["variable_coverage"][var]["observed_model_scenarios"]
            result[category]["variable_coverage"][var]["coverage_fraction"] = n / denominator

    return {"schema_version":"ar6-stratified-presence.v1",
            "scientific_status":"PRESENCE_ONLY_NO_ACCOUNTING_IDENTIFIABILITY",
            "source_sha256": sha_file(source_csv), "metadata_sha256": sha_file(metadata_path),
            "year": year, "region": "World", "category_column": category_column,
            "metadata_model_scenarios": len(md), "source_rows_scanned": source_series_count,
            "matched_model_scenarios": len(matched_source),
            "unmatched_source_model_scenarios_count": len(sources_without_metadata),
            "unmatched_metadata_model_scenarios_count": len(set(md) - matched_source),
            "strata": result,
            "limitations": [
                "Metadata classification imported verbatim, not inferred",
                "Observed records reflect only exact variable names and selected year",
                "Presence does not guarantee comparable gas/GWP units or semantics",
                "Metadata scenario category may represent a climate-assessment outcome, not modelling design",
                "No gross/net/CDR reconstruction or source data redistribution",
            ]}


def run_strata(source, metadata, output, *, year=2050, category_column="Category"):
    result = audit_strata(source, metadata, year=year, category_column=category_column)
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result
