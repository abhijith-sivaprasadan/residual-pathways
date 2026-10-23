"""Gas-specific reporting and N2O-only GWP convention sensitivity.

One observed N2O raw-gas mass is evaluated using two documented GWP100
assessment versions. This is NOT an aggregate GHG result or methane estimate.
"""
from __future__ import annotations
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from .stratify import metadata_rows, sha_file
from .gwp import GWP100


class GasAuditError(ValueError):
    pass


def nonco2_audit(source, metadata, *, sheet="meta_Ch3vetted_withclimate",year=2050):
    cohort={}
    for rec in metadata_rows(metadata,sheet_name=sheet):
        if not {"Model","Scenario","Category"} <= rec.keys():
            raise GasAuditError("Missing model/scenario/category metadata")
        key=(rec["Model"],rec["Scenario"])
        if key in cohort:raise GasAuditError("Duplicate metadata identity")
        cohort[key]=rec["Category"]
    reported=defaultdict(dict)
    matched=set()
    with Path(source).open(newline="",encoding="utf-8-sig") as fh:
        reader=csv.DictReader(fh)
        headers=reader.fieldnames or []
        y=str(year) if str(year) in headers else "X"+str(year)
        if len(headers)!=len(set(headers)) or not {"Model","Scenario","Region","Variable","Unit",y} <= set(headers):
            raise GasAuditError("Missing/duplicated IAMC fields")
        for line,row in enumerate(reader,2):
            if None in row:raise GasAuditError("Source row structural error")
            if row["Region"]!="World":continue
            key=(row["Model"],row["Scenario"])
            if key not in cohort:continue
            matched.add(key)
            gas=row["Variable"]
            if gas not in ("Emissions|CO2","Emissions|CH4","Emissions|N2O","Emissions|Kyoto Gases"):
                continue
            raw=(row[y] or "").strip()
            if not raw:continue
            try:val=float(raw)
            except ValueError as e:raise GasAuditError(f"Nonnumeric gas report line {line}") from e
            if not math.isfinite(val):raise GasAuditError(f"Nonfinite gas report line {line}")
            if gas in reported[key]:raise GasAuditError("Duplicate gas report")
            reported[key][gas]={"value":val,"unit":row["Unit"]}
    result=[]
    for cat in sorted(set(cohort.values())):
        ids=[k for k in matched if cohort[k]==cat]
        gcount={name:sum(name in reported[k] for k in ids)
            for name in ("Emissions|CO2","Emissions|CH4","Emissions|N2O","Emissions|Kyoto Gases")}
        nox=[reported[k]["Emissions|N2O"]["value"] for k in ids
             if "Emissions|N2O" in reported[k] and reported[k]["Emissions|N2O"]["unit"]=="kt N2O/yr"]
        mismatched=[k for k in ids if "Emissions|N2O" in reported[k]
                    and reported[k]["Emissions|N2O"]["unit"]!="kt N2O/yr"]
        if mismatched:raise GasAuditError("Unexpected N2O source unit; explicit handling required")
        original=GWP100["IPCC_AR6_2021_ORIGINAL"]["N2O"]
        corrected=GWP100["IPCC_AR6_2025_ERRATA"]["N2O"]
        # avg mass per reporting scenario; not sum over non-independent scenarios.
        mean_kt=sum(nox)/len(nox) if nox else None
        result.append({
            "category":cat,"eligible_source_scenarios":len(ids),
            "reporting_counts":gcount,"n2o_reported_kt_count":len(nox),
            "n2o_average_kt_per_reporting_scenario":mean_kt,
            "n2o_mean_mtco2e_per_reporting_scenario_original_2021":mean_kt/1000*original if mean_kt is not None else None,
            "n2o_mean_mtco2e_per_reporting_scenario_corrected_2025":mean_kt/1000*corrected if mean_kt is not None else None,
            "n2o_metric_change_mtco2e":mean_kt/1000*(corrected-original) if mean_kt is not None else None,
            "n2o_negative_source_values":sum(x<0 for x in nox),
            "methane_co2e":"BLOCKED_UNRESOLVED_FOSSIL_VS_NONFOSSIL_SOURCE_SPLIT",
        })
    return {
        "schema_version":"nonco2-coverage-metric-pilot.v1","source_sha256":sha_file(source),
        "metadata_sha256":sha_file(metadata),"metadata_sheet":sheet,"year":year,
        "metric":"GWP100","source_assessments":list(GWP100),
        "data_type":"ACTUAL_TEACHING_SOURCE_DERIVED_CATEGORY_AGGREGATES",
        "report":"N2O-only per-reporting-scenario mean. Not a population total or climate forecast.",
        "no_aggregate_ghg":"CH4 origin unknown; never double-convert existing CO2e or infer missing gases.",
        "classes":result}


def run_nonco2(source,metadata,destination,*,year=2050,sheet="meta_Ch3vetted_withclimate"):
    r=nonco2_audit(source,metadata,sheet=sheet,year=year)
    p=Path(destination);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    return r
