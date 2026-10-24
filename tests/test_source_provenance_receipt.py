"""No publisher authentication from user-supplied file names, SHA or URL."""
import json
from pathlib import Path

import pytest

from residual_pathways.source_provenance_receipt import (
    source_receipt, write, OriginError, EXPECTED, WORLD, METADATA,
)


def test_exact_file_names_and_local_hashes_are_not_publisher_proof(tmp_path,monkeypatch):
    world=tmp_path/WORLD
    meta=tmp_path/METADATA
    world.write_bytes(b"source World")
    meta.write_bytes(b"metadata")
    import residual_pathways.source_provenance_receipt as mod
    monkeypatch.setattr(mod,"EXPECTED",{
        WORLD:mod.digest(world), METADATA:mod.digest(meta)
    })
    x=source_receipt(world,meta)
    assert x["publisher_origin_authentication"]=="NOT_ESTABLISHED"
    assert x["file_download_receipt_status"]=="NOT_PROVIDED"
    assert x["source_hashes"][WORLD]["bytes"]==12


def test_receipt_redacts_url_query_and_private_notes(tmp_path,monkeypatch):
    root=tmp_path/"data/ar6-private";root.mkdir(parents=True)
    world=root/WORLD;meta=root/METADATA
    world.write_bytes(b"abc");meta.write_bytes(b"def")
    import residual_pathways.source_provenance_receipt as mod
    monkeypatch.setattr(mod,"EXPECTED",{WORLD:mod.digest(world),METADATA:mod.digest(meta)})
    private=root/"private_receipt.json"
    secret="secret-download-token-DO-NOT-PUBLISH"
    private.write_text(json.dumps({
        "download_origin_url":f"https://data.ene.iiasa.ac.at/ar6/safe/path?token={secret}",
        "observed_utc":"2026-10-24T13:00:00Z",
        "evidence_type":"HTTP_RESPONSE_SAVED",
        "author_notes":"PERSONAL_ACCOUNT_DO_NOT_PUBLISH",
    }))
    out=root/"manifest.json"
    data=write(world,meta,out,private)
    assert data["file_download_receipt_status"].startswith("AUTHOR_HELD_PRIVATE")
    assert data["publisher_origin_authentication"]=="NOT_ESTABLISHED"
    assert secret not in out.read_text()
    assert "PERSONAL_ACCOUNT_DO_NOT_PUBLISH" not in out.read_text()
    assert "2026-10-24T13:00" not in out.read_text()


def test_untrusted_host_is_rejected(tmp_path,monkeypatch):
    root=tmp_path/"ar6-private";root.mkdir()
    world=root/WORLD;meta=root/METADATA
    world.write_bytes(b"abc");meta.write_bytes(b"def")
    import residual_pathways.source_provenance_receipt as mod
    monkeypatch.setattr(mod,"EXPECTED",{WORLD:mod.digest(world),METADATA:mod.digest(meta)})
    private=root/"receipt.json"
    private.write_text(json.dumps({
        "download_origin_url":"https://iiasa.ac.at.attacker.net/path",
        "observed_utc":"2026-10-24",
        "evidence_type":"PORTAL_DOWNLOAD_LOG",
        "author_notes":"",
    }))
    with pytest.raises(OriginError):
        source_receipt(world,meta,private)
