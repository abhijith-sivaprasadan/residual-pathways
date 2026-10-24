"""Adjudicate ARC24-06 candidate-fingerprint diagnostics without exposing source data.

Consumes ONLY the private numeric-fingerprint *status* docket, not World source
rows. Reports whether the most exact/nonzero matching candidate is actually
well-covered, unique, and distinguishable from unrelated/crossed controls.

Numerical correspondence remains an unapproved hypothesis. No model or
scenario names, candidate IDs, values, original source rows or per-case
status vectors appear in the public summary.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from .arc24_engage_v2_identity_inventory import USER_OBSERVED_ENGAGE_SHA
from .arc24_engage_v2_probe import CASE_ID, FOCUS, YEARS

SLOTS = len(FOCUS) * len(YEARS)
GROUPS = {
    "EXACT_SCENARIO_OTHER_MODEL",
    "POLES_FAMILY_OTHER_SCENARIO",
}
PUBLISH_STATUS = "CORRESPONDENCE_HYPOTHESIS_NOT_SOURCE_ALIAS"
PRIVATE_SCHEMA = "residualpathways.engage_v2_fingerprint_private.v1"


class AdjudicationError(ValueError):
    pass


def _integer(row, name):
    value = row.get(name)
    if type(value) is not int or value < 0:
        raise AdjudicationError(f"Missing/invalid private numeric status field: {name}")
    return value


def _score(row):
    return (
        row["source_decimal_nonzero_exact"],
        row["source_decimal_exact"],
        row["variables_with_nonzero_exact"],
        row["source_decimal_compared"],
    )


def _leader_description(row):
    if row is None:
        return None
    compared = row["source_decimal_compared"]
    exact = row["source_decimal_exact"]
    # No original Model or Scenario, deterministic candidate code, row numbers,
    # source observations, or raw numeric time series may leave the private file.
    return {
        "candidate_group": row["candidate_group"],
        "exact_scenario_name": row["exact_scenario_name"],
        "poles_model_label": row["poles_model_label"],
        "reported_decimal_compared": compared,
        "exact_reported_decimal": exact,
        "exact_nonzero_reported_decimal": row["source_decimal_nonzero_exact"],
        "comparable_but_not_exact": compared - exact,
        "unassessed_of_55_possible_source_slots": SLOTS - compared,
        "ar6_source_variable_unit_slots_enumerated": row["source_slots_enumerated"],
        "ar6_source_slots_not_enumerated": SLOTS - row["source_slots_enumerated"],
        "engage_slots_missing_or_noncomparable": row["source_slots_enumerated"] - compared,
        "variables_with_nonzero_exact": row["variables_with_nonzero_exact"],
        "exact_fraction_of_comparable": round(exact / compared, 6) if compared else None,
        "source_alias_or_model_version_verified": False,
    }


def audit(packet):
    if (packet.get("schema") != PRIVATE_SCHEMA
            or packet.get("handling") != "LOCAL_ONLY_DO_NOT_PUBLISH"
            or packet.get("original_selected_case") != CASE_ID
            or packet.get("source_sha256") != USER_OBSERVED_ENGAGE_SHA):
        raise AdjudicationError("Unexpected private fingerprint schema/source fingerprint")

    cases = packet.get("candidates_ranked_as_unverified_hypotheses")
    if not isinstance(cases, list) or not cases or packet.get("candidate_count") != len(cases):
        raise AdjudicationError("Private candidate count inconsistent")
    seen=set()
    checked=[]
    enumerated_source_slots=set()
    for row in cases:
        if not isinstance(row,dict) or not row.get("original_model") or not row.get("original_scenario"):
            raise AdjudicationError("Malformed private candidate identity")
        if row.get("candidate_group") not in GROUPS:
            raise AdjudicationError("Unregistered candidate group")
        if (type(row.get("exact_scenario_name")) is not bool
                or type(row.get("poles_model_label")) is not bool):
            raise AdjudicationError("Candidate group flags missing")
        if row["candidate_group"]=="POLES_FAMILY_OTHER_SCENARIO" and (
                not row["poles_model_label"] or row["exact_scenario_name"]):
            raise AdjudicationError("Contradictory source-group flags")
        if row["candidate_group"]=="EXACT_SCENARIO_OTHER_MODEL" and not row["exact_scenario_name"]:
            raise AdjudicationError("Contradictory exact-scenario flag")
        key=(row["original_model"],row["original_scenario"])
        if key in seen:
            raise AdjudicationError("Duplicate candidate identity")
        seen.add(key)
        for name in ("source_decimal_compared","source_decimal_exact",
                     "source_decimal_nonzero_exact","variables_with_exact",
                     "variables_with_nonzero_exact"):
            _integer(row,name)
        compared=row["source_decimal_compared"]
        exact=row["source_decimal_exact"]
        nonzero=row["source_decimal_nonzero_exact"]
        if not (0<=nonzero<=exact<=compared<=SLOTS):
            raise AdjudicationError("Inconsistent source-decimal status counters")
        if not (0<=row["variables_with_nonzero_exact"]<=
                row["variables_with_exact"]<=len(FOCUS)):
            raise AdjudicationError("Inconsistent variable counts")
        status_counts=row.get("status_counts")
        if not isinstance(status_counts,dict) or any(
                type(v) is not int or v<0 for v in status_counts.values()):
            raise AdjudicationError("Malformed source comparison statuses")
        if (status_counts.get("EXACT_REPORTED_DECIMAL",0)!=exact
                or status_counts.get("EXACT_NONZERO",0)!=nonzero
                or status_counts.get("DISTINCT_VARIABLES_WITH_EXACT",0)!=row["variables_with_exact"]
                or status_counts.get("DISTINCT_VARIABLES_WITH_NONZERO_EXACT",0)!=row["variables_with_nonzero_exact"]):
            raise AdjudicationError("Reported exact/nonzero counts contradict status entries")
        if (sum(v for name,v in status_counts.items()
                if name == "EXACT_REPORTED_DECIMAL" or
                    name.startswith("NONZERO_REPORTED_DECIMAL__")) != compared):
            raise AdjudicationError("Comparable denominator inconsistent with statuses")
        source_slots=sum(v for name,v in status_counts.items()
               if name not in (
                   "EXACT_NONZERO",
                   "DISTINCT_VARIABLES_WITH_EXACT",
                   "DISTINCT_VARIABLES_WITH_NONZERO_EXACT",
               ))
        if not 0 < source_slots <= SLOTS or source_slots % len(YEARS) != 0:
            raise AdjudicationError("AR6 source variable-unit slot coverage requires manual audit")
        if compared>source_slots:
            raise AdjudicationError("Compared more source slots than registered")
        enumerated_source_slots.add(source_slots)
        row["source_slots_enumerated"]=source_slots
        checked.append(row)
    if len(enumerated_source_slots)!=1:
        raise AdjudicationError("Candidates use nonidentical source slot universes")

    ranked=sorted(checked,key=_score,reverse=True)
    leader=ranked[0]
    runner=ranked[1] if len(ranked)>1 else None
    maxexact=max(checked,key=lambda r:r["source_decimal_exact"])
    maxnonzero=max(checked,key=lambda r:r["source_decimal_nonzero_exact"])
    leader_score=_score(leader)
    ties=sum(_score(row)==leader_score for row in checked)
    by_group={}
    for group in sorted(GROUPS):
        group_rows=[row for row in checked if row["candidate_group"]==group]
        winner=max(group_rows,key=_score) if group_rows else None
        by_group[group]={
            "candidate_count":len(group_rows),
            "best":_leader_description(winner),
            "candidates_with_any_exact_nonzero":sum(
                row["source_decimal_nonzero_exact"]>0 for row in group_rows),
            "candidates_with_at_least_40_nonzero_exact":sum(
                row["source_decimal_nonzero_exact"]>=40 for row in group_rows),
        }
    report={
        "schema":"residualpathways.engage_v2_fingerprint_adjudication_public.v1",
        "case_id":CASE_ID,
        "status":PUBLISH_STATUS,
        "original_engage_v2_local_sha256":USER_OBSERVED_ENGAGE_SHA,
        "candidate_count":len(checked),
        "maximum_pre_registered_source_slots_per_candidate":SLOTS,
        "ar6_source_slots_enumerated_per_candidate":next(iter(enumerated_source_slots)),
        "candidate_groups":by_group,
        "ranking_rule":"NONZERO_EXACT_THEN_TOTAL_EXACT_THEN_DISTINCT_NONZERO_VARIABLES_THEN_COMPARABLE_COUNT",
        "top_ranked":_leader_description(leader),
        "runner_up":_leader_description(runner),
        "top_numerical_score_tie_count":ties,
        "top_two_nonzero_exact_gap":(
            leader["source_decimal_nonzero_exact"]-
            runner["source_decimal_nonzero_exact"] if runner else None),
        "top_two_total_exact_gap":(
            leader["source_decimal_exact"]-
            runner["source_decimal_exact"] if runner else None),
        "max_exact_and_max_nonzero_same_candidate": maxexact is maxnonzero,
        "top_ranked_equals_max_exact_candidate":leader is maxexact,
        "top_ranked_equals_max_nonzero_candidate":leader is maxnonzero,
        "candidates_full_55_exact":sum(
            row["source_decimal_exact"]==SLOTS and
            row["source_decimal_compared"]==SLOTS for row in checked),
        "candidates_with_at_least_40_nonzero_exact":sum(
            row["source_decimal_nonzero_exact"]>=40 for row in checked),
        "source_alias_confirmed":False,
        "source_processing_lineage":"NOT_ESTABLISHED",
        "physical_gross_and_atmospheric_removal":"NOT_ESTABLISHED",
        "science_review_state":"REVIEW_PENDING",
        "verified_i3":0,
        "interpretation":(
            "Exact decimal matches can be strong numerical correspondence "
            "without source-equivalent models, historical export metadata, "
            "physically independent positive gross emissions or atmospheric "
            "removal; source quantization and independent reviewer sign-off open."
        ),
    }
    return report


def write(private_source:Path, public_target:Path):
    private_source,public_target=Path(private_source).resolve(),Path(public_target).resolve()
    if (not private_source.is_file()
            or "ar6-private" not in private_source.parts
            or "ar6-private" in public_target.parts
            or private_source==public_target):
        raise AdjudicationError("Private source and separate public summary paths required")
    packet=json.loads(private_source.read_text(encoding="utf-8"))
    result=audit(packet)
    public_target.parent.mkdir(parents=True,exist_ok=True)
    public_target.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-source",type=Path,default=Path(
        "data/ar6-private/engage_v2_candidate_fingerprint_private.json"))
    parser.add_argument("--public-target",type=Path,default=Path(
        "results/ar6-canonical-gate/engage_v2_fingerprint_adjudication_public.json"))
    args=parser.parse_args()
    result=write(args.private_source,args.public_target)
    for key in ("candidate_count","top_ranked","runner_up",
                "top_numerical_score_tie_count",
                "top_two_nonzero_exact_gap","top_two_total_exact_gap",
                "max_exact_and_max_nonzero_same_candidate",
                "candidates_with_at_least_40_nonzero_exact"):
        print(key+": "+json.dumps(result[key],sort_keys=True))
    print("NO SOURCE ALIAS OR PHYSICAL CDR RECONSTRUCTION ESTABLISHED")


if __name__=="__main__":
    main()
