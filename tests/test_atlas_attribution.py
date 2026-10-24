"""Public Atlas must retain source attribution and scientific limits.

This checks that upstream credit is shipped with the website, even when the
optional empirical four-year candidate is absent.
"""
from pathlib import Path

ATLAS = Path(__file__).resolve().parents[1] / "atlas"

def test_source_license_and_dataset_citation_visible_in_html():
    html = (ATLAS / "index.html").read_text(encoding="utf-8")
    assert "https://doi.org/10.5281/zenodo.7197970" in html
    assert "https://data.ene.iiasa.ac.at/ar6/static/License/Legal.html" in html
    assert "Original scenario data copyright" in html
    assert "source has been transformed into category-level counts and fractions" in html
    assert "not endorsed by IIASA or IPCC" in html

def test_public_source_notice_does_not_upgrade_i3_or_conflate_i0():
    html = (ATLAS / "index.html").read_text(encoding="utf-8")
    js = (ATLAS / "coverage-release.js").read_text(encoding="utf-8")
    assert 'id="coverage-release-controls" hidden' in html
    assert 'science_review_state !== "REVIEW_PENDING"' in js
    assert 'data.i3_verified !== 0' in js
    assert 'data.physical_accounting !== "NOT_ESTABLISHED"' in js
    assert "model-family weighted" in js
