"""Synthetic structure and low-count disclosure preflight tests."""
import copy
from hashlib import sha256
import json

import pytest
from residual_pathways.publication_preflight import (
    review_bytes, PublicationPreflightError, WORLD_SHA, META_SHA,
)
from residual_pathways.coverage_release import YEARS, CATEGORIES


def fixture():
    variables = [
        "Emissions|CO2", "Emissions|CO2|Energy", "Emissions|CO2|AFOLU",
        "Carbon Sequestration|CCS|Fossil", "Carbon Sequestration|CCS|Biomass",
        "Carbon Sequestration|Direct Air Capture", "Emissions|CH4",
        "Emissions|N2O", "Emissions|CO2|Energy and Industrial Processes",
        "Carbon Sequestration|Land Use", "Carbon Sequestration|Enhanced Weathering",
    ]
    rows = [
        {"category": cat, "year": year, "variable": variable,
         "denominator": 150 if cat in CATEGORIES[:-1] else 152,
         "reporting": 100, "model_labels": 15,
         "scenario_fraction": 100/(150 if cat in CATEGORIES[:-1] else 152),
         "model_label_balanced_fraction": 0.6, "units": ["Mt CO2/yr"]}
        for year in YEARS for cat in CATEGORIES for variable in variables
    ]
    return {
        "schema": "residualpathways.coverage-only.v1",
        "version": "0.1.0-candidate",
        "scope": "World / climate-vetted C1-C8 / four years",
        "source_authentication": "LOCAL_FINGERPRINT_ONLY_PUBLISHER_RECEIPT_NOT_INDEPENDENTLY_VERIFIED",
        "metadata_concordance_status": "DIFFERENCES_RECORDED",
        "metadata_sheet": "meta_Ch3vetted_withclimate",
        "evidence": "EXACT_VARIABLE_REPORTING_PRESENCE_ONLY",
        "science_review_state": "REVIEW_PENDING",
        "physical_accounting": "NOT_ESTABLISHED",
        "i3_verified": 0,
        "years": YEARS, "categories": CATEGORIES, "variables": variables,
        "weighting": {"scenario": "Scenario weighted",
                      "model_label_balanced": "NOT a model-family estimate"},
        "limitations": ["No verified complete carbon partition"],
        "sha256": {"world_csv": WORLD_SHA, "metadata_xlsx": META_SHA},
        "cohort_size": 1202, "records": rows,
    }


def run(doc, *, pin=None, corrupt=False):
    raw = (json.dumps(doc, sort_keys=True) + "\n").encode()
    digest = sha256(raw).hexdigest()
    sidecar = ("0" * 64 if corrupt else digest) + "  coverage_release.json\n"
    return review_bytes(raw, sidecar, expected_sha256=pin or digest)


def test_valid_bundle_still_requires_human_release_review():
    out = run(fixture())
    assert out["automated_structural_checks"] == "PASS"
    assert out["status"] == "HUMAN_DISCLOSURE_AND_LICENSE_REVIEW_REQUIRED"
    assert out["small_cell_screen"]["flagged_count"] == 0
    assert out["human_approval"] is False
    assert out["verified_i3"] == 0


def test_small_cells_flagged_not_silently_approved():
    doc = fixture()
    doc["records"][0]["reporting"] = 2
    doc["records"][0]["scenario_fraction"] = 2 / 150
    out = run(doc)
    assert out["small_cell_screen"]["flagged_count"] == 1
    assert "SMALL_NONZERO_REPORTING_CELL" in out["small_cell_screen"]["flagged"][0]["reasons"]


@pytest.mark.parametrize("fault", ["hash", "bad_sidecar", "private", "i3", "source_sha", "row",
                                     "fraction", "denominator", "duplicate"])
def test_invalid_candidate_rejected(fault):
    doc = fixture()
    if fault == "private":
        doc["records"][0]["Model"] = "private"
    if fault == "i3":
        doc["i3_verified"] = 1
    if fault == "source_sha":
        doc["sha256"]["world_csv"] = "f" * 64
    if fault == "row":
        doc["records"].pop()
    if fault == "fraction":
        doc["records"][0]["scenario_fraction"] = 0.0
    if fault == "denominator":
        doc["records"][0]["denominator"] = 2
    if fault == "duplicate":
        doc["records"][0] = copy.deepcopy(doc["records"][1])
    with pytest.raises(PublicationPreflightError):
        run(doc, pin="f"*64 if fault == "hash" else None,
            corrupt=(fault == "bad_sidecar"))


def test_duplicate_json_keys_rejected():
    raw = b'{"schema":"x","schema":"y"}'
    digest = sha256(raw).hexdigest()
    with pytest.raises(PublicationPreflightError):
        review_bytes(raw, digest + "  coverage_release.json\n", expected_sha256=digest)
