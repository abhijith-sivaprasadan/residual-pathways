import csv
import pytest
from residual_pathways.stratify import audit_strata, StrataError


def writer(path, headings, rows):
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(headings)
        w.writerows(rows)
    return path


def test_scenario_category_join_and_missing_reporting(tmp_path):
    metadata = writer(tmp_path/"meta.csv", ["Model", "Scenario", "Category"], [
        ["A", "S", "C1"], ["B", "S", "C2"], ["C", "S", ""], ["D", "S", "C1"]
    ])
    data = writer(tmp_path/"input.csv", ["Model","Scenario","Region","Variable","Unit","2050"], [
        ["A", "S", "World", "Emissions|CO2", "Mt CO2/yr", "0"],
        ["A", "S", "World", "Emissions|CH4", "Mt CH4/yr", ""],
        ["B", "S", "World", "Emissions|CO2", "Mt CO2/yr", "-5"],
        ["C", "S", "World", "Emissions|CO2", "Mt CO2/yr", "30"],
        ["Z", "S", "World", "Emissions|CO2", "Mt CO2/yr", "10"],
    ])
    d = audit_strata(data, metadata)
    assert d["matched_model_scenarios"] == 3
    assert d["unmatched_metadata_model_scenarios_count"] == 1
    assert d["unmatched_source_model_scenarios_count"] == 1
    assert d["strata"]["C1"]["variable_coverage"]["Emissions|CO2"]["coverage_fraction"] == 1
    assert d["strata"]["C1"]["variable_coverage"]["Emissions|CH4"]["coverage_fraction"] == 0
    assert "MISSING_CATEGORY" in d["strata"]
    assert d["scientific_status"] == "PRESENCE_ONLY_NO_ACCOUNTING_IDENTIFIABILITY"


def test_duplicate_source_variable_rejected(tmp_path):
    md = writer(tmp_path/"meta.csv", ["Model","Scenario","Category"], [["A","S","C1"]])
    row = ["A","S","World","Emissions|CO2","Mt CO2/yr","1"]
    src = writer(tmp_path/"input.csv", ["Model","Scenario","Region","Variable","Unit","2050"], [row,row])
    with pytest.raises(StrataError, match="Multiple"):
        audit_strata(src,md)


def test_duplicate_metadata_key_rejected(tmp_path):
    md = writer(tmp_path/"meta.csv",["Model","Scenario","Category"],[["A","S","C1"],["A","S","C2"]])
    src = writer(tmp_path/"input.csv",["Model","Scenario","Region","Variable","Unit","2050"],[
        ["A","S","World","Emissions|CO2","Mt CO2/yr","1"]])
    with pytest.raises(StrataError, match="Duplicate model"):
        audit_strata(src,md)


def test_explicit_xlsx_sheet_required(tmp_path):
    from openpyxl import Workbook
    wb = Workbook()
    wb.active.title = 'README'
    wb.active.append(['Explanation, not model metadata'])
    sheet = wb.create_sheet('meta_Ch3vetted_withclimate')
    sheet.append(['Model','Scenario','Category'])
    sheet.append(['A','S','C1'])
    sheet.append(['B','S','C2'])
    meta = tmp_path / 'meta.xlsx'
    wb.save(meta)
    src = writer(tmp_path/'source.csv', ['Model','Scenario','Region','Variable','Unit','2050'], [
      ['A','S','World','Emissions|CO2','Mt CO2/yr','10'],
      ['B','S','World','Emissions|CO2','Mt CO2/yr','20']])
    with pytest.raises(StrataError, match='explicit --metadata-sheet'):
        audit_strata(src, meta)
    result = audit_strata(src, meta, metadata_sheet='meta_Ch3vetted_withclimate')
    assert result['matched_model_scenarios']==2
    assert result['metadata_sheet']=='meta_Ch3vetted_withclimate'
    with pytest.raises(StrataError, match='Missing requested metadata sheet'):
        audit_strata(src, meta, metadata_sheet='wrong')


def test_joint_presence_not_gross_decomposition(tmp_path):
    md = writer(tmp_path/'metadata.csv',['Model','Scenario','Category'],[['A','S','C1'],['B','S','C1']])
    names = ['Emissions|CO2','Carbon Sequestration|Direct Air Capture']
    src = writer(tmp_path/'world.csv',['Model','Scenario','Region','Variable','Unit','2050'],[
       ['A','S','World','Emissions|CO2','Mt CO2/yr','10'],
       ['A','S','World','Carbon Sequestration|Direct Air Capture','Mt CO2/yr','2'],
       ['B','S','World','Emissions|CO2','Mt CO2/yr','8']])
    r = audit_strata(src, md, variable_names=names)
    co = r['strata']['C1']['candidate_co_reporting']['co2_and_dac']
    assert co['model_scenarios']==1
    assert co['denominator']==2
    assert co['meaning']=='PRESENCE_ONLY_NOT_ACCOUNTING_IDENTIFIABILITY'
