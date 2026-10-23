"""Pinned official MESSAGEix Westeros baseline + controlled actual GAMS solves.

Requires the user's local GAMS installation and license. This module never
collects license files, solver listing files, or confidential GDX model inputs.
"""
from __future__ import annotations
from hashlib import sha1, sha256
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from urllib.request import urlopen
import json
import math
import shutil

TAG = "v3.11.1"
NOTEBOOKS = {
    "baseline": ("tutorial/westeros/westeros_baseline.ipynb",
                 "dfb09340ef09f994fb06eb49845d707867a404c9"),
    "emissions": ("tutorial/westeros/westeros_emissions_bounds.ipynb",
                  "9ec20c97604544b3c6b96e72d370095dd30a2429"),
}
BASE_CELLS = (6, 8, 11, 13, 15, 18, 22, 25, 28, 32, 33, 37, 39,
              43, 47, 49, 51, 53, 56, 59, 61, 63, 66, 68, 69)
EMISSION_CELLS = (4, 6, 8)
MODEL = "Westeros Electrified"
VERSION = "3.11.1"


class WesterosError(RuntimeError):
    pass


def blob_sha(data):
    return sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def verify_notebook(raw, kind):
    if kind not in NOTEBOOKS or blob_sha(raw) != NOTEBOOKS[kind][1]:
        raise WesterosError("Official notebook blob SHA mismatch; execution forbidden")
    try:
        nb = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise WesterosError("Invalid official notebook JSON") from exc
    if nb.get("nbformat") != 4 or not isinstance(nb.get("cells"), list):
        raise WesterosError("Unexpected official notebook format")
    for index in BASE_CELLS if kind == "baseline" else EMISSION_CELLS:
        if index >= len(nb["cells"]) or nb["cells"][index].get("cell_type") != "code":
            raise WesterosError("Official notebook cell layout changed")
    return nb


def load_official_sources(directory):
    dest = Path(directory)
    dest.mkdir(parents=True, exist_ok=True)
    notebooks, provenance = {}, {}
    for kind, (path, expected_blob) in NOTEBOOKS.items():
        url = f"https://raw.githubusercontent.com/iiasa/message_ix/{TAG}/{path}"
        with urlopen(url, timeout=40) as response:
            raw = response.read()
        notebooks[kind] = verify_notebook(raw, kind)
        (dest / (kind + ".ipynb")).write_bytes(raw)
        provenance[kind] = {"url": url, "git_tag": TAG, "git_blob_sha1": expected_blob,
                            "raw_sha256": sha256(raw).hexdigest()}
    return notebooks, provenance


def preflight():
    try:
        installed = version("message_ix")
    except PackageNotFoundError:
        installed = None
    return {"gams_available": bool(shutil.which("gams")),
            "message_ix_version": installed, "required_message_ix_version": VERSION,
            "license_secret_checked": False, "solve_executed": False}


def validate_environment(status):
    if not status["gams_available"]:
        raise WesterosError("GAMS executable not found on PATH")
    if status["message_ix_version"] != VERSION:
        raise WesterosError("Use a dedicated environment with message-ix[tutorial]==3.11.1")


def cell_text(notebook, index):
    return "".join(notebook["cells"][index]["source"])


def baseline_cell(notebook, index):
    code = cell_text(notebook, index)
    if index == 6:
        old = "mp = ixmp.Platform()"
        if code.count(old) != 1:
            raise WesterosError("Unexpected official platform construction")
        code = code.replace(old, "mp = ixmp.Platform(backend='jdbc', driver='hsqldb', url='jdbc:hsqldb:mem:rp_westeros')")
    elif index == 18:
        # Omit optional illustration only, preserve source GDP profile.
        code = code.replace('gdp_profile.plot(title="GDP profile")', "")
    elif index == 69:
        if code.strip() != "scenario.solve()":
            raise WesterosError("Unexpected official solve cell")
        code = "scenario.solve(model_dir=str(model_dir))"
    return code


def solved_objective(scenario):
    if not scenario.has_solution():
        raise WesterosError("MESSAGEix scenario has no solver solution")
    frame = scenario.var("OBJ")
    if frame.empty or "lvl" not in frame or len(frame) != 1:
        raise WesterosError("Solved model has no unique OBJ scalar")
    result = float(frame["lvl"].iloc[0])
    if not math.isfinite(result):
        raise WesterosError("Solver returned nonfinite objective")
    return result


def summary(scenario, name, change, source):
    return {"model": MODEL, "scenario": name,
            "status": "SOLVED_MESSAGEIX_GAMS_STYLIZED_WESTEROS",
            "has_solution": bool(scenario.has_solution()),
            "objective_value": solved_objective(scenario),
            "intervention": change, "not_ar6": True, "official_source": source}


def run_westeros(output_dir):
    """Three real solves or a failure. No simulated/assumed successful output."""
    import ixmp
    import message_ix
    from message_ix.util import copy_model

    dest = Path(output_dir)
    status = preflight()
    validate_environment(status)
    notebooks, sources = load_official_sources(dest / "official_notebooks")
    model_dir = (dest / "gams_model").resolve()
    copy_model(model_dir, quiet=True)
    ns = {"__name__": "__main__", "model_dir": model_dir}
    stage = "OFFICIAL_BASELINE"
    try:
        for index in BASE_CELLS:
            exec(compile(baseline_cell(notebooks["baseline"], index),
                         f"official_baseline_cell_{index}", "exec"), ns)
        base = ns["scenario"]
        mp = ns["mp"]
        baseline = summary(base, "baseline", "UNMODIFIED_OFFICIAL", sources["baseline"])

        stage = "WIND_CAPEX"
        wind = base.clone(MODEL, "rp_wind_capex_half", keep_solution=False)
        wind.check_out()
        old = wind.par("inv_cost", {"technology": "wind_ppl"})
        if old.empty or old["unit"].nunique() != 1 or old["unit"].iloc[0] != "USD/kW":
            raise WesterosError("Missing or unexpected official wind investment cost")
        if not all(float(v) == 1500 for v in old["value"]):
            raise WesterosError("Official notebook wind investment cost unexpectedly changed")
        wind.remove_par("inv_cost", old)
        revised = old.copy()
        revised["value"] = revised["value"] * 0.5
        wind.add_par("inv_cost", revised)
        wind.commit(comment="One-factor wind investment cost reduction, 1500 to 750 USD/kW")
        wind.solve(model_dir=str(model_dir))
        wind_result = summary(wind, "rp_wind_capex_half",
                              {"parameter": "wind_ppl inv_cost", "from": 1500, "to": 750,
                               "unit": "USD/kW"}, sources["baseline"])

        stage = "EMISSIONS_BOUND"
        bound = base.clone(MODEL, "rp_emission_bound", keep_solution=False)
        bound.check_out()
        ns.update({"scen": bound, "country": "Westeros"})
        for index in EMISSION_CELLS:
            exec(compile(cell_text(notebooks["emissions"], index),
                         f"official_emissions_cell_{index}", "exec"), ns)
        bound.commit(comment="Official emissions bound: 500 MtCO2 cumulative")
        bound.solve(model_dir=str(model_dir))
        bound_result = summary(bound, "rp_emission_bound",
                               {"type": "official_bound_emission_tutorial",
                                "cumulative_cap": 500, "unit": "MtCO2",
                                "coal_factor": 7.4, "factor_unit": "tCO2/kWa"},
                               sources["emissions"])
        result = {
            "schema_version": "westeros-actual-gams-v1", "status": "SUCCESS",
            "evidence_tier": "LOCALLY_EXECUTED_MESSAGEIX_GAMS_STYLIZED",
            "source_provenance": sources, "preflight": {**status, "solve_executed": True},
            "cases": [baseline, wind_result, bound_result],
            "limitations": "Not AR6, global IAM, CDR or residual gross emissions.",
            "license_handling": "No GAMS license key/content read, copied or serialized.",
        }
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "solved_manifest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result
    except Exception:
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "failed_manifest.json").write_text(json.dumps(
            {"status": "FAILED_NO_SOLVE_CLAIM", "stage": stage,
             "note": "Inspect the local console and GAMS listings; do not upload license data."},
            indent=2) + "\n")
        raise
    finally:
        if "mp" in ns:
            ns["mp"].close_db()
