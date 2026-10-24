"""Build the public Residual Pathways Atlas data from already-public aggregate files.

Never reads original AR6 World scenario rows or data/ar6-private. The optional
PathwaysHub path must point to an explicit local checkout or approved public
milestone JSON. No network fetch or source-data mirroring is performed.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "derived"
OUTPUT = ROOT / "atlas" / "data" / "atlas.json"


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _number(value):
    n = float(value)
    if not math.isfinite(n):
        raise ValueError("Non-finite source data")
    return n


def _csv_rows(path):
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def assemble(previous, *, hub=None, snapshot="2026-10-24"):
    coverage = _read_json(SOURCE / "ar6_teaching_2050_summary.json")
    historical = _read_json(SOURCE / "verified_tutorial_comparison_2050.json")
    gases = _csv_rows(SOURCE / "n2o_metric_sensitivity_2050.csv")
    gap_rows = _csv_rows(SOURCE / "innovation_gap_register.csv")

    assert coverage["schema_version"] == "ar6-teaching-2050-aggregate.v1"
    assert coverage["region"] == "World" and coverage["year"] == 2050
    cats = coverage["category_coverage"]
    assert len(cats) == 8
    assert sum(int(c["n"]) for c in cats) == coverage["vetted_totals"]["scenarios"] == 1202
    assert sum(int(c["dac"]) for c in cats) == coverage["vetted_totals"]["reported_dac"] == 422
    assert sum(int(c["all_six_candidate_presence"]) for c in cats) == coverage["vetted_totals"]["co_report_six"] == 330
    assert len(historical["rows"]) == 18 and len(historical["cohort_models"]) == 3
    assert all(r["year"] == 2050 and r["region"] == "World"
               and r["variable"] == "Emissions|CO2"
               and r["unit"] == "Mt CO2/yr" for r in historical["rows"])
    assert len(gases) == len(cats) == 8 and len(gap_rows) == 12
    assert previous["schema"] == "residualpathways.atlas.public.v1"

    operations = previous["operations"]
    if hub is not None:
        h = _read_json(Path(hub))
        if (h["schema_version"] != "workstream.v1"
                or not h["milestones"]):
            raise ValueError("Incompatible PathwaysHub protocol")
        operations = {
            "source": "https://github.com/abhijith-sivaprasadan/pathways-hub/blob/main/protocols/workstream_v3.json",
            "milestones": [
                {"id": m["id"], "name": m["name"], "status": m["status"]}
                for m in h["milestones"]
            ],
            "evidence": "AUTHOR_REPORTED_REPOSITORY_STATUS",
        }
    gas_rows = [{
        "category": r["category"],
        "reporting": int(r["reporting_model_scenarios"]),
        "meanOriginal": _number(r["mean_n2o_mtco2e_2021"]),
        "meanCorrected": _number(r["mean_n2o_mtco2e_2025"]),
        "delta": _number(r["metric_delta_mtco2e"]),
    } for r in gases]
    if [r["category"] for r in gas_rows] != [c["category"] for c in cats]:
        raise ValueError("N2O source categories not aligned")
    innovations = [{
        "id": r["id"], "sector": r["sector"],
        "title": r["hypothesis_topic"], "mechanism": r["potential_mechanism"],
        "status": r["evidence_status"], "source": r["source_context_url"],
        "caution": r["scientific_caution"]
    } for r in gap_rows]
    # Do not use private AR6 case records or lift unlicensed raw scenario rows.
    # The historical CD-LINKS tutorial observations are from an independently
    # published, expressly educational source and retain that provenance.
    result = {
        "schema": "residualpathways.atlas.public.v1",
        "date": snapshot,
        "scope": "World · climate-vetted AR6 2050 coverage + historical CD-LINKS + educational Westeros",
        "evidence": "SOURCE_BACKED_AGGREGATE_COUNTS_WITH_LIMITATIONS",
        "provenance": {
            "coverageSource": coverage["world_source"]["url"],
            "coverageSha256": coverage["world_source"]["sha256"],
            "coverageStatus": coverage["source_status"],
            "metadataStatus": coverage["metadata_source"]["source_status"],
            "metadataSha256": coverage["metadata_source"]["sha256"],
            "reference": "https://github.com/abhijith-sivaprasadan/residual-pathways",
            "protocol": "https://github.com/abhijith-sivaprasadan/residual-pathways/blob/main/docs/arc24_03_physical_carbon_flow_semantic_review_20261024.md",
        },
        "totals": {
            "scenarios": coverage["vetted_totals"]["scenarios"],
            "worldScenarioPairs": coverage["world_source"]["world_model_scenario_pairs"],
            "series": coverage["world_source"]["csv_iamc_series"],
            "dac": coverage["vetted_totals"]["reported_dac"],
            "six": coverage["vetted_totals"]["co_report_six"],
            "eipLand": coverage["vetted_totals"]["co_report_eip_afolu_land_beccs_dac"],
            "verifiedI3": 0,
        },
        "categories": cats,
        "variableCounts": coverage["candidate_counts_all_source"],
        "units": coverage["observed_units"],
        "n2o": gas_rows,
        "comparison": {
            "kind": "HISTORICAL_CD_LINKS_TUTORIAL_NET_CO2_NOT_GROSS",
            "year": 2050, "unit": "Mt CO2/yr",
            "models": historical["cohort_models"],
            "scenarios": historical["common_scenarios"],
            "rows": [
                {"model": r["model"], "scenario": r["scenario"],
                 "value": r["value"]}
                for r in historical["rows"]
            ],
        },
        "innovations": innovations,
        "operations": operations,
        "westeros": previous["westeros"],
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hub", type=Path,
                        help="Optional explicit local PathwaysHub workstream_v3.json")
    parser.add_argument("--snapshot", default="2026-10-24")
    parser.add_argument("--check", action="store_true",
                        help="Validate committed public atlas JSON against source files, no write")
    args = parser.parse_args()
    previous = _read_json(OUTPUT)
    result = assemble(previous, hub=args.hub, snapshot=args.snapshot)
    if args.check:
        if result != previous:
            raise SystemExit("Atlas bundle differs from source regeneration; rerun build_data.py and review changes")
        print("Atlas source consistency: PASS")
        return
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(f"Public atlas bundle generated: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
