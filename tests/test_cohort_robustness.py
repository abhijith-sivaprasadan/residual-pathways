import csv
import json
import pytest
from residual_pathways.cohort_robustness import compute, CohortError

def paths(tmp_path):
    source=tmp_path/"input.csv"
    meta=tmp_path/"metadata.csv"
    with meta.open("w",newline="") as f:
        w=csv.writer(f);w.writerow(["Model","Scenario","Category"])
        w.writerows([["M1","a","C1"],["M1","b","C1"],["M2","c","C1"],
                     ["M3","d","C2"]])
    with source.open("w",newline="") as f:
        w=csv.writer(f)
        w.writerow(["Model","Scenario","Region","Variable","Unit","2030","2050"])
        w.writerows([["M1","a","World","Emissions|CO2","Mt CO2/yr","0","10"],
                     ["M1","b","World","Emissions|CO2","Mt CO2/yr","","20"],
                     ["M2","c","World","Emissions|CO2","Mt CO2/yr","7",""],
                     ["M3","d","World","Emissions|CO2","Mt CO2/yr","","0"]])
    return source,meta

def test_exact_scenario_vs_model_label_weighting(tmp_path):
    s,m=paths(tmp_path)
    d=compute(s,m,["Emissions|CO2"],years=(2030,2050))
    c1=[x for x in d["records"] if x["category"]=="C1" and x["year"]==2030][0]
    assert c1["eligible_scenarios"]==3
    assert c1["unique_model_labels"]==2
    assert c1["reporting_scenarios"]==2
    assert c1["scenario_weighted_fraction"]==pytest.approx(2/3)
    assert c1["model_label_balanced_fraction"]==pytest.approx(.75)
    c2=[x for x in d["records"] if x["category"]=="C2" and x["year"]==2050][0]
    assert c2["reporting_scenarios"]==1   # a numeric zero is reported, not missing
    assert c2["scenario_weighted_fraction"]==1

def test_duplicate_source_variable_year_rejected(tmp_path):
    s,m=paths(tmp_path)
    with s.open("a") as f:f.write("M1,a,World,Emissions|CO2,Mt CO2/yr,0,10\n")
    with pytest.raises(CohortError,match="Duplicate"):
        compute(s,m,["Emissions|CO2"],years=(2050,))

def test_invalid_numeric_rejected(tmp_path):
    s,m=paths(tmp_path)
    s.write_text(s.read_text().replace(",7,\\n",",NaN,\\n"))
    with pytest.raises(CohortError,match="Nonfinite"):
        compute(s,m,["Emissions|CO2"],years=(2030,))
