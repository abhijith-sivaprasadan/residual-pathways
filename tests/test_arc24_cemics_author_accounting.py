"""Regression tests for author-defined operational CDR versus sectoral gross."""
import csv
from hashlib import md5
import json

import pytest

from residual_pathways import arc24_cemics_author_accounting as ledger
from residual_pathways import arc24_cemics_crosswalk as crosswalk
from residual_pathways import arc24_cemics_alias_fingerprint as fp
from residual_pathways.case_audit import CaseAuditError, TOTAL, UNIT
from residual_pathways.stratify import sha_file


SYNTHETIC = {
    ledger.TOTAL: "15.00",
    ledger.REGROWTH: "-2.0",
    ledger.EW: "1.0",
    ledger.BECCS: "3.00",
    ledger.DAC: "0",
    ledger.GROSS_FI: "25.0",
    ledger.AFOLU: "6.0",
    ledger.LAND: "4.0",
    ledger.FOSSIL_CCS: "5.0",
}
# Source-defined CDR = 2+1+3+0 = 6; derived positive = 15+6=21.
# Separate gross fossil+industry=25: different scope, NOT a balancing error.


def fixture(tmp_path, monkeypatch, *, missing=None, gross="25.0",
            tamper_author_rmd=False, duplicate_author=False,
            hierarchy_regrowth=False, author_only_gross=False):
    private = tmp_path / "data" / "ar6-private"
    private.mkdir(parents=True)
    mif = private / "CDRoptionsAR6_complete.mif"
    rmd = private / "CDRoptions.Rmd"
    world = private / "AR6_Scenarios_Database_World_v1.1.csv"
    variables = dict(SYNTHETIC)
    variables[ledger.GROSS_FI] = gross
    if missing:
        del variables[missing]
    with mif.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Model", "Scenario", "Region", "Variable", "Unit", "2050", ""])
        for name, value in variables.items():
            source_name = (
                "Emissions|CO2|Land|Land-use Change|+|Regrowth"
                if hierarchy_regrowth and name == ledger.REGROWTH else name
            )
            w.writerow([fp.ARCHIVE_MODEL, fp.AUTHOR_NO, "World", source_name,
                        UNIT, value, ""])
            if duplicate_author and name == ledger.EW:
                w.writerow([fp.ARCHIVE_MODEL, fp.AUTHOR_NO, "World", name,
                            UNIT, value, ""])
    world_variables = {
        name: value for name, value in variables.items()
        if not (hierarchy_regrowth and name == ledger.REGROWTH)
        and not (author_only_gross and name == ledger.GROSS_FI)
    }
    with world.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Model", "Scenario", "Region", "Variable", "Unit", "2050"])
        for name, value in world_variables.items():
            w.writerow([ledger.MODEL, fp.AR6_MIN, "World", name, UNIT, value])
    rmd.write_text(
        ("data <- deletePlus(data)\n" if hierarchy_regrowth else "")
        + "\n".join(ledger.EXACT_FORMULAS)
        + ("\n# tampered" if tamper_author_rmd else "")
        + "\n", encoding="utf-8",
    )
    packet = private / "canonical_selected24_packet.json"
    cases = []
    for n in range(1, 25):
        cases.append({
            "case_id": f"ARC24-{n:02d}",
            "model": ledger.MODEL if n == 3 else "UNRELATED",
            "scenario": fp.AR6_MIN if n == 3 else "UNRELATED",
            "source_observations": {
                k: {"raw": v, "unit": UNIT, "value": float(v)}
                for k, v in world_variables.items()
            } if n == 3 else {},
        })
    packet.write_text(json.dumps({
        "schema": "residualpathways.ar6_canonical_selected24.private.v1",
        "handling": "LOCAL_ONLY_DO_NOT_PUBLISH",
        "source_sha256": sha_file(world), "cases": cases,
    }))
    monkeypatch.setattr(ledger, "EXPECTED_ARCHIVE_MD5",
                        md5(mif.read_bytes()).hexdigest())
    monkeypatch.setattr(ledger, "AUTHOR_SUPPORT_MD5",
                        {"authors_rmd": md5(rmd.read_bytes()).hexdigest()})
    return mif, world, packet, rmd, tmp_path / "results" / "public.json"


def run(items):
    return ledger.derive_source_worksheet(*items)


def test_study_formula_source_derived_and_gross_comparison_distinguished(tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch)
    out = run(args)
    status = out["operational_study_accounting"]
    assert status["status"] == "AUTHORS_EXPLICIT_FORMULA_COMPUTABLE_NOT_I3"
    assert status["operational_CDRtotal_sign"] == "POSITIVE"
    assert status["operational_CO2pos_sign"] == "POSITIVE"
    assert status["regrowth_CDR_sign"] == "POSITIVE"
    assert status["DAC_sign"] == "ZERO"
    difference = out["study_CO2pos_vs_separate_gross_fossil_industry"]
    assert difference["status"] == "DIFFERENT_SCOPES_NUMERIC_COMPARISON_ONLY"
    assert difference["source_decimal_relation"] == "NONZERO_REPORTED_DECIMAL_DIFFERENCE"
    assert difference["CO2pos_minus_gross_fossil_industry_sign"] == "NEGATIVE"
    assert difference["absolute_gap_relative_band"] == "FROM_1_TO_BELOW_10_PERCENT" or (
        difference["absolute_gap_relative_band"] == "AT_LEAST_10_PERCENT"
    )
    assert out["verified_i3"] == 0
    data = args[4].read_text()
    assert '"15.00"' not in data and '"25.0"' not in data
    assert '"21.0"' not in data
    assert "CEMICS_SSP1-1p5C-noCDR" not in data


def test_missing_critical_original_source_term_not_zero(tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch, missing=ledger.EW)
    out = run(args)
    assert out["operational_study_accounting"]["status"] == (
        "NOT_COMPUTABLE_MISSING_OR_UNVERIFIED_SOURCE_TERM"
    )
    assert ledger.EW in out["operational_study_accounting"]["missing_or_unverified_operational_terms"]
    assert out["study_CO2pos_vs_separate_gross_fossil_industry"]["status"] == (
        "NOT_COMPARABLE_UNVERIFIED_INPUT"
    )


def test_nonidentical_gross_separate_ledger_even_if_equal(tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch, gross="21")
    out = run(args)
    compare = out["study_CO2pos_vs_separate_gross_fossil_industry"]
    assert compare["source_decimal_relation"] == "EXACT_REPORTED_DECIMAL_EQUALITY"
    assert compare["comparison_is_a_expected_closure_equation"] is False
    assert not out["operational_study_accounting"]["physical_gross_positive_emissions_certified"]


def test_same_unit_duplicate_not_auto_selected(tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch, duplicate_author=True)
    out = run(args)
    item = next(r for r in out["individual_source_terms"] if r["variable"] == ledger.EW)
    assert item["source_comparison_status"] == "AMBIGUOUS_DUPLICATE_ROWS_SAME_UNIT"
    assert out["operational_study_accounting"]["status"] == (
        "NOT_COMPUTABLE_MISSING_OR_UNVERIFIED_SOURCE_TERM"
    )


def test_source_hash_tampering_stops_output(tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch)
    args[0].write_bytes(args[0].read_bytes() + b"\nchanged\n")
    with pytest.raises(CaseAuditError, match="MIF MD5 changed"):
        run(args)
    assert not args[4].exists()


def test_original_Rmd_formula_change_fail_closed(tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch, tamper_author_rmd=True)
    rmd = args[3]
    rmd.write_text(rmd.read_text().replace(
        "CO2pos <- CO2tot + CDRtotal", "CO2pos <- CO2tot - CDRtotal"
    ))
    # Preserve the checksum *matching fixture's new bytes* to ensure the
    # actual embedded original author formula contract is independently checked.
    monkeypatch.setattr(
        ledger, "AUTHOR_SUPPORT_MD5",
        {"authors_rmd": md5(rmd.read_bytes()).hexdigest()}
    )
    with pytest.raises(CaseAuditError, match="seven CDR/positive CO2 equations absent"):
        run(args)


def test_raw_AR6_packet_mismatch_fail_closed(tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch)
    obj = json.loads(args[2].read_text())
    obj["cases"][2]["source_observations"][ledger.TOTAL]["raw"] = "991"
    args[2].write_text(json.dumps(obj))
    with pytest.raises(CaseAuditError, match="source packet differs"):
        run(args)


def test_refuse_public_output_in_private_area(tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch)
    with pytest.raises(CaseAuditError, match="must remain private"):
        run((*args[:4], args[0].parent / "insecure_public.json"))



def test_original_author_deleteplus_regrowth_and_author_only_gross_scope(
        tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch, hierarchy_regrowth=True,
                   author_only_gross=True)
    result = run(args)
    byname = {r["variable"]: r for r in result["individual_source_terms"]}
    reg = byname[ledger.REGROWTH]
    assert reg["original_author_raw_variable"] == (
        "Emissions|CO2|Land|Land-use Change|+|Regrowth"
    )
    assert reg["raw_author_regrowth_hierarchy_candidate_count"] == 1
    assert reg["source_comparison_status"] == (
        "AUTHOR_ONLY_REGROWTH_AFTER_DELETEPLUS_AR6_ABSENT"
    )
    assert reg["source_value_sign"] == "NEGATIVE"
    assert reg["ar6_source_present"] is False
    gross = byname[ledger.GROSS_FI]
    assert gross["source_comparison_status"] == (
        "AUTHOR_ONLY_GROSS_FOSSIL_INDUSTRY_AR6_ABSENT"
    )
    assert gross["ar6_source_present"] is False
    operational = result["operational_study_accounting"]
    assert operational["status"] == "AUTHORS_EXPLICIT_FORMULA_COMPUTABLE_NOT_I3"
    assert operational["regrowth_ar6_independently_reported"] is False
    assert operational["source_author_preprocessing_confirmed"]
    assert operational["missing_or_unverified_operational_terms"] == []
    assert operational["operational_CDRtotal_sign"] == "POSITIVE"
    assert operational["operational_CO2pos_sign"] == "POSITIVE"
    assert operational["operational_term_provenance"][ledger.REGROWTH] == (
        "AUTHOR_MIF_RMD_DELETEPLUS_ONLY"
    )
    compare = result["study_CO2pos_vs_separate_gross_fossil_industry"]
    assert compare["status"] == "DIFFERENT_SCOPES_AUTHOR_GROSS_ONLY_COMPARISON"
    assert compare["CO2pos_minus_gross_fossil_industry_sign"] == "NEGATIVE"
    assert compare["comparison_is_a_expected_closure_equation"] is False
    serialized = args[-1].read_text(encoding="utf-8")
    assert '"15.00"' not in serialized and '"25.0"' not in serialized
    assert '"-2.0"' not in serialized and '"21.00"' not in serialized
    assert result["verified_i3"] == 0


def test_ambiguous_two_plus_hierarchy_names_do_not_enter_CDR(
        tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch, hierarchy_regrowth=True)
    with args[0].open("a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, delimiter=";")
        writer.writerow([fp.ARCHIVE_MODEL, fp.AUTHOR_NO, "World",
                         "Emissions|CO2|Land|Land-use Change|++|Regrowth",
                         UNIT, "-2.0", ""])
    monkeypatch.setattr(
        ledger, "EXPECTED_ARCHIVE_MD5", md5(args[0].read_bytes()).hexdigest()
    )
    result = run(args)
    reg = next(row for row in result["individual_source_terms"]
               if row["variable"] == ledger.REGROWTH)
    assert reg["source_comparison_status"] == (
        "AMBIGUOUS_AFTER_AUTHOR_DELETEPLUS"
    )
    assert result["operational_study_accounting"]["status"] == (
        "NOT_COMPUTABLE_MISSING_OR_UNVERIFIED_SOURCE_TERM"
    )


def test_deleteplus_must_be_in_original_author_code_for_alias(
        tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch, hierarchy_regrowth=True)
    args[3].write_text(
        args[3].read_text().replace("data <- deletePlus(data)\n", ""),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        ledger, "AUTHOR_SUPPORT_MD5",
        {"authors_rmd": md5(args[3].read_bytes()).hexdigest()}
    )
    with pytest.raises(CaseAuditError, match="lacks source deletePlus preprocessing"):
        run(args)


def test_duplicate_same_unit_author_only_gross_blocks_comparison(
        tmp_path, monkeypatch):
    args = fixture(tmp_path, monkeypatch, hierarchy_regrowth=True,
                   author_only_gross=True)
    with args[0].open("a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, delimiter=";")
        writer.writerow([fp.ARCHIVE_MODEL, fp.AUTHOR_NO, "World",
                         ledger.GROSS_FI, UNIT, "25.0", ""])
    monkeypatch.setattr(
        ledger, "EXPECTED_ARCHIVE_MD5", md5(args[0].read_bytes()).hexdigest()
    )
    result = run(args)
    gross = next(row for row in result["individual_source_terms"]
                 if row["variable"] == ledger.GROSS_FI)
    assert gross["source_comparison_status"] == (
        "AUTHOR_ONLY_UNIQUE_EXPECTED_UNIT_NOT_FOUND"
    )
    assert result["operational_study_accounting"]["status"] == (
        "AUTHORS_EXPLICIT_FORMULA_COMPUTABLE_NOT_I3"
    )
    assert result["study_CO2pos_vs_separate_gross_fossil_industry"]["status"] == (
        "NOT_COMPARABLE_UNVERIFIED_INPUT"
    )
