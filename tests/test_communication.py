from pathlib import Path
from residual_pathways.communication import write_communication

ROOT=Path(__file__).resolve().parents[1]

def test_figure_brief_provenance_and_no_gross_claim(tmp_path):
    m=write_communication(ROOT,tmp_path)
    svg=(tmp_path/"reporting_funnel.svg").read_text()
    note=(tmp_path/"policy_brief.md").read_text()
    assert "C8" in svg and "<svg" in svg
    assert "not I3 accounting" in svg
    assert "261" in note and "1,202" in note
    assert "not estimate a technology" in note
    assert m["scientific_claims"]=="COVERAGE_AND_METRIC_COMPARISON_ONLY_NO_I3"
    assert len(m["policy_brief_sha256"])==64
