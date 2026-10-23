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
