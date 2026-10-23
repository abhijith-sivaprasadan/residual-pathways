import pytest
from residual_pathways.accounting import check_accounting, AccountingError, sensitivity

def fixture():
    return {
        "boundary":{"model":"fixture","scenario":"fixture","region":"World","year":2050,"gas":"CO2","sector_scope":"synthetic"},
        "net":{"id":"net","value":100,"unit":"Mt CO2/yr","quantization_mt":0.01,"quantization_source_url":"https://example.org/fixture"},
        "positive_components":[{"id":"gross","value":120,"unit":"Mt CO2/yr","quantization_mt":0.01,"quantization_source_url":"https://example.org/fixture"}],
        "atmospheric_removals":[{"id":"cdr","value":20,"unit":"Mt CO2/yr","quantization_mt":0.01,"quantization_source_url":"https://example.org/fixture","kind":"atmospheric_removal"}],
        "semantic_review":{"reviewer":"SYNTHETIC-TEST-NOT-REAL","source_definition_refs":["https://example.org/fixture"],
            "exhaustive_positive_partition":True,"nonoverlapping_components":True,
            "same_gas_region_year_boundary":True,"verified_source_definitions":True,
            "fossil_ccs_excluded_from_removal":True,"land_net_gross_separated":True},
        "source_sha256":"synthetic","source_document_url":"https://example.org/fixture",
    }

def test_exact_accounting_does_not_claim_independent_science():
    r=check_accounting(fixture())
    assert r["abs_error_mt"]=="0"
    assert all(r["gates"].values())
    assert r["classification"]=="PENDING_INDEPENDENT_REVIEW"

def test_zero_net_cancellation():
    c=fixture();c["net"]["value"]=0;c["positive_components"][0]["value"]=100;c["atmospheric_removals"][0]["value"]=100
    assert check_accounting(c)["gates"]["materiality_pass"]

def test_deliberate_five_mt_inconsistency():
    c=fixture();c["net"]["value"]=5;c["positive_components"][0]["value"]=100;c["atmospheric_removals"][0]["value"]=100
    r=check_accounting(c)
    assert r["classification"]=="NOT_I3"
    assert not r["gates"]["source_precision_pass"] and not r["gates"]["materiality_pass"]

def test_overlap_fail_even_if_equal():
    c=fixture();c["semantic_review"]["nonoverlapping_components"]=False
    assert check_accounting(c)["classification"]=="NOT_I3"

def test_missing_land_flag_fails_not_assumed_zero():
    c=fixture();c["semantic_review"]["land_net_gross_separated"]=False
    assert not check_accounting(c)["gates"]["semantic_pass"]

def test_unknown_source_quantization_fails_closed():
    c=fixture();c["positive_components"][0].pop("quantization_mt")
    r=check_accounting(c)
    assert r["epsilon_source_mt"] is None and r["classification"]=="NOT_I3"

def test_fossil_ccs_not_removal():
    c=fixture();c["atmospheric_removals"][0]["kind"]="fossil_ccs_capture"
    with pytest.raises(AccountingError,match="Fossil CCS"):
        check_accounting(c)

def test_missing_value_duplicate_and_nonfinite():
    c=fixture();c["net"]["value"]=None
    with pytest.raises(AccountingError):check_accounting(c)
    c=fixture();c["net"]["id"]="gross"
    with pytest.raises(AccountingError):check_accounting(c)
    c=fixture();c["positive_components"][0]["value"]="NaN"
    with pytest.raises(AccountingError):check_accounting(c)

def test_sensitivity_does_not_fix_bad_semantics():
    c=fixture();c["semantic_review"]["exhaustive_positive_partition"]=False
    assert all(r["classification"]=="NOT_I3" for r in sensitivity(c).values())

def test_unattributed_quantization_is_not_source_precision():
    c=fixture();c["net"].pop("quantization_source_url")
    assert check_accounting(c)["classification"]=="NOT_I3"
