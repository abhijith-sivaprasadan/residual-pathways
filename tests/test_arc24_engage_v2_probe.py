"""Synthetic-source tests for exact ENGAGE v2 and AR6 crosswalk, no raw release."""
import csv
from pathlib import Path
import json
import pytest

from residual_pathways.arc24_engage_v2_probe import (
    evaluate,write,EngageSourceError,_digest,FOCUS,V2_FILENAME,
    MODEL,SCENARIO,TOTAL,AFOLU,DEMAND,SUPPLY,INDUSTRY,OTHER,
)

YEARS = (2030,2040,2050,2060,2070)
FAKE = {
    TOTAL:"100",AFOLU:"10",DEMAND:"30",SUPPLY:"40",
    INDUSTRY:"15",OTHER:"5",
    "Emissions|CO2|Energy and Industrial Processes":"85",
    "Carbon Sequestration|CCS|Fossil":"4",
    "Carbon Sequestration|CCS|Biomass":"3",
    "Carbon Sequestration|Land Use":"2",
    "Carbon Sequestration|Direct Air Capture":"0",
}


def _write_csv(path, names):
    with path.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=["Model","Scenario","Region","Variable","Unit",*map(str,YEARS)])
        writer.writeheader()
        for name in names:
            writer.writerow({"Model":MODEL,"Scenario":SCENARIO,"Region":"World",
                             "Variable":name,"Unit":"Mt CO2/yr",
                             **{str(y):FAKE[name] for y in YEARS}})


def _inputs(tmp):
    private=tmp/"data/ar6-private"
    private.mkdir(parents=True,exist_ok=True)
    ar=private/"AR6_Scenarios_Database_World_v1.1.csv"
    en=private/V2_FILENAME
    _write_csv(ar,FOCUS)
    _write_csv(en,[n for n in FOCUS if n!=OTHER])
    source=[{"case_id":f"ARC24-{i:02d}","model":MODEL if i==6 else "synthetic",
             "scenario":SCENARIO if i==6 else f"synthetic-{i}",
             "source_observations":({TOTAL:{"unit":"Mt CO2/yr","raw":"100"}} if i==6 else {})}
            for i in range(1,25)]
    packet=private/"canonical_selected24_packet.json"
    packet.write_text(json.dumps({
        "schema":"residualpathways.ar6_canonical_selected24.private.v1",
        "handling":"LOCAL_ONLY_DO_NOT_PUBLISH",
        "source_sha256":_digest(ar),
        "cases":source,
    }))
    return ar,en,packet


def test_postprocessed_other_is_hypothesis_not_physical_proof(tmp_path):
    ar,en,packet=_inputs(tmp_path)
    output=tmp_path/"results/probe.json"
    res=write(ar,en,packet,output,expected_world_sha256=_digest(ar))
    assert res["status"]=="EXACT_CASE_MATCH_SOURCE_COMPARISONS_AVAILABLE"
    assert res["engage_v2_source_rows_for_case"]==len(FOCUS)-1
    assert res["derived_notebook_other_status_counts"]=={"EXACT_REPORTED_DECIMAL":5}
    assert res["source_reported_decimal_status_counts"]["ENGAGE_V2_SOURCE_VARIABLE_ABSENT"]==5
    assert res["verified_i3"]==0
    public=output.read_text()
    assert "synthetic-" not in public
    assert SCENARIO not in public
    assert '"100"' not in public
    assert "NOT_ESTABLISHED" in public


def test_source_unavailable_is_not_equivalence(tmp_path):
    ar,en,packet=_inputs(tmp_path)
    text=en.read_text().replace(SCENARIO,"another-not-identical-source-case")
    en.write_text(text)
    res=evaluate(ar,en,packet,expected_world_sha256=_digest(ar))
    assert res["status"]=="ENGAGE_V2_EXACT_MODEL_SCENARIO_NOT_FOUND"
    assert res["engage_v2_source_rows_for_case"]==0
    assert res["source_reported_decimal_status_counts"]=={}
    assert res["derived_notebook_other_status_counts"]=={}
    assert res["rows"]==[]
    assert res["unassessed_comparison_slots"]==55
    assert res["unassessed_notebook_years"]==5
    assert res["matching_basis"]=="EXACT_PAIR_ABSENT_NO_COMPARISON_PERFORMED"


def test_incorrect_ar6_hash_rejected(tmp_path):
    ar,en,packet=_inputs(tmp_path)
    with pytest.raises(EngageSourceError,match="World v1.1"):
        evaluate(ar,en,packet)


def test_missing_private_packet_guard(tmp_path):
    ar,en,packet=_inputs(tmp_path)
    with pytest.raises(EngageSourceError,match="private source"):
        evaluate(ar,en,tmp_path/"packet_public.json",expected_world_sha256=_digest(ar))


def test_wrong_saved_case_value_rejected(tmp_path):
    ar,en,packet=_inputs(tmp_path)
    document=json.loads(packet.read_text())
    document["cases"][5]["source_observations"][TOTAL]["raw"]="999"
    packet.write_text(json.dumps(document))
    with pytest.raises(EngageSourceError,match="2050 source"):
        evaluate(ar,en,packet,expected_world_sha256=_digest(ar))
