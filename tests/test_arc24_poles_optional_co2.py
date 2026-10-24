"""Synthetic input tests for redacted AR6 POLES optional CO2 variable presence."""
import csv
import json
import pytest

from residual_pathways.arc24_poles_optional_co2 import (
    optional_sector_presence, write_optional_sectors, OPTIONAL,
)
from residual_pathways.case_audit import CaseAuditError
from residual_pathways.stratify import sha_file


def fixture(tmp_path, *, duplicate=False):
    private = tmp_path / "data" / "ar6-private"
    private.mkdir(parents=True)
    world = private / "AR6_Scenarios_Database_World_v1.1.csv"
    cases = []
    for i in range(1, 25):
        cases.append({
            "case_id": f"ARC24-{i:02d}",
            "model": "POLES ENGAGE" if i in (6, 9, 12, 21) else "OTHER",
            "scenario": f"UNPUBLISHED_SCENARIO_{i:02d}",
            "category": f"C{(i-1)//3+1}",
        })
    with world.open("w", newline="", encoding="utf-8") as fd:
        writer = csv.writer(fd)
        writer.writerow(["Model","Scenario","Region","Variable","Unit",
                         "2030","2040","2050","2060","2070"])
        # Coverage deliberately differs by scenario, year, value and unit.
        writer.writerow(["POLES ENGAGE", "UNPUBLISHED_SCENARIO_06", "World",
                         OPTIONAL[0], "Mt CO2/yr", "1", "0", "-1", "", "2"])
        writer.writerow(["POLES ENGAGE", "UNPUBLISHED_SCENARIO_09", "World",
                         OPTIONAL[1], "Mt CO2/yr", "-3", "3", "0", "0", "5"])
        writer.writerow(["POLES ENGAGE", "UNPUBLISHED_SCENARIO_12", "World",
                         OPTIONAL[2], "kg", "1", "2", "3", "4", "5"])
        writer.writerow(["POLES ENGAGE", "UNPUBLISHED_SCENARIO_21", "World",
                         OPTIONAL[3], "Mt CO2/yr", "0", "", "1", "4", "-2"])
        if duplicate:
            writer.writerow(["POLES ENGAGE", "UNPUBLISHED_SCENARIO_06", "World",
                             OPTIONAL[0], "Mt CO2/yr", "1", "0", "-1", "", "2"])
    packet = private / "canonical_selected24_packet.json"
    packet.write_text(json.dumps({
        "schema": "residualpathways.ar6_canonical_selected24.private.v1",
        "handling": "LOCAL_ONLY_DO_NOT_PUBLISH",
        "source_sha256": sha_file(world),
        "cases": cases,
    }))
    return world, packet, tmp_path / "results" / "arc24_poles_optional_co2_public.json"


def test_distinguishes_zero_missing_negative_and_unit_mismatch(tmp_path):
    world, packet, output = fixture(tmp_path)
    result = write_optional_sectors(world, packet, output)
    assert result["status"] == "ORIGINAL_SOURCE_PRESENCE_ONLY_NO_ADJUSTED_ACCOUNTING"
    assert result["num_case_years"] == 20
    assert result["verified_i3"] == 0
    grid = {(o["case_id"],o["year"]): o["optional_sector_states"]
            for o in result["observations"]}
    assert grid[("ARC24-06", 2030)][OPTIONAL[0]] == "POSITIVE"
    assert grid[("ARC24-06", 2040)][OPTIONAL[0]] == "REPORTED_ZERO"
    assert grid[("ARC24-06", 2050)][OPTIONAL[0]] == "NEGATIVE"
    assert grid[("ARC24-06", 2060)][OPTIONAL[0]] == "MISSING_YEAR_VALUE"
    assert grid[("ARC24-06", 2050)][OPTIONAL[1]] == "SERIES_NOT_REPORTED"
    assert grid[("ARC24-12", 2050)][OPTIONAL[2]] == "INCOMPATIBLE_UNIT"
    assert grid[("ARC24-21", 2070)][OPTIONAL[3]] == "NEGATIVE"
    out = output.read_text()
    assert "UNPUBLISHED_SCENARIO" not in out
    assert '"1"' not in out
    assert "POLES ENGAGE" not in out


def test_source_sha_change_blocks_false_reuse(tmp_path):
    world, packet, output = fixture(tmp_path)
    payload = json.loads(packet.read_text())
    payload["source_sha256"] = "a"*64
    packet.write_text(json.dumps(payload))
    with pytest.raises(CaseAuditError, match="fingerprint"):
        optional_sector_presence(world, packet, output)


def test_private_output_path_rejected(tmp_path):
    world, packet, output = fixture(tmp_path)
    with pytest.raises(CaseAuditError, match="private"):
        write_optional_sectors(world, packet, packet.parent / "leak.json")


def test_duplicate_original_source_row_is_rejected(tmp_path):
    world, packet, output = fixture(tmp_path, duplicate=True)
    with pytest.raises(CaseAuditError, match="Duplicate"):
        optional_sector_presence(world, packet, output)


def test_missing_or_relabelled_poles_target_rejected(tmp_path):
    world, packet, output = fixture(tmp_path)
    data = json.loads(packet.read_text())
    data["cases"][5]["model"] = "DIFFERENT MODEL"
    packet.write_text(json.dumps(data))
    with pytest.raises(CaseAuditError, match="POLES"):
        optional_sector_presence(world, packet, output)
