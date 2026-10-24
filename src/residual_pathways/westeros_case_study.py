"""Derived-only Westeros three-scenario report; never runs GAMS or reads ixmp."""
from __future__ import annotations

from hashlib import sha256
from html import escape
from io import StringIO
from pathlib import Path
import csv
import json
import math
import re

from .westeros_analysis import MEASURES, TECHNOLOGIES, YEARS, require
from .westeros_no_cap import CONTROL_NAME, PARITY_PARS

SCENARIOS = ("baseline", CONTROL_NAME, "emission_bound")
UPSTREAM_COMMIT = "2d521407a430a08de997a771e7b38d88f7e7d2b6"


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _read(path):
    p = Path(path).resolve()
    require(p.is_file() and 0 < p.stat().st_size < 2_000_000, "Invalid input file")
    raw = p.read_bytes()
    try:
        doc = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                         parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
    except (UnicodeError, ValueError) as exc:
        raise ValueError("Source JSON is malformed or non-finite") from exc
    require(type(doc) is dict, "Source must be a JSON object")
    return doc, sha256(raw).hexdigest(), p


def _number(value, label):
    require(type(value) in (float, int) and math.isfinite(value),
            f"Non-numeric or nonfinite {label}")
    return float(value)


def _eq(a, b, tolerance=1e-6):
    return abs(a - b) <= tolerance


def validate_case_study(source, cap):
    """Independently recompute claims from the stored comparison rows."""
    require(source.get("schema") == "residualpathways.westeros.control_comparison.v1",
            "Unsupported control input schema")
    require(source.get("status") == "ACTUAL_MESSAGEIX_GAMS_CONTROL_SOLVED",
            "No successful saved control solve")
    require(source.get("scientific_scope") == "EDUCATIONAL_WESTEROS_NOT_AR6",
            "Incorrect scientific scope")
    require(source.get("provenance") == "AUTHOR_LOCAL_GAMS_NOT_INDEPENDENTLY_REPRODUCED",
            "Unsupported evidence provenance")
    require(source.get("control_scenario") == CONTROL_NAME, "Wrong control scenario")
    require(source.get("intervention") ==
            "remove exactly one emissions bound; retain CO2 emissions accounting",
            "Wrong intervention")
    require(type(source.get("control_version")) is int and source["control_version"] > 0,
            "Invalid saved control version")
    run_id = source.get("source_run_id")
    require(type(run_id) is str and re.fullmatch(
        r"[0-9]{8}T[0-9]{6}Z_[0-9a-f]{8}", run_id), "Unrecognized source run ID")
    parity = source.get("verified_inputs")
    require(type(parity) is dict and parity.get("source_cap_rows") == 1 and
            parity.get("control_cap_rows") == 0 and
            parity.get("only_intended_change") == "bound_emission parameter rows removed",
            "Model input parity gate incomplete")
    verified_counts = parity.get("parameter_rows_verified")
    require(type(verified_counts) is dict and set(PARITY_PARS).issubset(verified_counts),
            "Missing source/control parameter comparisons")
    require(all(type(verified_counts[p]) is int and verified_counts[p] >= 0
                for p in PARITY_PARS) and verified_counts["emission_factor"] > 0,
            "Invalid input parity row counts")

    objectives = source.get("objectives_native")
    require(type(objectives) is dict and set(objectives) == set(SCENARIOS),
            "Three scenario objectives required")
    obj = {s: _number(objectives[s], s) for s in SCENARIOS}
    baseline, control, bounded = [obj[s] for s in SCENARIOS]
    require(baseline > 0 and control > 0 and bounded > control,
            "Unexpected objective signs")
    require(_eq(baseline, control, .001),
            "Control objective does not match unbounded baseline")
    effect = bounded - control
    require(_eq(effect, _number(source["cap_effect"]["difference_native"], "cap effect"),
                1e-4) and
            _eq(100 * effect / control,
                _number(source["cap_effect"]["relative_percent"], "relative cap effect"),
                1e-5) and source["cap_effect"]["attributable_to_bound_only"] is True,
            "Incorrect source cap-effect comparison")
    require(_eq(control - baseline,
                _number(source["baseline_vs_control"]["difference"],
                        "baseline/control difference"), 1e-5) and
            source["baseline_vs_control"]["numerically_equivalent"] is True,
            "Baseline/control gate inconsistent")

    incoming_rows = source.get("comparisons")
    require(type(incoming_rows) is list and
            len(incoming_rows) == len(MEASURES) * len(TECHNOLOGIES) * len(YEARS),
            "Exactly 36 complete model rows required")
    rows = []
    seen = set()
    for row in incoming_rows:
        require(type(row) is dict and row.get("complete") is True,
                "Incomplete technology comparison")
        metric, tech, year = row.get("metric"), row.get("technology"), row.get("year")
        require(metric in MEASURES and tech in TECHNOLOGIES and
                type(year) is int and year in YEARS,
                "Invalid metric/technology/year")
        key = (metric, tech, year)
        require(key not in seen, "Duplicate technology/model year")
        seen.add(key)
        vals = {s: _number(row.get(s), f"{key}/{s}") for s in SCENARIOS}
        require(all(v >= -1e-8 for v in vals.values()),
                "Unphysical negative output")
        for field, computed in [
            ("control_minus_baseline", vals[CONTROL_NAME] - vals["baseline"]),
            ("cap_minus_control", vals["emission_bound"] - vals[CONTROL_NAME]),
        ]:
            require(_eq(_number(row.get(field), field), computed),
                    f"Wrong saved delta for {key}")
        rows.append({"metric": metric, "technology": tech, "year": year, **vals,
                     "control_minus_baseline": vals[CONTROL_NAME] - vals["baseline"],
                     "cap_minus_control": vals["emission_bound"] - vals[CONTROL_NAME]})
    rows.sort(key=lambda r: (tuple(MEASURES).index(r["metric"]),
                             r["year"], TECHNOLOGIES.index(r["technology"])))
    activity = [r for r in rows if r["metric"] == "ACT"]
    require(all(_eq(r["baseline"], r[CONTROL_NAME], 1e-5) for r in activity),
            "Control ACT values do not match baseline")
    parity_by_metric = {
        metric: all(_eq(r["baseline"], r[CONTROL_NAME], 1e-5)
                    for r in rows if r["metric"] == metric)
        for metric in MEASURES
    }
    generation = []
    for year in YEARS:
        look = {r["technology"]: r for r in activity
                if r["year"] == year and r["technology"] in ("coal_ppl", "wind_ppl")}
        require(set(look) == {"coal_ppl", "wind_ppl"}, "Missing power activity")
        base_total = look["coal_ppl"]["baseline"] + look["wind_ppl"]["baseline"]
        require(base_total > 0, "No source power activity")
        for scenario in SCENARIOS:
            coal = look["coal_ppl"][scenario]
            wind = look["wind_ppl"][scenario]
            require(_eq(base_total, coal + wind, 1e-4),
                    "Coal-plus-wind production changes between scenarios")
            generation.append({"year": year, "scenario": scenario,
                               "coal_GWa": coal, "wind_GWa": wind,
                               "total_GWa": coal + wind,
                               "wind_share_percent": 100 * wind / (coal + wind)})

    require(cap.get("source_run_id", cap.get("run_id")) == run_id and
            cap.get("upstream_commit") == UPSTREAM_COMMIT and
            cap.get("status") == "NUMERICALLY_SATURATED" and
            cap.get("duration_source") == "SAVED_SCENARIO_PARAMETER",
            "Emissions-cap audit is from a different run or is not confirmed")
    require(cap.get("evidence_scope") == "AUTHOR_REPORTED_LOCAL_SAVED_IXMP_EDUCATIONAL" and
            cap.get("shadow_price_status") == "NOT_ESTABLISHED",
            "Unexpected cap provenance or shadow-price claim")
    require(cap.get("periods_in_category") == list(YEARS),
            "Wrong modeled cap year category")
    duration = cap.get("period_durations")
    require(type(duration) is dict and set(duration) == set(map(str, YEARS)),
            "Incorrect saved period durations")
    require(all(_eq(_number(duration[str(y)], "period duration"), 10) for y in YEARS),
            "Incorrect saved period duration")
    cap_val = _number(cap.get("bound_value"), "cap value")
    actual = _number(cap.get("computed_average_annual"), "actual average")
    slack = _number(cap.get("slack"), "cap slack")
    tol = _number(cap.get("tolerance"), "cap tolerance")
    require(_eq(cap_val, 500) and 0 < tol <= 0.001 and
            _eq(slack, cap_val - actual) and abs(slack) <= tol and
            _eq(_number(cap.get("emission_scaling"), "scaling"), 1),
            "Emissions cap reconciliation failed")

    return {
        "schema": "residualpathways.westeros.case_study.v1",
        "status": "READY_AUTHOR_REPORTED_EDUCATIONAL_CASE_STUDY",
        "provenance": "AUTHOR_LOCAL_GAMS_NOT_INDEPENDENTLY_REPRODUCED",
        "scope": "FICTIONAL_WESTEROS_TUTORIAL_NOT_AR6",
        "source_run_id": run_id,
        "upstream_commit": UPSTREAM_COMMIT,
        "control_version": source["control_version"],
        "objectives_native": obj,
        "cap_effect": {"difference_native": effect, "relative_percent": 100 * effect / control},
        "baseline_control_activity_parity": True,
        "baseline_control_parity_by_metric": parity_by_metric,
        "cap_reconciliation": {
            "average_annual_MtCO2": actual, "bound_average_annual_MtCO2": cap_val,
            "slack": slack, "duration_years": {str(y): duration[str(y)] for y in YEARS},
            "carbon_shadow_price": "NOT_ESTABLISHED",
        },
        "generation": generation,
        "comparisons": rows,
    }


def generation_svg(data):
    entries = {(r["year"], r["scenario"]): r for r in data["generation"]}
    fig = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="850" height="465" viewBox="0 0 850 465">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="24" y="35" font-family="sans-serif" font-size="20">Three-scenario Westeros generation mix</text>',
        '<text x="24" y="57" font-family="sans-serif" font-size="12">Coal (grey) and wind (teal), activity in GWa</text>',
    ]
    max_total = max(r["total_GWa"] for r in entries.values())
    labels = {"baseline": "Baseline", CONTROL_NAME: "CO2 accounting only",
              "emission_bound": "CO2 cap"}
    for i, year in enumerate(YEARS):
        for j, scenario in enumerate(SCENARIOS):
            y = 88 + i * 118 + j * 31
            row = entries[(year, scenario)]
            coal_w = max(0, row["coal_GWa"]) / max_total * 445
            wind_w = max(0, row["wind_GWa"]) / max_total * 445
            fig.extend([
                f'<text x="20" y="{y+14}" font-family="sans-serif" font-size="12">{year}: {escape(labels[scenario])}</text>',
                f'<rect x="217" y="{y}" width="{coal_w:.2f}" height="19" fill="#575a61"/>',
                f'<rect x="{217+coal_w:.2f}" y="{y}" width="{wind_w:.2f}" height="19" fill="#26889b"/>',
                f'<text x="686" y="{y+14}" font-family="sans-serif" font-size="12">{row["wind_share_percent"]:.2f}% wind</text>',
            ])
    fig += [
        '<text x="20" y="451" font-family="sans-serif" font-size="11">Source: author-reported locally saved MESSAGEix solutions; educational model only</text>',
        '</svg>'
    ]
    return "\n".join(fig) + "\n"


def objective_svg(data):
    obj = data["objectives_native"]
    fig = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="760" height="330" viewBox="0 0 760 330">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="20" y="34" font-family="sans-serif" font-size="20">Objective cost of the emissions limit</text>',
        '<text x="20" y="56" font-family="sans-serif" font-size="12">Native model objective units, not currency</text>',
    ]
    mx = max(obj.values()) * 1.1
    for i, scenario in enumerate(SCENARIOS):
        value = obj[scenario]
        x = 104 + i * 217
        h = value / mx * 190
        y = 257 - h
        color = "#a4abb6" if i < 2 else "#bd682f"
        fig += [
            f'<rect x="{x}" y="{y:.3f}" width="105" height="{h:.3f}" fill="{color}"/>',
            f'<text x="{x-8}" y="{y-8:.3f}" font-family="monospace" font-size="12">{value:.2f}</text>',
            f'<text x="{x-12}" y="283" font-family="sans-serif" font-size="12">{["Baseline","CO2-only","CO2 capped"][i]}</text>',
        ]
    fig += [
        '<text x="20" y="316" font-family="sans-serif" font-size="11">Author-run educational model; independent reproduction pending</text>',
        '</svg>'
    ]
    return "\n".join(fig) + "\n"


def report(data):
    obj = data["objectives_native"]
    penalty = data["cap_effect"]
    cap = data["cap_reconciliation"]
    lines = [
        "# Isolating an emissions constraint in MESSAGEix Westeros",
        "",
        "A controlled three-scenario educational modelling case study.",
        "",
        "## Research question",
        "",
        "Does an emissions bound, rather than emissions bookkeeping, drive coal-to-wind substitution in the optimal fictional electricity system?",
        "",
        "## Experimental design",
        "",
        "| Case | CO2 bookkeeping | 500 MtCO2 average-annual cap | Native objective |",
        "|---|---|---|---:|",
        f"| Baseline | No | No | {obj['baseline']:.6f} |",
        f"| Control | Yes | No | {obj[CONTROL_NAME]:.6f} |",
        f"| Constrained | Yes | Yes | {obj['emission_bound']:.6f} |",
        "",
        f"The stored control objective equals the baseline. Imposing the cap increases the objective by **{penalty['difference_native']:.6f} native units**, or **{penalty['relative_percent']:.4f}%**.",
        "",
        "## Generation activity and substitution",
        "",
        "| Year | Case | Coal (GWa) | Wind (GWa) | Wind share |",
        "|---|---|---:|---:|---:|",
    ]
    labels = {"baseline": "Baseline", CONTROL_NAME: "CO2 only", "emission_bound": "CO2 cap"}
    for row in data["generation"]:
        lines.append(f"| {row['year']} | {labels[row['scenario']]} | {row['coal_GWa']:.6f} | {row['wind_GWa']:.6f} | {row['wind_share_percent']:.2f}% |")
    lines.extend([
        "",
        "Control activity matches the baseline across all stored ACT entries. With the cap, coal decreases while wind increases by the same amount in years 710 and 720; combined generation remains unchanged.",
        "",
        "## Capacity and investment checking",
        "",
        "Parameter parity was checked by the control solver. After rerunning validation on every saved technology-year row, the baseline/control equivalence is:",
    ])
    for key, match in data["baseline_control_parity_by_metric"].items():
        lines.append(f"- {key}: {'matches baseline' if match else 'differs; equal objective need not imply same decision variables'}")
    lines.extend([
        "",
        "## Emissions accounting",
        "",
        f"The separately saved model audit gives a duration-weighted average annual CO2 value of **{cap['average_annual_MtCO2']:.6f} MtCO2** against **{cap['bound_average_annual_MtCO2']:.6f} MtCO2**, with computed slack **{cap['slack']:.6f}**. The emissions constraint is numerically saturated.",
        "",
        "## Reproducibility and limitations",
        "",
        f"- Pinned official MESSAGEix Westeros source commit: {data['upstream_commit']}.",
        "- Three solved objectives and all 36 model-variable/technology/year pairs have been rechecked against the input JSON.",
        "- This report was generated without GAMS or ixmp from already-solved local derived results.",
        "- The objective uses native units, not EUR/USD; the cap is duration-normalized, not an unnormalized 30-year cumulative budget.",
        "- No carbon shadow price is estimated because the emissions-constraint equation marginal was unavailable.",
        "- This is a fictional tutorial, not AR6/IAMC evidence, real power-system forecasting, or independently reproduced scientific research.",
        "- Derived file SHA-256 digests establish byte integrity, not solver authenticity.",
        "",
    ])
    return "\n".join(lines)


def publish_case_study(control_path, cap_path, output_dir):
    control, control_hash, control_file = _read(control_path)
    cap, cap_hash, cap_file = _read(cap_path)
    sidecar = cap_file.parent / "cap_reconciliation.sha256"
    require(sidecar.is_file() and sidecar.read_text(encoding="ascii").strip() == cap_hash,
            "Cap audit SHA-256 mismatch or sidecar missing")
    case = validate_case_study(control, cap)
    target = Path(output_dir).resolve()
    require(target != control_file.parent and target != cap_file.parent
            and control_file.parent not in target.parents
            and cap_file.parent not in target.parents,
            "Do not write public derived files into a private input folder")
    target.mkdir(parents=True, exist_ok=True)
    outputs = {
        "case_study.json": (json.dumps(case, indent=2, sort_keys=True, allow_nan=False) + "\n").encode(),
        "case_study.md": report(case).encode(),
        "generation_mix.svg": generation_svg(case).encode(),
        "objective_comparison.svg": objective_svg(case).encode(),
    }
    buf = StringIO(newline="")
    fields = ("metric", "technology", "year", *SCENARIOS,
              "control_minus_baseline", "cap_minus_control")
    writer = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(case["comparisons"])
    outputs["technology_comparisons.csv"] = buf.getvalue().encode()
    hashes = {}
    for name, contents in outputs.items():
        (target / name).write_bytes(contents)
        hashes[name] = {"sha256": sha256(contents).hexdigest(), "bytes": len(contents)}
    manifest = {
        "schema": "residualpathways.westeros.case_study.files.v1",
        "scope": "DERIVED_ONLY_AUTHOR_REPORTED_LOCAL_EDUCATIONAL",
        "source_control_comparison_sha256": control_hash,
        "source_cap_reconciliation_sha256": cap_hash,
        "source_run_id": case["source_run_id"],
        "upstream_commit": UPSTREAM_COMMIT,
        "independently_reproduced": False,
        "files": hashes,
    }
    (target / "publication_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return case, manifest
