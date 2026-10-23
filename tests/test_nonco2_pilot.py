import csv
import pytest
from residual_pathways.nonco2_pilot import nonco2_audit,GasAuditError

def sample(tmp_path):
    m=tmp_path/"m.csv";s=tmp_path/"s.csv"
    with m.open("w",newline="") as fh:
        w=csv.writer(fh);w.writerow(["Model","Scenario","Category"])
        w.writerows([["M","A","C1"],["M","B","C1"],["N","A","C2"]])
    with s.open("w",newline="") as fh:
        w=csv.writer(fh);w.writerow(["Model","Scenario","Region","Variable","Unit","2050"])
        w.writerows([
           ["M","A","World","Emissions|N2O","kt N2O/yr","100"],
           ["M","B","World","Emissions|N2O","kt N2O/yr","0"],
           ["N","A","World","Emissions|N2O","kt N2O/yr","200"],
           ["M","A","World","Emissions|CH4","Mt CH4/yr","10"],
           ["M","B","World","Emissions|Kyoto Gases","Mt CO2e/yr","1000"]])
    return s,m

def test_actual_means_and_no_methane_inference(tmp_path):
    s,m=sample(tmp_path)
    r=nonco2_audit(s,m)
    a=r["classes"][0]
    assert a["n2o_reported_kt_count"]==2
    assert a["n2o_average_kt_per_reporting_scenario"]==50
    assert a["n2o_mean_mtco2e_per_reporting_scenario_original_2021"]==pytest.approx(13.65)
    assert a["n2o_mean_mtco2e_per_reporting_scenario_corrected_2025"]==pytest.approx(13.35)
    assert a["n2o_metric_change_mtco2e"]==pytest.approx(-0.30)
    assert a["methane_co2e"].startswith("BLOCKED")
    assert r["no_aggregate_ghg"].startswith("CH4 origin unknown")

def test_wrong_n2o_unit_rejected(tmp_path):
    s,m=sample(tmp_path)
    s.write_text(s.read_text().replace("kt N2O/yr","Mt N2O/yr",1))
    with pytest.raises(GasAuditError,match="N2O source unit"):
        nonco2_audit(s,m)

def test_co2e_already_reported_is_not_reconverted(tmp_path):
    s,m=sample(tmp_path)
    r=nonco2_audit(s,m)
    a=r["classes"][0]
    assert a["reporting_counts"]["Emissions|Kyoto Gases"]==1
    assert a["n2o_mean_mtco2e_per_reporting_scenario_corrected_2025"]==pytest.approx(13.35)
