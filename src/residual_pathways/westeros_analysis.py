"""Read-only analysis of actually solved, locally persisted Westeros ixmp scenarios.

The official pinned Westeros baseline omits CO2 emission accounting. Do not
infer baseline emissions or a binding marginal from the emissions-bound case.
Neither this module nor its tests invoke GAMS or modify model parameters.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
from html import escape
from pathlib import Path
import csv
import json
import math

from .messageix_westeros import MODEL, NOTEBOOKS, objective_level, temporary_environment
from .westeros_evidence import evidence_from_private_manifest

YEARS = (700, 710, 720)
TECHNOLOGIES = ("coal_ppl", "wind_ppl", "grid", "bulb")
MEASURES = {
    "ACT": ("year_act", "technology", "model activity; sum over vintages and modes"),
    "CAP": ("year_act", "technology", "installed capacity; sum over vintages"),
    "CAP_NEW": ("year_vtg", "technology", "new-capacity decision; annualized over model period"),
}
STAGES = tuple(stage for stage, _, _ in NOTEBOOKS)


class WesterosAnalysisError(ValueError):
    """Input failed the local, no-new-solve analysis gate."""


def require(condition, msg):
    if not condition:
        raise WesterosAnalysisError(msg)


def number(value, context):
    require(type(value) in (float, int), f"{context}: numeric level required")
    require(math.isfinite(value), f"{context}: non-finite level")
    return float(value)


def records(item, label):
    """Read pandas DataFrame rows; accepting list of mappings eases pure unit tests."""
    if hasattr(item, "to_dict"):
        rows = item.to_dict(orient="records")
    elif isinstance(item, list):
        rows = item
    else:
        raise WesterosAnalysisError(f"{label}: unexpected indexed representation")
    require(isinstance(rows, list), f"{label}: rows must be a list")
    require(len(rows) <= 50000, f"{label}: row limit exceeded")
    return rows


def reduce_metric(item, metric):
    """Aggregate exact annual Westeros domain, not missing tuples or time slices."""
    require(metric in MEASURES, "Unknown metric")
    year_key, _, _ = MEASURES[metric]
    rows = records(item, metric)
    require(bool(rows), f"{metric}: no saved rows")
    values = defaultdict(list)
    for row in rows:
        require(isinstance(row, dict), f"{metric}: malformed row")
        require(row.get("node_loc") == "Westeros", f"{metric}: unexpected node")
        tech = row.get("technology")
        require(tech in TECHNOLOGIES, f"{metric}: unexpected technology {tech!r}")
        rawyear = row.get(year_key)
        require(type(rawyear) in (str, int) and str(rawyear).isdigit(), f"{metric}: invalid year")
        year = int(rawyear)
        if metric == "ACT":
            require(row.get("time") == "year", "ACT: subannual activity cannot be summed without duration weights")
            require(row.get("mode") == "standard", "ACT: unexpected operating mode")
        if year in YEARS:
            values[(metric, tech, year)].append(number(row.get("lvl"), metric))
        else:
            # Historical records outside this model horizon are not compared.
            require(year == 690, f"{metric}: unexpected model year {year}")
    require(bool(values), f"{metric}: no model-horizon data")
    result = {}
    for key, components in values.items():
        total = math.fsum(components)
        require(math.isfinite(total), f"{metric}: aggregate overflow")
        result[key] = total
    return result


def _optional_indexed(scenario, kind, name):
    checker = getattr(scenario, f"has_{kind}", None)
    if callable(checker) and not checker(name):
        return None
    method = getattr(scenario, kind, None)
    if method is None:
        return None
    try:
        return method(name)
    except KeyError:
        return None


def _raw_optional_rows(obj, label, *, value_key):
    """Preserve the exact recorded indices; do not add overlapping emission types."""
    if obj is None:
        return {"status": "NOT_AVAILABLE", "records": []}
    out = []
    for row in records(obj, label):
        require(isinstance(row, dict), f"{label}: unexpected row type")
        entry = {}
        for field, value in row.items():
            require(isinstance(field, str) and field.isidentifier(), f"{label}: invalid column name")
            if field in ("lvl", "mrg", "value"):
                entry[field] = number(value, f"{label}.{field}")
            elif field in ("year", "year_act", "year_vtg"):
                require(str(value).isdigit(), f"{label}: invalid year")
                entry[field] = int(value)
            elif field == "unit" or isinstance(value, str):
                require(isinstance(value, str) and len(value) <= 120, f"{label}: unexpected text")
                entry[field] = value
            else:
                raise WesterosAnalysisError(f"{label}: unexpected field {field}")
        require(value_key in entry, f"{label}: missing {value_key}")
        out.append(entry)
    return {"status": "AVAILABLE" if out else "EMPTY", "records": out}


def scenario_snapshot(scenario, stage, expected):
    """Read only solved variables; the exact saved scenario version is selected."""
    require(stage in STAGES, "Unknown stage")
    require(scenario.has_solution(), f"{stage}: no persisted solution")
    require(scenario.version == expected["version"], f"{stage}: wrong scenario version")
    obj = objective_level(scenario.var("OBJ"), stage)
    require(math.isclose(obj, expected["objective_native"], rel_tol=1e-7, abs_tol=1e-3),
            f"{stage}: saved objective differs from successful manifest")
    metrics = {}
    for metric in MEASURES:
        data = _optional_indexed(scenario, "var", metric)
        require(data is not None, f"{stage}: missing {metric} variable")
        metrics[metric] = reduce_metric(data, metric)
    bound = _raw_optional_rows(_optional_indexed(scenario, "par", "bound_emission"),
                               "bound_emission", value_key="value") if stage == "emission_bound" else {
                                   "status": "NOT_MODELED_IN_BASELINE", "records": []}
    emissions = _raw_optional_rows(_optional_indexed(scenario, "var", "EMISS"),
                                   "EMISS", value_key="lvl") if stage == "emission_bound" else {
                                       "status": "NOT_MODELED_IN_BASELINE", "records": []}
    equation = _raw_optional_rows(_optional_indexed(scenario, "equ", "EMISSION_CONSTRAINT"),
                                  "EMISSION_CONSTRAINT", value_key="lvl") if stage == "emission_bound" else {
                                      "status": "NOT_MODELED_IN_BASELINE", "records": []}
    return {"scenario": stage, "version": scenario.version, "objective_native": obj,
            "metrics": metrics, "bound_emission": bound, "EMISS": emissions,
            "EMISSION_CONSTRAINT": equation}


def compare_snapshots(snapshots, run_id):
    """Never silently replace absent solved groups with zero."""
    require(set(snapshots) == set(STAGES), "Need exactly the two expected solved scenarios")
    for stage, s in snapshots.items():
        require(s["scenario"] == stage, "Scenario mismatch")
    obj_a = number(snapshots["baseline"]["objective_native"], "baseline.OBJ")
    obj_b = number(snapshots["emission_bound"]["objective_native"], "emission_bound.OBJ")
    require(obj_a != 0, "Zero baseline objective prevents percentage comparison")
    change = obj_b - obj_a
    require(math.isfinite(change), "Objective change overflow")
    out_rows = []
    for metric in MEASURES:
        baseline = snapshots["baseline"]["metrics"][metric]
        bounded = snapshots["emission_bound"]["metrics"][metric]
        for tec in TECHNOLOGIES:
            for year in YEARS:
                k = (metric, tec, year)
                a, b = baseline.get(k), bounded.get(k)
                if a is None and b is None:
                    continue
                # Missing groups are genuinely unobserved, not zero.
                out_rows.append({"metric": metric, "technology": tec, "year": year,
                                 "baseline": a, "emission_bound": b,
                                 "delta": None if a is None or b is None else b - a,
                                 "comparison": "PAIRED" if a is not None and b is not None
                                               else "MISSING_IN_ONE_SCENARIO"})
    require(any(r["metric"] == "ACT" and r["comparison"] == "PAIRED" for r in out_rows),
            "No comparable technology activity was stored")
    return {
        "schema": "residualpathways.westeros.analysis.v1",
        "status": "LOCAL_STORED_IXMP_ANALYSIS",
        "scientific_scope": "EDUCATIONAL_MESSAGEIX_GAMS_NOT_AR6",
        "run_id": run_id,
        "years": list(YEARS),
        "technologies": list(TECHNOLOGIES),
        "objective": {"baseline": obj_a, "emission_bound": obj_b,
                      "difference_native": change, "change_percent": change / obj_a * 100},
        "comparisons": out_rows,
        "emissions_bound": {
            "baseline_emissions": "NOT_MODELED_IN_BASELINE",
            "bounded_emissions": snapshots["emission_bound"]["EMISS"],
            "bound_parameter": snapshots["emission_bound"]["bound_emission"],
            "constraint_equation": snapshots["emission_bound"]["EMISSION_CONSTRAINT"],
            "binding_status": "NOT_ESTABLISHED",
            "shadow_price_status": "NOT_ESTABLISHED",
            "interpretation": "Raw EMISS types can overlap; never add across type_tec. A bound_emission multi-period label is an average-annual constraint per MESSAGEix formulation, not automatically a cumulative total. Equation marginals, if saved, are unconverted raw solver records, not certified prices.",
        },
        "method": "ACT aggregates observed vintage/mode rows for the single annual time slice; CAP aggregates observed vintages; CAP_NEW is annualized installed capacity decision; missing domain tuples remain missing, not inferred zero.",
        "assertions_not_made": ["baseline CO2 reduction", "binding emission cap", "carbon shadow price",
                                "independent solver reproduction", "AR6 gross/net/CDR decomposition"],
    }


def svg_chart(summary, metric):
    """Portable zero-dependency, two-series SVG, with no guessed units."""
    from .messageix_westeros import UPSTREAM_RELEASE
    require(metric in MEASURES, "Unexpected metric chart")
    rows = [r for r in summary["comparisons"] if r["metric"] == metric and r["comparison"] == "PAIRED"]
    rows = sorted(rows, key=lambda r: (r["year"], TECHNOLOGIES.index(r["technology"])))
    if not rows:
        return None
    vmax = max(abs(v) for r in rows for v in (r["baseline"], r["emission_bound"]))
    vmax = max(vmax, 1e-12)
    width, barwidth = 920, 540
    height = 135 + len(rows) * 44
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(metric)} scenario comparison">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="24" y="29" font-family="sans-serif" font-size="18" font-weight="bold">{escape(metric)} — Westeros, native model values</text>',
             '<text x="24" y="51" font-family="sans-serif" font-size="12" fill="#555">Blue: baseline; orange: emissions-bound. Paired saved rows only; no missing=zero assumption.</text>',
             '<rect x="26" y="65" width="13" height="11" fill="#2864a5"/><text x="44" y="75" font-family="sans-serif" font-size="12">Baseline</text>',
             '<rect x="140" y="65" width="13" height="11" fill="#ca6920"/><text x="158" y="75" font-family="sans-serif" font-size="12">Emissions-bound</text>']
    for i, row in enumerate(rows):
        y = 100 + i * 44
        label = f'{row["year"]} · {row["technology"]}'
        a, b = row["baseline"], row["emission_bound"]
        # All three plotted Westeros variables are nonnegative by core model
        # semantics; do not depict a negative against a misleading 0-left axis.
        require(a >= -1e-8 and b >= -1e-8, f"{metric}: negative level not supported by chart")
        aw = max(0, a) / vmax * barwidth
        bw = max(0, b) / vmax * barwidth
        parts.extend([
            f'<text x="24" y="{y+11}" font-family="sans-serif" font-size="12">{escape(label)}</text>',
            f'<rect x="197" y="{y}" width="{aw:.2f}" height="13" fill="#2864a5"/>',
            f'<rect x="197" y="{y+16}" width="{bw:.2f}" height="13" fill="#ca6920"/>',
            f'<text x="749" y="{y+11}" font-family="monospace" font-size="11">{a:.4g}</text>',
            f'<text x="749" y="{y+27}" font-family="monospace" font-size="11">{b:.4g}</text>',
        ])
    parts.append(f'<text x="24" y="{height-13}" font-family="sans-serif" font-size="11" fill="#555">Pinned MESSAGEix {escape(UPSTREAM_RELEASE)} educational tutorial · comparison is not externally reviewed</text>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def report_md(data):
    obj = data["objective"]
    lines = [
        "# Westeros technology response to an emissions bound",
        "", "**Locally read from saved ixmp; no GAMS solve performed by this analysis command.**",
        "", "## Objective", "",
        f"- Baseline saved OBJ: **{obj['baseline']:.6f}** (native units)",
        f"- Emissions-bound saved OBJ: **{obj['emission_bound']:.6f}** (native units)",
        f"- Difference: **{obj['difference_native']:.6f}** (**{obj['change_percent']:.4f}%**)",
        "", "## Technology activity, installed capacity, and new-capacity decisions",
        "", "Comparable saved rows (values in native model units, not standardized to MWh or GW by this report):", "",
        "| Variable | Technology | Year | Baseline | Bound | Difference |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in data["comparisons"]:
        def fmt(v):
            return "not stored" if v is None else f"{v:.6g}"
        lines.append(f"| {r['metric']} | {r['technology']} | {r['year']} | {fmt(r['baseline'])} | {fmt(r['emission_bound'])} | {fmt(r['delta'])} |")
    lines.extend([
        "", "## Emissions and the binding question", "",
        "- The baseline tutorial **does not define CO2 emission accounting**. Therefore no baseline CO2 counterfactual or percentage reduction is inferred.",
        "- For the emissions-bound case, raw bound parameters, EMISS values and any saved EMISSION_CONSTRAINT levels/marginals are preserved in summary.json with their indices.",
        "- The constraint's binding status and shadow-price interpretation are **NOT_ESTABLISHED**. A raw equation marginal is not yet a validated carbon price.",
        "- Multi-period bound_emission is normalized by summed period durations in the published MESSAGEix core equation; the tutorial's 'cumulative' category is not enough to call the 500 bound a physical multi-decade cumulative total.",
        "", "## Method and limitations", "",
        "- ACT is aggregated by technology and active year over vintages/modes for the annual 'year' timeslice. CAP sums installed capacity across vintages; CAP_NEW reflects an annualized new-capacity decision.",
        "- Only directly stored model-horizon tuples are compared. Missing values are **not** replaced by zero, and no unseen technologies are invented.",
        "- OBJ values are those persisted by ixmp (single-precision rounding may differ from solver console).",
        "- This is a small educational Westeros model, not MESSAGEix-GLOBIOM, AR6 data, physical gross/net/CDR accounting, real-world prices, or an independent scientific audit.",
        "", "See: https://docs.messageix.org/en/v3.11.1/model/MESSAGE/model_core.html", "",
    ])
    return "\n".join(lines)


def analyze_run(private_manifest, output_dir):
    """Analyze an exact local run directory, writing derived-only results."""
    import ixmp
    import message_ix
    private_manifest = Path(private_manifest).resolve()
    require(private_manifest.name == "manifest.private.json", "Expected local private manifest")
    require(private_manifest.is_file(), "Private manifest missing")
    require(private_manifest.stat().st_size < 1_000_000, "Private manifest unexpectedly large")
    private = json.loads(private_manifest.read_text(encoding="utf-8"))
    evidence = evidence_from_private_manifest(private)
    run_dir = private_manifest.parent
    require((run_dir / "ixmp_config" / "config.json").is_file(), "Private ixmp config is missing")
    require((run_dir / "ixmp_database" / "westeros.properties").is_file()
            or (run_dir / "ixmp_database" / "westeros.script").is_file(),
            "Private HSQLDB database not found")
    output_dir = Path(output_dir).resolve()
    require(output_dir != run_dir and run_dir not in output_dir.parents,
            "Refusing to write analysis into original private run")
    require(private_manifest not in output_dir.parents, "Invalid output directory")
    expected = {r["scenario"]: r for r in private["solved_scenarios"]}
    snapshots = {}
    with temporary_environment({"IXMP_DATA": run_dir / "ixmp_config"}):
        mp = ixmp.Platform()
        try:
            for stage in STAGES:
                # Specify the saved version: do not use a changing default.
                s = message_ix.Scenario(mp, model=MODEL, scenario=stage,
                                        version=expected[stage]["version"])
                snapshots[stage] = scenario_snapshot(s, stage, expected[stage])
        finally:
            mp.close_db()
    summary = compare_snapshots(snapshots, evidence["source_run_id"])
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    def write(name, raw):
        p = output_dir / name
        p.write_bytes(raw)
        paths[name] = sha256(raw).hexdigest()
    write("summary.json", (json.dumps(summary, sort_keys=True, indent=2, allow_nan=False)+"\n").encode())
    csvcols = ("metric", "technology", "year", "baseline", "emission_bound", "delta", "comparison")
    from io import StringIO
    buf = StringIO(newline="")
    cw = csv.DictWriter(buf, fieldnames=csvcols, lineterminator="\n")
    cw.writeheader()
    cw.writerows(summary["comparisons"])
    write("technology_comparison.csv", buf.getvalue().encode("utf-8"))
    write("report.md", report_md(summary).encode("utf-8"))
    for metric in MEASURES:
        svg = svg_chart(summary, metric)
        if svg:
            write(f"{metric.lower()}_comparison.svg", svg.encode("utf-8"))
    manifest = {"schema": "residualpathways.westeros.analysis.files.v1",
                "scope": "LOCAL_DERIVED_IXMP_ANALYSIS_NO_NEW_GAMS_SOLVE",
                "run_id": evidence["source_run_id"], "files_sha256": paths}
    (output_dir / "analysis_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return summary, manifest
