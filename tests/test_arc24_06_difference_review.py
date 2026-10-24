"""Source-free tests: isolate three decimals without leaking licensed values."""
import csv
import json
from pathlib import Path

import pytest

from residual_pathways.arc24_engage_v2_probe import (
    MODEL, SCENARIO, UNIT, FOCUS, YEARS, TOTAL, V2_FILENAME, _digest, _data
)
from residual_pathways.arc24_engage_v2_candidate_fingerprint import (
    load_candidates, fingerprint
)
from residual_pathways.arc24_06_difference_review import (
    DifferenceReviewError, analyze_differences, review
)
import residual_pathways.arc24_engage_v2_fingerprint_adjudication as adj

FAKE = {name:str(21+7*i) for i,name in enumerate(FOCUS)}
LEADER_MODEL = "POLES-ENGAGE new source model label"
CONTROL_SCENARIO = "EN_NPi2020_500f"

def write_world(path,pairs):
    fieldnames=["Model","Scenario","Region","Variable","Unit",*map(str,YEARS)]
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fieldnames)
        w.writeheader()
        for model,scenario,delta in pairs:
            for variable in FOCUS:
                row={"Model":model,"Scenario":scenario,"Region":"World",
                    "Variable":variable,"Unit":UNIT}
                for year in YEARS:
                    adjustment=(1 if model==LEADER_MODEL and
                         (variable,year) in {
                         (FOCUS[0],2030),(FOCUS[2],2050),(FOCUS[4],2070)} else 0)
                    row[str(year)]=str(int(FAKE[variable])+delta+adjustment)
                w.writerow(row)

def synthetic(tmp):
    private=tmp/"data/ar6-private"
    private.mkdir(parents=True)
    world=private/"AR6_Scenarios_Database_World_v1.1.csv"
    en=private/V2_FILENAME
    packet=private/"canonical_selected24_packet.json"
    fingerprint_path=private/"engage_v2_candidate_fingerprint_private.json"
    write_world(world,[(MODEL,SCENARIO,0)])
    write_world(en,[(LEADER_MODEL,SCENARIO,0),
                    (LEADER_MODEL,CONTROL_SCENARIO,77)])
    packet.write_text(json.dumps({
        "schema":"residualpathways.ar6_canonical_selected24.private.v1",
        "handling":"LOCAL_ONLY_DO_NOT_PUBLISH",
        "source_sha256":_digest(world),
        "cases":[
            {"case_id":f"ARC24-{i:02d}",
             "model":MODEL if i==6 else "other-model",
             "scenario":SCENARIO if i==6 else f"other-run{i}",
             "source_observations":({TOTAL:{"unit":UNIT,"raw":FAKE[TOTAL]}} if i==6 else {})}
            for i in range(1,25)
        ]
    }))
    original,_=_data(world)
    pairs={(LEADER_MODEL,SCENARIO),(LEADER_MODEL,CONTROL_SCENARIO)}
    source=load_candidates(en,pairs)
    results=fingerprint(original,source,pairs)
    fingerprint_path.write_text(json.dumps({
        "schema":"residualpathways.engage_v2_fingerprint_private.v1",
        "handling":"LOCAL_ONLY_DO_NOT_PUBLISH",
        "original_selected_case":"ARC24-06",
        "source_sha256":_digest(en),
        "candidate_count":len(results),
        "candidates_ranked_as_unverified_hypotheses":results
    }))
    return private,world,en,packet,fingerprint_path

def test_three_source_differences_identified_with_no_values(tmp_path,monkeypatch):
    private,world,en,packet,fp=synthetic(tmp_path)
    monkeypatch.setattr(adj,"USER_OBSERVED_ENGAGE_SHA",_digest(en))
    safe=tmp_path/"results/safe.json"
    hidden=private/"three.json"
    result=review(world,en,packet,fp,safe,hidden,
        expected_world_sha=_digest(world),expected_engage_sha=_digest(en),
        verify_expected=(52,52))
    assert result["source_case_compared_cells"]==55
    assert result["exact_reported_decimal_matches"]==52
    assert result["exact_nonzero_matches"]==52
    assert result["different_reported_decimal_cells"]==3
    assert result["difference_sign_retain_count"]==3
    assert result["difference_sign_flip_count"]==0
    assert sum(result["difference_precision_bands"].values())==3
    assert result["verified_i3"]==0
    p=json.loads(hidden.read_text())
    changed=p["differences_by_variable_unit_year_no_values"]
    assert {(x["variable"],x["year"]) for x in changed}=={
        (FOCUS[0],2030),(FOCUS[2],2050),(FOCUS[4],2070)}
    assert all(x["original_reported_decimal_status"].startswith(
        "NONZERO_REPORTED_DECIMAL__") for x in changed)
    public_text=safe.read_text()
    assert LEADER_MODEL not in public_text and SCENARIO not in public_text
    assert FOCUS[0] not in public_text
    assert '"77"' not in public_text
    assert '"21"' not in public_text
    # The private report includes identifying field/year context but no values.
    assert '"22"' not in hidden.read_text()


def test_sign_and_zero_transition_classification():
    orig={(name,UNIT):{y:__import__("decimal").Decimal("5") for y in YEARS}
          for name in FOCUS}
    cand={(name,UNIT):{y:__import__("decimal").Decimal("5") for y in YEARS}
          for name in FOCUS}
    cand[(FOCUS[0],UNIT)][2030]=__import__("decimal").Decimal("0")
    cand[(FOCUS[1],UNIT)][2040]=__import__("decimal").Decimal("-5")
    pub,private=analyze_differences(orig,cand,"POLES source","run")
    assert pub["difference_zero_transition_count"]==1
    assert pub["difference_sign_flip_count"]==1
    assert pub["exact_reported_decimal_matches"]==53
    assert len(private["differences_by_variable_unit_year_no_values"])==2
    assert pub["source_model_scenario_alias"]=="NOT_ESTABLISHED"


def test_private_result_path_and_original_fingerprint_guard(tmp_path,monkeypatch):
    private,world,en,packet,fp=synthetic(tmp_path)
    monkeypatch.setattr(adj,"USER_OBSERVED_ENGAGE_SHA",_digest(en))
    with pytest.raises(DifferenceReviewError,match="private"):
        review(world,en,packet,fp,private/"incorrect-public.json",
               tmp_path/"outside.json",
               expected_world_sha=_digest(world),expected_engage_sha=_digest(en),
               verify_expected=(52,52))
    with pytest.raises(DifferenceReviewError,match="fingerprints"):
        review(world,en,packet,fp,tmp_path/"safe.json",
               private/"safe.json",expected_world_sha=_digest(world))


def test_unregistered_source_candidate_count_disagreement(tmp_path,monkeypatch):
    private,world,en,packet,fp=synthetic(tmp_path)
    monkeypatch.setattr(adj,"USER_OBSERVED_ENGAGE_SHA",_digest(en))
    data=json.loads(fp.read_text())
    data["candidates_ranked_as_unverified_hypotheses"][0]["source_decimal_exact"]=53
    fp.write_text(json.dumps(data))
    with pytest.raises(adj.AdjudicationError):
        review(world,en,packet,fp,tmp_path/"results/safe.json",private/"report.json",
            expected_world_sha=_digest(world),expected_engage_sha=_digest(en),
            verify_expected=(52,52))
