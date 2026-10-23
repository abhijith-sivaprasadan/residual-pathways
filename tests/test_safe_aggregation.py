import pytest
from residual_pathways.safe_aggregation import UnsafeAggregation, approved_partition_sum, guard_semihierarchy

def obs():
    return {"A":{"value":0,"unit":"Mt CO2/yr","year":2050,"region":"World"},
            "B":{"value":10,"unit":"Mt CO2/yr","year":2050,"region":"World"}}

REVIEW={"nonoverlap_reviewed":True,"exhaustive_reviewed":True,"reference_url":"https://example.org/fixture"}

def test_zero_remains_reported_and_missing_never_assumed():
    result=approved_partition_sum(obs(),["A","B"],approval=REVIEW)
    assert result["sum"]==10
    with pytest.raises(UnsafeAggregation,match="Missing"):
        approved_partition_sum(obs(),["A","B","C"],approval=REVIEW)

def test_no_unreviewed_additivity_even_when_values_look_good():
    with pytest.raises(UnsafeAggregation,match="independently reviewed"):
        approved_partition_sum(obs(),["A","B"],approval={})

def test_guard_nested_hierarchy():
    with pytest.raises(UnsafeAggregation,match="semi-hierarchical"):
        guard_semihierarchy("Emissions|CO2",["Emissions|CO2|Energy","Emissions|CO2|Energy|Fossil"])
    with pytest.raises(UnsafeAggregation,match="semi-hierarchical"):
        guard_semihierarchy("Emissions|CO2",["Emissions|CO2|Energy"])

def test_duplicates_and_wrong_units_fail():
    with pytest.raises(UnsafeAggregation,match="Duplicate"):
        approved_partition_sum(obs(),["A","A"],approval=REVIEW)
    data=obs();data["B"]["unit"]="Gt CO2/yr"
    with pytest.raises(UnsafeAggregation,match="mismatch"):
        approved_partition_sum(data,["A","B"],approval=REVIEW)

def test_nonfinite_and_missing_value_rejected():
    data=obs();data["B"]["value"]=float("nan")
    with pytest.raises(UnsafeAggregation,match="Nonfinite"):
        approved_partition_sum(data,["A","B"],approval=REVIEW)
    data=obs();data["B"]["value"]=None
    with pytest.raises(UnsafeAggregation,match="Missing"):
        approved_partition_sum(data,["A","B"],approval=REVIEW)
