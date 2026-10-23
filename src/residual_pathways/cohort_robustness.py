"""Real-source completeness robustness by climate category, year and exact model label.

Counts are not emissions values. Exact model labels are NOT inferred to be
independent model families or probabilistic draws.
"""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import csv
import json
import math
from .stratify import metadata_rows, sha_file


class CohortError(ValueError):
    pass


def compute(input_csv, metadata, candidate_names, *,
            years=(2030,2050,2070,2100), metadata_sheet="meta_Ch3vetted_withclimate"):
    if not years or len(set(years)) != len(years) or not all(type(y) is int for y in years):
        raise CohortError("Prespecified unique integer years required")
    if not candidate_names or len(candidate_names) != len(set(candidate_names)):
        raise CohortError("Unique candidate variable names required")
    cohort={}
    for row in metadata_rows(metadata,sheet_name=metadata_sheet):
        if not {"Model","Scenario","Category"} <= row.keys():
            raise CohortError("Missing source-identification metadata")
        key=(row["Model"],row["Scenario"])
        if key in cohort or not row["Category"].startswith("C") or row["Category"][1:] not in "12345678":
            raise CohortError("Duplicate or out-of-cohort scenario metadata")
        cohort[key]=row["Category"]
    if not cohort:
        raise CohortError("Empty metadata cohort")
    present=defaultdict(set)
    reached=set()
    units=defaultdict(set)
    with Path(input_csv).open(newline="",encoding="utf-8-sig") as fh:
        reader=csv.DictReader(fh)
        h=reader.fieldnames or []
        year_fields={y:(str(y) if str(y) in h else f"X{y}") for y in years}
        if len(h)!=len(set(h)) or not {"Model","Scenario","Region","Variable","Unit",*year_fields.values()} <= set(h):
            raise CohortError("Source missing unique identity and requested year headers")
        for line,row in enumerate(reader,2):
            if None in row: raise CohortError(f"Invalid CSV structure line {line}")
            if row["Region"]!="World":continue
            key=(row["Model"],row["Scenario"])
            if key not in cohort:continue
            reached.add(key)
            name=row["Variable"]
            if name not in candidate_names:continue
            for year,field in year_fields.items():
                raw=(row.get(field) or "").strip()
                if not raw:continue
                try:v=float(raw)
                except ValueError as e:raise CohortError(f"Invalid source number on line {line}") from e
                if not math.isfinite(v):raise CohortError(f"Nonfinite source number line {line}")
                marker=(key,name,year)
                if marker in present:
                    raise CohortError("Duplicate model-scenario-variable-year source record")
                present[marker].add(row["Unit"])
                units[(name,year)].add(row["Unit"])
    def fraction(num,den):return num/den if den else None
    categories=sorted(set(cohort.values()))
    result=[]
    for cat in categories:
        keys=sorted(k for k in reached if cohort[k]==cat)
        unique_models=sorted(set(k[0] for k in keys))
        for year in years:
            for name in candidate_names:
                n=sum((k,name,year) in present for k in keys)
                per_model=[]
                for model in unique_models:
                    own=[k for k in keys if k[0]==model]
                    per_model.append(sum((k,name,year) in present for k in own)/len(own))
                model_balanced=sum(per_model)/len(per_model) if per_model else None
                result.append({"category":cat,"year":year,"variable":name,
                               "eligible_scenarios":len(keys),"unique_model_labels":len(unique_models),
                               "reporting_scenarios":n,"scenario_weighted_fraction":fraction(n,len(keys)),
                               "model_label_balanced_fraction":model_balanced,
                               "units_seen":sorted(units[(name,year)])})
    return {
        "schema_version":"reported-presence-robustness.v1",
        "source_sha256":sha_file(input_csv),"metadata_sha256":sha_file(metadata),
        "metadata_sheet":metadata_sheet,"region":"World","years":list(years),
        "eligible_metadata_scenarios":len(cohort),"matched_source_scenarios":len(reached),
        "variable_names":list(candidate_names),"records":result,
        "interpretation":"Availability of reported exact-name values. Not physical gross/negative emissions or CDR deployment.",
        "weighting_notice":"Model-label-balanced is equal average of within-exact-model-name reporting fractions; exact names may belong to same underlying family. No independent IAM family mapping or probabilities inferred.",
    }


def write_robustness(source, metadata, candidate_json, destination, *,
                     years=(2030,2050,2070,2100), sheet="meta_Ch3vetted_withclimate"):
    vars_=list(json.loads(Path(candidate_json).read_text()).values())
    result=compute(source,metadata,vars_,years=years,metadata_sheet=sheet)
    p=Path(destination)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result
