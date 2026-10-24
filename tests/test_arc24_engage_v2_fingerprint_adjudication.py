"""Synthetic private candidate-status tests; no AR6/ENGAGE observations included."""
import json
from pathlib import Path

import pytest

from residual_pathways.arc24_engage_v2_fingerprint_adjudication import (
    audit,write,AdjudicationError,USER_OBSERVED_ENGAGE_SHA
)

def candidate(name,group,exact,nonzero,compared=55):
    mismatch=compared-exact
    absent=55-compared
    assert nonzero<=exact and mismatch>=0 and absent>=0
    statuses={
        "EXACT_REPORTED_DECIMAL":exact,
        "EXACT_NONZERO":nonzero,
        "DISTINCT_VARIABLES_WITH_EXACT":11 if exact>=11 else 1,
        "DISTINCT_VARIABLES_WITH_NONZERO_EXACT":10 if nonzero>=10 else int(nonzero>0),
        "NONZERO_REPORTED_DECIMAL__BELOW_0_1_PERCENT":mismatch,
        "MISSING_YEAR_VALUE":absent,
    }
    return {
        "candidate_code":"PRIVATE-"+name,
        "original_model":"POLES SOURCE" if group=="POLES_FAMILY_OTHER_SCENARIO" else "SYNTHETIC MODEL",
        "original_scenario":name,
        "candidate_group":group,
        "exact_scenario_name":group=="EXACT_SCENARIO_OTHER_MODEL",
        "poles_model_label":group=="POLES_FAMILY_OTHER_SCENARIO",
        "source_decimal_compared":compared,
        "source_decimal_exact":exact,
        "source_decimal_nonzero_exact":nonzero,
        "variables_with_exact":statuses["DISTINCT_VARIABLES_WITH_EXACT"],
        "variables_with_nonzero_exact":statuses["DISTINCT_VARIABLES_WITH_NONZERO_EXACT"],
        "match_fraction":round(exact/compared,6),
        "status_counts":statuses,
        "model_version_equivalent":"NOT_VERIFIED",
        "scenario_alias_approved":False,
        "physical_accounting":"NOT_ESTABLISHED",
    }

def packet():
    candidates=[
        candidate("SCENARIO-LEADER","EXACT_SCENARIO_OTHER_MODEL",52,51,55),
        candidate("CONTROL-ONE","POLES_FAMILY_OTHER_SCENARIO",48,44,55),
        candidate("CONTROL-TWO","POLES_FAMILY_OTHER_SCENARIO",10,9,55),
    ]
    return {
        "schema":"residualpathways.engage_v2_fingerprint_private.v1",
        "handling":"LOCAL_ONLY_DO_NOT_PUBLISH",
        "original_selected_case":"ARC24-06",
        "source_sha256":USER_OBSERVED_ENGAGE_SHA,
        "candidate_count":len(candidates),
        "candidates_ranked_as_unverified_hypotheses":candidates,
    }


def test_full_55_source_denominators_and_cross_control_rank():
    p=packet()
    report=audit(p)
    assert report["candidate_count"]==3
    assert report["top_ranked"]["exact_reported_decimal"]==52
    assert report["top_ranked"]["exact_nonzero_reported_decimal"]==51
    assert report["top_ranked"]["comparable_but_not_exact"]==3
    assert report["top_ranked"]["unassessed_of_55_possible_source_slots"]==0
    assert report["top_two_nonzero_exact_gap"]==7
    assert report["top_two_total_exact_gap"]==4
    assert report["candidate_groups"]["EXACT_SCENARIO_OTHER_MODEL"]["candidate_count"]==1
    assert report["candidate_groups"]["POLES_FAMILY_OTHER_SCENARIO"]["candidate_count"]==2
    assert report["top_numerical_score_tie_count"]==1
    assert report["source_alias_confirmed"] is False
    assert report["verified_i3"]==0
    text=json.dumps(report)
    assert "SCENARIO-LEADER" not in text
    assert "CONTROL-ONE" not in text
    assert "PRIVATE-" not in text


def test_partial_comparable_fraction_is_not_52_of_55():
    p=packet()
    winner=p["candidates_ranked_as_unverified_hypotheses"][0]
    winner["source_decimal_compared"]=52
    winner["status_counts"]["NONZERO_REPORTED_DECIMAL__BELOW_0_1_PERCENT"]=0
    winner["status_counts"]["MISSING_YEAR_VALUE"]=3
    report=audit(p)
    assert report["top_ranked"]["exact_fraction_of_comparable"]==1.0
    assert report["top_ranked"]["unassessed_of_55_possible_source_slots"]==3
    assert report["top_ranked"]["comparable_but_not_exact"]==0


def test_reject_mismatched_counters_and_modified_input():
    p=packet()
    p["candidates_ranked_as_unverified_hypotheses"][0]["source_decimal_exact"]=55
    with pytest.raises(AdjudicationError):
        audit(p)
    p=packet()
    p["source_sha256"]="bad"
    with pytest.raises(AdjudicationError):
        audit(p)


def test_privacy_guard(tmp_path):
    private=tmp_path/"data/ar6-private"
    private.mkdir(parents=True)
    p=private/"status-private.json"
    p.write_text(json.dumps(packet()))
    output=tmp_path/"results/public.json"
    result=write(p,output)
    assert result["verified_i3"]==0
    assert "SCENARIO-LEADER" not in output.read_text()
    assert "PRIVATE-" not in output.read_text()
    with pytest.raises(AdjudicationError):
        write(p,private/"incorrect.json")


def test_alternative_max_exact_and_max_nonzero_can_differ():
    p=packet()
    first=p["candidates_ranked_as_unverified_hypotheses"][0]
    first["source_decimal_nonzero_exact"]=40
    first["status_counts"]["EXACT_NONZERO"]=40
    second=p["candidates_ranked_as_unverified_hypotheses"][1]
    second["source_decimal_nonzero_exact"]=44
    second["status_counts"]["EXACT_NONZERO"]=44
    report=audit(p)
    assert report["max_exact_and_max_nonzero_same_candidate"] is False
    assert report["top_ranked_equals_max_nonzero_candidate"] is True
    assert report["top_ranked_equals_max_exact_candidate"] is False
