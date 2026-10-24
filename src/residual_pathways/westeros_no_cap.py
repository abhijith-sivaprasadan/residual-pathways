"""Isolated, licensed MESSAGEix control solve: CO2 accounting without an emission cap.

Source model: the pinned official Westeros emissions-bound scenario, already
solved on the author's machine. Clone across ixmp Platforms into a NEW private
HSQLDB. Remove only bound_emission; keep emission factors, technology data,
year mappings and all other assumptions. Never modify the original database.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import csv
import json
import math
import os
import shutil
import uuid

from .messageix_westeros import MODEL, objective_level, temporary_environment
from .westeros_analysis import MEASURES, TECHNOLOGIES, YEARS, reduce_metric, records, require
from .westeros_evidence import evidence_from_private_manifest

CONTROL_NAME = "emissions_accounting_no_cap"
PARITY_PARS = (
    "demand", "input", "output", "technical_lifetime", "capacity_factor",
    "growth_activity_up", "historical_activity", "historical_new_capacity",
    "interestrate", "inv_cost", "fix_cost", "var_cost", "emission_factor",
)


def _get_rows(scenario, par):
    """Canonical read of parameter values for source-vs-control verification."""
    value = scenario.par(par)
    return records(value, par)


def _fingerprint_rows(rows):
    """Compare cell text and indices independent of JDBC retrieval order."""
    return sorted(json.dumps({str(k): str(v) for k, v in row.items()},
                             sort_keys=True, separators=(",", ":")) for row in rows)


def verify_clone_inputs(source_bound, control):
    """Fail if any known modelling parameter besides bound_emission changed."""
    observed = {}
    for name in PARITY_PARS:
        parent_rows = _get_rows(source_bound, name)
        child_rows = _get_rows(control, name)
        require(_fingerprint_rows(parent_rows) == _fingerprint_rows(child_rows),
                f"Unexpected source/control parameter difference in {name}")
        if name == "emission_factor":
            require(bool(parent_rows), "No emission_factor retained")
        observed[name] = len(parent_rows)
    existing = _get_rows(control, "bound_emission")
    require(not existing, "CO2 bound remains on control clone")
    source_bounds = _get_rows(source_bound, "bound_emission")
    require(len(source_bounds) == 1, "Expected exactly one upstream bound")
    require(source_bounds[0].get("value") == 500.0, "Source CO2 cap differs from expected")
    return {"parameter_rows_verified": observed,
            "source_cap_rows": len(source_bounds),
            "control_cap_rows": len(existing),
            "only_intended_change": "bound_emission parameter rows removed"}


def snapshot_metrics(scenario):
    metrics = {}
    for name in MEASURES:
        metrics[name] = reduce_metric(scenario.var(name), name)
    return metrics


def build_three_case_comparison(snapshots, run_id, control_version, parity):
    require(set(snapshots) == {"baseline", CONTROL_NAME, "emission_bound"},
            "Three-case snapshots incomplete")
    objectives = {}
    for label, snap in snapshots.items():
        require(bool(snap["has_solution"]), f"{label}: saved solution missing")
        obj = snap["objective_native"]
        require(type(obj) in (float, int) and math.isfinite(obj), f"{label}: invalid OBJ")
        objectives[label] = float(obj)
    a, control, bounded = (objectives[k] for k in
                          ("baseline", CONTROL_NAME, "emission_bound"))
    agreement_tolerance = max(0.01, abs(a) * 1e-6)
    agreement = abs(control - a) <= agreement_tolerance
    rows = []
    for measure in MEASURES:
        for tech in TECHNOLOGIES:
            for year in YEARS:
                key = (measure, tech, year)
                values = {label: snapshots[label]["metrics"][measure].get(key)
                          for label in snapshots}
                if all(value is None for value in values.values()):
                    continue
                rows.append({
                    "metric": measure, "technology": tech, "year": year,
                    **values,
                    "control_minus_baseline": (values[CONTROL_NAME] - values["baseline"])
                    if values[CONTROL_NAME] is not None and values["baseline"] is not None else None,
                    "cap_minus_control": (values["emission_bound"] - values[CONTROL_NAME])
                    if values["emission_bound"] is not None and values[CONTROL_NAME] is not None else None,
                    "complete": all(value is not None for value in values.values()),
                })
    require(len(rows) >= 30, "Too few stored technology-year results for credible comparison")
    return {
        "schema": "residualpathways.westeros.control_comparison.v1",
        "status": "ACTUAL_MESSAGEIX_GAMS_CONTROL_SOLVED" if agreement else
                  "CONTROL_SOLVED_BUT_BASELINE_OBJECTIVE_MISMATCH",
        "provenance": "AUTHOR_LOCAL_GAMS_NOT_INDEPENDENTLY_REPRODUCED",
        "scientific_scope": "EDUCATIONAL_WESTEROS_NOT_AR6",
        "source_run_id": run_id,
        "control_scenario": CONTROL_NAME,
        "control_version": control_version,
        "intervention": "remove exactly one emissions bound; retain CO2 emissions accounting",
        "verified_inputs": parity,
        "objectives_native": objectives,
        "baseline_vs_control": {"difference": control - a,
                                "numerically_equivalent": agreement,
                                "absolute_tolerance": agreement_tolerance},
        "cap_effect": {"difference_native": bounded - control,
                       "relative_percent": 100 * (bounded - control) / control if control else None,
                       "attributable_to_bound_only": agreement},
        "comparisons": rows,
        "assertions_not_made": ["carbon shadow price", "independent replication",
                                "AR6 emissions", "real-world cost"],
    }


def run_control(private_manifest, output_root="results/westeros_control_private"):
    """Run only one new solve, in new private HSQLDB, preserving original sources."""
    path = Path(private_manifest).resolve()
    require(path.is_file() and path.name == "manifest.private.json",
            "Select successful source manifest.private.json")
    require(path.stat().st_size < 1_000_000, "Original manifest unexpectedly large")
    source = json.loads(path.read_text(encoding="utf-8"))
    evidence = evidence_from_private_manifest(source)
    source_dir = path.parent
    require((source_dir / "ixmp_config" / "config.json").is_file(), "Original ixmp config missing")
    require((source_dir / "ixmp_database" / "westeros.script").is_file()
            or (source_dir / "ixmp_database" / "westeros.properties").is_file(),
            "Original solved ixmp HSQLDB missing")
    output_root = Path(output_root).resolve()
    require(output_root != source_dir and source_dir not in output_root.parents,
            "Cannot write experiment inside original private solve directory")
    new_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    experiment_dir = output_root / new_id
    experiment_dir.mkdir(parents=True, exist_ok=False)
    journal = {
        "schema": "residualpathways.westeros.control_run.private.v1",
        "status": "NOT_YET_SOLVED", "source_run_id": evidence["source_run_id"],
        "control_run_id": new_id, "scientific_scope": "EDUCATIONAL_MESSAGEIX_GAMS_NOT_AR6",
        "source_model": MODEL, "source_scenario": "emission_bound",
        "control_name": CONTROL_NAME, "source_upstream_commit": evidence["upstream_commit"],
        "source_scenario_version": next(x["version"] for x in evidence["scenarios"]
                                        if x["scenario"] == "emission_bound"),
        "private_database_stored": True,
        "licensed_gams_solve_performed": False,
    }
    def persist():
        (experiment_dir / "manifest.private.json").write_text(
            json.dumps(journal, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8")
    persist()

    # ixmp configuration is initialized on import; import inside this context.
    with temporary_environment({"IXMP_DATA": source_dir / "ixmp_config"}):
        import ixmp
        import message_ix
        src = ixmp.Platform()
        dst = None
        try:
            dst_db = experiment_dir / "ixmp_database" / "control"
            dst_db.parent.mkdir(parents=True, exist_ok=True)
            dst = ixmp.Platform(backend="jdbc", driver="hsqldb",
                                path=dst_db.resolve().as_posix())
            expected = {r["scenario"]: r for r in evidence["scenarios"]}
            base = message_ix.Scenario(src, model=MODEL, scenario="baseline",
                                       version=expected["baseline"]["version"])
            bounded = message_ix.Scenario(src, model=MODEL, scenario="emission_bound",
                                          version=expected["emission_bound"]["version"])
            for label, sc in (("baseline", base), ("emission_bound", bounded)):
                require(sc.has_solution(), f"{label} original solution missing")
                objective = objective_level(sc.var("OBJ"), label)
                require(math.isclose(objective, expected[label]["objective_native"],
                                     rel_tol=1e-7, abs_tol=1e-3),
                        f"{label} objective differs from original manifest")
            journal["status"] = "CLONING_INPUTS"
            persist()
            # ixmp JDBCBackend 3.11.1 explicitly forbids cross-platform
            # clone(keep_solution=False). The supported two-step equivalent is
            # a full cross-platform clone, followed by clearing its copied
            # solution on the destination *before* checking out parameters.
            clone = bounded.clone(model=MODEL, scenario=CONTROL_NAME,
                                  annotation="Isolated emissions accounting without cap",
                                  keep_solution=True, platform=dst)
            # ixmp.TimeSeries.__init__ stores platform as weakref.proxy(mp);
            # therefore `clone.platform is dst` is False even for the correct
            # destination. Check the underlying backend objects instead.
            require(clone.platform._backend is dst._backend
                    and clone.platform._backend is not src._backend,
                    "Clone is not attached to the isolated destination backend")
            require(clone.has_solution(), "Cross-platform clone did not copy the solution")
            clone.remove_solution()
            require(not clone.has_solution(), "Copied source solution was not cleared")
            journal["clone_method"] = "CROSS_PLATFORM_KEEP_SOLUTION_THEN_REMOVE_SOLUTION"
            persist()
            clone.check_out()
            # ixmp.Scenario.remove_par(name) *deletes the entire parameter*.
            # Pass the saved parameter rows as key to delete ONLY their values,
            # keeping the empty bound_emission item defined for MESSAGEix/GAMS.
            old_bound_rows = clone.par("bound_emission")
            require(len(old_bound_rows) == 1, "Expected exactly one bound to remove")
            clone.remove_par("bound_emission", old_bound_rows)
            clone.commit(comment="Remove CO2 bound values only; retain parameter and emission factors")
            parity = verify_clone_inputs(bounded, clone)
            journal["status"] = "SOLVING_CONTROL"
            journal["input_parity"] = parity
            persist()
            clone.set_as_default()
            clone.solve()
            require(clone.has_solution(), "Control solver did not persist a solution")
            journal["licensed_gams_solve_performed"] = True
            journal["control_version"] = clone.version
            journal["control_objective_native"] = objective_level(clone.var("OBJ"), CONTROL_NAME)
            persist()
            snapshots = {}
            for label, sc in (("baseline", base), ("emission_bound", bounded),
                              (CONTROL_NAME, clone)):
                snapshots[label] = {"objective_native": objective_level(sc.var("OBJ"), label),
                                    "has_solution": sc.has_solution(),
                                    "metrics": snapshot_metrics(sc)}
            comparison = build_three_case_comparison(
                snapshots, evidence["source_run_id"], clone.version, parity)
            journal["status"] = comparison["status"]
            journal["derived_report"] = "three_case_comparison.json"
            raw = (json.dumps(comparison, indent=2, sort_keys=True, allow_nan=False)
                   + "\n").encode("utf-8")
            (experiment_dir / "three_case_comparison.json").write_bytes(raw)
            journal["derived_sha256"] = sha256(raw).hexdigest()
            from io import StringIO
            buf = StringIO(newline="")
            columns = ("metric", "technology", "year", "baseline", CONTROL_NAME,
                       "emission_bound", "control_minus_baseline", "cap_minus_control", "complete")
            writer = csv.DictWriter(buf, fieldnames=columns, lineterminator="\n")
            writer.writeheader()
            writer.writerows(comparison["comparisons"])
            (experiment_dir / "three_case_comparison.csv").write_text(
                buf.getvalue(), encoding="utf-8", newline="")
            persist()
            if not comparison["baseline_vs_control"]["numerically_equivalent"]:
                raise RuntimeError("Control solved but objective differs from baseline; inspect private report")
            return comparison, experiment_dir
        except Exception as exc:
            if journal["status"] != "CONTROL_SOLVED_BUT_BASELINE_OBJECTIVE_MISMATCH":
                journal["status"] = "FAILED_NOT_VERIFIED"
            journal["failure_type"] = type(exc).__name__
            persist()
            raise
        finally:
            if dst is not None:
                dst.close_db()
            src.close_db()
