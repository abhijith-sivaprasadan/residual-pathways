"""Synthetic original-source field lineage tests: no numerical CDR imputation."""
import csv
from hashlib import md5
import json
import pytest

from residual_pathways import arc24_cemics_field_lineage as fl
from residual_pathways import arc24_cemics_crosswalk as cx
from residual_pathways.case_audit import CaseAuditError
from residual_pathways.stratify import sha_file


def source_fixture(tmp_path, monkeypatch, *, raw_regrowth="plus",
                   include_gross_in_ar6=False):
    private=tmp_path/"data"/"ar6-private"
    private.mkdir(parents=True)
    mif=private/"CDRoptionsAR6_complete.mif"
    world=private/"AR6_Scenarios_Database_World_v1.1.csv"
    rmd=private/"CDRoptions.Rmd"
    packet=private/"canonical_selected24_packet.json"
    name=(fl.REGROWTH if raw_regrowth=="exact"
          else "Emissions|CO2|Land|Land-use Change|+|Regrowth"
          if raw_regrowth=="plus"
          else "Emissions|CO2|Land|Land-use Change|++|Regrowth")
    with mif.open("w",encoding="utf-8",newline="") as file:
        writer=csv.writer(file,delimiter=";")
        writer.writerow(["Model","Scenario","Region","Variable","Unit","2050",""])
        writer.writerow(["REMIND-MAgPIE","CEMICS_SSP1-1p5C-noCDR","World",
                         name,"Mt CO2/yr","-2.5",""])
        writer.writerow(["REMIND-MAgPIE","CEMICS_SSP1-1p5C-noCDR","World",
                         fl.GROSS,"Mt CO2/yr","30.0",""])
    with world.open("w",encoding="utf-8",newline="") as file:
        writer=csv.writer(file)
        writer.writerow(["Model","Scenario","Region","Variable","Unit","2050"])
        writer.writerow([cx.MODEL,cx.SCENARIO,"World","Emissions|CO2",
                         "Mt CO2/yr","15"])
        if include_gross_in_ar6:
            writer.writerow([cx.MODEL,cx.SCENARIO,"World",fl.GROSS,
                             "Mt CO2/yr","30"])
    rmd.write_text(
        'data <- deletePlus(data)\n'
        'CDRaff <- -data[,,"Emissions|CO2|Land|Land-use Change|Regrowth (Mt CO2/yr)"]\n',
        encoding="utf-8",
    )
    cases=[{
        "case_id":f"ARC24-{i:02d}",
        "model":cx.MODEL if i==3 else "OTHER",
        "scenario":cx.SCENARIO if i==3 else "OTHER",
        "source_observations":{"Emissions|CO2":{"raw":"15","unit":"Mt CO2/yr"}}
        if i==3 else {},
    } for i in range(1,25)]
    packet.write_text(json.dumps({
        "schema":"residualpathways.ar6_canonical_selected24.private.v1",
        "handling":"LOCAL_ONLY_DO_NOT_PUBLISH",
        "source_sha256":sha_file(world),
        "cases":cases,
    }))
    monkeypatch.setattr(fl,"EXPECTED_ARCHIVE_MD5",md5(mif.read_bytes()).hexdigest())
    monkeypatch.setattr(fl,"AUTHOR_SUPPORT_MD5",{
        "authors_rmd":md5(rmd.read_bytes()).hexdigest()
    })
    return mif,world,packet,rmd,tmp_path/"results"/"lineage.json"


def test_source_plus_hierarchy_marker_is_diagnostic_not_auto_alias(tmp_path,monkeypatch):
    args=source_fixture(tmp_path,monkeypatch)
    result=fl.inventory(*args)
    author=result["original_author_fields"][0]
    ar6=result["original_ar6_fields"][0]
    assert author["raw_exact_name_present"] is False
    assert author["unique_marker_candidate_without_exact_match"] is True
    assert author["marker_candidate_count"]==1
    assert author["marker_candidate_source_units"][0]["units"][0][
        "year2050_cells_present"]==1
    assert ar6["marker_candidate_count"]==0
    assert not result["automatic_variable_rename_accepted"]
    assert result["operational_CDRtotal_computed"] is False
    assert result["verified_i3"]==0
    published=args[-1].read_text()
    assert '"-2.5"' not in published
    assert '"30.0"' not in published


def test_direct_name_is_not_reported_as_hierarchy_alias(tmp_path,monkeypatch):
    args=source_fixture(tmp_path,monkeypatch,raw_regrowth="exact",
                        include_gross_in_ar6=True)
    result=fl.inventory(*args)
    assert result["original_author_fields"][0]["raw_exact_name_present"]
    assert result["original_author_fields"][0]["marker_candidate_count"]==0
    assert result["original_ar6_fields"][1]["raw_exact_name_present"]
    assert result["verified_i3"]==0


def test_double_plus_marker_candidate_visible_not_substituted(tmp_path,monkeypatch):
    args=source_fixture(tmp_path,monkeypatch,raw_regrowth="plusplus")
    result=fl.inventory(*args)
    assert result["original_author_fields"][0]["marker_candidate_count"]==1
    assert "|++|" in result["original_author_fields"][0][
        "hierarchy_marker_candidate_names"][0]
    assert not result["automatic_variable_rename_accepted"]


def test_remove_only_whole_hierarchy_tokens():
    assert fl.remove_hierarchy_markers("A|+|B|++|C")=="A|B|C"
    assert fl.remove_hierarchy_markers("C++|D|+-|E")=="C++|D|+-|E"


def test_author_source_md5_fails_closed(tmp_path,monkeypatch):
    args=source_fixture(tmp_path,monkeypatch)
    args[0].write_bytes(args[0].read_bytes()+b"\nmodified")
    with pytest.raises(CaseAuditError,match="MIF MD5 mismatch"):
        fl.inventory(*args)
    assert not args[-1].exists()


def test_source_Rmd_preprocessing_cannot_be_invented(tmp_path,monkeypatch):
    args=source_fixture(tmp_path,monkeypatch)
    args[3].write_text(args[3].read_text().replace(
        "data <- deletePlus(data)","data <- data"
    ))
    monkeypatch.setattr(fl,"AUTHOR_SUPPORT_MD5",{
        "authors_rmd":md5(args[3].read_bytes()).hexdigest()
    })
    with pytest.raises(CaseAuditError,match="deletePlus"):
        fl.inventory(*args)


def test_private_report_location_refused(tmp_path,monkeypatch):
    args=source_fixture(tmp_path,monkeypatch)
    with pytest.raises(CaseAuditError,match="must stay under ar6-private"):
        fl.inventory(*(list(args[:-1])+[args[0].parent/"bad.json"]))



def test_field_lineage_cli_uses_real_json_field_name(tmp_path, monkeypatch, capsys):
    """Regression for user-observed KeyError after successfully written JSON."""
    args = source_fixture(tmp_path, monkeypatch)
    from residual_pathways.__main__ import main
    monkeypatch.setattr("sys.argv", [
        "residual_pathways", "arc24-cemics-field-lineage",
        "--mif", str(args[0]), "--world", str(args[1]),
        "--packet", str(args[2]), "--rmd", str(args[3]),
        "--output", str(args[4]),
    ])
    main()
    printed = capsys.readouterr().out
    assert "hierarchy candidates: 1" in printed
    assert "No substitution or derived CDR; I3: 0" in printed
    assert args[4].is_file()
