"""Synthetic source-locked CEMICS numerical fingerprint and negative controls."""
import csv
from hashlib import md5
import json
import pytest

from residual_pathways import arc24_cemics_alias_fingerprint as cf
from residual_pathways.case_audit import CaseAuditError, TOTAL, SIX
from residual_pathways.stratify import sha_file

VARS = (TOTAL,SIX[0],SIX[1],SIX[2])
YEARS = (2030,2040,2050,2060,2070)


def build(tmp_path, monkeypatch, *, make_alias_different=False):
    private=tmp_path/"data"/"ar6-private"
    private.mkdir(parents=True)
    mif=private/"CDRoptionsAR6_complete.mif"
    world=private/"AR6_Scenarios_Database_World_v1.1.csv"
    rmd=private/"CDRoptions.Rmd"
    orig={
        cf.AUTHOR_NO: {v:[str(10 + (i+1) + j) for j in range(5)]
                       for i,v in enumerate(VARS)},
        cf.AUTHOR_FULL: {v:[str(50 + (i+1) + j) for j in range(5)]
                         for i,v in enumerate(VARS)},
    }
    pub={
        cf.AR6_MIN: {v:values[:] for v,values in orig[cf.AUTHOR_NO].items()},
        cf.AR6_FULL: {v:values[:] for v,values in orig[cf.AUTHOR_FULL].items()},
    }
    if make_alias_different:
        pub[cf.AR6_MIN][TOTAL][3]="1000"
    with mif.open("w",newline="",encoding="utf-8") as f:
        writer=csv.writer(f,delimiter=";")
        writer.writerow(["Model","Scenario","Region","Variable","Unit"]+
                        list(map(str,YEARS))+[""])
        for name,variables in orig.items():
            for variable,values in variables.items():
                writer.writerow([cf.ARCHIVE_MODEL,name,"World",variable,
                                 "Mt CO2/yr"]+values+[""])
    with world.open("w",newline="",encoding="utf-8") as f:
        writer=csv.writer(f)
        writer.writerow(["Model","Scenario","Region","Variable","Unit"]+
                        list(map(str,YEARS)))
        for name,variables in pub.items():
            for variable,values in variables.items():
                writer.writerow([cf.MODEL,name,"World",variable,"Mt CO2/yr"]+values)
    cases=[]
    for i in range(1,25):
        cases.append({
            "case_id":f"ARC24-{i:02d}",
            "model":cf.MODEL if i==3 else "UNRELATED",
            "scenario":cf.AR6_MIN if i==3 else "UNRELATED",
            "source_observations":{
                var:{"unit":"Mt CO2/yr","raw":value[2],"value":float(value[2])}
                for var,value in pub[cf.AR6_MIN].items()
            } if i==3 else {},
        })
    packet=private/"canonical_selected24_packet.json"
    packet.write_text(json.dumps({
        "schema":"residualpathways.ar6_canonical_selected24.private.v1",
        "handling":"LOCAL_ONLY_DO_NOT_PUBLISH",
        "cases":cases,"source_sha256":sha_file(world),
    }))
    rmd.write_bytes(b"noCDR means archive label;\nmin CDR name in prose;\nfullCDR scenario\n")
    monkeypatch.setattr(cf,"EXPECTED_ARCHIVE_MD5",md5(mif.read_bytes()).hexdigest())
    monkeypatch.setattr(cf,"AUTHOR_SUPPORT_MD5",{
        "authors_rmd":md5(rmd.read_bytes()).hexdigest()
    })
    return mif,world,packet,rmd,tmp_path/"results"/"cemics_alias.json"


def test_identity_controls_and_redaction(tmp_path,monkeypatch):
    mif,world,packet,rmd,output=build(tmp_path,monkeypatch)
    result=cf.write_author_alias_fingerprints(mif,world,packet,output,rmd=rmd)
    bycode={x["comparison"]:x for x in result["comparisons"]}
    assert result["verified_i3"]==0
    assert result["scientific_source_alias_verified"] is False
    assert bycode["FULL_SAME_LABEL_CONTROL"]["exact_decimal_matches"]==20
    assert bycode["NOCDR_TO_MINCDR_HYPOTHESIS"]["exact_decimal_matches"]==20
    assert bycode["FULL_TO_MINCDR_NEGATIVE_CONTROL"]["exact_decimal_matches"]==0
    assert bycode["NOCDR_TO_FULL_NEGATIVE_CONTROL"]["exact_decimal_matches"]==0
    assert bycode["NOCDR_TO_MINCDR_HYPOTHESIS"]["shared_variable_names"]==4
    assert result["author_Rmd_source_text_evidence"]["keyword_line_counts"]["nocdr"]==1
    assert "110" not in output.read_text()
    assert '"10"' not in output.read_text()
    assert "scenario-name mapping is approved" not in output.read_text()


def test_not_matching_years_cannot_claim_source_alias(tmp_path,monkeypatch):
    mif,world,packet,rmd,output=build(
        tmp_path,monkeypatch,make_alias_different=True)
    result=cf.compare_author_aliases(mif,world,packet,output)
    bycode={x["comparison"]:x for x in result["comparisons"]}
    assert bycode["NOCDR_TO_MINCDR_HYPOTHESIS"]["exact_decimal_matches"]==19
    assert bycode["NOCDR_TO_MINCDR_HYPOTHESIS"]["year_variable_compared"]==20
    assert bycode["NOCDR_TO_MINCDR_HYPOTHESIS"]["status_counts"]["NONZERO_AT_LEAST_10_PERCENT"]==1
    assert not result["scientific_source_alias_verified"]


def test_author_mif_checksum_failure(tmp_path,monkeypatch):
    mif,world,packet,rmd,output=build(tmp_path,monkeypatch)
    mif.write_bytes(mif.read_bytes()+b"\nmodified")
    with pytest.raises(CaseAuditError,match="MIF MD5"):
        cf.write_author_alias_fingerprints(mif,world,packet,output)
    assert not output.exists()


def test_ar6_world_checksum_failure(tmp_path,monkeypatch):
    mif,world,packet,rmd,output=build(tmp_path,monkeypatch)
    data=json.loads(packet.read_text())
    data["source_sha256"]="0"*64
    packet.write_text(json.dumps(data))
    with pytest.raises(CaseAuditError,match="source SHA changed"):
        cf.compare_author_aliases(mif,world,packet,output)


def test_2050_original_selection_mismatch(tmp_path,monkeypatch):
    mif,world,packet,rmd,output=build(tmp_path,monkeypatch)
    data=json.loads(packet.read_text())
    data["cases"][2]["source_observations"][TOTAL]["raw"]="999"
    packet.write_text(json.dumps(data))
    with pytest.raises(CaseAuditError,match="2050 value differs"):
        cf.compare_author_aliases(mif,world,packet,output)


def test_private_output_not_allowed(tmp_path,monkeypatch):
    mif,world,packet,rmd,output=build(tmp_path,monkeypatch)
    with pytest.raises(CaseAuditError,match="must remain private"):
        cf.write_author_alias_fingerprints(
            mif,world,packet,mif.parent/"unsafe_public.json")


def test_supporting_Rmd_checksum_enforced(tmp_path,monkeypatch):
    mif,world,packet,rmd,output=build(tmp_path,monkeypatch)
    rmd.write_bytes(rmd.read_bytes()+b"\nchanged")
    with pytest.raises(CaseAuditError,match="R Markdown MD5 mismatch"):
        cf.compare_author_aliases(mif,world,packet,output,rmd_path=rmd)
