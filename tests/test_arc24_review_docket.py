"""Model-specific ARC24 docket tests with synthetic source identities."""
import json
from pathlib import Path

import pytest
from residual_pathways.arc24_review_docket import (
    make_queue, build, DocketError, WORLD_SHA, META_SHA, PRIORITIES, GATES,
)


def private_packet():
    return {
        "schema":"residualpathways.ar6_canonical_selected24.private.v1",
        "handling":"LOCAL_ONLY_DO_NOT_PUBLISH",
        "source_sha256":WORLD_SHA, "metadata_sha256":META_SHA,
        "cases":[
            {"case_id":f"ARC24-{i:02d}","model":"POLES ENGAGE" if i==6 else "UNTESTED-SYNTHETIC",
             "scenario":f"DO_NOT_EXPORT_SECRET_SCENARIO_{i}", "category":f"C{(i-1)//3+1}",
             "year":2050,"source_observations":{"Emissions|CO2":{"value":i}}}
            for i in range(1,25)
        ],
    }


def test_private_docket_scopes_and_safe_public_queue():
    internal,pub=make_queue(private_packet())
    assert len(internal["cases"]) == 24
    assert len(pub["cases"]) == 24
    assert pub["reviewed_cases"] == pub["verified_i3_cases"] == 0
    assert sum(x["priority"] for x in pub["cases"])==len(PRIORITIES)
    assert all(x["identifiability_grade"]=="NOT_DETERMINED" for x in pub["cases"])
    model=next(x for x in internal["cases"] if x["case_id"]=="ARC24-06")
    assert model["research_group"] == "POLES-ENGAGE / GLOBIOM LAND AND CO2 OTHER"
    assert set(model["evidence_gates"]) == set(GATES)
    assert not model["verified_i3"]
    assert "DO_NOT_EXPORT_SECRET_SCENARIO" not in json.dumps(pub)
    assert "source_observations" not in json.dumps(internal)


def test_private_path_enforcement(tmp_path):
    private_dir=tmp_path/"data/ar6-private";private_dir.mkdir(parents=True)
    inp=private_dir/"packet.json";inp.write_text(json.dumps(private_packet()))
    output=tmp_path/"results/review.json"
    docket=private_dir/"docket.json"
    result=build(inp,docket,output)
    assert result["reviewed_cases"]==0
    assert output.exists() and docket.exists()
    assert "DO_NOT_EXPORT_SECRET_SCENARIO" not in output.read_text()
    assert "DO_NOT_EXPORT_SECRET_SCENARIO" in docket.read_text()
    with pytest.raises(DocketError):
        build(inp,tmp_path/"BAD_PUBLIC_DOCKET.json",output)


def test_reject_unregistered_inputs():
    bad=private_packet()
    bad["metadata_sha256"]="f"*64
    with pytest.raises(DocketError):
        make_queue(bad)
