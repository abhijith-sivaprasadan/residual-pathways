"""Create a private, model-specific ARC24 evidence checklist without assigning I0–I3.

Requires the author's ignored canonical_selected24_packet.json. The review
docket retains identity only in data/ar6-private; no source observations are
copied. The optional public queue contains anonymous case IDs and audit gates.

Source-context references may guide manual review but do NOT authenticate a
specific scenario/version's gross/land/BECCS/DAC ledger or source precision.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

WORLD_SHA="4cf39b6b0d968e25ed389318acb1674f92146f977e9db4bfb7970f048ff73977"
META_SHA="fd1bc32db8463769e18f0560ced603a49598c12e1abfa06787ff763c55f06716"
GATES=(
    "exact_model_version_and_original_scenario_run_crosswalk",
    "gas_world_year_unit_sign_and_reporting_scope",
    "disjoint_exhaustive_positive_gross_emissions_branches",
    "afolu_net_vs_gross_land_flux_and_baseline",
    "biomass_uptake_beccs_capture_storage_lifecycle_overlap",
    "fossil_point_source_ccs_excluded_from_atmospheric_cdr",
    "dac_and_weathering_net_durable_removal_proof",
    "full_scope_component_completeness_and_nonoverlap",
    "source_declared_quantization_precision_not_display_digits",
    "physical_and_arithmetic_independent_reconciliations",
    "independent_second_reviewer_signoff",
)
FAMILY_SOURCES={
    "REMIND-MAgPIE 2.1-4.2": {
        "research_group":"CEMICS MIN-CDR SOURCE CROSSWALK",
        "primary_leads":[
            "https://doi.org/10.1088/1748-9326/ac0a11",
            "https://zenodo.org/records/5103024",
            "https://doi.org/10.5194/gmd-14-6571-2021",
        ],
        "warning":"Do not substitute Strefler SSP2 plot values for exact SSP1 AR6 case; authors' MIF/Rmd-to-AR6 scenario mapping remains source-specific.",
    },
    "POLES ENGAGE": {
        "research_group":"POLES-ENGAGE / GLOBIOM LAND AND CO2 OTHER",
        "primary_leads":[
            "https://www.iamcdocumentation.eu/Emissions_-_POLES",
            "https://data.ece.iiasa.ac.at/engage-netzero-analysis/notebooks/1_categorization.html",
        ],
        "warning":"CO2 Other can be a computed remainder. An algebraic near-match is not an independently observed positive-emissions process.",
    },
    "COFFEE 1.1": {
        "research_group":"COFFEE-TEA REPORTING CONFIGURATION",
        "primary_leads":[
            "https://www.iamcdocumentation.eu/Emissions_-_COFFEE-TEA",
            "https://www.iamcdocumentation.eu/Carbon_dioxide_removal_(CDR)_options_-_COFFEE-TEA",
        ],
        "warning":"COFFEE-TEA documentation must not be presumed identical to the exact AR6 COFFEE 1.1 submission.",
    },
    "WITCH 5.0": {
        "research_group":"WITCH-5 / GLOBIOM LAND LINKAGE",
        "primary_leads":[
            "https://www.iamcdocumentation.eu/Reference_card_-_WITCH",
            "https://doc.witchmodel.org/model-scope.html",
        ],
        "warning":"Present-day WITCH docs may not describe the exact historical AR6 WITCH 5.0 configuration.",
    },
}
PRIORITIES=("ARC24-03","ARC24-06","ARC24-09","ARC24-12","ARC24-15",
            "ARC24-18","ARC24-21","ARC24-24")


class DocketError(ValueError):
    pass


def make_queue(packet:dict):
    if (packet.get("schema")!="residualpathways.ar6_canonical_selected24.private.v1"
            or packet.get("handling")!="LOCAL_ONLY_DO_NOT_PUBLISH"
            or packet.get("source_sha256")!=WORLD_SHA
            or packet.get("metadata_sha256")!=META_SHA):
        raise DocketError("Wrong canonical private packet or unregistered source hashes")
    cases=packet.get("cases")
    if not isinstance(cases,list) or len(cases)!=24:
        raise DocketError("Exactly 24 canonical cases required")
    if {c.get("case_id") for c in cases} != {f"ARC24-{i:02d}" for i in range(1,25)}:
        raise DocketError("Unexpected case identifiers")
    work=[]
    public=[]
    for case in sorted(cases,key=lambda x:x["case_id"]):
        if (not case.get("model") or not case.get("scenario")
                or case.get("category") not in {f"C{i}" for i in range(1,9)}
                or case.get("year")!=2050):
            raise DocketError("Malformed model scenario or World study scope")
        model=case["model"]
        guidance=FAMILY_SOURCES.get(model,{})
        priority=case["case_id"] in PRIORITIES
        manual={gate:{"state":"NOT_REVIEWED","source_ref":None,
                       "reviewer_notes":None} for gate in GATES}
        private={
            "case_id":case["case_id"],"model":model,"scenario":case["scenario"],
            "category":case["category"],"year":2050,"priority":priority,
            "research_group":guidance.get("research_group","SOURCE_MODEL_SPECIFIC_REVIEW_REQUIRED"),
            "primary_source_leads":guidance.get("primary_leads",[]),
            "version_warning":guidance.get("warning","Locate exact primary model/run documentation."),
            "evidence_gates":manual,
            "first_reviewer":None,"first_review_date":None,
            "independent_reviewer":None,"independent_review_date":None,
            "review_status":"NOT_REVIEWED",
            "identifiability_grade":"NOT_DETERMINED",
            "verified_i3":False,
            "interpretation":"Source-lead triage only. Presence, arithmetic or sign screens are NOT scientific grading.",
        }
        work.append(private)
        public.append({
            "case_id":case["case_id"],"category":case["category"],
            "priority":priority,"review_status":"NOT_REVIEWED",
            "identifiability_grade":"NOT_DETERMINED","verified_i3":False,
            "evidence_gate_count":len(GATES),"evidence_gates_completed":0,
        })
    return ({
        "schema":"residualpathways.arc24.private_scientific_review_docket.v1",
        "handling":"LOCAL_ONLY_DO_NOT_PUBLISH",
        "source_sha256":WORLD_SHA,"metadata_sha256":META_SHA,
        "grades_must_be_entered_by_human":True,
        "cases":work,
    },{
        "schema":"residualpathways.arc24.review_queue_public.v1",
        "science_review_state":"REVIEW_PENDING",
        "reviewed_cases":0,"verified_i3_cases":0,
        "source_sha256":WORLD_SHA,"metadata_sha256":META_SHA,
        "cases":public,
        "selection_notice":"Purposive three per C1-C8; no population I3 rate estimate.",
        "disclosure":"No Model/Scenario identities, observational values or private reviewer text.",
    })


def build(private_packet, private_docket, public_summary):
    input_path=Path(private_packet).resolve()
    private_docket=Path(private_docket).resolve()
    public_summary=Path(public_summary).resolve()
    if (not input_path.is_file() or input_path.stat().st_size>30_000_000
            or "ar6-private" not in input_path.parts
            or "ar6-private" not in private_docket.parts
            or "ar6-private" in public_summary.parts
            or private_docket==public_summary
            or input_path==private_docket):
        raise DocketError("Only local private inputs/outputs in ar6-private are allowed")
    packet=json.loads(input_path.read_text(encoding="utf-8"))
    work,public=make_queue(packet)
    private_docket.parent.mkdir(parents=True,exist_ok=True)
    public_summary.parent.mkdir(parents=True,exist_ok=True)
    private_docket.write_text(json.dumps(work,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    public_summary.write_text(json.dumps(public,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return public


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--packet",type=Path,default=Path("data/ar6-private/canonical_selected24_packet.json"))
    p.add_argument("--private-docket",type=Path,default=Path("data/ar6-private/arc24_review_docket.json"))
    p.add_argument("--public-queue",type=Path,default=Path("results/ar6-canonical-gate/arc24_review_queue_public.json"))
    args=p.parse_args()
    out=build(args.packet,args.private_docket,args.public_queue)
    print("CASES QUEUED:",len(out["cases"]),"REVIEWED:",out["reviewed_cases"],
          "I3 VERIFIED:",out["verified_i3_cases"])
    print("No scenario identity or source value added to the public queue.")
    print("Private docket:",args.private_docket)


if __name__=="__main__":
    main()
