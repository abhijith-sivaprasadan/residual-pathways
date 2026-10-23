import pytest
from residual_pathways.gwp import gas_to_co2e, GWPScopeError


def test_versioned_methane_fossil():
    a = gas_to_co2e(1, "CH4", "Mt CH4/yr", metric="GWP100",
                    assessment_version="IPCC_AR6_2021_ORIGINAL", methane_origin="FOSSIL")
    b = gas_to_co2e(1, "CH4", "Mt CH4/yr", metric="GWP100",
                    assessment_version="IPCC_AR6_2025_ERRATA", methane_origin="FOSSIL")
    assert a.co2e_mt_per_year == pytest.approx(29.8)
    assert b.co2e_mt_per_year == pytest.approx(28.1)
    assert a.assessment_version != b.assessment_version


def test_nonfossil_and_n2o():
    methane = gas_to_co2e(1, "CH4", "Mt CH4/yr", metric="GWP100",
                          assessment_version="IPCC_AR6_2025_ERRATA", methane_origin="NONFOSSIL")
    n2o = gas_to_co2e(.1, "N2O", "Mt N2O/yr", metric="GWP100",
                      assessment_version="IPCC_AR6_2025_ERRATA")
    assert methane.co2e_mt_per_year == pytest.approx(25.3)
    assert n2o.co2e_mt_per_year == pytest.approx(26.7)


@pytest.mark.parametrize("kwargs", [
    {"gas": "CH4", "unit": "Mt CH4/yr"},
    {"gas": "CH4", "unit": "Mt CO2e/yr", "methane_origin": "FOSSIL"},
    {"gas": "CH4", "unit": "Mt CH4/yr", "methane_origin": "MIXED"},
    {"gas": "N2O", "unit": "Mt N2O/yr", "methane_origin": "FOSSIL"},
    {"gas": "N2O", "unit": "Mt N2O/yr", "metric": "GWP20"},
    {"gas": "N2O", "unit": "Mt N2O/yr", "assessment_version": "AR6"},
])
def test_ambiguous_or_wrong_metric_rejected(kwargs):
    args = {"amount": 1, "gas": "N2O", "unit": "Mt N2O/yr", "metric": "GWP100",
            "assessment_version": "IPCC_AR6_2025_ERRATA"}
    args.update(kwargs)
    with pytest.raises(GWPScopeError):
        gas_to_co2e(**args)


def test_nan_and_bool_rejected():
    for value in (float("nan"), True):
        with pytest.raises(GWPScopeError):
            gas_to_co2e(value, "N2O", "Mt N2O/yr", metric="GWP100",
                        assessment_version="IPCC_AR6_2025_ERRATA")


def test_actual_ar6_n2o_unit_kt_yields_mtco2e_without_thousandfold_error():
    x = gas_to_co2e(100, 'N2O', 'kt N2O/yr', metric='GWP100', assessment_version='IPCC_AR6_2025_ERRATA')
    y = gas_to_co2e(0.1, 'N2O', 'Mt N2O/yr', metric='GWP100', assessment_version='IPCC_AR6_2025_ERRATA')
    assert x.input_mt_per_year == pytest.approx(0.1)
    assert x.co2e_mt_per_year == pytest.approx(26.7)
    assert x.co2e_mt_per_year == pytest.approx(y.co2e_mt_per_year)
