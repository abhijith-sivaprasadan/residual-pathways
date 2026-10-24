"""Synthetic regression tests for original-source ENGAGE v2 candidate fingerprint.

No original IAMC rows are included: values are simple invented controls.
"""
import csv
import json
from pathlib import Path

import pytest

from residual_pathways.arc24_engage_v2_probe import (
    CASE_ID, MODEL, SCENARIO, YEARS, FOCUS, TOTAL, UNIT, V2_FILENAME, _digest
)
from residual_pathways.arc24_engage_v2_candidate_fingerprint import (
    execute, fingerprint, candidate_groups, compare, FingerprintError
)

FAKE={name:str(5+i*7) for i,name in enumerate(FOCUS)}
FAKE["Carbon Sequestration|Direct Air Capture"]="0"
SOURCE_POLES="POLES-ENGAGE 2.0"

def _write_source(path, candidates):
    with path.open("w",newline="",encoding="utf-8") as f:
        fields=["Model","Scenario","Region","Variable","Unit",*map(str,YEARS)]
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        for model, scenario, delta in candidates:
            for name in FOCUS:
                val=str(int(FAKE[name])+delta)
                w.writerow({
                    "Model":model,"Scenario":scenario,"Region":"World",
                    "Variable":name,"Unit":UNIT,
                    **{str(y):val for y in YEARS}
                })

def _prepare(tmp_path):
    private=tmp_path/"data/ar6-private"
    private.mkdir(parents=True)
    ar6=private/"AR6_Scenarios_Database_World_v1.1.csv"
    engage=private/V2_FILENAME
    packet=private/"canonical_selected24_packet.json"
    _write_source(ar6,[(MODEL,SCENARIO,0)])
    _write_source(engage,[
        (SOURCE_POLES,SCENARIO,0),  # controlled identity-label-only change
        (SOURCE_POLES,"EN_NPi2020_500f",33),  # POLES crossed scenario
        ("NONPOLES MODEL",SCENARIO,99), # same scenario name, different source model
    ])
    packet.write_text(json.dumps({
        "schema":"residualpathways.ar6_canonical_selected24.private.v1",
        "handling":"LOCAL_ONLY_DO_NOT_PUBLISH",
        "source_sha256":_digest(ar6),
        "cases":[
            {"case_id":f"ARC24-{i:02d}",
             "model":MODEL if i==6 else "SYNTHETIC",
             "scenario":SCENARIO if i==6 else f"OTHER{i}",
             "source_observations":({TOTAL:{"unit":UNIT,"raw":FAKE[TOTAL]}} if i==6 else {})}
            for i in range(1,25)
        ]
    }))
    return ar6,engage,packet,private


def test_name_change_positive_and_crossed_controls(tmp_path):
    ar6,engage,packet,private=_prepare(tmp_path)
    public=tmp_path/"results/public.json"
    hidden=private/"candidates.json"
    result=execute(ar6,engage,packet,public,hidden,
                   expected_world_sha=_digest(ar6),
                   expected_engage_sha=_digest(engage))
    assert result["candidate_total"]==3
    assert result["exact_scenario_other_model_candidates"]==2
    assert result["poles_family_other_scenario_controls"]==1
    assert result["exact_scenario_under_poles_model_found"] is True
    assert result["maximum_exact_reported_decimal_cells"]==55
    assert result["maximum_exact_nonzero_cells"]==50
    assert result["any_fully_exact_source_series_candidate"] is True
    assert result["source_model_equivalence"]=="NOT_ESTABLISHED"
    assert result["verified_i3"]==0
    public_text=public.read_text()
    for token in (SCENARIO,SOURCE_POLES,"NONPOLES MODEL",'"33"','"99"'):
        assert token not in public_text
    internals=json.loads(hidden.read_text())
    assert internals["handling"]=="LOCAL_ONLY_DO_NOT_PUBLISH"
    assert len(internals["candidates_ranked_as_unverified_hypotheses"])==3
    winner=internals["candidates_ranked_as_unverified_hypotheses"][0]
    assert winner["original_model"]==SOURCE_POLES
    assert winner["source_decimal_exact"]==55
    assert winner["source_decimal_nonzero_exact"]==50
    assert winner["model_version_equivalent"]=="NOT_VERIFIED"
    assert winner["scenario_alias_approved"] is False


def test_no_identical_name_model_pair_not_auto_mapped():
    groups=candidate_groups({
        ("MODEL-A",SCENARIO),
        ("POLES-V2","another-scenario"),
        ("UNRELATED","another-scenario")
    })
    assert len(groups)==2
    assert set(groups.values())=={
        "EXACT_SCENARIO_OTHER_MODEL","POLES_FAMILY_OTHER_SCENARIO"
    }
    assert compare({("Emissions|CO2",UNIT):{2050:None}}, {})["SOURCE_VARIABLE_OR_UNIT_NOT_SHARED"]==len(YEARS)


def test_wrong_engage_source_bytes_rejected(tmp_path):
    ar6,engage,packet,private=_prepare(tmp_path)
    with pytest.raises(FingerprintError,match="source files"):
        execute(ar6,engage,packet,tmp_path/"report.json",private/"dossier.json",
                expected_world_sha=_digest(ar6))


def test_private_public_separation(tmp_path):
    ar6,engage,packet,private=_prepare(tmp_path)
    with pytest.raises(FingerprintError,match="source-protected"):
        execute(ar6,engage,packet,private/"bad_public.json",
                tmp_path/"not_private.json",
                expected_world_sha=_digest(ar6),
                expected_engage_sha=_digest(engage))


def test_duplicate_original_candidate_variable_rejected(tmp_path):
    ar6,engage,packet,private=_prepare(tmp_path)
    with engage.open("a",encoding="utf-8") as f:
        line=f"{SOURCE_POLES},{SCENARIO},World,{TOTAL},{UNIT},"+ ",".join("1" for _ in YEARS) + "\n"
        f.write(line)
    with pytest.raises(FingerprintError,match="Ambiguous repeated"):
        execute(ar6,engage,packet,tmp_path/"results/report.json",private/"hidden.json",
                expected_world_sha=_digest(ar6),
                expected_engage_sha=_digest(engage))
