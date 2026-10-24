"""Local-only workbook semantic difference classifier for AR6 v1.1 metadata.

Why: coordinate differences can be caused entirely by row/column reordering,
even if source-joined Model+Scenario values agree. Non-identity sheets must be
compared by normalized row inventories to classify the remaining differences.

NO original cell values or scenario identities leave this local diagnostic.
Passing does not authenticate the IIASA publisher or its download route.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from .metadata_concordance import _load, _records, normalized
from .stratify import sha_file

OFFICIAL_SHA = "fd1bc32db8463769e18f0560ced603a49598c12e1abfa06787ff763c55f06716"
EARLIER_SHA = "7d22453bdda52e95cea4df46d362018951dd7114e62f01f5bcea65d6e24a7790"


class SheetReviewError(ValueError):
    pass


def header(cells):
    cols = {c: json.dumps(v, ensure_ascii=False) for (r,c),v in cells.items() if r==1}
    if len(set(cols.values())) != len(cols):
        return None
    return cols


def row_signatures(cells):
    """Multiset insensitive to row order; keyed by header names when possible."""
    labels=header(cells)
    entries={}
    for (r,c),v in cells.items():
        if r==1: continue
        label=labels.get(c) if labels else str(c)
        if label is None:
            raise SheetReviewError("Data column without a nonblank header")
        entries.setdefault(r,[]).append((label,json.dumps(v,ensure_ascii=False)))
    return Counter(json.dumps(sorted(row),ensure_ascii=False) for row in entries.values())


def identity_positions(cells):
    heads={(tuple(v)): col for (row,col),v in cells.items() if row==1}
    mc=heads.get(("text","Model"));sc=heads.get(("text","Scenario"))
    if mc is None or sc is None: return None
    rows={}
    for (r,c),v in cells.items():
        if r>1 and c==mc:
            rows.setdefault(r,{})["model"]=tuple(v)
        if r>1 and c==sc:
            rows.setdefault(r,{})["scenario"]=tuple(v)
    positions={}
    for row,values in rows.items():
        if set(values)=={"model","scenario"}:
            key=(values["model"],values["scenario"])
            if key in positions:
                raise SheetReviewError("Duplicate identity row")
            positions[key]=row
    return positions


def review(official, earlier, *, required_hashes=True):
    official=Path(official); earlier=Path(earlier)
    sh_a=sha_file(official);sh_b=sha_file(earlier)
    if required_hashes and (sh_a != OFFICIAL_SHA or sh_b != EARLIER_SHA):
        raise SheetReviewError("Workbook hashes do not match registered local inputs")
    a,b=_load(official),_load(earlier)
    sheets=[]
    for name in sorted(set(a)|set(b)):
        if name not in a or name not in b:
            sheets.append({"sheet":name,"status":"SHEET_ONLY_ON_ONE_SIDE",
                           "present_in_both":False})
            continue
        ac,bc=a[name],b[name]
        ha,hb=header(ac),header(bc)
        header_equal=(ha is not None and hb is not None and
                      set(ha.values())==set(hb.values()))
        canonical_a=row_signatures(ac)
        canonical_b=row_signatures(bc)
        row_eq=canonical_a==canonical_b
        positional=sum(ac.get(k)!=bc.get(k) for k in set(ac)|set(bc))
        arec,brec=_records(ac),_records(bc)
        joined=(arec is not None and brec is not None)
        identical_join=False
        moved_identity=0
        if joined:
            identical_join=arec==brec
            pa,pb=identity_positions(ac),identity_positions(bc)
            if pa is not None and pb is not None:
                moved_identity=sum(pa[k]!=pb[k] for k in set(pa)&set(pb))
        if positional==0:
            status="IDENTICAL_NORMALIZED_CELL_COORDINATES"
        elif joined and identical_join:
            status="IDENTITY_JOIN_IDENTICAL_POSITIONAL_DIFFERENCES_ONLY"
        elif row_eq and header_equal:
            status="SAME_NORMALIZED_ROWS_POSITIONAL_DIFFERENCES_ONLY"
        else:
            status="NON_IDENTITY_SHEET_CONTENT_DIFFERENCE_UNRESOLVED" if not joined else "IDENTITY_JOIN_CONTENT_DIFFERENCE"
        missing_rows=sum((canonical_a-canonical_b).values())
        extra_rows=sum((canonical_b-canonical_a).values())
        sheets.append({
            "sheet":name,"status":status,"present_in_both":True,
            "normalized_positional_differences":positional,
            "header_label_set_equal":header_equal,
            "normalized_header_positions_equal":ha==hb if ha is not None and hb is not None else None,
            "normalized_row_multiset_equal":row_eq,
            "row_signatures_only_official":missing_rows,
            "row_signatures_only_earlier":extra_rows,
            "identity_join_available":joined,
            "identity_join_identical":identical_join if joined else None,
            "identity_rows_with_different_row_index":moved_identity if joined else None,
        })
    return {
        "schema":"ar6-metadata-sheet-review-public.v1",
        "status":"LOCAL_CONTENT_REVIEW_NOT_PUBLISHER_AUTHENTICATION",
        "official_sha256":sh_a,"earlier_sha256":sh_b,
        "sheets":sheets,
        "disclosure":"Only sheet-level aggregate counts and statuses. No Model/Scenario, cell values, formulas or per-row hashes.",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--official",type=Path,required=True)
    p.add_argument("--earlier",type=Path,required=True)
    p.add_argument("--output",type=Path,default=Path("results/ar6-canonical-gate/metadata_sheet_review_local.json"))
    p.add_argument("--synthetic-test-only-skip-hashes",action="store_true")
    args=p.parse_args()
    result=review(args.official,args.earlier,
                  required_hashes=not args.synthetic_test_only_skip_hashes)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    for sheet in result["sheets"]:
        print(sheet["sheet"],sheet["status"],
              "positional_differences",sheet.get("normalized_positional_differences","NA"),
              "changed_normalized_rows",sheet.get("row_signatures_only_official","NA"))
    print("NO PUBLISHER AUTHENTICATION INFERRED")


if __name__=="__main__":
    main()
