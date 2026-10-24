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



def test_expanded_family_inventory_sees_land_and_gross_not_in_old_narrow_context(
        tmp_path, monkeypatch):
    args = source_fixture(tmp_path, monkeypatch)
    # Populate the original source with multiple reporting leaves which the
    # old search only matching Regrowth, LUC and Gross Fossil omitted.
    original_source_extra = [
        ("Emissions|CO2|Land|Forest Conversion", "12.3"),
        ("Emissions|CO2|Land|+|Deforestation", "7.8"),
        ("Emissions|CO2|Industry|Process", "6.1"),
        ("Carbon Sequestration|Land Use", "3.4"),
        ("Carbon Sequestration|CCS|Biomass", "2.5"),
    ]
    with args[0].open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        for name, value in original_source_extra:
            writer.writerow(["REMIND-MAgPIE", "CEMICS_SSP1-1p5C-noCDR",
                             "World", name, "Mt CO2/yr", value, ""])
    monkeypatch.setattr(
        fl, "EXPECTED_ARCHIVE_MD5", md5(args[0].read_bytes()).hexdigest()
    )
    result = fl.inventory(*args)
    groups = result["expanded_emissions_family_inventory"]
    assert groups["co2_land_reporting"]["total_distinct_variable_names"] >= 3
    assert groups["gross_co2_reporting"]["total_distinct_variable_names"] == 1
    assert groups["fossil_and_industry_reporting"]["total_distinct_variable_names"] >= 2
    assert groups["land_sequestration_reporting"]["total_distinct_variable_names"] == 1
    land = {
        row["original_variable_name"]
        for row in groups["co2_land_reporting"]["reported_fields"]
    }
    assert "Emissions|CO2|Land|Forest Conversion" in land
    assert "Emissions|CO2|Land|+|Deforestation" in land
    assert "Emissions|CO2|Land|Land-use Change|+|Regrowth" in land
    assert result["operational_CDRtotal_computed"] is False
    assert not result["automatic_variable_rename_accepted"]
    assert result["verified_i3"] == 0
    public = args[-1].read_text(encoding="utf-8")
    for private_cell in ('"12.3"', '"7.8"', '"6.1"', '"3.4"', '"2.5"'):
        assert private_cell not in public


def test_family_name_buckets_not_interpreted_as_additive_partition():
    assert fl._within_group("Emissions|CO2|Land|Regrowth", "co2_land_reporting")
    assert fl._within_group(
        "Emissions|CO2|Land|Regrowth", "broad_land_emissions_and_cdr")
    assert not fl._within_group(
        "Carbon Sequestration|CCS|Fossil", "co2_land_reporting")
    assert not fl._within_group("Emissions|CO2|AFOLU", "co2_land_reporting")
    assert fl._within_group("Emissions|CO2|AFOLU", "afolu_or_other_reporting")
    with pytest.raises(CaseAuditError, match="Unknown emissions"):
        fl._within_group("Some name", "unknown")


def test_emissions_family_name_inventory_limit_reports_truncation():
    original = {}
    for n in range(fl.MAX_NAMES_PER_GROUP + 3):
        original[f"Emissions|CO2|Land|Synthetic Branch {n:04d}"] = [
            ("Mt CO2/yr", {2050: None})
        ]
    groups = fl._family_inventory(original, {})
    land = groups["co2_land_reporting"]
    assert land["total_distinct_variable_names"] == fl.MAX_NAMES_PER_GROUP + 3
    assert len(land["reported_fields"]) == fl.MAX_NAMES_PER_GROUP
    assert land["names_truncated"]
    assert all(not item["source_2050_value_reported"] for item in land["reported_fields"])



def test_land_relationships_compare_values_but_not_approve_physical_identity(
        tmp_path, monkeypatch):
    args=source_fixture(tmp_path, monkeypatch)
    mif, world, packet, rmd, output = args
    # Regrowth = -2.5 in the fixture; negated author study removal is +2.5.
    with mif.open("a", encoding="utf-8", newline="") as f:
        w=csv.writer(f, delimiter=";")
        for field,val in ((fl.LAND,"5.0"),(fl.AFFORESTATION,"2.5")):
            w.writerow(["REMIND-MAgPIE","CEMICS_SSP1-1p5C-noCDR",
                        "World",field,"Mt CO2/yr",val,""])
    with world.open("a", encoding="utf-8", newline="") as f:
        w=csv.writer(f)
        for field,val in ((fl.LAND,"5.0"),(fl.AFFORESTATION,"2.5")):
            w.writerow([cx.MODEL,cx.SCENARIO,"World",field,
                        "Mt CO2/yr",val])
    packet_data=json.loads(packet.read_text())
    packet_data["source_sha256"]=sha_file(world)
    packet.write_text(json.dumps(packet_data))
    monkeypatch.setattr(
        fl,"EXPECTED_ARCHIVE_MD5",md5(mif.read_bytes()).hexdigest())
    result=fl.inventory(*args)
    land=result["source_land_relationship_fingerprint"]
    assert land["verified_i3"]==0
    assert land["raw_carbon_observations_exported"] is False
    assert land["disjoint_removal_partition_certified"] is False
    byterm={x["operational_source_term"]:x
            for x in land["original_source_terms"]}
    assert byterm["rmd_regrowth_removal"]["year2050_source_sign"]=="POSITIVE"
    assert byterm["rmd_regrowth_removal"][
        "year2050_ar6_crosswalk_status"]=="AR6_NOT_REPORTED_UNDER_SOURCE_NAME"
    assert byterm["land_use_afforestation"][
        "year2050_ar6_crosswalk_status"]=="EXACT_REPORTED_DECIMAL_MATCH"
    results={x["comparison"]:x for x in land["nine_year_comparisons"]}
    reg_aff=results["NEGATED_REGROWTH_VS_REPORTED_AFFORESTATION"]
    assert reg_aff["source_comparison_status_counts"]["EXACT_REPORTED_DECIMAL_MATCH"]==1
    assert reg_aff["source_comparison_status_counts"]["MISSING_SHARED_SOURCE_YEAR_VALUE"]==8
    assert reg_aff["observations_compared"]==1
    reg_agg=results["NEGATED_REGROWTH_VS_LAND_USE_AGGREGATE"]
    assert reg_agg["source_comparison_status_counts"]["NONZERO_AT_LEAST_10_PERCENT"]==1
    aff_agg=results["AFFORESTATION_VS_LAND_USE_AGGREGATE"]
    assert aff_agg["source_comparison_status_counts"]["NONZERO_AT_LEAST_10_PERCENT"]==1
    out=output.read_text()
    for num in ('"-2.5"','"2.5"','"5.0"'):
        assert num not in out
    assert not result["operational_CDRtotal_computed"]


def test_multiple_raw_regrowth_alias_candidates_disable_relation(
        tmp_path, monkeypatch):
    args=source_fixture(tmp_path,monkeypatch)
    with args[0].open("a",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter=";")
        w.writerow(["REMIND-MAgPIE","CEMICS_SSP1-1p5C-noCDR","World",
                    "Emissions|CO2|Land|Land-use Change|++|Regrowth",
                    "Mt CO2/yr","-2.5",""])
    monkeypatch.setattr(fl,"EXPECTED_ARCHIVE_MD5",
                        md5(args[0].read_bytes()).hexdigest())
    result=fl.inventory(*args)
    land=result["source_land_relationship_fingerprint"]
    first=land["original_source_terms"][0]
    assert first["year2050_source_status"]=="AMBIGUOUS_OR_ABSENT_AUTHOR_SOURCE"
    assert all(
        c["source_comparison_status_counts"].get(
            "UNVERIFIED_SOURCE_COMPONENT")==9
        for c in land["nine_year_comparisons"][:2]
    )
    assert land["verified_i3"]==0
