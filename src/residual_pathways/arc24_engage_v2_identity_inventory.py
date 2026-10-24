"""Inventory original ENGAGE v2.0 World identities without assuming an AR6 alias.

Input: author-held 94.56 MB original-named ENGAGE r2.0 World CSV and private
ARC24 selected packet, both kept in data/ar6-private. Original unmodified
bytes are pinned against the user's observed SHA256; that is NOT IIASA
publisher authentication.

Public output: aggregate counts/status only. Private candidate output:
at most 12 lexical *leads* (model/scenario identifiers but NO observations).
Lexical similarity must never be promoted into source equivalence, I0 or I3.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from difflib import SequenceMatcher
from hashlib import sha256
import json
from pathlib import Path
import re

from .arc24_engage_v2_probe import (
    MODEL, SCENARIO, CASE_ID, WORLD_SHA, V2_FILENAME, _digest
)

USER_OBSERVED_ENGAGE_SHA = "c92b8944b1d2a71eed7a07702c42e48f6f3e3eee59a4404d145d0babc61315da"

class EngageIdentityError(ValueError):
    pass

def normalized(value):
    return re.sub(r"[^a-z0-9]","",value.casefold())

def scan_pairs(path):
    """One source scan; collapse multiple variables per World pair by exact identity."""
    found=set()
    total_rows=0
    world_rows=0
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        cols=reader.fieldnames or []
        if not {"Model","Scenario","Region","Variable","Unit"}.issubset(cols) or len(cols)!=len(set(cols)):
            raise EngageIdentityError("ENGAGE v2.0 original World IAMC columns unexpected")
        for n,row in enumerate(reader,2):
            if None in row or any(v is None for v in row.values()):
                raise EngageIdentityError(f"Malformed ENGAGE CSV source line {n}")
            total_rows+=1
            if row["Region"]=="World":
                world_rows+=1
                if not row["Model"] or not row["Scenario"]:
                    raise EngageIdentityError("Blank Model/Scenario in World record")
                found.add((row["Model"],row["Scenario"]))
    return found,total_rows,world_rows

def analyze(pairs, *, target_model=MODEL,target_scenario=SCENARIO):
    pairs=set(pairs)
    nmodel=normalized(target_model); nscenario=normalized(target_scenario)
    all_model={m for m,s in pairs}
    exact_pair=(target_model,target_scenario) in pairs
    same_scenario={m for m,s in pairs if s==target_scenario}
    same_model={s for m,s in pairs if m==target_model}
    casefold_scenarios={(m,s) for m,s in pairs if s.casefold()==target_scenario.casefold()}
    norm_scenarios={(m,s) for m,s in pairs if normalized(s)==nscenario}
    norm_models={m for m in all_model if normalized(m)==nmodel}
    poles_models={m for m in all_model if "poles" in m.casefold()}
    poes={(m,s) for m,s in pairs if m in poles_models}
    target_prefix = target_scenario.rsplit("_",1)[0].casefold()
    prefix_matches={(m,s) for m,s in poes if s.casefold().startswith(target_prefix)}
    lexical=[]
    for m,s in poes:
        score=SequenceMatcher(None,s.casefold(),target_scenario.casefold()).ratio()
        if score >= .75:
            lexical.append((round(score,4),m,s))
    lexical.sort(key=lambda x:(-x[0],x[1],x[2]))
    private=[
        {"model":m,"scenario":s,"lexical_similarity_not_identity":score}
        for score,m,s in lexical[:12]
    ]
    status = ("EXACT_MATCH_FOUND" if exact_pair
              else "EXACT_SCENARIO_FOUND_DIFFERENT_OR_UNKNOWN_MODEL" if same_scenario
              else "EXACT_MODEL_FOUND_SCENARIO_ABSENT" if target_model in all_model
              else "NEITHER_EXACT_NAME_FOUND")
    public={
        "schema":"residualpathways.engage_v2_identity_inventory_public.v1",
        "status":status,
        "exact_model_scenario_world_pair_found":exact_pair,
        "distinct_world_model_scenario_pairs":len(pairs),
        "distinct_world_model_labels":len(all_model),
        "exact_scenario_pairs_across_all_model_labels":len(same_scenario),
        "exact_model_label_found":target_model in all_model,
        "exact_model_label_world_scenario_pairs":len(same_model),
        "case_insensitive_exact_scenario_pairs":len(casefold_scenarios),
        "normalized_punctuation_insensitive_scenario_pairs":len(norm_scenarios),
        "exact_model_case_punctuation_normalized":len(norm_models),
        "poles_containing_model_label_count":len(poles_models),
        "poles_family_candidate_pairs":len(poes),
        "poles_scenario_prefix_matches":len(prefix_matches),
        "poles_scenario_lexical_similarity_at_least_0_75":len(lexical),
        "private_lexical_leads_retained":len(private),
        "identity_review":"ONLY_LEXICAL_CANDIDATES_NO_ALIAS_ESTABLISHED",
        "ar6_source_processing_lineage":"NOT_ESTABLISHED",
        "science_review_state":"REVIEW_PENDING",
        "verified_i3":0,
        "limitations":[
            "Source title and author-observed SHA do not authenticate acquisition from IIASA.",
            "The counts describe names only, not numerical equivalence, model run version or CDR physics.",
            "Prefix and lexical similarity do not establish same scenario; original developer mapping needed.",
            "Private lexical leads, source scenario names and emissions values are never in the public report.",
        ],
    }
    return public,private

def execute(engage,packet,public_path,private_path,*,expected_engage_sha=USER_OBSERVED_ENGAGE_SHA):
    engage,packet,public_path,private_path=map(lambda v:Path(v).resolve(),(engage,packet,public_path,private_path))
    if (not engage.is_file() or not packet.is_file()
            or "ar6-private" not in engage.parts or "ar6-private" not in packet.parts
            or "ar6-private" not in private_path.parts
            or "ar6-private" in public_path.parts
            or len({engage,packet,public_path,private_path})!=4
            or engage.name!=V2_FILENAME):
        raise EngageIdentityError("ENGAGE CSV, canonical packet and private leads must stay in ar6-private")
    sha=_digest(engage)
    if sha!=expected_engage_sha:
        raise EngageIdentityError("ENGAGE World bytes differ from the registered author-observed SHA")
    pack=json.loads(packet.read_text(encoding="utf-8"))
    cases=pack.get("cases")
    if (pack.get("schema")!="residualpathways.ar6_canonical_selected24.private.v1"
            or pack.get("handling")!="LOCAL_ONLY_DO_NOT_PUBLISH"
            or pack.get("source_sha256")!=WORLD_SHA
            or not isinstance(cases,list) or len(cases)!=24):
        raise EngageIdentityError("Original AR6 private canonical packet invalid")
    actual=[x for x in cases if x.get("case_id")==CASE_ID]
    if len(actual)!=1 or (actual[0].get("model"),actual[0].get("scenario")) != (MODEL,SCENARIO):
        raise EngageIdentityError("ARC24-06 selected original source identity changed")
    pairs,total_rows,world_rows=scan_pairs(engage)
    pub,leads=analyze(pairs)
    pub.update({
        "case_id":CASE_ID,
        "source_sha256":sha,
        "source_bytes":engage.stat().st_size,
        "source_rows_scanned":total_rows,
        "world_rows_scanned":world_rows,
        "source_origin_authentication":"NOT_ESTABLISHED",
    })
    private={
        "schema":"residualpathways.engage_v2_lexical_leads.private.v1",
        "handling":"LOCAL_ONLY_DO_NOT_PUBLISH",
        "candidate_count":len(leads),
        "candidate_scenario_names_not_validated_as_aliases":leads,
        "source_sha256":sha,
        "exact_ar6_case_id":CASE_ID,
    }
    public_path.parent.mkdir(parents=True,exist_ok=True)
    private_path.parent.mkdir(parents=True,exist_ok=True)
    public_path.write_text(json.dumps(pub,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    private_path.write_text(json.dumps(private,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return pub

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--engage",type=Path,default=Path("data/ar6-private/ENGAGE_scenario_data_world_r2.0.csv"))
    p.add_argument("--packet",type=Path,default=Path("data/ar6-private/canonical_selected24_packet.json"))
    p.add_argument("--public-output",type=Path,default=Path("results/ar6-canonical-gate/engage_v2_identity_inventory_public.json"))
    p.add_argument("--private-leads",type=Path,default=Path("data/ar6-private/engage_v2_candidate_identities_private.json"))
    a=p.parse_args()
    report=execute(a.engage,a.packet,a.public_output,a.private_leads)
    for key in ("status","distinct_world_model_scenario_pairs","exact_model_label_found",
                "exact_scenario_pairs_across_all_model_labels",
                "poles_containing_model_label_count","poles_family_candidate_pairs",
                "poles_scenario_prefix_matches",
                "poles_scenario_lexical_similarity_at_least_0_75"):
        print(f"{key}: {report[key]}")
    print("Candidate identity spellings in private file only:",a.private_leads)
    print("NO SCENARIO ALIAS OR PHYSICAL I3 ESTABLISHED")

if __name__=="__main__":
    main()
