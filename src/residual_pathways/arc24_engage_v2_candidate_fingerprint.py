"""Controlled AR6 ARC24-06 -> ENGAGE v2.0 candidate source fingerprint.

Tests every v2.0 World pair with the identical scenario name plus every
POLES-containing model's World scenarios. The full candidate pool (not just
the 12 lexical leads) provides negative/control comparisons. Compares
original Decimal values by *exact source variable name, exact unit, year*.

This can ESTABLISH or reject numerical-source correspondence in the tested
11-variable x 5-year scope; it does not declare a model alias, physically
independent emissions, source precision, or I0/I1/I2/I3 classification.

All model/scenario identities and per-candidate results remain ONLY in
data/ar6-private. Public output contains aggregate counts with no source
observations, aliases, candidate IDs or original source names.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

from .arc24_engage_v2_probe import (
    CASE_ID, MODEL, SCENARIO, YEARS, FOCUS, WORLD_SHA, V2_FILENAME,
    _data as original_ar6, _decimal, _digest, _status, EngageSourceError
)
from .arc24_engage_v2_identity_inventory import (
    USER_OBSERVED_ENGAGE_SHA, scan_pairs, EngageIdentityError
)

class FingerprintError(ValueError):
    pass


def candidate_groups(pairs):
    """Register all exact-scenario controls and all source POLES family pairs."""
    pairset=set(pairs)
    return {
        pair: (
            ("EXACT_SCENARIO_OTHER_MODEL" if scenario == SCENARIO else
             "POLES_FAMILY_OTHER_SCENARIO")
        )
        for pair in pairset
        for model, scenario in (pair,)
        if scenario == SCENARIO or "poles" in model.casefold()
    }


def load_candidates(csvpath, candidate_pairs):
    """One streaming read of 95MB source; reject duplicate source/unit keys."""
    original={}
    with csvpath.open("r", newline="",encoding="utf-8-sig") as file:
        reader=csv.DictReader(file)
        head=reader.fieldnames or []
        if len(head)!=len(set(head)) or not {
                "Model","Scenario","Region","Variable","Unit"}.issubset(head):
            raise FingerprintError("ENGAGE v2.0 IAMC schema invalid")
        year_cols={
            y:next((v for v in (str(y),f"X{y}") if v in head),None)
            for y in YEARS
        }
        if year_cols[2050] is None:
            raise FingerprintError("Source ENGAGE v2.0 lacks 2050")
        for i,row in enumerate(reader,2):
            if None in row or any(v is None for v in row.values()):
                raise FingerprintError(f"Malformed source ENGAGE row {i}")
            if row["Region"]!="World" or row["Variable"] not in FOCUS:
                continue
            pair=(row["Model"],row["Scenario"])
            if pair not in candidate_pairs:
                continue
            key=(row["Variable"],row["Unit"])
            selected=original.setdefault(pair,{})
            if key in selected:
                raise FingerprintError("Ambiguous repeated variable and unit for source candidate")
            selected[key]={
                y:_decimal(row[col]) if col else None
                for y,col in year_cols.items()
            }
    return original


def compare(ar6_values, candidate_values, years=YEARS):
    counts=Counter()
    distinct_nonzero=set()
    distinct_exact=set()
    for (variable,unit),value_by_year in ar6_values.items():
        if variable not in FOCUS:
            continue
        values=candidate_values.get((variable,unit))
        if not values:
            counts["SOURCE_VARIABLE_OR_UNIT_NOT_SHARED"]+=len(years)
            continue
        for year in years:
            a,b=value_by_year.get(year),values.get(year)
            if a is None or b is None:
                counts["MISSING_YEAR_VALUE"]+=1
            else:
                status=_status(a,b)
                counts[status]+=1
                if status=="EXACT_REPORTED_DECIMAL":
                    distinct_exact.add(variable)
                    if a!=0 and b!=0:
                        distinct_nonzero.add(variable)
                        counts["EXACT_NONZERO"]+=1
    counts["DISTINCT_VARIABLES_WITH_EXACT"]=len(distinct_exact)
    counts["DISTINCT_VARIABLES_WITH_NONZERO_EXACT"]=len(distinct_nonzero)
    return dict(counts)


def fingerprint(original, candidates, pairs):
    groups=candidate_groups(pairs)
    rows=[]
    for idx,pair in enumerate(sorted(groups),1):
        counts=compare(original,candidates.get(pair,{}))
        compared=sum(n for k,n in counts.items()
                     if k=="EXACT_REPORTED_DECIMAL" or k.startswith("NONZERO_REPORTED_DECIMAL__"))
        exact=counts.get("EXACT_REPORTED_DECIMAL",0)
        nonzero=counts.get("EXACT_NONZERO",0)
        rows.append({
            "candidate_code":f"E2-{idx:03d}",
            "original_model":pair[0],
            "original_scenario":pair[1],
            "candidate_group":groups[pair],
            "exact_scenario_name":pair[1]==SCENARIO,
            "poles_model_label":"poles" in pair[0].casefold(),
            "source_decimal_compared":compared,
            "source_decimal_exact":exact,
            "source_decimal_nonzero_exact":nonzero,
            "variables_with_exact":counts.get("DISTINCT_VARIABLES_WITH_EXACT",0),
            "variables_with_nonzero_exact":counts.get("DISTINCT_VARIABLES_WITH_NONZERO_EXACT",0),
            "match_fraction":round(exact/compared,6) if compared else None,
            "status_counts":dict(sorted(counts.items())),
            "model_version_equivalent":"NOT_VERIFIED",
            "scenario_alias_approved":False,
            "physical_accounting":"NOT_ESTABLISHED",
        })
    rows.sort(key=lambda r:(
        -r["source_decimal_nonzero_exact"],
        -r["source_decimal_exact"],
        -r["variables_with_nonzero_exact"],
        r["candidate_code"]
    ))
    return rows


def summarize(rows, pairs):
    counts=Counter(r["candidate_group"] for r in rows)
    exact_scenario_poles=sum(r["exact_scenario_name"] and r["poles_model_label"] for r in rows)
    comparisons=[r for r in rows if r["source_decimal_compared"]>0]
    best=max((r["source_decimal_exact"] for r in comparisons),default=0)
    best_nonzero=max((r["source_decimal_nonzero_exact"] for r in comparisons),default=0)
    return {
        "schema":"residualpathways.engage_v2_candidate_fingerprint_public.v1",
        "case_id":CASE_ID,
        "status":"SOURCE_DECIMAL_CANDIDATE_COMPARISON_NO_ALIAS_ASSIGNED",
        "registration_rule":"ALL_EXACT_SCENARIO_NAME_PAIRS_PLUS_ALL_POLES_CONTAINING_MODEL_WORLD_PAIRS",
        "candidate_total":len(rows),
        "exact_scenario_other_model_candidates":counts["EXACT_SCENARIO_OTHER_MODEL"],
        "poles_family_other_scenario_controls":counts["POLES_FAMILY_OTHER_SCENARIO"],
        "exact_scenario_under_poles_model_found":bool(exact_scenario_poles),
        "exact_scenario_under_poles_model_count":exact_scenario_poles,
        "candidates_with_any_comparable_decimal":len(comparisons),
        "maximum_exact_reported_decimal_cells":best,
        "maximum_exact_nonzero_cells":best_nonzero,
        "candidate_cells_per_full_series_test":len(YEARS)*len(FOCUS),
        "any_fully_exact_source_series_candidate":any(
            r["source_decimal_compared"]==len(YEARS)*len(FOCUS)
            and r["source_decimal_exact"]==r["source_decimal_compared"]
            for r in rows
        ),
        "source_model_equivalence":"NOT_ESTABLISHED",
        "source_scenario_rename":"NOT_ESTABLISHED",
        "independent_physical_gross_partition":"NOT_ESTABLISHED",
        "independent_physical_atmospheric_removal":"NOT_ESTABLISHED",
        "science_review_state":"REVIEW_PENDING",
        "verified_i3":0,
        "interpretation":"Reproducible source-variable/unit/year Decimal fingerprints are hypotheses, NOT independently verified run lineage or physical carbon-accounting evidence.",
    }


def execute(world,engage,packet,public,private,*,expected_world_sha=WORLD_SHA,
            expected_engage_sha=USER_OBSERVED_ENGAGE_SHA):
    world,engage,packet,public,private=[
        Path(s).resolve() for s in (world,engage,packet,public,private)
    ]
    if (len({world,engage,packet,public,private})!=5
            or any("ar6-private" not in p.parts for p in (world,engage,packet,private))
            or "ar6-private" in public.parts
            or not all(p.is_file() for p in (world,engage,packet))
            or engage.name!=V2_FILENAME):
        raise FingerprintError("Use source-protected files and separate private/public outputs")
    if _digest(world)!=expected_world_sha or _digest(engage)!=expected_engage_sha:
        raise FingerprintError("Real source files do not match approved local SHA fingerprints")
    info=json.loads(packet.read_text(encoding="utf-8"))
    cases=info.get("cases")
    if (info.get("schema")!="residualpathways.ar6_canonical_selected24.private.v1"
            or info.get("handling")!="LOCAL_ONLY_DO_NOT_PUBLISH"
            or info.get("source_sha256")!=expected_world_sha
            or not isinstance(cases,list) or len(cases)!=24):
        raise FingerprintError("Canonical private ARC24 source packet invalid")
    match=[c for c in cases if c.get("case_id")==CASE_ID]
    if len(match)!=1 or (match[0].get("model"),match[0].get("scenario"))!=(MODEL,SCENARIO):
        raise FingerprintError("Canonical selected ARC24-06 identity changed")
    ar6_values, original_rows=original_ar6(world)
    if original_rows==0:
        raise FingerprintError("Target ARC24-06 source not found in registered AR6 World CSV")
    for variable,entry in match[0].get("source_observations",{}).items():
        key=(variable,entry.get("unit"))
        if variable in FOCUS:
            if key not in ar6_values or ar6_values[key][2050]!=_decimal(entry.get("raw")):
                raise FingerprintError("Case packet conflicts with 2050 original source")
    all_pairs,_,_ = scan_pairs(engage)
    registered=candidate_groups(all_pairs)
    if not registered:
        raise FingerprintError("No registered ENGAGE v2.0 candidate pairs")
    source=load_candidates(engage,set(registered))
    rows=fingerprint(ar6_values,source,all_pairs)
    public_result=summarize(rows,all_pairs)
    public_result.update({
        "ar6_world_sha256":expected_world_sha,
        "engage_v2_local_sha256":expected_engage_sha,
        "engage_v2_publisher_authentication":"NOT_ESTABLISHED",
        "identity_register":"MODEL_SCENARIO_WORLD_PAIR_ONLY",
        "recorded_decimal_source_precision":"NOT_ESTABLISHED",
    })
    private_result={
        "schema":"residualpathways.engage_v2_fingerprint_private.v1",
        "handling":"LOCAL_ONLY_DO_NOT_PUBLISH",
        "original_selected_case":CASE_ID,
        "source_sha256":expected_engage_sha,
        "candidate_count":len(rows),
        "candidates_ranked_as_unverified_hypotheses":rows,
    }
    public.parent.mkdir(parents=True,exist_ok=True)
    private.parent.mkdir(parents=True,exist_ok=True)
    public.write_text(json.dumps(public_result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    private.write_text(json.dumps(private_result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return public_result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--world",type=Path,default=Path("data/ar6-private/AR6_Scenarios_Database_World_v1.1.csv"))
    p.add_argument("--engage",type=Path,default=Path("data/ar6-private/ENGAGE_scenario_data_world_r2.0.csv"))
    p.add_argument("--packet",type=Path,default=Path("data/ar6-private/canonical_selected24_packet.json"))
    p.add_argument("--public",type=Path,default=Path("results/ar6-canonical-gate/engage_v2_candidate_fingerprint_public.json"))
    p.add_argument("--private",type=Path,default=Path("data/ar6-private/engage_v2_candidate_fingerprint_private.json"))
    a=p.parse_args()
    result=execute(a.world,a.engage,a.packet,a.public,a.private)
    for name in (
        "candidate_total","exact_scenario_other_model_candidates",
        "poles_family_other_scenario_controls",
        "exact_scenario_under_poles_model_found",
        "candidates_with_any_comparable_decimal",
        "maximum_exact_reported_decimal_cells",
        "maximum_exact_nonzero_cells","any_fully_exact_source_series_candidate"
    ):
        print(f"{name}: {result[name]}")
    print("No source data or identifying candidate names in public report.")
    print("Private review dossier:",a.private)
    print("SCIENTIFIC GRADES NOT DETERMINED; I3 VERIFIED 0")


if __name__=="__main__":
    main()
