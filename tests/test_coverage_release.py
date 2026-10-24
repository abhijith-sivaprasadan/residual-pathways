"""Synthetic aggregate-only release tests; no private AR6 data."""
import copy
import json
import pytest

from residual_pathways.coverage_release import assemble, freeze, ReleaseError, CATEGORIES, YEARS

WORLD = "a" * 64
META = "b" * 64
VARIABLES = ["Emissions|CO2", "Carbon Sequestration|Direct Air Capture"]


def inputs():
    rows = []
    for cat in CATEGORIES:
        for year in YEARS:
            for var in VARIABLES:
                rows.append({
                    "category": cat, "year": year, "variable": var,
                    "eligible_scenarios": 3, "unique_model_labels": 2,
                    "reporting_scenarios": 2, "scenario_weighted_fraction": 2/3,
                    "model_label_balanced_fraction": 0.75, "units_seen": ["Mt CO2/yr"],
                })
    source = {
        "schema_version": "reported-presence-robustness.v1",
        "source_sha256": WORLD, "metadata_sha256": META,
        "region": "World", "metadata_sheet": "meta_Ch3vetted_withclimate",
        "years": YEARS, "variable_names": VARIABLES,
        "matched_source_scenarios": 24,
        "records": rows,
    }
    comparison = {
        "schema_version": "ar6-metadata-concordance-public.v1",
        "official_named": {"sha256": META},
        "status": "DIFFERENCES_RECORDED",
    }
    return source, comparison


def test_freeze_safe_public_coverage(tmp_path):
    source, cmp = inputs()
    output = tmp_path / "release.json"
    src, conf = tmp_path / "input.json", tmp_path / "comparison.json"
    src.write_text(json.dumps(source))
    conf.write_text(json.dumps(cmp))
    digest = freeze(src, conf, output, expected_world=WORLD, expected_metadata=META)
    package = json.loads(output.read_text())
    assert len(package["records"]) == 8 * 4 * 2
    assert package["cohort_size"] == 24
    assert package["science_review_state"] == "REVIEW_PENDING"
    assert package["i3_verified"] == 0
    assert package["version"].endswith("-candidate")
    assert output.with_suffix(".json.sha256").read_text().startswith(digest)
    assert "Model" not in package["records"][0]
    assert "Scenario" not in package["records"][0]


def test_source_fingerprint_mismatch_rejected():
    source, cmp = inputs()
    with pytest.raises(ReleaseError, match="fingerprints"):
        assemble(source, expected_world="c"*64, expected_metadata=META, concordance=cmp)


@pytest.mark.parametrize("bad_change", ["missing", "extra", "invalid_count", "bad_fraction", "missing_year"])
def test_fail_closed_on_invalid_source_aggregates(bad_change):
    source, cmp = inputs()
    if bad_change == "missing":
        source["records"].pop()
    if bad_change == "extra":
        source["records"][0]["Scenario"] = "Secret"
    if bad_change == "invalid_count":
        source["records"][0]["reporting_scenarios"] = 4
    if bad_change == "bad_fraction":
        source["records"][0]["scenario_weighted_fraction"] = 1.0
    if bad_change == "missing_year":
        source["years"] = YEARS[:-1]
    with pytest.raises(ReleaseError):
        assemble(source, expected_world=WORLD, expected_metadata=META, concordance=cmp)


def test_no_unreviewed_i3_auto_promotion():
    source, cmp = inputs()
    x = assemble(source, expected_world=WORLD, expected_metadata=META, concordance=cmp)
    assert x["i3_verified"] == 0
    assert "model-family estimate" in x["weighting"]["model_label_balanced"]
    assert x["metadata_concordance_status"] == "DIFFERENCES_RECORDED"
