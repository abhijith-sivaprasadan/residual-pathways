"""Case-study fixtures are synthetic; NO GAMS/ixmp execution in this suite."""
import copy
from hashlib import sha256
import json

import pytest

from residual_pathways.westeros_case_study import (
    SCENARIOS, CONTROL_NAME, generation_svg, objective_svg,
    publish_case_study, report, validate_case_study,
)
from residual_pathways.westeros_no_cap import PARITY_PARS
from residual_pathways.westeros_analysis import WesterosAnalysisError


def synthetic_control():
    b = 159025.828125
    c = 191510.796875
    acts = {
        700: (47.37429150867584, 13.736819602435279,
              47.37429150867584, 13.736819602435276),
        710: (89.55085163044144, 1.560259480669675,
              76.82565352959837, 14.285457581512746),
        720: (115.55555555555556, 0.0,
              78.50275766442846, 37.05279789112709),
    }
    rows = []
    for metric in ("ACT", "CAP", "CAP_NEW"):
        for year in (700, 710, 720):
            for tech in ("coal_ppl", "wind_ppl", "grid", "bulb"):
                if metric == "ACT" and tech in ("coal_ppl", "wind_ppl"):
                    coal, wind, coal_bound, wind_bound = acts[year]
                    v = coal if tech == "coal_ppl" else wind
                    vb = coal_bound if tech == "coal_ppl" else wind_bound
                else:
                    v = 40.0
                    vb = 42.0 if year > 700 and tech == "wind_ppl" else v
                rows.append({
                    "metric": metric, "year": year, "technology": tech,
                    "baseline": v, CONTROL_NAME: v, "emission_bound": vb,
                    "control_minus_baseline": 0.0, "cap_minus_control": vb - v,
                    "complete": True,
                })
    return {
        "schema": "residualpathways.westeros.control_comparison.v1",
        "status": "ACTUAL_MESSAGEIX_GAMS_CONTROL_SOLVED",
        "provenance": "AUTHOR_LOCAL_GAMS_NOT_INDEPENDENTLY_REPRODUCED",
        "scientific_scope": "EDUCATIONAL_WESTEROS_NOT_AR6",
        "source_run_id": "20261023T230104Z_e182e730",
        "control_scenario": CONTROL_NAME,
        "control_version": 1,
        "intervention": "remove exactly one emissions bound; retain CO2 emissions accounting",
        "verified_inputs": {
            "only_intended_change": "bound_emission parameter rows removed",
            "source_cap_rows": 1, "control_cap_rows": 0,
            "parameter_rows_verified": {p: 1 for p in PARITY_PARS},
        },
        "objectives_native": {
            "baseline": b, CONTROL_NAME: b, "emission_bound": c,
        },
        "baseline_vs_control": {
            "difference": 0.0, "numerically_equivalent": True,
            "absolute_tolerance": .159,
        },
        "cap_effect": {
            "difference_native": c - b,
            "relative_percent": 100 * (c - b) / b,
            "attributable_to_bound_only": True,
        },
        "comparisons": rows,
    }


def synthetic_cap():
    return {
        "status": "NUMERICALLY_SATURATED",
        "run_id": "20261023T230104Z_e182e730",
        "upstream_commit": "2d521407a430a08de997a771e7b38d88f7e7d2b6",
        "evidence_scope": "AUTHOR_REPORTED_LOCAL_SAVED_IXMP_EDUCATIONAL",
        "duration_source": "SAVED_SCENARIO_PARAMETER",
        "period_durations": {"700": 10.0, "710": 10.0, "720": 10.0},
        "periods_in_category": [700, 710, 720],
        "emission_scaling": 1.0,
        "shadow_price_status": "NOT_ESTABLISHED",
        "bound_value": 500.0, "computed_average_annual": 500.0,
        "slack": 0.0, "tolerance": .0005,
    }


def test_three_case_validates_recalculated_substitution_and_scope():
    result = validate_case_study(synthetic_control(), synthetic_cap())
    assert result["status"] == "READY_AUTHOR_REPORTED_EDUCATIONAL_CASE_STUDY"
    assert result["cap_effect"]["difference_native"] == 32484.96875
    assert result["baseline_control_activity_parity"] is True
    assert len(result["comparisons"]) == 36
    assert result["cap_reconciliation"]["carbon_shadow_price"] == "NOT_ESTABLISHED"
    assert all(result["baseline_control_parity_by_metric"].values())
    yr720 = [r for r in result["generation"]
             if r["year"] == 720 and r["scenario"] == "emission_bound"][0]
    assert yr720["coal_GWa"] == pytest.approx(78.50275766442846)
    assert yr720["wind_GWa"] == pytest.approx(37.05279789112709)
    assert "svg" in generation_svg(result)
    assert "svg" in objective_svg(result)
    assert "shadow price" in report(result).lower()


@pytest.mark.parametrize("mutation", [
    lambda x: x["objectives_native"].update({CONTROL_NAME: 170000}),
    lambda x: x["comparisons"][0].update({"control_minus_baseline": 7}),
    lambda x: x["comparisons"][0].update({CONTROL_NAME: 7}),
    lambda x: x["comparisons"][0].update({"emission_bound": 7}),
    lambda x: x["comparisons"].pop(),
    lambda x: x["comparisons"].append(copy.deepcopy(x["comparisons"][0])),
    lambda x: x["verified_inputs"].update({"control_cap_rows": 1}),
    lambda x: x["verified_inputs"]["parameter_rows_verified"].pop("emission_factor"),
    lambda x: x.update({"scientific_scope": "AR6"}),
    lambda x: x["objectives_native"].update({"emission_bound": float("nan")}),
])
def test_control_tampering_rejected(mutation):
    data = synthetic_control()
    mutation(data)
    with pytest.raises((WesterosAnalysisError, ValueError, TypeError)):
        validate_case_study(data, synthetic_cap())


@pytest.mark.parametrize("mutation", [
    lambda x: x.update({"status": "NOT_ESTABLISHED"}),
    lambda x: x.update({"run_id": "20260101T000000Z_deadbeef"}),
    lambda x: x.update({"shadow_price_status": "PRICED"}),
    lambda x: x.update({"duration_source": "ASSUMED"}),
    lambda x: x["period_durations"].update({"710": 11}),
    lambda x: x.update({"slack": 25}),
])
def test_cap_tampering_rejected(mutation):
    cap = synthetic_cap()
    mutation(cap)
    with pytest.raises((WesterosAnalysisError, ValueError)):
        validate_case_study(synthetic_control(), cap)


def test_publish_five_derived_files_hashes_and_no_original_manifest(tmp_path):
    private = tmp_path / "private" / "control"
    private.mkdir(parents=True)
    audit_dir = tmp_path / "private" / "cap"
    audit_dir.mkdir(parents=True)
    control_path = private / "three_case_comparison.json"
    cap_path = audit_dir / "cap_reconciliation.json"
    control = synthetic_control()
    control["credential"] = "SHOULD_NOT_LEAK_PRIVATE_CONTENT"
    control_path.write_text(json.dumps(control))
    cap_raw = (json.dumps(synthetic_cap()) + "\n").encode()
    cap_path.write_bytes(cap_raw)
    (audit_dir / "cap_reconciliation.sha256").write_text(sha256(cap_raw).hexdigest() + "\n")
    dest = tmp_path / "results" / "case_study"
    data, manifest = publish_case_study(control_path, cap_path, dest)
    assert len(manifest["files"]) == 5
    for name, record in manifest["files"].items():
        raw = (dest / name).read_bytes()
        assert sha256(raw).hexdigest() == record["sha256"]
        assert record["bytes"] == len(raw)
        assert b"SHOULD_NOT_LEAK" not in raw
    assert not (dest / "manifest.private.json").exists()
    assert not (dest / "three_case_comparison.json").exists()
    assert b"NO GAMS" not in (dest / "case_study.md").read_bytes()
    assert data["cap_effect"]["relative_percent"] == pytest.approx(20.427479694974863)


def test_hash_mismatch_rejected(tmp_path):
    private = tmp_path / "source"
    private.mkdir()
    a = private / "three_case_comparison.json"
    b = private / "cap_reconciliation.json"
    a.write_text(json.dumps(synthetic_control()))
    b.write_text(json.dumps(synthetic_cap()))
    (private / "cap_reconciliation.sha256").write_text("0" * 64)
    with pytest.raises(WesterosAnalysisError, match="SHA-256"):
        publish_case_study(a, b, tmp_path / "public")


def test_output_inside_source_rejected(tmp_path):
    private = tmp_path / "private"
    private.mkdir()
    a = private / "three_case_comparison.json"
    b = private / "cap_reconciliation.json"
    a.write_text(json.dumps(synthetic_control()))
    raw = json.dumps(synthetic_cap()).encode()
    b.write_bytes(raw)
    (private / "cap_reconciliation.sha256").write_text(sha256(raw).hexdigest())
    with pytest.raises(WesterosAnalysisError, match="private"):
        publish_case_study(a, b, private / "public")
