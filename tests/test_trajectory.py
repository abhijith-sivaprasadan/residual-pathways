from residual_pathways.trajectory import examine, write_trajectory
from residual_pathways.core import COHORT


def test_signed_trajectories_not_gross(tmp_path):
    rows = []
    for i, model in enumerate(COHORT):
        rows.append({"Model": model, "Scenario": "Shared", "Region": "World",
                     "Variable": "Emissions|CO2", "Unit": "Mt CO2/yr",
                     "values": {"2050": 10. - i, "2100": -2. if i == 0 else 3.}})
    result = examine(rows, years=(2050, 2100))
    assert len(result["observations"]) == 6
    assert result["year_summaries"][0]["negative_reported_co2_count"] == 0
    assert result["year_summaries"][1]["negative_reported_co2_count"] == 1
    assert all(x["meaning"] == "reported_CO2_not_a_gross_or_CDR_decomposition" for x in result["observations"])
    write_trajectory(result, tmp_path)
    assert "Negative reported" in (tmp_path / "decadal_report.md").read_text()
