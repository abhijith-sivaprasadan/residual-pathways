"""Strict IAMC data inspection, conservative accounting, and matched comparisons."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

KEYS = ("Model", "Scenario", "Region", "Variable", "Unit")
COHORT = ("MESSAGEix-GLOBIOM 1.0", "REMIND-MAgPIE 1.7-3.0", "IMAGE 3.0.1")
TARGET = "Emissions|CO2"
WORLD = "World"


class DataError(ValueError):
    """Input cannot be used for credible scenario analysis."""


def read_iamc(path: str | Path) -> tuple[list[dict], dict]:
    path = Path(path)
    raw = path.read_bytes()
    source_sha = hashlib.sha256(raw).hexdigest()
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)) or not set(KEYS).issubset(headers):
            raise DataError("IAMC requires unique Model/Scenario/Region/Variable/Unit columns")
        years = sorted(int(x) for x in headers if x.isdecimal() and len(x) == 4)
        if not years:
            raise DataError("No annual numeric year columns found")
        if any(x not in KEYS and x not in set(map(str, years)) for x in headers):
            raise DataError("Unexpected/non-annual columns; no silent reinterpretation")
        seen = set()
        rows = []
        missing = 0
        for line, row in enumerate(reader, start=2):
            if None in row:
                raise DataError(f"Row {line}: extra CSV fields")
            dimensions = tuple((row.get(k) or "").strip() for k in KEYS)
            if not all(dimensions):
                raise DataError(f"Row {line}: missing IAMC dimension")
            if dimensions in seen:
                raise DataError(f"Row {line}: duplicate IAMC dimensions: {dimensions}")
            seen.add(dimensions)
            vals = {}
            for year in years:
                original = (row.get(str(year)) or "").strip()
                if not original:
                    missing += 1
                    continue
                try:
                    value = float(original)
                except ValueError as exc:
                    raise DataError(f"Row {line}: invalid {year} numerical value") from exc
                if not math.isfinite(value):
                    raise DataError(f"Row {line}: non-finite {year} numerical value")
                vals[str(year)] = value
            rows.append(dict(zip(KEYS, dimensions), values=vals))
    if not rows:
        raise DataError("No records")
    return rows, {"sha256": source_sha, "rows": len(rows), "years": years,
                  "missing_cells": missing, "observed_cells": sum(len(r["values"]) for r in rows)}


def coverage(rows: list[dict], years=(2030, 2050, 2100)) -> dict:
    models = sorted({r["Model"] for r in rows})
    scenarios = sorted({(r["Model"], r["Scenario"]) for r in rows})
    vars_ = sorted({r["Variable"] for r in rows})
    units = sorted({r["Unit"] for r in rows})
    world_co2 = [r for r in rows if r["Region"] == WORLD and r["Variable"] == TARGET]
    return {
        "models": models,
        "model_count": len(models),
        "model_scenario_count": len(scenarios),
        "variables": vars_,
        "units": units,
        "world_co2_series_count": len(world_co2),
        "world_co2_2050_count": sum("2050" in r["values"] for r in world_co2),
        "coverage_by_selected_year": {
            str(year): {
                "reported_world_co2_series": sum(str(year) in r["values"] for r in world_co2),
                "gross_net_cdr_identifiability": "UNRESOLVED_NO_EXHAUSTIVE_PARTITION"
            } for year in years
        },
        "disclaimer": "Emissions|CO2 without a reviewed accounting dictionary is reported CO2; it must not be labelled residual gross, net or CDR.",
    }


def compare(rows: list[dict], models=COHORT, year=2050) -> list[dict]:
    """Only exact World/Emissions|CO2/Mt CO2/yr, common scenarios and observed year values."""
    yr = str(year)
    selected = [r for r in rows if r["Model"] in models and
                r["Region"] == WORLD and r["Variable"] == TARGET and
                r["Unit"] == "Mt CO2/yr" and yr in r["values"]]
    by_scenario = {}
    for row in selected:
        by_scenario.setdefault(row["Scenario"], {})[row["Model"]] = row
    output = []
    for scenario, by_model in sorted(by_scenario.items()):
        if any(model not in by_model for model in models):
            continue
        for model in models:
            output.append({"model": model, "scenario": scenario, "region": WORLD,
                           "variable": TARGET, "unit": "Mt CO2/yr",
                           "year": year, "value": by_model[model]["values"][yr],
                           "meaning": "reported_CO2_not_a_gross_or_CDR_decomposition"})
    return output


def identifiability(variables: set[str], *, reviewed_semantics=False,
                    exhaustive=False, nonoverlap=False,
                    reconciliation=None) -> tuple[str, str]:
    """Fail closed. Names alone do not establish accounting semantics."""
    if not variables:
        return "I0", "no_variables"
    if not reviewed_semantics:
        return "I0", "unreviewed_variable_semantics"
    if not {"net_co2", "gross_positive_co2", "atmospheric_removals"} <= variables:
        if "net_co2" in variables:
            return ("I2", "incomplete_gross_or_removal") if len(variables) > 1 else ("I1", "net_only")
        return "I0", "missing_verified_net"
    if not (exhaustive and nonoverlap):
        return "I2", "partition_not_exhaustive_or_overlapping"
    if not reconciliation or reconciliation.get("status") != "PASS":
        return "I2", "identity_unreconciled_or_precision_unknown"
    return "I3", "complete_semantics_and_reconciliation"


def reconcile(net: float, gross: float, removed: float, *,
              quantization_steps: tuple[float, float, float] | None,
              semantics_verified: bool,
              partition_exhaustive: bool,
              nonoverlapping: bool) -> dict:
    """Provisional v3 I3 tests; input in Mt CO2/yr and quantization documented by source."""
    vals = (net, gross, removed)
    if not all(math.isfinite(x) for x in vals):
        raise DataError("Non-finite accounting component")
    error = abs(net - (gross - removed))
    if not (semantics_verified and partition_exhaustive and nonoverlapping):
        return {"status": "BLOCKED_SEMANTICS", "absolute_error": error}
    if quantization_steps is None:
        return {"status": "PRECISION_UNRESOLVED", "absolute_error": error}
    if len(quantization_steps) != 3 or not all(math.isfinite(q) and q > 0 for q in quantization_steps):
        raise DataError("Require three positive source-documented quantization steps")
    eps_round = 0.5 * sum(quantization_steps)
    eps_numeric = 1e-9 * max(1., sum(abs(x) for x in vals))
    eps_material = max(0.1, 1e-4 * abs(net))
    small = [abs(x) for x in vals if 0 < abs(x) < 10]
    if small:
        eps_material = min(eps_material, 0.01 * min(small))
    return {"status": "PASS" if error <= eps_round + eps_numeric and error <= eps_material else "FAIL",
            "absolute_error": error, "rounding_bound": eps_round + eps_numeric,
            "materiality_bound": eps_material,
            "tolerance_status": "PROVISIONAL_REQUIRES_G0_PRECISION_PILOT"}


def build_results(rows: list[dict], metadata: dict) -> dict:
    selected = compare(rows)
    groups = sorted({r["scenario"] for r in selected})
    return {
        "schema_version": "residualpathways.analysis.v1",
        "source": {"repository": "IAMconsortium/pyam",
                   "path": "docs/tutorials/tutorial_data.csv",
                   "git_revision": "88706bd70051ff630b73096c050e3697364e2302",
                   **metadata},
        "coverage": coverage(rows),
        "comparison": {
            "cohort_models": list(COHORT), "common_scenarios": groups,
            "matched_rows": len(selected), "rows": selected,
            "year": 2050, "unit": "Mt CO2/yr",
            "interpretation": "Published CD-LINKS tutorial scenarios; descriptive differences, not controlled innovation effects."
        },
        "__source_rows": rows,
        "accounting": {"status": "NOT_IDENTIFIABLE_FROM_THIS_SOURCE",
                       "i3_scenarios": 0,
                       "i3_claims": [],
                       "reason": "The tutorial file has no reviewed exhaustive positive-emissions/removals partition, so gross/net/CDR reconciliation is not attempted."},
    }


def write_outputs(results: dict, directory: str | Path) -> None:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    saved_results = {k: v for k, v in results.items() if k != "__source_rows"}
    (directory / "results.json").write_text(json.dumps(saved_results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (directory / "coverage.json").write_text(json.dumps(results["coverage"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    comparison = results["comparison"]
    with (directory / "model_comparison.csv").open("w", newline="", encoding="utf-8") as fd:
        wr = csv.DictWriter(fd, fieldnames=["model", "scenario", "region", "variable", "unit", "year", "value", "meaning"])
        wr.writeheader()
        wr.writerows(comparison["rows"])
    report = [
        "# Reported CO2 in common CD-LINKS tutorial scenarios",
        "",
        "Source: IAMconsortium/pyam, pinned git revision " + results["source"]["git_revision"],
        "Input SHA-256: " + results["source"]["sha256"],
        "",
        f"The source has {results['coverage']['model_count']} models and {results['coverage']['model_scenario_count']} model-scenario pairs.",
        f"The exact 2050 comparison uses {len(comparison['cohort_models'])} selected models, {len(comparison['common_scenarios'])} common scenarios and {comparison['matched_rows']} model-scenario observations.",
        "",
        "## Key boundary",
        "Reported Emissions|CO2 is not a verified gross/net/CDR partition. "
        "No residual gross emissions or attributed innovation-gap effects are calculated.",
        "",
        "## Comparable scenarios",
    ]
    for scenario in comparison["common_scenarios"]:
        matched = [r for r in comparison["rows"] if r["scenario"] == scenario]
        low, high = min(r["value"] for r in matched), max(r["value"] for r in matched)
        report.append(f"- {scenario}: 2050 reported CO2 range {low:,.2f}–{high:,.2f} Mt CO2/yr across the three models.")
    report.extend(["", "These historical scenario outcomes are descriptive; different models are not controlled experiments.",
                   "Data completeness is an outcome, not a reason to manufacture missing values.", ""])
    (directory / "report.md").write_text("\n".join(report), encoding="utf-8")
    import hashlib
    digest = hashlib.sha256((directory / "results.json").read_bytes()).hexdigest()
    release = {"schema_version": "1.0.0", "release_id": "pyam-cd-links-tutorial-v0.1",
               "source_commit": results["source"]["git_revision"], "provenance_type": "PUBLISHED_PUBLIC_TUTORIAL",
               "metric_id": "reported_co2_2050_matched_cohort", "identifiability_level": "I0",
               "publication_permission": "DERIVED_ANALYSIS_ONLY", "dataset_sha256": digest,
               "scientific_status": "COVERAGE_AND_COMPARISON_ONLY",
               "input_sha256": results["source"]["sha256"]}
    (directory / "release").mkdir(exist_ok=True)
    (directory / "release" / "manifest.json").write_text(json.dumps(release, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    from .trajectory import examine, write_trajectory
    write_trajectory(examine(results["__source_rows"]), directory)

    from .plots import render_2050
    render_2050(comparison["rows"], directory / "co2_2050.svg")
