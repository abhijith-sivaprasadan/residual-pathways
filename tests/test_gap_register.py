import csv
from pathlib import Path

def test_gap_hypotheses_are_evidence_delimited():
    p=Path(__file__).resolve().parents[1]/"data/derived/innovation_gap_register.csv"
    with p.open(newline="",encoding="utf-8") as f:
        records=list(csv.DictReader(f))
    assert len(records)>=10
    assert len({r["id"] for r in records})==len(records)
    assert all(r["source_context_url"].startswith("https://www.ipcc.ch/") for r in records)
    assert all(r["evidence_status"]=="REFERENCE_TOPIC_ONLY_REQUIRES_CASE_REVIEW" for r in records)
    assert all(r["causal_status"]=="UNTESTED_HYPOTHESIS" for r in records)
    assert all(r["controlled_test_hypothesis"] and r["scientific_caution"] for r in records)
