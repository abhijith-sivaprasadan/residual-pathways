"""Synthetic ARC24-03 CEMICS v2 author-to-AR6 crosswalk validation."""
import csv
from hashlib import md5
import json

import pytest

from residual_pathways import arc24_cemics_crosswalk as cx
from residual_pathways.case_audit import SIX, TOTAL, CaseAuditError
from residual_pathways.stratify import sha_file

VARS = (TOTAL,) + tuple(SIX) + ("Emissions|CO2|Other",)


def fixture(tmp_path, monkeypatch, *, delimiter=";", region="World",
            model=cx.MODEL, omit=False, tamper=False, trailing=False):
    private = tmp_path / "data" / "ar6-private"
    private.mkdir(parents=True)
    mif = private / "CDRoptionsAR6_complete.mif"
    world = private / "AR6_Scenarios_Database_World_v1.1.csv"
    records = []
    for i, variable in enumerate(VARS):
        raw = str(i * 0.25)
        records.append((variable, raw))
    with world.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Model","Scenario","Region","Variable","Unit","2050"])
        for var, value in records:
            writer.writerow([cx.MODEL, cx.SCENARIO, "World", var, "Mt CO2/yr", value])
    with mif.open("w", newline="", encoding="utf-8") as f:
        f.write("# original scientific source, test fixture only\n")
        f.write("# header below is IAMC-wide form\n")
        writer = csv.writer(f, delimiter=delimiter)
        writer.writerow(["Model","Scenario","Region","Variable","Unit","2050"] +
                        ([""] if trailing else []))
        for v, val in records:
            if omit and v == TOTAL:
                continue
            # Scientific dataset version may serialize numbers differently.
            writer.writerow([model, cx.SCENARIO, region, v, "Mt CO2/yr",
                             "0.51" if tamper and v == TOTAL else val] +
                            ([""] if trailing else []))
    source_md5 = md5(mif.read_bytes()).hexdigest()
    monkeypatch.setattr(cx, "EXPECTED_ARCHIVE_MD5", source_md5)
    cases = []
    for i in range(1, 25):
        observations = (
            {name: {"unit": "Mt CO2/yr", "raw": value, "value": float(value)}
             for name, value in records if name != "Emissions|CO2|Other"}
            if i == 3 else {}
        )
        cases.append({
            "case_id": f"ARC24-{i:02d}",
            "model": cx.MODEL if i == 3 else "EXTERNAL MODEL",
            "scenario": cx.SCENARIO if i == 3 else "EXTERNAL SCENARIO",
            "source_observations": observations,
        })
    packet = private / "canonical_selected24_packet.json"
    packet.write_text(json.dumps({
        "schema": "residualpathways.ar6_canonical_selected24.private.v1",
        "handling": "LOCAL_ONLY_DO_NOT_PUBLISH",
        "source_sha256": sha_file(world), "cases": cases,
    }))
    return mif, world, packet, tmp_path / "results" / "crosswalk.json"


@pytest.mark.parametrize("delimiter", [";", ",", "\t"])
def test_exact_source_crosswalk_and_privacy(tmp_path, monkeypatch, delimiter):
    mif, world, packet, public = fixture(
        tmp_path, monkeypatch, delimiter=delimiter)
    result = cx.crosswalk(mif, world, packet, public)
    assert result["status"] == (
        "EXACT_MODEL_SCENARIO_WORLD_YEAR_FOUND_SOURCE_SEMANTICS_UNVERIFIED"
    )
    assert result["archive_exact_world_variable_count"] == len(VARS)
    assert result["overlapping_variable_names"] == len(VARS)
    assert result["overlap_status_counts"] == {
        "EXACT_REPORTED_DECIMAL_MATCH": len(VARS)
    }
    assert result["scientific_grade"] == "NOT_DETERMINED"
    assert not result["verified_i3"]
    raw = public.read_text()
    assert '"0.25"' not in raw
    assert '"0.51"' not in raw
    assert "EXTERNAL SCENARIO" not in raw


def test_original_mif_trailing_delimiter_format(tmp_path, monkeypatch):
    mif, world, packet, public = fixture(
        tmp_path, monkeypatch, trailing=True, delimiter=";")
    result = cx.crosswalk(mif, world, packet, public)
    assert result["archive_exact_world_variable_count"] == len(VARS)
    assert result["overlap_status_counts"]["EXACT_REPORTED_DECIMAL_MATCH"] == len(VARS)


def test_nonzero_source_difference_not_claimed_equivalent(tmp_path, monkeypatch):
    mif, world, packet, public = fixture(tmp_path, monkeypatch, tamper=True)
    result = cx.crosswalk(mif, world, packet, public)
    cand = [r for r in result["selected_variable_comparisons"]
            if r["variable"] == TOTAL][0]
    assert cand["comparison_status"] == "NONZERO_REPORTED_DECIMAL_DIFFERENCE"
    assert cand["difference_band"] == "AT_LEAST_10_PERCENT"


def test_absent_archive_variable_distinguished(tmp_path, monkeypatch):
    mif, world, packet, public = fixture(tmp_path, monkeypatch, omit=True)
    result = cx.crosswalk(mif, world, packet, public)
    cand = [r for r in result["selected_variable_comparisons"]
            if r["variable"] == TOTAL][0]
    assert cand["comparison_status"] == "ARCHIVE_VARIABLE_NOT_REPORTED"


def test_same_scenario_other_model_not_assumed_identical(tmp_path, monkeypatch):
    mif, world, packet, public = fixture(
        tmp_path, monkeypatch, model="REMIND MODEL DIFFERENT VERSION")
    result = cx.crosswalk(mif, world, packet, public)
    assert result["status"] == "SCENARIO_NAME_MATCH_ONLY_MODEL_MAPPING_UNVERIFIED"
    assert result["archive_exact_world_variable_count"] == 0
    assert result["same_scenario_distinct_model_label_count"] == 1


def test_same_model_scenario_other_region_not_world(tmp_path, monkeypatch):
    mif, world, packet, public = fixture(
        tmp_path, monkeypatch, region="R5ASIA")
    result = cx.crosswalk(mif, world, packet, public)
    assert result["status"] == "MATCHED_MODEL_SCENARIO_BUT_WORLD_REGION_NOT_FOUND"
    assert result["archive_region_name_counts_exact_pair"] == {"R5ASIA": len(VARS)}


def test_source_archive_md5_wrong_fails_closed(tmp_path, monkeypatch):
    mif, world, packet, public = fixture(tmp_path, monkeypatch)
    mif.write_text(mif.read_text() + "\n# changed\n")
    with pytest.raises(CaseAuditError, match="MD5 mismatch"):
        cx.crosswalk(mif, world, packet, public)
    assert not public.exists()


def test_private_case_world_sha_wrong_fails_closed(tmp_path, monkeypatch):
    mif, world, packet, public = fixture(tmp_path, monkeypatch)
    obj = json.loads(packet.read_text())
    obj["source_sha256"] = "0" * 64
    packet.write_text(json.dumps(obj))
    with pytest.raises(CaseAuditError, match="SHA has changed"):
        cx.crosswalk(mif, world, packet, public)
    assert not public.exists()


def test_2050_original_packet_disagreement_fails_closed(tmp_path, monkeypatch):
    mif, world, packet, public = fixture(tmp_path, monkeypatch)
    obj = json.loads(packet.read_text())
    obj["cases"][2]["source_observations"][TOTAL]["raw"] = "999"
    packet.write_text(json.dumps(obj))
    with pytest.raises(CaseAuditError, match="2050 case"):
        cx.crosswalk(mif, world, packet, public)


def test_public_output_not_in_private_area(tmp_path, monkeypatch):
    mif, world, packet, public = fixture(tmp_path, monkeypatch)
    with pytest.raises(CaseAuditError, match="remain in private"):
        cx.crosswalk(mif, world, packet, mif.parent / "leak.json")


def test_author_text_legacy_cp1252_does_not_corrupt_source(tmp_path):
    """Regression for the real author Rmd/README's non-UTF8 source bytes."""
    path = tmp_path / "legacy.Rmd"
    original = b"scenario CEMICS_SSP1-1p5C-minCDR\nGross CO2 \xc2 and \x96 BECCS\n"
    path.write_bytes(original)
    lines, decoding = cx._read_author_text_lines(path)
    assert decoding["decoded_as"] == "cp1252"
    assert decoding["utf8_strict_success"] is False
    assert "NOT_SOURCE_CERTIFIED" in decoding["encoding_certainty"]
    assert len(lines) == 2
    assert cx.SCENARIO in lines[0]
    assert "BECCS" in lines[1]
    assert path.read_bytes() == original


def test_utf8_author_text_uses_strict_decode(tmp_path):
    path = tmp_path / "normal.txt"
    path.write_text("Carbon removals — SSP1\n", encoding="utf-8-sig")
    lines, decoding = cx._read_author_text_lines(path)
    assert decoding["decoded_as"] == "utf-8-sig"
    assert decoding["utf8_strict_success"] is True
    assert lines[0].endswith("SSP1")


def test_legacy_latin1_fallback_explicitly_flagged(tmp_path):
    path = tmp_path / "latin1.txt"
    path.write_bytes(b"Gross emissions \x81 SSP1\n")
    lines, decoding = cx._read_author_text_lines(path)
    assert decoding["decoded_as"] == "latin-1"
    assert "NOT_SOURCE_CERTIFIED" in decoding["encoding_certainty"]
    assert lines[0].startswith("Gross emissions")


def test_binary_nul_author_file_rejected(tmp_path):
    path = tmp_path / "corrupt.txt"
    path.write_bytes(b"First line\x00second line")
    with pytest.raises(CaseAuditError, match="NUL"):
        cx._read_author_text_lines(path)


def test_full_crosswalk_supporting_documents_with_cp1252(tmp_path, monkeypatch):
    mif, world, packet, public = fixture(tmp_path, monkeypatch)
    docs = mif.parent
    rmd = docs / "CDRoptions.Rmd"
    readme = docs / "readme_zenodo.txt"
    rmd.write_bytes(
        b"Example author workflow \xc2 : SSP1\n"
        b"Scenario CEMICS_SSP1-1p5C-minCDR, BECCS, gross emissions\n"
    )
    readme.write_bytes(b"CEMICS archive includes DAC \x96 land removals\n")
    monkeypatch.setattr(cx, "AUTHOR_SUPPORT_MD5", {
        "authors_rmd": md5(rmd.read_bytes()).hexdigest(),
        "authors_readme": md5(readme.read_bytes()).hexdigest(),
    })
    result = cx.crosswalk(
        mif, world, packet, public, rmd_path=rmd, readme_path=readme
    )
    info = result["author_methodology_code_presence"]
    assert info["authors_rmd"]["source_md5_verified"] is True
    assert info["authors_readme"]["source_md5_verified"] is True
    assert info["authors_rmd"]["decoded_as"] == "cp1252"
    assert info["authors_rmd"]["exact_scenario_line_numbers"] == [2]
    assert info["authors_readme"]["decoded_as"] == "cp1252"
    assert result["scientific_grade"] == "NOT_DETERMINED"
    assert not result["verified_i3"]
    serialized = public.read_text(encoding="utf-8")
    assert "Example author workflow" not in serialized
    assert "land removals" not in serialized


def test_bad_supporting_document_md5_still_fails_closed(tmp_path, monkeypatch):
    mif, world, packet, public = fixture(tmp_path, monkeypatch)
    rmd = mif.parent / "CDRoptions.Rmd"
    rmd.write_bytes(b"Study \xc2 BECCS\n")
    with pytest.raises(CaseAuditError, match="MD5 mismatch"):
        cx.crosswalk(mif, world, packet, public, rmd_path=rmd)
    assert not public.exists()


def test_entire_scenario_absent_does_not_claim_all_carbon_variables_missing(
        tmp_path, monkeypatch):
    mif, world, packet, public = fixture(
        tmp_path, monkeypatch, model="OTHER MODEL")
    # Replace the sole author scenario label, preserving the updated MD5.
    body = mif.read_text()
    mif.write_text(body.replace(cx.SCENARIO, "different_CEMICS_scenario"))
    monkeypatch.setattr(
        cx, "EXPECTED_ARCHIVE_MD5", md5(mif.read_bytes()).hexdigest())
    result = cx.crosswalk(mif, world, packet, public)
    assert result["status"] == "SCENARIO_NOT_LOCATED_IN_AUTHOR_MIF"
    assert all(
        item["comparison_status"] == "CASE_SCENARIO_ABSENT_FIELDS_NOT_ASSESSED"
        for item in result["selected_variable_comparisons"]
    )
    assert not result["verified_i3"]
