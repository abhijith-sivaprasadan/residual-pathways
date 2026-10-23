"""Signed decadal IAMC observations. Never reclassify a negative reported value as gross."""
from __future__ import annotations
import csv
import json
from pathlib import Path
from .core import compare, COHORT


YEARS = tuple(range(2010, 2101, 10))


def examine(rows, years=YEARS):
    output = []
    by_year = []
    for year in years:
        cohort = compare(rows, year=year)
        for item in cohort:
            output.append(item)
        by_year.append({
            "year": year,
            "matched_observations": len(cohort),
            "negative_reported_co2_count": sum(x["value"] < 0 for x in cohort),
            "zero_reported_co2_count": sum(x["value"] == 0 for x in cohort),
            "positive_reported_co2_count": sum(x["value"] > 0 for x in cohort),
            "status": "DESCRIPTIVE_SIGN_ONLY",
        })
    return {
        "trajectory_schema": "reported_co2_decadal.v1",
        "matched_cohort": list(COHORT),
        "variable": "Emissions|CO2", "region": "World", "unit": "Mt CO2/yr",
        "years": list(years), "year_summaries": by_year, "observations": output,
        "interpretation": "The sign of reported aggregate CO2 is descriptive and cannot independently identify gross, net, or removal components.",
    }


def write_trajectory(trajectory, folder):
    target = Path(folder)
    target.mkdir(parents=True, exist_ok=True)
    (target / "decadal_trajectory.json").write_text(json.dumps(trajectory, indent=2, sort_keys=True) + "\n")
    fields = ["model", "scenario", "region", "variable", "unit", "year", "value", "meaning"]
    with (target / "decadal_trajectory.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(trajectory["observations"])
    text = ["# Decadal signed, source-reported CO2 observations", "",
            "Source: the same revision-pinned historical CD-LINKS pyam teaching dataset.",
            "Each complete three-model scenario cohort is matched by scenario, region, variable, year and unit.",
            "Negative reported Emissions|CO2 values cannot be a quantity of positive gross atmospheric emissions.",
            "Nevertheless a signed aggregate is not automatically a verified net/gross/CDR partition.", "",
            "| Year | Matched observations | Positive | Negative | Zero |",
            "|---:|---:|---:|---:|---:|"]
    for row in trajectory["year_summaries"]:
        text.append(f"| {row['year']} | {row['matched_observations']} | "
                    f"{row['positive_reported_co2_count']} | {row['negative_reported_co2_count']} | "
                    f"{row['zero_reported_co2_count']} |")
    text += ["", "This is not a causal innovation-impact estimate, not an emissions-removals decomposition, "
             "and not an AR6 ensemble finding.", ""]
    (target / "decadal_report.md").write_text("\n".join(text))
