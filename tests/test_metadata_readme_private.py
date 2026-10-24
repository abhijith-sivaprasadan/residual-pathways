"""Single-cell README audit never exposes workbook content via public stdout."""
from pathlib import Path
from openpyxl import Workbook
import pytest
from residual_pathways.metadata_readme_private import compare_readme,write,ReadmeAuditError


def fixture(path,value):
    book=Workbook()
    sheet=book.active
    sheet.title="README"
    sheet["A1"]="Source"
    sheet["A2"]=value
    book.save(path)


def test_private_readme_difference_and_path_guard(tmp_path):
    original=tmp_path/"official.xlsx"; earlier=tmp_path/"old.xlsx"
    fixture(original,"scientific note official")
    fixture(earlier,"scientific note earlier")
    report=compare_readme(original,earlier,pinned=False)
    assert report["number_of_changes"]==1
    assert report["changes"][0]["row"]==2
    assert report["changes"][0]["column"]==1
    assert "official" in report["changes"][0]["official_value"]["value"]
    assert report["workbook_authentication"]=="NOT_ESTABLISHED"
    with pytest.raises(ReadmeAuditError):
        write(original,earlier,tmp_path/"PUBLIC.json")


def test_pinned_original_hash_is_required(tmp_path):
    original=tmp_path/"official.xlsx"; earlier=tmp_path/"old.xlsx"
    fixture(original,"same")
    fixture(earlier,"same")
    with pytest.raises(ReadmeAuditError,match="bytes differ"):
        compare_readme(original,earlier)
