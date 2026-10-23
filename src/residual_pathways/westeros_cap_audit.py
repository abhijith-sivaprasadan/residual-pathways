"""Evidence-scoped read-only reconciliation of a saved Westeros emission bound.

Core MESSAGEix v3.11.1: EMISSION_CONSTRAINT = weighted average by
duration_period of emission_scaling*(EMISS + historical_emission).
No solver execution, no claim that a missing equation marginal is a carbon price.
"""
from __future__ import annotations
import json
import math
from hashlib import sha256
from pathlib import Path

from .messageix_westeros import MODEL, objective_level, temporary_environment
from .westeros_evidence import evidence_from_private_manifest
from .westeros_analysis import records, require, number, WesterosAnalysisError

MODEL_YEARS = (700, 710, 720)
EXPECTED_YEAR_SET = (690, 700, 710, 720)
ALLOWED_FIELDS = {
    "cat_year": ("type_year", "year"),
    "cat_emission": ("type_emission", "emission"),
}


def _rows(scene, kind, name):
    fn = getattr(scene, kind, None)
    if fn is None:
        return []
    check = getattr(scene, "has_" + kind, None)
    if callable(check) and not check(name):
        return []
    try:
        return records(fn(name), name)
    except KeyError:
        return []


def _years(scene_or_values):
    values = scene_or_values.set("year") if hasattr(scene_or_values, "set") else scene_or_values
    if hasattr(values, "tolist"):
        values = values.tolist()
    require(isinstance(values, list), "year must be an indexed set")
    output = []
    for v in values:
        require(type(v) in (int, str) and str(v).isdigit(), "Invalid year set")
        output.append(int(v))
    require(len(set(output)) == len(output), "Duplicate year in source")
    return sorted(output)


def _lookup_one(rows, fields, key, value_field, label):
    matches = [r for r in rows if all(str(r.get(f)) == str(v) for f, v in zip(fields, key))]
    require(len(matches) <= 1, f"{label}: duplicate source parameter row")
    return number(matches[0][value_field], label) if matches else None


def _cat_members(rows, col, cat, value_col):
    require(all(isinstance(row, dict) and col in row and value_col in row for row in rows),
            "Invalid category map")
    result = [str(r[value_col]) for r in rows if r[col] == cat]
    require(len(result) == len(set(result)), "Duplicate category member")
    return result


def reconcile_cap(data):
    """Use one node, one emissions category, explicit year membership.

    If the saved scenario cannot establish the effective period weights or
    category mapping, mark the result NOT_ESTABLISHED, not a false negative.
    """
    note = {
        "status": "NOT_ESTABLISHED",
        "shadow_price_status": "NOT_ESTABLISHED",
        "bound_value": None,
        "computed_average_annual": None,
        "slack": None,
        "period_durations": {},
        "periods_in_category": [],
        "emission_scaling": None,
        "reason": "",
        "method": "Pinned MESSAGEix 3.11.1 EMISSION_CONSTRAINT: sum_y duration_period[y] * emission_scaling * (EMISS + historical_emission) / sum_y duration_period[y]",
    }
    def stop(reason):
        note["reason"] = reason
        return note
    b = [r for r in data["bound_emission"] if r.get("node") == "Westeros"
         and r.get("type_emission") == "GHG" and r.get("type_tec") == "all"
         and r.get("type_year") == "cumulative"]
    if len(b) != 1 or b[0].get("unit") != "MtCO2":
        return stop("Expected one Westeros GHG/all/cumulative bound in MtCO2")
    bound = number(b[0].get("value"), "bound_emission")
    note["bound_value"] = bound
    years = _years(data["year_set"])
    if years != list(EXPECTED_YEAR_SET):
        return stop("Year set differs from the pinned Westeros tutorial")
    mapped_years = _cat_members(data["cat_year"], "type_year", "cumulative", "year")
    mapped_years = sorted(int(y) for y in mapped_years if y.isdigit())
    if mapped_years != list(MODEL_YEARS):
        return stop("Cumulative category does not contain exactly the expected model years")
    note["periods_in_category"] = mapped_years
    mapped_emissions = _cat_members(data["cat_emission"], "type_emission", "GHG", "emission")
    if mapped_emissions != ["CO2"]:
        return stop("Emission category does not map uniquely to CO2")
    rawdur = data["duration_period"]
    if rawdur:
        durations = {}
        for year in mapped_years:
            d = _lookup_one(rawdur, ("year",), (year,), "value", "duration_period")
            if d is None or d <= 0:
                return stop("Missing/invalid duration_period on a mapped year")
            durations[year] = d
        duration_source = "SAVED_SCENARIO_PARAMETER"
    else:
        # add_horizon provides the 4 exact 10-year labels. MESSAGEix computes
        # duration_period at GDX export when not stored as a parameter.
        durations = {year: year - years[years.index(year) - 1] for year in mapped_years}
        if any(d <= 0 for d in durations.values()):
            return stop("Invalid reconstructed period durations")
        duration_source = "DERIVED_FROM_PINNED_YEAR_SET"
    note["period_durations"] = {str(y): durations[y] for y in mapped_years}
    note["duration_source"] = duration_source

    scaling = _lookup_one(data["emission_scaling"],
                          ("type_emission", "emission"), ("GHG", "CO2"),
                          "value", "emission_scaling")
    if scaling is None:
        # MESSAGE/data_load.gms explicitly initializes uncoded scaling to 1.
        scaling = 1.0
        note["scaling_source"] = "PINNED_GAMS_DATA_LOAD_DEFAULT_ONE"
    else:
        note["scaling_source"] = "SAVED_SCENARIO_PARAMETER"
    if scaling <= 0:
        return stop("Invalid emission_scaling")
    note["emission_scaling"] = scaling
    terms = []
    for year in mapped_years:
        matching = [r for r in data["EMISS"] if r.get("node") == "Westeros"
                    and r.get("type_tec") == "all" and r.get("emission") == "CO2"
                    and str(r.get("year")) == str(year)]
        if len(matching) != 1:
            return stop(f"Expected one Westeros CO2 EMISS record for {year}")
        value = number(matching[0].get("lvl"), "EMISS")
        hist = _lookup_one(data["historical_emission"], ("node", "emission", "type_tec", "year"),
                           ("Westeros", "CO2", "all", year), "value", "historical_emission")
        # Absent historical-emission parameter means zero in GAMS.
        historical = 0.0 if hist is None else hist
        terms.append((value + historical) * scaling * durations[year])
    total_duration = math.fsum(durations.values())
    value = math.fsum(terms) / total_duration
    require(math.isfinite(value), "Overflow in emission bound calculation")
    slack = bound - value
    tolerance = max(1e-5, 1e-6 * max(abs(value), abs(bound)))
    note.update({"computed_average_annual": value, "slack": slack,
                 "tolerance": tolerance, "reason": "Reconstructed from saved EMISS and scenario definitions",
                 "status": "NUMERICALLY_SATURATED" if abs(slack) <= tolerance
                           else "WITHIN_BOUND_WITH_SLACK" if slack > tolerance
                           else "APPARENT_BOUND_VIOLATION"})
    if note["status"] == "APPARENT_BOUND_VIOLATION":
        note["reason"] = "LHS exceeds bound; inspect model period and source accounting definitions"
    note["binding_interpretation"] = (
        "Numerical cap saturation, not a validated dual or independent solver audit"
        if note["status"] == "NUMERICALLY_SATURATED" else
        "Not numerically saturated at the specified tolerance"
    )
    return note


def audit_saved_run(private_manifest, output_dir):
    """Extract only necessary unredacted records, then publish derived-only audit."""
    private_manifest = Path(private_manifest).resolve()
    require(private_manifest.name == "manifest.private.json" and private_manifest.is_file(),
            "Require the saved local private manifest")
    require(private_manifest.stat().st_size < 1_000_000, "Unexpected private manifest size")
    source = json.loads(private_manifest.read_text(encoding="utf-8"))
    verified = evidence_from_private_manifest(source)
    run_dir = private_manifest.parent
    require((run_dir / "ixmp_config" / "config.json").is_file(), "Missing ixmp configuration")
    require((run_dir / "ixmp_database" / "westeros.properties").is_file()
            or (run_dir / "ixmp_database" / "westeros.script").is_file(),
            "Missing original private saved ixmp database")
    output_dir = Path(output_dir).resolve()
    require(output_dir != run_dir and run_dir not in output_dir.parents,
            "Never write audit into private run directory")
    with temporary_environment({"IXMP_DATA": run_dir / "ixmp_config"}):
        import ixmp
        import message_ix
        platform = ixmp.Platform()
        try:
            scenario = message_ix.Scenario(platform, model=MODEL, scenario="emission_bound",
                                           version=next(r["version"] for r in verified["scenarios"]
                                                        if r["scenario"] == "emission_bound"))
            require(scenario.has_solution(), "Bounded scenario has no persisted solution")
            saved_obj = objective_level(scenario.var("OBJ"), "emission_bound")
            expected_obj = next(r["objective_native"] for r in verified["scenarios"]
                                if r["scenario"] == "emission_bound")
            require(math.isclose(saved_obj, expected_obj, rel_tol=1e-7, abs_tol=1e-3),
                    "Saved objective differs from successful run manifest")
            data = {
                "year_set": _years(scenario),
                "cat_year": _rows(scenario, "set", "cat_year"),
                "cat_emission": _rows(scenario, "set", "cat_emission"),
                "duration_period": _rows(scenario, "par", "duration_period"),
                "emission_scaling": _rows(scenario, "par", "emission_scaling"),
                "historical_emission": _rows(scenario, "par", "historical_emission"),
                "bound_emission": _rows(scenario, "par", "bound_emission"),
                "EMISS": _rows(scenario, "var", "EMISS"),
            }
        finally:
            platform.close_db()
    result = reconcile_cap(data)
    result["run_id"] = verified["source_run_id"]
    result["upstream_commit"] = verified["upstream_commit"]
    result["evidence_scope"] = "AUTHOR_REPORTED_LOCAL_SAVED_IXMP_EDUCATIONAL"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    dest = output_dir / "cap_reconciliation.json"
    dest.write_bytes(raw)
    (output_dir / "cap_reconciliation.sha256").write_text(sha256(raw).hexdigest() + "\n",
                                                           encoding="utf-8")
    return result
