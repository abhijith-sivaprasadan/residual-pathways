"""ARC24-06: isolate nonidentical decimals for the uniquely leading ENGAGE v2 case.

Requires the user's original AR6 and ENGAGE World CSVs and the previous
private candidate fingerprint. No source values or candidate names are
written outside the ignored data/ar6-private directory.

This diagnoses correspondence differences; it does NOT assign a source
model-version alias, attribute change causes (rounding/revision/reclassification)
or verify any independent gross-positive/atmospheric-removal carbon accounting.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path

from .arc24_engage_v2_probe import (
    CASE_ID, MODEL, SCENARIO, WORLD_SHA, YEARS, FOCUS, UNIT,
    _data as ar6_data, _digest, _status,
)
from .arc24_engage_v2_candidate_fingerprint import (
    load_candidates, compare, _digest as fingerprint_digest,
)
from .arc24_engage_v2_identity_inventory import USER_OBSERVED_ENGAGE_SHA
from .arc24_engage_v2_fingerprint_adjudication import (
    audit, PRIVATE_SCHEMA, SLOTS,
)

class DifferenceReviewError(ValueError):
    pass


def _sign(value: Decimal):
    if value == 0:
        return "ZERO"
    return "POSITIVE" if value > 0 else "NEGATIVE"


def analyze_differences(original, candidate, source_model, source_scenario):
    """Return private identifiers and public non-identifying aggregates."""
    differences=[]
    count=Counter()
    status_bands=Counter()
    for variable in FOCUS:
        key=(variable,UNIT)
        if key not in original or key not in candidate:
            raise DifferenceReviewError("A source variable or exact unit is absent; never imply comparable")
        for year in YEARS:
            a=original[key].get(year)
            b=candidate[key].get(year)
            if a is None or b is None:
                raise DifferenceReviewError("A source year is missing; exact 55-cell comparison invalid")
            count["compared"]+=1
            result=_status(a,b)
            if result=="EXACT_REPORTED_DECIMAL":
                count["exact"]+=1
                if a!=0 and b!=0:
                    count["exact_nonzero"]+=1
                continue
            count["different"]+=1
            status_bands[result]+=1
            # All original source values remain in memory only. No output
            # contains source numeric emissions, values, or delta magnitude.
            source_sign=_sign(a)
            target_sign=_sign(b)
            if source_sign==target_sign:
                count["same_sign"]+=1
            elif "ZERO" in (source_sign,target_sign):
                count["zero_nonzero_transition"]+=1
            else:
                count["opposite_sign"]+=1
            differences.append({
                "variable":variable,
                "unit":UNIT,
                "year":year,
                "engage_v2_sign":target_sign,
                "ar6_v1_1_sign":source_sign,
                "original_reported_decimal_status":result,
                "interpretation":"CAUSE_NOT_ESTABLISHED; exact source documentation required",
            })
    if count["compared"]!=SLOTS:
        raise DifferenceReviewError("Incomplete predefined 11x5 source comparison")
    safe={
        "schema":"residualpathways.arc24_06_difference_review_public.v1",
        "case_id":CASE_ID,
        "status":"NUMERICAL_CORRESPONDENCE_CANDIDATE_ONLY",
        "ar6_source_sha256":WORLD_SHA,
        "engage_v2_local_sha256":USER_OBSERVED_ENGAGE_SHA,
        "source_case_compared_cells":count["compared"],
        "exact_reported_decimal_matches":count["exact"],
        "exact_nonzero_matches":count["exact_nonzero"],
        "different_reported_decimal_cells":count["different"],
        "difference_precision_bands":dict(sorted(status_bands.items())),
        "difference_sign_retain_count":count["same_sign"],
        "difference_zero_transition_count":count["zero_nonzero_transition"],
        "difference_sign_flip_count":count["opposite_sign"],
        "different_variable_years_disclosed":False,
        "number_of_candidate_source_pairs_examined":1,
        "causal_interpretation":"UNKNOWN_NOT_PROVEN_ROUNDING_OR_EXPORT_CHANGE",
        "source_model_scenario_alias":"NOT_ESTABLISHED",
        "positive_gross_and_atmospheric_cdr":"NOT_ESTABLISHED",
        "science_review_state":"REVIEW_PENDING",
        "verified_i3":0,
        "disclosure":"Only aggregate diagnostic counts, no source-specific variable-years, model labels, scenario identities, source values, or unique candidate IDs.",
    }
    private={
        "schema":"residualpathways.arc24_06_difference_review_private.v1",
        "handling":"LOCAL_ONLY_DO_NOT_PUBLISH",
        "case_id":CASE_ID,
        "source_model":source_model,
        "source_scenario":source_scenario,
        "ar6_model":MODEL,
        "ar6_scenario":SCENARIO,
        "ar6_source_sha256":WORLD_SHA,
        "engage_v2_local_sha256":USER_OBSERVED_ENGAGE_SHA,
        "differences_by_variable_unit_year_no_values":differences,
        "exact_count":count["exact"],
        "exact_nonzero_count":count["exact_nonzero"],
        "note":"Variable/year/sign/status only. No numeric emissions stored; author must check original export settings.",
    }
    return safe,private


def review(world,engage,packet_path,fingerprint_private,public_output,private_output,
           *,expected_world_sha=WORLD_SHA,expected_engage_sha=USER_OBSERVED_ENGAGE_SHA,
           verify_expected=(52,51)):
    paths=[Path(p).resolve() for p in (
        world,engage,packet_path,fingerprint_private,public_output,private_output)]
    world,engage,packet_path,fingerprint_private,public_output,private_output=paths
    if (len(set(paths)) != len(paths)
            or any("ar6-private" not in p.parts for p in (
                world,engage,packet_path,fingerprint_private,private_output))
            or "ar6-private" in public_output.parts
            or not all(p.is_file() for p in (
                world,engage,packet_path,fingerprint_private))):
        raise DifferenceReviewError("All source inputs and per-cell findings must remain private")
    if _digest(world)!=expected_world_sha or _digest(engage)!=expected_engage_sha:
        raise DifferenceReviewError("Original source bytes do not match the registered author-local fingerprints")
    fp=json.loads(fingerprint_private.read_text(encoding="utf-8"))
    # The status-only schema and source digest must match and the best source
    # candidate must be uniquely determined BEFORE reading source rows.
    # audit() validates all 76 source-comparison counters without aliasing.
    expected_result=audit(fp)
    if expected_result["top_numerical_score_tie_count"]!=1:
        raise DifferenceReviewError("No unique numerical leader")
    ranked=sorted(fp["candidates_ranked_as_unverified_hypotheses"],
        key=lambda r:(
            r["source_decimal_nonzero_exact"],
            r["source_decimal_exact"],
            r["variables_with_nonzero_exact"],
            r["source_decimal_compared"],
        ),reverse=True)
    winner=ranked[0]
    if not (winner.get("exact_scenario_name") and winner.get("poles_model_label")):
        raise DifferenceReviewError("Top candidate does not have the preregistered exact-scenario/POLES grouping")

    packet=json.loads(packet_path.read_text(encoding="utf-8"))
    cases=packet.get("cases")
    if (packet.get("schema")!="residualpathways.ar6_canonical_selected24.private.v1"
        or packet.get("handling")!="LOCAL_ONLY_DO_NOT_PUBLISH"
        or packet.get("source_sha256") != expected_world_sha
        or not isinstance(cases,list) or len(cases)!=24):
        raise DifferenceReviewError("Original AR6 case packet invalid")
    matched=[x for x in cases if x.get("case_id")==CASE_ID]
    if len(matched)!=1 or (
        matched[0].get("model"),matched[0].get("scenario"))!=(MODEL,SCENARIO):
        raise DifferenceReviewError("Source ARC24-06 case identity changed")

    original, original_count=ar6_data(world)
    if original_count==0:
        raise DifferenceReviewError("ARC24-06 source case absent from original AR6 World")

    pair=(winner["original_model"],winner["original_scenario"])
    source=load_candidates(engage,{pair})
    if pair not in source:
        raise DifferenceReviewError("Leading ENGAGE source pair absent")
    safe,private=analyze_differences(original,source[pair],*pair)
    exact=safe["exact_reported_decimal_matches"]
    nonzero=safe["exact_nonzero_matches"]
    if (exact != winner["source_decimal_exact"]
            or nonzero != winner["source_decimal_nonzero_exact"]
            or safe["source_case_compared_cells"]!=winner["source_decimal_compared"]):
        raise DifferenceReviewError("Current source observations disagree with the private scored fingerprint")
    if verify_expected is not None and (exact,nonzero)!=verify_expected:
        raise DifferenceReviewError("Original empirical result changed; investigate before publication")
    safe["ar6_source_sha256"]=expected_world_sha
    safe["engage_v2_local_sha256"]=expected_engage_sha
    private["ar6_source_sha256"]=expected_world_sha
    private["engage_v2_local_sha256"]=expected_engage_sha
    public_output.parent.mkdir(parents=True,exist_ok=True)
    private_output.parent.mkdir(parents=True,exist_ok=True)
    public_output.write_text(json.dumps(safe,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    private_output.write_text(json.dumps(private,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return safe


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--world",type=Path,default=Path("data/ar6-private/AR6_Scenarios_Database_World_v1.1.csv"))
    p.add_argument("--engage",type=Path,default=Path("data/ar6-private/ENGAGE_scenario_data_world_r2.0.csv"))
    p.add_argument("--packet",type=Path,default=Path("data/ar6-private/canonical_selected24_packet.json"))
    p.add_argument("--private-fingerprint",type=Path,default=Path("data/ar6-private/engage_v2_candidate_fingerprint_private.json"))
    p.add_argument("--public",type=Path,default=Path("results/ar6-canonical-gate/arc24_06_difference_review_public.json"))
    p.add_argument("--private",type=Path,default=Path("data/ar6-private/arc24_06_differences_private.json"))
    args=p.parse_args()
    result=review(args.world,args.engage,args.packet,args.private_fingerprint,
                  args.public,args.private)
    for key in ("source_case_compared_cells","exact_reported_decimal_matches",
                "exact_nonzero_matches","different_reported_decimal_cells",
                "difference_precision_bands","difference_sign_retain_count",
                "difference_zero_transition_count","difference_sign_flip_count",
                "source_model_scenario_alias","verified_i3"):
        print(f"{key}: {json.dumps(result[key],sort_keys=True)}")
    print("Per-variable-year differences: private only, in",args.private)
    print("No explanation (rounding/revision/method change) has been inferred.")


if __name__=="__main__":
    main()
