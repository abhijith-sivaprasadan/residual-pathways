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
    cases = sub.add_parser("case-audit", help="Source-backed 24-case preflight; no I3 claim")
    cases.add_argument("--input", required=True)
    cases.add_argument("--metadata", required=True)
    cases.add_argument("--metadata-sheet", default="meta_Ch3vetted_withclimate")
    cases.add_argument("--candidates", default="config/ar6_variable_candidates.json")
    cases.add_argument("--public-output", default="results/ar6-teaching-pilot/case_audit_24_public.json")
    cases.add_argument("--private-output", default="data/ar6-private/case_audit_review_packet.json")
    cases.add_argument("--year", type=int, default=2050)
    canonical = sub.add_parser("ar6-canonical-gate", help="Hash local official v1.1 files and compare 24 teaching-source cases; NEVER certifies origin or I3")
    canonical.add_argument("--world", required=True, help="Locally downloaded official World v1.1 CSV")
    canonical.add_argument("--metadata", required=True, help="Locally downloaded official metadata workbook")
    canonical.add_argument("--packet", default="data/ar6-private/case_audit_review_packet.json", help="Original private RP24 teaching-source review packet")
    canonical.add_argument("--public-output", default="results/ar6-canonical-gate/summary_public.json")
    canonical.add_argument("--private-output", default="data/ar6-private/canonical_rp24_review.json")
    canonical_select = sub.add_parser("ar6-canonical-select", help="Select a fresh 24-case cohort directly from local official-named v1.1 files; no teaching packet needed")
    canonical_select.add_argument("--world", required=True, help="User-downloaded IIASA World v1.1 CSV")
    canonical_select.add_argument("--metadata", required=True, help="User-downloaded IIASA metadata v1.1 XLSX")
    canonical_select.add_argument("--public-output", default="results/ar6-canonical-gate/selected24_public.json")
    canonical_select.add_argument("--private-output", default="data/ar6-private/canonical_selected24_packet.json")
    sign_screen = sub.add_parser("arc24-sign-screen", help="Read-only signs and accounting risk warnings for local 24-case data; no I3 claims")
    sign_screen.add_argument("--packet", default="data/ar6-private/canonical_selected24_packet.json")
    sign_screen.add_argument("--output", default="results/ar6-canonical-gate/arc24_sign_screen_public.json")
    aa = sub.add_parser("arc24-arithmetic", help="Check exact published decimal total-CO2=EIP+net-AFOLU arithmetic; private numerical residuals, NO I3")
    aa.add_argument("--packet", default="data/ar6-private/canonical_selected24_packet.json")
    aa.add_argument("--public-output", default="results/ar6-canonical-gate/arc24_arithmetic_public.json")
    aa.add_argument("--private-output", default="data/ar6-private/arc24_arithmetic_private.json")
    tl = sub.add_parser("arc24-poles-timeline", help="Check four POLES source cases at 2030/2040/2050/2060/2070; public bands only, no I3")
    tl.add_argument("--world", default="data/ar6-private/AR6_Scenarios_Database_World_v1.1.csv")
    tl.add_argument("--packet", default="data/ar6-private/canonical_selected24_packet.json")
    tl.add_argument("--output", default="results/ar6-canonical-gate/arc24_poles_timeline_public.json")
    oc = sub.add_parser("arc24-poles-optional-co2", help="Screen four POLES AR6 cases for optional Other/Waste/Capture/Product CO2 series; no accounting adjustment")
    oc.add_argument("--world", default="data/ar6-private/AR6_Scenarios_Database_World_v1.1.csv")
    oc.add_argument("--packet", default="data/ar6-private/canonical_selected24_packet.json")
    oc.add_argument("--output", default="results/ar6-canonical-gate/arc24_poles_optional_co2_public.json")
    oi = sub.add_parser("arc24-poles-other-identity", help="Check if CO2 Other equals the reported total-EIP-net-AFOLU residual in four source-locked POLES cases; no I3")
    oi.add_argument("--world", default="data/ar6-private/AR6_Scenarios_Database_World_v1.1.csv")
    oi.add_argument("--packet", default="data/ar6-private/canonical_selected24_packet.json")
    oi.add_argument("--output", default="results/ar6-canonical-gate/arc24_poles_other_identity_public.json")
    em = sub.add_parser("arc24-poles-eip-mapping", help="Compare expanded ENGAGE source CO2 hierarchy to combined EIP in four POLES scenarios; redacted, no I3")
    em.add_argument("--world", default="data/ar6-private/AR6_Scenarios_Database_World_v1.1.csv")
    em.add_argument("--packet", default="data/ar6-private/canonical_selected24_packet.json")
    em.add_argument("--output", default="results/ar6-canonical-gate/arc24_poles_eip_mapping_public.json")
    cx = sub.add_parser("arc24-cemics-crosswalk", help="Source-locked CEMICS v2 author's AR6-aligned dataset versus ARC24-03; no gross/CDR I3 claim")
    cx.add_argument("--mif", default="data/ar6-private/cemics-v2/CDRoptionsAR6_complete.mif")
    cx.add_argument("--world", default="data/ar6-private/AR6_Scenarios_Database_World_v1.1.csv")
    cx.add_argument("--packet", default="data/ar6-private/canonical_selected24_packet.json")
    cx.add_argument("--rmd", default="data/ar6-private/cemics-v2/CDRoptions.Rmd")
    cx.add_argument("--readme", default="data/ar6-private/cemics-v2/readme_zenodo.txt")
    cx.add_argument("--output", default="results/ar6-canonical-gate/arc24_cemics_source_crosswalk_public.json")
    ni = sub.add_parser("arc24-cemics-names", help="Read authors' checksum-locked MIF Model/Scenario name inventory without implying exact ARC24-03 provenance")
    ni.add_argument("--mif", default="data/ar6-private/cemics-v2/CDRoptionsAR6_complete.mif")
    ni.add_argument("--rmd", default="data/ar6-private/cemics-v2/CDRoptions.Rmd")
    ni.add_argument("--output", default="results/ar6-canonical-gate/arc24_cemics_name_inventory_public.json")
    fp = sub.add_parser("arc24-cemics-alias-fingerprint", help="Compare archive noCDR/AR6 minCDR using fullCDR positive and swapped negative controls; source SHA/MD5 locked, no I3")
    fp.add_argument("--mif", default="data/ar6-private/cemics-v2/CDRoptionsAR6_complete.mif")
    fp.add_argument("--world", default="data/ar6-private/AR6_Scenarios_Database_World_v1.1.csv")
    fp.add_argument("--packet", default="data/ar6-private/canonical_selected24_packet.json")
    fp.add_argument("--rmd", default="data/ar6-private/cemics-v2/CDRoptions.Rmd")
    fp.add_argument("--output", default="results/ar6-canonical-gate/arc24_cemics_alias_fingerprint_public.json")
    ac = sub.add_parser("arc24-cemics-author-accounting", help="Evaluate source-verified 2050 original author CDRtotal and CO2pos definitions; compare distinct gross fossil-industry scope, no I3")
    ac.add_argument("--mif", default="data/ar6-private/cemics-v2/CDRoptionsAR6_complete.mif")
    ac.add_argument("--world", default="data/ar6-private/AR6_Scenarios_Database_World_v1.1.csv")
    ac.add_argument("--packet", default="data/ar6-private/canonical_selected24_packet.json")
    ac.add_argument("--rmd", default="data/ar6-private/cemics-v2/CDRoptions.Rmd")
    ac.add_argument("--output", default="results/ar6-canonical-gate/arc24_cemics_author_accounting_public.json")
    fl = sub.add_parser("arc24-cemics-field-lineage", help="Trace original author Rmd deletePlus regrowth and gross variable name keys across verified original MIF/World without numbers")
    fl.add_argument("--mif", default="data/ar6-private/cemics-v2/CDRoptionsAR6_complete.mif")
    fl.add_argument("--world", default="data/ar6-private/AR6_Scenarios_Database_World_v1.1.csv")
    fl.add_argument("--packet", default="data/ar6-private/canonical_selected24_packet.json")
    fl.add_argument("--rmd", default="data/ar6-private/cemics-v2/CDRoptions.Rmd")
    fl.add_argument("--output", default="results/ar6-canonical-gate/arc24_cemics_field_lineage_public.json")
    robustness = sub.add_parser("cohort-robustness", help="Year/category/model-label reporting fractions")
    robustness.add_argument("--input", required=True)
    robustness.add_argument("--metadata", required=True)
    robustness.add_argument("--metadata-sheet", default="meta_Ch3vetted_withclimate")
    robustness.add_argument("--candidates", default="config/ar6_variable_candidates.json")
    robustness.add_argument("--output", default="results/ar6-teaching-pilot/robustness_4years.json")
    gases = sub.add_parser("nonco2-pilot", help="Gas coverage and IPCC N2O GWP100 version sensitivity")
    gases.add_argument("--input", required=True)
    gases.add_argument("--metadata", required=True)
    gases.add_argument("--metadata-sheet", default="meta_Ch3vetted_withclimate")
    gases.add_argument("--output", default="results/ar6-teaching-pilot/nonco2_2050.json")
    gases.add_argument("--year", type=int, default=2050)
    pyomo = sub.add_parser("validate-pyomo", help="Run independent Pyomo formulation; synthetic HiGHS not MESSAGEix")
    pyomo.add_argument("--output", default="results/pyomo_validation.json")
    brief = sub.add_parser("publish-brief",help="Generate derived coverage figure and policy brief")
    brief.add_argument("--output",default="results/communication")
    westeros = sub.add_parser("westeros-validate", help="ACTUALLY solve pinned Westeros with user's GAMS license")
    westeros.add_argument("--output", default="results/messageix_westeros")
    wsrc = sub.add_parser("westeros-source-check", help="Hash-check official notebook sources without licensed solves")
    wsrc.add_argument("--output", default="results/messageix_source_check")
    wexport = sub.add_parser("westeros-export", help="Export allowlisted local solve metadata to PathwaysHub")
    wexport.add_argument("--input", required=True, help="Exact private manifest.private.json from a successful run")
    wexport.add_argument("--output", default="results/westeros_handoff")
    wanalyze = sub.add_parser("westeros-analyze", help="Analyze saved Westeros ixmp variables without a new GAMS solve")
    wanalyze.add_argument("--manifest", required=True, help="Original successful local manifest.private.json")
    wanalyze.add_argument("--output", default="results/westeros_analysis")
    capcheck = sub.add_parser("westeros-cap-check", help="Reconcile stored CO2 emissions with duration-weighted bound without a new solve")
    capcheck.add_argument("--manifest", required=True, help="Successful private manifest from saved two-scenario run")
    capcheck.add_argument("--output", default="results/westeros_cap_check")
    control = sub.add_parser("westeros-no-cap-control", help="Solve one isolated CO2-accounting control without the emissions cap")
    control.add_argument("--manifest", required=True, help="Successful original private two-scenario manifest")
    control.add_argument("--output", default="results/westeros_control_private")
    study = sub.add_parser("westeros-case-study", help="Publish validated derived-only three-scenario figures/report (no GAMS)")
    study.add_argument("--control-json", required=True, help="Successful private three_case_comparison.json")
    study.add_argument("--cap-json", required=True, help="Saved cap_reconciliation.json plus adjacent SHA-256")
    study.add_argument("--output", default="results/westeros_case_study")
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
    elif args.command == "publish-brief":
        from .communication import write_communication
        r=write_communication(Path("."),args.output)
        print("Published derived-only source-locked brief:",r["figure_sha256"])
    elif args.command == "validate-pyomo":
        from .pyomo_validation import verify_all
        r=verify_all(args.output)
        print("Independent Pyomo/SciPy algebra crosscheck:",len(r["cases"]),"agreements")
    elif args.command == "nonco2-pilot":
        from .nonco2_pilot import run_nonco2
        r=run_nonco2(args.input,args.metadata,args.output,year=args.year,sheet=args.metadata_sheet)
        print("Gas-specific class rows:",len(r["classes"]),"no methane origin invented")
    elif args.command == "cohort-robustness":
        from .cohort_robustness import write_robustness
        r=write_robustness(args.input,args.metadata,args.candidates,args.output,
                           sheet=args.metadata_sheet)
        print("Robustness rows:",len(r["records"]),"source-matched scenarios:",r["matched_source_scenarios"])
    elif args.command == "westeros-source-check":
        from .westeros import source_preflight
        result = source_preflight(args.output)
        print("Verified pinned official notebook inputs (NO GAMS SOLVE):", result["status"])
    elif args.command == "westeros-export":
        from .westeros_evidence import export_westeros_evidence
        index = export_westeros_evidence(args.input, args.output)
        print("Sanitized local-evidence export created (NOT independently attested).")
        print("Artifact SHA-256:", index["artifact_sha256"])
        print("Output:", Path(args.output).resolve())
    elif args.command == "arc24-cemics-field-lineage":
        from .arc24_cemics_field_lineage import inventory
        result = inventory(args.mif, args.world, args.packet,
                           args.rmd, args.output)
        print("CEMICS original-source field names:", result["status"])
        for branch in ("original_author_fields", "original_ar6_fields"):
            print(branch)
            for term in result[branch]:
                print(term["requested_postprocessed_rmd_name"],
                      "exact:", term["raw_exact_name_present"],
                      "hierarchy candidates:",
                      term["marker_candidate_count"])
        print("No substitution or derived CDR; I3:", result["verified_i3"])
    elif args.command == "arc24-cemics-author-accounting":
        from .arc24_cemics_author_accounting import derive_source_worksheet
        result = derive_source_worksheet(args.mif, args.world, args.packet,
                                         args.rmd, args.output)
        print("Author CEMICS 2050 formula study:", result["status"])
        print("Operational source CDR identity:",
              result["operational_study_accounting"]["status"])
        print("Unverified operational source terms:",
              result["operational_study_accounting"]["missing_or_unverified_operational_terms"])
        print("CO2pos versus independent gross fossil+industry:",
              result["study_CO2pos_vs_separate_gross_fossil_industry"]["status"])
        print("Verified physical I3:", result["verified_i3"])
    elif args.command == "arc24-cemics-alias-fingerprint":
        from .arc24_cemics_alias_fingerprint import write_author_alias_fingerprints
        result = write_author_alias_fingerprints(
            args.mif, args.world, args.packet, args.output, rmd=args.rmd)
        print("CEMICS source alias hypothesis:", result["status"])
        for item in result["comparisons"]:
            print(item["comparison"], "shared variables:",
                  item["shared_variable_names"], "case-year checks:",
                  item["year_variable_compared"], "exact:",
                  item["exact_decimal_matches"])
        print("Alias independently verified:", result["scientific_source_alias_verified"])
        print("Verified I3:", result["verified_i3"])
    elif args.command == "arc24-cemics-names":
        from .arc24_cemics_name_inventory import inspect_source_names
        result = inspect_source_names(args.mif, args.output, rmd_path=args.rmd)
        print("CEMICS source identity inventory:", result["status"])
        print("Archive Model labels:", result["distinct_models"])
        print("Archive Scenario labels:", result["distinct_scenarios"])
        print("Normalized scenario matches:", len(result["normalized_scenario_matches"]))
        print("CEMICS/SSP1/CDR candidate Model+Scenario pairs:",
              result["cemics_ssp1_cdr_candidate_pair_count"])
        print("No scenario alias has been verified; I3:", result["verified_i3"])
    elif args.command == "arc24-cemics-crosswalk":
        from .arc24_cemics_crosswalk import crosswalk
        result = crosswalk(args.mif, args.world, args.packet, args.output,
                           rmd_path=args.rmd, readme_path=args.readme)
        print("CEMICS author source crosswalk:", result["status"])
        print("Exact Model/Scenario rows:", result["archive_exact_model_scenario_row_count"])
        print("Exact World variable series:", result["archive_exact_world_variable_count"])
        print("Shared source variable names:", result["overlapping_variable_names"])
        print("Source comparison statuses:", result["overlap_status_counts"])
        print("No source CO2 values exported; I3:", result["verified_i3"])
    elif args.command == "arc24-poles-eip-mapping":
        from .arc24_poles_eip_mapping import write_eip_mapping
        result = write_eip_mapping(args.world, args.packet, args.output)
        print("POLES detailed hierarchy:", result["status"])
        print("Expanded ENGAGE total hierarchy statuses:", result["expanded_status_counts"])
        print("Detailed energy+industrial versus EIP statuses:", result["eip_detail_status_counts"])
        print("Availability:", result["availability_counts"])
        print("Verified I3:", result["verified_i3"])
        print("Source numbers and model identities remain local.")
    elif args.command == "arc24-poles-other-identity":
        from .arc24_poles_other_identity import write_other_comparison
        result = write_other_comparison(args.world, args.packet, args.output)
        print("POLES Other hypothesis:", result["status"])
        print("Exact reported-decimal identity / other statuses:", result["identity_status_counts"])
        print("Sign matches:", result["sign_matches"], "Sign mismatches:", result["sign_mismatches"])
        print("Verified I3:", result["verified_i3"])
        print("Coded results only; unmodified source values remain local.")
    elif args.command == "arc24-poles-optional-co2":
        from .arc24_poles_optional_co2 import write_optional_sectors
        result = write_optional_sectors(args.world, args.packet, args.output)
        print("POLES optional CO2 sector screen:", result["status"])
        print("Case-years screened:", result["num_case_years"])
        for name, counts in result["status_by_optional_variable"].items():
            print(name, counts)
        print("No optional terms added to EIP; verified I3:", result["verified_i3"])
    elif args.command == "arc24-poles-timeline":
        from .arc24_poles_timeline import write_timeline
        result = write_timeline(args.world, args.packet, args.output)
        print("POLES temporal diagnostic:", result["status"])
        print("Selected scenarios:", result["cases"])
        print("Case/year observations:", len(result["observations"]))
        print("Verified scientific I3:", result["reviewed_i3_cases"])
        print("Only coded signed bands are published; source values remain local.")
    elif args.command == "arc24-arithmetic":
        from .arc24_aggregate_arithmetic import write_aggregate_screen
        result = write_aggregate_screen(args.packet, args.public_output, args.private_output)
        print("ARC24 aggregate diagnostic:", result["status"])
        print("Arithmetic check statuses:", result["status_counts"])
        print("Reviewed I3 cases:", result["reviewed_i3_cases"])
        print("No original scenario values or residual magnitudes shown in public output.")
    elif args.command == "arc24-sign-screen":
        from .arc24_sign_screen import write_sign_report
        result = write_sign_report(args.packet, args.output)
        print("ARC24 diagnostic:", result["status"])
        print("Signed net-negative AFOLU cases:", result["negative_afolu_cases"])
        print("Missing separately reported land sequestration:", result["missing_land_sequestration_cases"])
        print("Verified I3:", result["verified_i3_cases"])
    elif args.command == "ar6-canonical-select":
        from .ar6_canonical_gate import select_canonical_24
        result = select_canonical_24(args.world, args.metadata,
                                     args.public_output, args.private_output)
        print("Source-selected 24-case cohort:", result["status"])
        print("Selected cases:", len(result["cases"]))
        print("Six-variable-complete cases:", result["six_variable_complete_cases"])
        print("Official acquisition provenance independently authenticated:", False)
        print("Expert-reconciled I3 cases:", result["verified_i3_cases"])
    elif args.command == "ar6-canonical-gate":
        from .ar6_canonical_gate import source_gate
        result = source_gate(args.world, args.metadata, args.packet,
                             args.public_output, args.private_output)
        print("Canonical source evidence gate:", result["status"])
        print("Local World SHA-256:", result["world_sha256"])
        print("Matched RP24 cases in World:", result["source_matched_rp24_cases"])
        print("Matched RP24 cases in vetted metadata:", result["metadata_matched_rp24_cases"])
        print("No original model IDs/observations published. I3 cases:", result["verified_i3_cases"])
    elif args.command == "westeros-case-study":
        from .westeros_case_study import publish_case_study
        result, inventory = publish_case_study(args.control_json, args.cap_json, args.output)
        print("Publication gate:", result["status"])
        print("Cap objective penalty:", result["cap_effect"]["difference_native"])
        print("Baseline/control ACT matches:", result["baseline_control_activity_parity"])
        print("Hashed derived files:", len(inventory["files"]))
        print("No GAMS or ixmp used.")
    elif args.command == "westeros-no-cap-control":
        from .westeros_no_cap import run_control
        result, output_dir = run_control(args.manifest, args.output)
        print("Control solve status:", result["status"])
        print("Baseline and control numerically equivalent:", result["baseline_vs_control"]["numerically_equivalent"])
        print("Isolated cap objective effect (native units):", result["cap_effect"]["difference_native"])
        print("Private control output:", output_dir)
    elif args.command == "westeros-cap-check":
        from .westeros_cap_audit import audit_saved_run
        result = audit_saved_run(args.manifest, args.output)
        print("Emissions cap:", result["status"])
        print("Average annual:", result["computed_average_annual"])
        print("Bound:", result["bound_value"])
        print("Period durations:", result["period_durations"])
        print("Shadow price:", result["shadow_price_status"])
        print("No GAMS solve performed.")
    elif args.command == "westeros-analyze":
        from .westeros_analysis import analyze_run
        summary, manifest = analyze_run(args.manifest, args.output)
        print("Analysis:", summary["status"])
        print("Objective difference (stored ixmp):", summary["objective"]["difference_native"])
        print("Comparable or missing technology rows:", len(summary["comparisons"]))
        print("Hashed output files:", len(manifest["files_sha256"]))
        print("No GAMS solve performed.")
    elif args.command == "westeros-validate":
        from .westeros import run_westeros
        result = run_westeros(args.output)
        print("Actual MESSAGEix/GAMS solves:", len(result["cases"]),
              "status:", result["status"])
    elif args.command == "gams-preflight":
        from .preflight import write_preflight
        x = write_preflight(args.output)
        print(x["scientific_status"], "GAMS discovered:", x["gams_executable_discovered"])
    elif args.command == "case-audit":
        from .case_audit import run_case_audit
        result = run_case_audit(args.input, args.metadata, args.candidates,
                                args.public_output, args.private_output,
                                args.year, args.metadata_sheet)
        print("RP24 audit:", result["summary"]["case_count"],
              "source-grounded cases; human-reviewed:", result["summary"]["reviewed_cases"],
              "I3 verified:", result["summary"]["verified_i3_cases"])
    elif args.command == "audit-ar6-strata":
        from .stratify import run_strata
        import json
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
