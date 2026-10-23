"""CLI for IAMC coverage and descriptive comparison."""
import argparse
from pathlib import Path
from urllib.request import urlopen

from .core import read_iamc, build_results, write_outputs

SOURCE_REVISION = "88706bd70051ff630b73096c050e3697364e2302"
TUTORIAL_URL = f"https://raw.githubusercontent.com/IAMconsortium/pyam/{SOURCE_REVISION}/docs/tutorials/tutorial_data.csv"


def main():
    parser = argparse.ArgumentParser(description="ResidualPathways research baseline")
    sub = parser.add_subparsers(dest="command", required=True)
    get = sub.add_parser("fetch-tutorial", help="Download exact pinned public IAMC example")
    get.add_argument("--output", default="data/tutorial_data.csv")
    run = sub.add_parser("analyze", help="Validate and compare published IAMC series")
    run.add_argument("--input", required=True)
    run.add_argument("--output", default="results/tutorial")
    run.add_argument("--pyam-check", action="store_true", help="Parse using real pyam package too")
    ar6 = sub.add_parser("audit-ar6", help="Stream locally authorized AR6 World data; publish coverage only")
    ar6.add_argument("--input", required=True)
    ar6.add_argument("--candidates", default="config/ar6_variable_candidates.json")
    ar6.add_argument("--output", default="results/ar6/coverage_2050.json")
    ar6.add_argument("--year", type=int, default=2050)
    sensitivity = sub.add_parser("model-sensitivity", help="Synthetic SciPy/HiGHS optimisation; NOT MESSAGEix")
    sensitivity.add_argument("--output", default="results/model_sensitivity")
    strata = sub.add_parser("audit-ar6-strata", help="AR6 presence by metadata category; no gross claims")
    strata.add_argument("--input", required=True)
    strata.add_argument("--metadata", required=True)
    strata.add_argument("--category-column", required=True)
    strata.add_argument("--metadata-sheet", help="Explicit XLSX sheet, e.g. meta_Ch3vetted_withclimate")
    strata.add_argument("--candidates", help="JSON mapping of labels to exact IAMC variable names")
    strata.add_argument("--output", default="results/ar6/stratified_2050.json")
    strata.add_argument("--year", type=int, default=2050)
    pf = sub.add_parser("gams-preflight", help="Readiness audit only; never claims a MESSAGEix solve")
    pf.add_argument("--output", default="results/gams_preflight.json")
    args = parser.parse_args()
    if args.command == "fetch-tutorial":
        dest = Path(args.output)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with urlopen(TUTORIAL_URL, timeout=30) as response:
            raw = response.read()
        if b"Model,Scenario,Region,Variable,Unit," not in raw[:160]:
            raise SystemExit("Upstream content is not expected IAMC CSV")
        dest.write_bytes(raw)
        print(f"Downloaded pinned IAMC source to {dest}")
    elif args.command == "gams-preflight":
        from .preflight import write_preflight
        x = write_preflight(args.output)
        print(x["scientific_status"], "GAMS discovered:", x["gams_executable_discovered"])
    elif args.command == "audit-ar6-strata":
        from .stratify import run_strata
        import json
        from pathlib import Path
        names = tuple(json.loads(Path(args.candidates).read_text()).values()) if args.candidates else None
        x = run_strata(args.input, args.metadata, args.output, year=args.year, category_column=args.category_column, metadata_sheet=args.metadata_sheet, variable_names=names)
        print("Metadata-stratified World model-scenarios:", x["matched_model_scenarios"])
    elif args.command == "model-sensitivity":
        from .stylized_model import run_experiments
        r = run_experiments(args.output)
        print("Executed", len(r["results"]), "synthetic HiGHS cases (not MESSAGEix)")
    elif args.command == "audit-ar6":
        from .coverage_audit import run_audit
        result = run_audit(args.input, args.candidates, args.output, year=args.year)
        print(f"AR6-format input: {result['world_model_scenario_pairs']} World model-scenario pairs; semantic status unresolved")
    elif args.command == "analyze":
        rows, meta = read_iamc(args.input)
        if args.pyam_check:
            import pyam
            iamc = pyam.IamDataFrame(args.input)
            observed = sum(len(x["values"]) for x in rows)
            if len(iamc.data) != observed:
                raise SystemExit(f"Independent pyam parser disagrees on observations: {len(iamc.data)} vs {observed}")
            print(f"pyam independently parsed {len(iamc.data)} IAMC observations")
        result = build_results(rows, meta)
        write_outputs(result, args.output)
        print(f"Wrote {result['comparison']['matched_rows']} matched observations; I3 = 0 (insufficient reporting)")


if __name__ == "__main__":
    main()
