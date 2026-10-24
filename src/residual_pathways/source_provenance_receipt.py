"""Local-only AR6 publisher acquisition evidence inventory.

DOES NOT authenticate downloads merely because bytes have official names,
a user-entered URL or a SHA matching an independent redistribution.
Never include delivery URLs, session tokens, email addresses or headers in
public output. Author-held receipts remain in ignored data/ar6-private/.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import urlsplit

WORLD = "AR6_Scenarios_Database_World_v1.1.csv"
METADATA = "AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx"
EXPECTED = {
    WORLD:"4cf39b6b0d968e25ed389318acb1674f92146f977e9db4bfb7970f048ff73977",
    METADATA:"fd1bc32db8463769e18f0560ced603a49598c12e1abfa06787ff763c55f06716",
}
DOI = "https://doi.org/10.5281/zenodo.7197970"
EXPLORER = "https://data.ene.iiasa.ac.at/ar6/#/downloads"


class OriginError(ValueError):
    pass


def digest(path):
    h=sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda:file.read(4*1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def source_receipt(world, metadata, receipt=None):
    sources={}
    for expected_path,path in ((WORLD,Path(world)),(METADATA,Path(metadata))):
        if not path.exists() or path.name != expected_path:
            raise OriginError("Expected locally held exact original-named source file")
        actual=digest(path)
        if actual!=EXPECTED[expected_path]:
            raise OriginError("AR6 source bytes differ from pinned local source fingerprint")
        sources[expected_path]={"sha256":actual,"bytes":path.stat().st_size}
    origin={
        "schema":"ar6-provenance-evidence-inventory.v1",
        "official_record":DOI,
        "official_explorer":EXPLORER,
        "source_hashes":sources,
        "public_record_verification":"IIASA_SITE_AND_ZENODO_DESCRIBE_VERSION_AND_FILE_NAMES",
        "bytes_verification":"LOCAL_HASHES_MATCH_PINNED_AUTHOR_REPORT_AND_PRIOR_WORLD_REDISTRIBUTION",
        "publisher_checksum_independent":"NOT_AVAILABLE_IN_CURRENT_EVIDENCE",
        "publisher_origin_authentication":"NOT_ESTABLISHED",
        "file_download_receipt_status":"NOT_PROVIDED",
        "evidence_basis":"LOCAL_FILE_HASHES_AND_PUBLIC_SOURCE_CATALOG",
        "limitations":[
            "Public documentation and matching source bytes do not authenticate one user's download transaction",
            "Any acquisition receipt is private; email links, HTTP query tokens and account identifiers must not be published",
            "This cannot upgrade REVIEW_PENDING, I0, I1, I2 or I3 on model-specific physical carbon accounting",
        ],
    }
    if receipt is not None:
        rp=Path(receipt)
        if not rp.is_file() or "ar6-private" not in rp.resolve().parts or rp.stat().st_size>20000:
            raise OriginError("Only small private receipt JSON inside data/ar6-private allowed")
        ob=json.loads(rp.read_text(encoding="utf-8"))
        if (not isinstance(ob,dict) or
                set(ob) != {"download_origin_url","observed_utc","evidence_type","author_notes"}):
            raise OriginError("Receipt must contain the four documented local-only fields")
        url=ob["download_origin_url"]
        if not isinstance(url,str) or len(url)>4096:
            raise OriginError("Receipt URL invalid")
        parsed=urlsplit(url)
        host=(parsed.hostname or "").lower()
        if parsed.scheme!="https" or not (host=="iiasa.ac.at" or host.endswith(".iiasa.ac.at")):
            raise OriginError("Claimed download origin is not on an IIASA HTTPS host")
        if not isinstance(ob["observed_utc"],str) or not ob["observed_utc"].strip():
            raise OriginError("Receipt observation timestamp missing")
        if ob["evidence_type"] not in ("BROWSER_DOWNLOAD_HISTORY","IIASA_EMAIL_LINK",
                                       "HTTP_RESPONSE_SAVED","PORTAL_DOWNLOAD_LOG"):
            raise OriginError("Unrecognized receipt evidence kind")
        origin["file_download_receipt_status"]="AUTHOR_HELD_PRIVATE_INDICATOR_PROVIDED_NOT_INDEPENDENTLY_AUTHENTICATED"
        origin["evidence_basis"]="LOCAL_HASHES_PUBLIC_CATALOG_AND_AUTHOR_HELD_PRIVATE_RECEIPT"
        origin["receipt_kind"]=ob["evidence_type"]
        origin["receipt_host"]=host
        # Important: NEVER copy the original signed URL, notes, account, or
        # timestamp into public output, even though the input is private.
    return origin


def write(world,metadata,output,receipt=None):
    data=source_receipt(world,metadata,receipt=receipt)
    path=Path(output)
    if "ar6-private" not in path.resolve().parts:
        raise OriginError("Provenance output must stay within ignored ar6-private")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    return data


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--world",type=Path,default=Path("data/ar6-private/AR6_Scenarios_Database_World_v1.1.csv"))
    p.add_argument("--metadata",type=Path,default=Path("data/ar6-private/AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx"))
    p.add_argument("--receipt",type=Path)
    p.add_argument("--output",type=Path,default=Path("data/ar6-private/acquisition_evidence_inventory.json"))
    args=p.parse_args()
    result=write(args.world,args.metadata,args.output,args.receipt)
    print("Publisher authentication:",result["publisher_origin_authentication"])
    print("Private receipt evidence:",result["file_download_receipt_status"])
    print("Only safe site name/hashes retained. Not a publisher attestation.")


if __name__=="__main__":
    main()
