"""Local-only execution of official, SHA-pinned MESSAGEix/GAMS Westeros notebooks.

Never opens, prints, copies, or uploads a GAMS license. Passing CI unit tests
does NOT demonstrate a licensed solve on a user's machine.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from urllib.request import urlopen
import json
import math
import os
import shutil
import sys
import uuid

UPSTREAM_COMMIT = "2d521407a430a08de997a771e7b38d88f7e7d2b6"
UPSTREAM_RELEASE = "v3.11.1"
NOTEBOOKS = (
    ("baseline", "westeros_baseline.ipynb", 'scenario.var("OBJ")'),
    ("emission_bound", "westeros_emissions_bounds.ipynb", 'scen.var("OBJ")'),
)
MODEL = "Westeros Electrified"


class WesterosError(RuntimeError):
    pass


def installed_version(name):
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def preflight():
    return {
        "schema_version": "westeros-local-preflight.v1",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "gams_on_path": shutil.which("gams") is not None,
        "java_on_path": shutil.which("java") is not None,
        "message_ix_version": installed_version("message-ix"),
        "ixmp_version": installed_version("ixmp"),
        "nbclient_version": installed_version("nbclient"),
        "ipykernel_version": installed_version("ipykernel"),
        "required_message_ix_version": "3.11.1",
        "upstream_commit": UPSTREAM_COMMIT,
        "actual_solve_performed": False,
        "license_checked": False,
        "evidence": "ENVIRONMENT_ONLY_NOT_A_GAMS_SOLVE",
    }


def model_cells_until_objective(notebook, objective_expression):
    """Retain all upstream build/solve/OBJ cells; omit later plotting only."""
    cells = notebook.get("cells")
    if not isinstance(cells, list):
        raise WesterosError("Malformed notebook")
    solved = False
    stop = None
    for i, cell in enumerate(cells):
        if not isinstance(cell, dict):
            raise WesterosError("Malformed notebook cell")
        source = cell.get("source", "")
        source = "".join(source) if isinstance(source, list) else source
        if cell.get("cell_type") == "code":
            if ".solve()" in source:
                solved = True
            if objective_expression in source:
                if not solved:
                    raise WesterosError("Objective precedes actual solve")
                stop = i + 1
                break
    if stop is None:
        raise WesterosError("Upstream solve/objective cells missing")
    # JSON notebooks may store source as a list of lines. nbclient requires
    # a string for every cell, including markdown, before executing cells.
    normalized_cells = []
    for cell in cells[:stop]:
        source = cell.get("source", "")
        if isinstance(source, list):
            if not all(isinstance(line, str) for line in source):
                raise WesterosError("Malformed notebook cell source")
            source = "".join(source)
        elif not isinstance(source, str):
            raise WesterosError("Malformed notebook cell source")
        normalized_cells.append({**cell, "source": source})
    result = dict(notebook)
    result["cells"] = normalized_cells
    return result


def source_url(name):
    if name not in [n for _, n, _ in NOTEBOOKS]:
        raise WesterosError("Unexpected notebook name")
    return (f"https://raw.githubusercontent.com/iiasa/message_ix/{UPSTREAM_COMMIT}"
            f"/tutorial/westeros/{name}")


def fetch_notebook(filename, target):
    url = source_url(filename)
    with urlopen(url, timeout=90) as response:
        raw = response.read(8_000_001)
    if len(raw) > 8_000_000:
        raise WesterosError("Unexpected notebook size")
    try:
        notebook = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise WesterosError("Notebook is not valid JSON") from exc
    if notebook.get("nbformat") != 4:
        raise WesterosError("Unexpected source notebook format")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return notebook, {"source_url": url, "sha256": sha256(raw).hexdigest()}


def setup_private_kernel(run_dir):
    """Make this exact virtualenv's Python available without global install."""
    root = run_dir / "jupyter"
    dest = root / "kernels" / "rp-messageix"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "kernel.json").write_text(json.dumps({
        "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "RP private MESSAGEix",
        "language": "python",
    }), encoding="utf-8")
    return root


def setup_private_ixmp(run_dir):
    """Create an isolated HSQLDB default for the official notebooks."""
    dest = run_dir / "ixmp_config"
    dest.mkdir(parents=True, exist_ok=True)
    db = run_dir / "ixmp_database" / "westeros"
    db.parent.mkdir(parents=True, exist_ok=True)
    (dest / "config.json").write_text(json.dumps({
        "platform": {"default": "local", "local": {
            "class": "jdbc", "driver": "hsqldb", "path": db.resolve().as_posix()
        }}
    }, indent=2) + "\n", encoding="utf-8")
    return dest


@contextmanager
def temporary_environment(values):
    previous = {name: os.environ.get(name) for name in values}
    try:
        os.environ.update({name: str(value) for name, value in values.items()})
        yield
    finally:
        for name, old in previous.items():
            if old is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = old


def read_gams_solutions():
    """Read values persisted by actually solved scenarios from private ixmp."""
    import ixmp
    import message_ix
    mp = ixmp.Platform()
    try:
        result = []
        for stage, _, _ in NOTEBOOKS:
            scenario = message_ix.Scenario(mp, model=MODEL, scenario=stage)
            if not scenario.has_solution():
                raise WesterosError(f"No solved variables for {stage}")
            obj = scenario.var("OBJ")
            if obj.empty or "lvl" not in obj.columns:
                raise WesterosError(f"Missing solved objective for {stage}")
            values = [float(x) for x in obj["lvl"].tolist()]
            if len(values) != 1 or not math.isfinite(values[0]):
                raise WesterosError(f"Invalid/multiple objective levels for {stage}")
            result.append({"scenario": stage, "version": scenario.version,
                           "objective_native": values[0], "has_solution": True})
        return result
    finally:
        mp.close_db()


def run(output_root="results/messageix_private", *, download_only=False, timeout=1800):
    environment = preflight()
    if not download_only:
        missing = [
            label for label, ok in (
                ("GAMS", environment["gams_on_path"]),
                ("Java", environment["java_on_path"]),
                ("nbclient", environment["nbclient_version"] is not None),
                ("ipykernel", environment["ipykernel_version"] is not None),
            ) if not ok
        ]
        if missing:
            raise WesterosError("Missing installed prerequisites: " + ", ".join(missing))
        if environment["message_ix_version"] != "3.11.1":
            raise WesterosError("MESSAGEix version must be 3.11.1 for pinned official notebooks")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    run_dir = Path(output_root).resolve() / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "schema": "local-westeros-execution.v1",
        "run_id": run_id, "status": "DOWNLOADING",
        "model": MODEL, "upstream_commit": UPSTREAM_COMMIT,
        "upstream_release": UPSTREAM_RELEASE,
        "environment": environment, "notebooks": [],
        "solved_scenarios": [], "license_content_stored": False,
        "evidence_scope": "EDUCATIONAL_MESSAGEIX_GAMS_NOT_AR6",
    }
    manifest_path = run_dir / "manifest.private.json"

    def save():
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    save()
    try:
        selected = []
        for stage, filename, obj_expr in NOTEBOOKS:
            original, source = fetch_notebook(filename, run_dir / "source" / filename)
            partial = model_cells_until_objective(original, obj_expr)
            selected.append((stage, partial))
            manifest["notebooks"].append({
                "stage": stage, **source, "model_cells": len(partial["cells"])
            })
        save()
        if download_only:
            manifest["status"] = "UPSTREAM_NOTEBOOKS_DOWNLOADED_NOT_EXECUTED"
            save()
            return manifest, manifest_path

        import nbformat
        from nbclient import NotebookClient

        kernel_path = setup_private_kernel(run_dir)
        ixmp_path = setup_private_ixmp(run_dir)
        env = {
            "IXMP_DATA": ixmp_path,
            "JUPYTER_PATH": str(kernel_path) + os.pathsep + os.environ.get("JUPYTER_PATH", ""),
            "MPLBACKEND": "Agg",
        }
        with temporary_environment(env):
            for stage, original in selected:
                notebook = nbformat.from_dict(original)
                notebook["cells"].append(nbformat.v4.new_code_cell("mp.close_db()"))
                client = NotebookClient(
                    notebook, kernel_name="rp-messageix",
                    resources={"metadata": {"path": str(run_dir / "source")}},
                    timeout=timeout, allow_errors=False, store_widget_state=False
                )
                try:
                    client.execute()
                finally:
                    nbformat.write(notebook, run_dir / f"{stage}.executed.private.ipynb")
            manifest["solved_scenarios"] = read_gams_solutions()
        manifest["status"] = "ACTUAL_MESSAGEIX_GAMS_SOLVED"
        manifest["environment"]["actual_solve_performed"] = True
        save()
        return manifest, manifest_path
    except Exception as exc:
        manifest["status"] = "FAILED_NOT_VERIFIED"
        manifest["error_type"] = type(exc).__name__
        save()
        raise


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="Official Westeros local execution")
    parser.add_argument("--output", default="results/messageix_private")
    parser.add_argument("--download-only", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args(argv)
    if args.preflight:
        print(json.dumps(preflight(), indent=2, sort_keys=True))
    else:
        manifest, path = run(args.output, download_only=args.download_only)
        print("Local-only manifest:", path)
        print("Status:", manifest["status"])


if __name__ == "__main__":
    main()
