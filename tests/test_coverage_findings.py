"""Frozen AR6 coverage study reproducibility and claim-boundary tests."""
from hashlib import sha256
from pathlib import Path
import csv
import xml.etree.ElementTree as ET

import pytest

from residual_pathways.coverage_findings import (
    CANDIDATE_SHA, FindingsError, build, load_candidate, summaries, YEARS,
)

ROOT=Path(__file__).resolve().parents[1]
ARTIFACT=ROOT / "atlas/data/coverage_release.json"


def test_frozen_empirical_count_and_all_years():
    data, rows, digest = load_candidate(ARTIFACT)
    assert digest == CANDIDATE_SHA
    cohort, counts, categories = summaries(data,rows)
    assert cohort == 1202
    assert counts["Carbon Sequestration|Direct Air Capture"] == 422
    assert counts["Carbon Sequestration|Enhanced Weathering"] == 190
    assert counts["Carbon Sequestration|Land Use"] == 783
    assert counts["Emissions|CO2"] == cohort
    assert categories["C8"]["n"] == 29
    assert len(data["records"]) == 352
    for year in YEARS:
        assert sum(rows[c,year,"Carbon Sequestration|Direct Air Capture"]["reporting"]
                   for c in data["categories"]) == 422


def test_script_generates_deterministic_paper_csv_and_svg(tmp_path):
    one = build(ARTIFACT, tmp_path / "once")
    two = build(ARTIFACT, tmp_path / "twice")
    assert one.keys() == two.keys()
    for key in one:
        assert one[key].read_bytes() == two[key].read_bytes()
    text = one["results"].read_text()
    assert "422/1,202" in text
    assert "190/1,202" in text
    assert "NOT_ESTABLISHED" in text
    assert "REVIEW_PENDING" in text
    assert "not causal" in text.lower() or "not causal climate" in text.lower()
    for key in ("fig1","fig2","fig3"):
        root = ET.parse(one[key]).getroot()
        assert root.tag.endswith("svg")
    with one["table"].open(newline="",encoding="utf-8") as f:
        cells=list(csv.DictReader(f))
    assert len(cells) == 352
    assert {row["year"] for row in cells} == {"2030","2050","2070","2100"}


def test_tampered_source_rejected(tmp_path):
    modified=tmp_path/"invalid.json"
    original=ARTIFACT.read_bytes()
    modified.write_bytes(original.replace(b"REVIEW_PENDING",b"REVIEW_APPROVED"))
    with pytest.raises(FindingsError,match="pinned"):
        load_candidate(modified)
