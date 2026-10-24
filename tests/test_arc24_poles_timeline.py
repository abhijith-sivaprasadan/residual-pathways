"""Synthetic source-locked temporal falsification checks for four POLES cases."""
import csv
import json

import pytest

from residual_pathways.arc24_poles_timeline import investigate, write_timeline
from residual_pathways.case_audit import TOTAL, SIX, CaseAuditError
from residual_pathways.stratify import sha_file

COMPONENTS = (TOTAL, SIX[0], SIX[1])
TARGETS = {6, 9, 12, 21}


def fixture(tmp_path):
    folder = tmp_path / "data" / "ar6-private"
    folder.mkdir(parents=True)
    path = folder / "AR6_Scenarios_Database_World_v1.1.csv"
    cases = []
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Model", "Scenario", "Region", "Variable", "Unit",
                         "2030", "2050", "2070"])
        for i in range(1, 25):
            targeted = i in TARGETS
            model = "POLES ENGAGE" if targeted else "CONTROL MODEL"
            scn = f"PRIVATE_SCENARIO_{i}"
            obs = {}
            if targeted:
                vals = {
                    TOTAL: "105" if i in (12, 21) else "95",
                    SIX[0]: "100",
                    SIX[1]: "0",
                }
                for v in COMPONENTS:
                    writer.writerow([model, scn, "World", v, "Mt CO2/yr",
                                     "100" if v == TOTAL else
                                     "100" if v == SIX[0] else "0",
                                     vals[v],
                                     "100" if v == TOTAL else
                                     "100" if v == SIX[0] else "0"])
                    obs[v] = {"raw": vals[v], "value": float(vals[v]),
                              "unit": "Mt CO2/yr"}
            cases.append({
                "case_id": f"ARC24-{i:02d}", "model": model,
                "scenario": scn, "category": f"C{(i-1)//3+1}",
                "source_observations": obs,
            })
    packet = folder / "canonical_selected24_packet.json"
    packet.write_text(json.dumps({
        "schema": "residualpathways.ar6_canonical_selected24.private.v1",
        "handling": "LOCAL_ONLY_DO_NOT_PUBLISH",
        "source_sha256": sha_file(path), "cases": cases,
    }))
    public = tmp_path / "results" / "poles_public.json"
    return path, packet, public


def test_signs_across_years_and_no_private_data_in_public(tmp_path):
    csv_path, packet, public = fixture(tmp_path)
    result = write_timeline(csv_path, packet, public)
    assert result["cases"] == 4
    assert len(result["observations"]) == 20
    assert result["reviewed_i3_cases"] == 0
    by_key = {(r["case_id"], r["year"]): r for r in result["observations"]}
    assert by_key[("ARC24-06", 2050)]["signed_residual_band"] == "NEGATIVE__FROM_1_TO_BELOW_10_PERCENT"
    assert by_key[("ARC24-12", 2050)]["signed_residual_band"] == "POSITIVE__FROM_1_TO_BELOW_10_PERCENT"
    assert by_key[("ARC24-09", 2030)]["signed_residual_band"] == "ZERO"
    assert by_key[("ARC24-21", 2070)]["signed_residual_band"] == "ZERO"
    assert by_key[("ARC24-06", 2040)]["arithmetic_status"] == "YEAR_COLUMN_ABSENT"
    assert by_key[("ARC24-06", 2060)]["arithmetic_status"] == "YEAR_COLUMN_ABSENT"
    s = public.read_text()
    assert "PRIVATE_SCENARIO" not in s
    assert "POLES ENGAGE" not in s
    assert '"105"' not in s
    assert '"95"' not in s


def test_source_hash_mismatch_is_blocked(tmp_path):
    csv_path, packet, public = fixture(tmp_path)
    d = json.loads(packet.read_text())
    d["source_sha256"] = "wrong"
    packet.write_text(json.dumps(d))
    with pytest.raises(CaseAuditError, match="World source CSV changed"):
        investigate(csv_path, packet, public)
    assert not public.exists()


def test_model_identity_tampering_detected(tmp_path):
    csv_path, packet, public = fixture(tmp_path)
    d = json.loads(packet.read_text())
    d["cases"][5]["model"] = "WRONG MODEL"
    packet.write_text(json.dumps(d))
    with pytest.raises(CaseAuditError, match="POLES ENGAGE"):
        investigate(csv_path, packet, public)


def test_prior_2050_packet_mismatch_rejected(tmp_path):
    csv_path, packet, public = fixture(tmp_path)
    d = json.loads(packet.read_text())
    d["cases"][5]["source_observations"][TOTAL]["raw"] = "100"
    packet.write_text(json.dumps(d))
    with pytest.raises(CaseAuditError, match="2050 selected packet"):
        investigate(csv_path, packet, public)


def test_disallows_private_output(tmp_path):
    csv_path, packet, public = fixture(tmp_path)
    with pytest.raises(CaseAuditError, match="Private source"):
        investigate(csv_path, packet, packet.parent / "bad_public.json")
