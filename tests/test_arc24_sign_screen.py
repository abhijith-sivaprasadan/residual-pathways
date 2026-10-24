"""Synthetic regression tests for sign screens, not scientific review of AR6."""
import json
import pytest

from residual_pathways.arc24_sign_screen import sign, sign_report, write_sign_report, VARIABLES
from residual_pathways.case_audit import CaseAuditError, UNIT


def fixture():
    cases = []
    for i in range(1, 25):
        source = {v: {"value": 1, "unit": UNIT} for v in VARIABLES}
        if i == 3:
            source["Carbon Sequestration|Direct Air Capture"]["value"] = 0
        if i == 6:
            source["Emissions|CO2|AFOLU"]["value"] = -2
        cases.append({
            "case_id": f"ARC24-{i:02d}", "model": f"PRIVATE_MODEL_{i}",
            "scenario": f"PRIVATE_SCENARIO_{i}", "category": "C1",
            "source_observations": source,
        })
    return {"handling": "LOCAL_ONLY_DO_NOT_PUBLISH",
            "source_sha256": "abc123", "metadata_sha256": "def456",
            "cases": cases}


def test_screen_24_private_cases_sign_and_no_i3(tmp_path):
    payload = fixture()
    inp = tmp_path / "data" / "ar6-private" / "canonical_selected24_packet.json"
    inp.parent.mkdir(parents=True)
    inp.write_text(json.dumps(payload))
    dest = tmp_path / "results" / "ar6" / "signs.json"
    result = write_sign_report(inp, dest)
    assert len(result["cases"]) == 24
    assert result["negative_afolu_cases"] == 1
    assert result["verified_i3_cases"] == 0
    assert result["reviewed_cases"] == 0
    case3 = next(c for c in result["cases"] if c["case_id"] == "ARC24-03")
    case6 = next(c for c in result["cases"] if c["case_id"] == "ARC24-06")
    assert case3["variable_signs"]["Carbon Sequestration|Direct Air Capture"] == "ZERO"
    assert "DAC_REPORTED_ZERO_NOT_MISSING" in case3["diagnostic_flags"]
    assert "LAND_SEQUESTRATION_AND_NET_AFOLU_COEXIST_DO_NOT_DOUBLE_COUNT" in case6["diagnostic_flags"]
    assert "NEGATIVE_NET_AFOLU_CO2_NOT_GROSS_LAND_CDR" in case6["diagnostic_flags"]
    serialized = dest.read_text()
    assert "PRIVATE_MODEL" not in serialized
    assert "PRIVATE_SCENARIO" not in serialized
    assert "\"value\"" not in serialized
    assert "SOURCE_SIGN_SCREEN_ONLY_NO_I3" in serialized


def test_missing_is_not_zero_and_wrong_unit_not_accepted():
    payload = fixture()
    del payload["cases"][0]["source_observations"]["Carbon Sequestration|Land Use"]
    payload["cases"][0]["source_observations"]["Carbon Sequestration|CCS|Fossil"]["unit"] = "kg"
    result = sign_report(payload)
    data = result["cases"][0]["variable_signs"]
    assert data["Carbon Sequestration|Land Use"] == "MISSING"
    assert data["Carbon Sequestration|CCS|Fossil"] == "INCOMPATIBLE_UNIT"
    assert result["missing_land_sequestration_cases"] == 1


@pytest.mark.parametrize("bad", [None, True, "nan", "Infinity", "invalid"])
def test_invalid_missing_or_nonfinite_source_is_rejected(bad):
    with pytest.raises(CaseAuditError):
        sign(bad)


def test_private_and_public_output_cannot_overlap(tmp_path):
    payload = fixture()
    inp = tmp_path / "data" / "ar6-private" / "original.json"
    inp.parent.mkdir(parents=True)
    inp.write_text(json.dumps(payload))
    with pytest.raises(CaseAuditError, match="Public output"):
        write_sign_report(inp, inp)
    with pytest.raises(CaseAuditError, match="Public output"):
        write_sign_report(inp, inp.parent / "output.json")


def test_duplicate_cases_and_invalid_packet_fail_closed():
    packet = fixture()
    packet["cases"][1]["case_id"] = packet["cases"][0]["case_id"]
    with pytest.raises(CaseAuditError):
        sign_report(packet)
    packet = fixture()
    packet["handling"] = "SOURCE_PUBLIC"
    with pytest.raises(CaseAuditError):
        sign_report(packet)
