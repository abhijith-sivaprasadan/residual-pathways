"""Synthetic tests for original Strefler CEMICS author-archive name inventory."""
import csv
from hashlib import md5
import json
import pytest

from residual_pathways import arc24_cemics_name_inventory as inv
from residual_pathways import arc24_cemics_crosswalk as src
from residual_pathways.case_audit import CaseAuditError


def sources(tmp_path, monkeypatch, *, wrong_digest=False):
    private = tmp_path / "data" / "ar6-private"
    private.mkdir(parents=True)
    mif = private / "CDRoptionsAR6_complete.mif"
    with mif.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Model", "Scenario", "Region", "Variable", "Unit", "2050", ""])
        rows = [
            ("REMIND-MAgPIE 2.1-4.2", "CEMICS_SSP1_1p5C_minCDR", "World", "Emissions|CO2", "Mt CO2/yr", 1),
            ("REMIND-MAgPIE 2.1-4.2", "CEMICS_SSP1_1p5C_minCDR", "World", "Emissions|CO2|AFOLU", "Mt CO2/yr", 2),
            ("REMIND 2.1", "CEMICS_SSP2-1p5C-fullCDR", "World", "Emissions|CO2", "Mt CO2/yr", 3),
            ("REMIND 2.1", "other_baseline", "World", "Emissions|CO2", "Mt CO2/yr", 4),
        ]
        for r in rows:
            w.writerow(list(r) + [""])
    monkeypatch.setattr(src, "EXPECTED_ARCHIVE_MD5",
                        "f" * 32 if wrong_digest else md5(mif.read_bytes()).hexdigest())
    monkeypatch.setattr(inv, "EXPECTED_ARCHIVE_MD5", src.EXPECTED_ARCHIVE_MD5)
    rmd = private / "CDRoptions.Rmd"
    rmd.write_bytes(b"SSP1\nminCDR\nGross emissions \xc2 BECCS\n")
    out = tmp_path / "results" / "name_inventory.json"
    return mif, rmd, out


def test_normalized_scenario_name_not_promoted_to_provenance(tmp_path, monkeypatch):
    mif, rmd, out = sources(tmp_path, monkeypatch)
    result = inv.inspect_source_names(mif, out, rmd_path=rmd)
    assert result["distinct_models"] == 2
    assert result["distinct_scenarios"] == 3
    assert result["distinct_model_scenario_pairs"] == 3
    assert result["total_source_rows"] == 4
    assert result["exact_original_model_scenario_label"] is False
    assert len(result["normalized_scenario_matches"]) == 1
    assert result["normalized_scenario_matches"][0]["scenario"] == "CEMICS_SSP1_1p5C_minCDR"
    assert result["verified_i3"] == 0
    assert result["rmd_keyword_index"]["encoding_interpretation"]["decoded_as"] == "cp1252"
    text = out.read_text()
    assert "Emissions|CO2|AFOLU" not in text
    assert '"2050": 1' not in text
    assert "NOT_DETERMINED" in text


def test_checksum_failure_does_not_write_output(tmp_path, monkeypatch):
    mif, rmd, out = sources(tmp_path, monkeypatch, wrong_digest=True)
    with pytest.raises(CaseAuditError, match="MD5 mismatch"):
        inv.inspect_source_names(mif, out, rmd_path=rmd)
    assert not out.exists()


def test_private_output_path_rejected(tmp_path, monkeypatch):
    mif, rmd, out = sources(tmp_path, monkeypatch)
    with pytest.raises(CaseAuditError, match="must stay private"):
        inv.inspect_source_names(mif, mif.parent / "unsafe.json")


def test_missing_scenario_alias_no_scientific_promotion(tmp_path, monkeypatch):
    mif, rmd, out = sources(tmp_path, monkeypatch)
    data = mif.read_text()
    data = data.replace("CEMICS_SSP1_1p5C_minCDR", "unrelated_paper_scenario")
    mif.write_text(data)
    monkeypatch.setattr(inv, "EXPECTED_ARCHIVE_MD5", md5(mif.read_bytes()).hexdigest())
    result = inv.inspect_source_names(mif, out)
    assert result["normalized_scenario_matches"] == []
    assert result["exact_original_model_scenario_label"] is False
    assert result["verified_i3"] == 0
