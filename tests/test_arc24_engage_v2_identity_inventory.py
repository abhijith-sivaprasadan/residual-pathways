"""No identity alias or source measurement should be inferred from name inventory."""
import csv
import json
from pathlib import Path
import pytest

from residual_pathways.arc24_engage_v2_identity_inventory import (
    analyze, execute, EngageIdentityError
)
from residual_pathways.arc24_engage_v2_probe import (
    MODEL,SCENARIO,V2_FILENAME,_digest
)

def _files(tmp):
    d=tmp/"data"/"ar6-private";d.mkdir(parents=True)
    csv_path=d/V2_FILENAME
    rows=[
        ("POLES ENGAGE v2", "EN_NPi2020_400f", "World","100"),
        ("POLES ENGAGE v2", "EN_NPi2020_400f", "World","101"),
        ("POLES ENGAGE", "EN_NPi2020_500f", "World","700"),
        ("POLES ENGAGE", "EN_NPi2020_400f", "R5.2ASIA","900"),
        ("OTHER MODEL", "other-scenario", "World","300"),
    ]
    with csv_path.open("w",newline="",encoding="utf8") as f:
        writer=csv.writer(f)
        writer.writerow(["Model","Scenario","Region","Variable","Unit","2050"])
        for i,(m,s,r,v) in enumerate(rows):
            writer.writerow([m,s,r,f"Emissions|CO2|Test{i}","Mt CO2/yr",v])
    packet=d/"canonical_selected24_packet.json"
    packet.write_text(json.dumps({
        "schema":"residualpathways.ar6_canonical_selected24.private.v1",
        "handling":"LOCAL_ONLY_DO_NOT_PUBLISH",
        "source_sha256":"4cf39b6b0d968e25ed389318acb1674f92146f977e9db4bfb7970f048ff73977",
        "cases":[
            {"case_id":f"ARC24-{i:02d}",
             "model":MODEL if i==6 else "DIFFERENT",
             "scenario":SCENARIO if i==6 else f"case{i}"} for i in range(1,25)
        ]}))
    return csv_path,packet,d

def test_inventory_never_equates_name_similarity_to_identity(tmp_path):
    path,packet,d=_files(tmp_path)
    public=tmp_path/"results"/"safe.json"
    private=d/"candidates.json"
    out=execute(path,packet,public,private,expected_engage_sha=_digest(path))
    assert out["status"]=="EXACT_SCENARIO_FOUND_DIFFERENT_OR_UNKNOWN_MODEL"
    assert out["exact_model_scenario_world_pair_found"] is False
    assert out["distinct_world_model_scenario_pairs"]==3
    assert out["exact_model_label_found"] is True
    assert out["exact_scenario_pairs_across_all_model_labels"]==1
    assert out["poles_containing_model_label_count"]==2
    assert out["world_rows_scanned"]==4
    assert out["source_rows_scanned"]==5
    assert out["verified_i3"]==0
    assert "EN_NPi2020_500f" not in public.read_text()
    assert "POLES ENGAGE v2" not in public.read_text()
    assert '"900"' not in public.read_text()
    data=json.loads(private.read_text())
    assert data["handling"]=="LOCAL_ONLY_DO_NOT_PUBLISH"
    assert data["candidate_count"] >= 1
    assert any(x["scenario"]=="EN_NPi2020_500f" for x in data["candidate_scenario_names_not_validated_as_aliases"])

def test_exact_identity_and_case_difference():
    pub, private=analyze({(MODEL,SCENARIO),("POLES ENGAGE", "EN_NPi2020_500f")})
    assert pub["status"]=="EXACT_MATCH_FOUND"
    assert pub["exact_model_scenario_world_pair_found"] is True
    assert pub["exact_model_label_found"] is True
    assert len(private)>=1

def test_absent_model_and_scenario_is_not_an_alias():
    pub,_=analyze({("ANOTHER MODEL","DIFFERENT")})
    assert pub["status"]=="NEITHER_EXACT_NAME_FOUND"
    assert pub["poles_family_candidate_pairs"]==0
    assert pub["private_lexical_leads_retained"]==0
    assert pub["verified_i3"]==0

def test_wrong_author_observed_source_hash_rejected(tmp_path):
    path,packet,d=_files(tmp_path)
    with pytest.raises(EngageIdentityError,match="author-observed"):
        execute(path,packet,tmp_path/"results/out.json",d/"private.json")

def test_private_and_public_output_path_enforced(tmp_path):
    path,packet,d=_files(tmp_path)
    with pytest.raises(EngageIdentityError,match="ar6-private"):
        execute(path,packet,d/"incorrect-public.json",tmp_path/"outside.json",
                expected_engage_sha=_digest(path))
