"""Non-invasive MESSAGEix / GAMS readiness check; NEVER pretends to solve a model."""
from __future__ import annotations
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import json
import shutil


def inspect_environment():
    gams_available = shutil.which("gams") is not None
    try:
        msg_version = version("message_ix")
    except PackageNotFoundError:
        msg_version = None
    return {
        "schema_version": "gams-preflight.v1",
        "gams_executable_discovered": gams_available,
        "message_ix_installed_version": msg_version,
        "gams_license_checked": False,
        "westeros_solved": False,
        "scientific_status": "NOT_A_MESSAGEIX_EXPERIMENT",
        "blocking_steps": [
            "Confirm operational GAMS executable plus license appropriate for Westeros",
            "Install and configure current message_ix and ixmp",
            "Run official Westeros baseline notebook with retained solver logs",
            "Verify reproducibility, results, dimensions and version-pinned model inputs",
            "Only then construct and execute controlled intervention cases",
        ],
        "reference": "https://docs.messageix.org/en/stable/tutorials.html",
        "security": "No GAMS license keys, environment secrets, file paths or platform account metadata are logged",
    }


def write_preflight(destination):
    result = inspect_environment()
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
