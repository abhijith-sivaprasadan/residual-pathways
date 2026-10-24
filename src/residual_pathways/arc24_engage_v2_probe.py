"""ARC24-06 source-locked AR6 World vs optional original ENGAGE v2.0 data.

Source provenance research ONLY. Read the user's separately downloaded original
ENGAGE Global Scenarios v2.0 World CSV when available. Compare exact source
model + scenario + variable + World region + unit + year observations. Do not
assume ENGAGE v2.0 equals IPCC AR6 v1.1 or that reporting is physical CDR.

Also test the *explicitly authored ENGAGE notebook* derived Other formula
as a separate postprocessing HYPOTHESIS. This cannot prove the AR6 Other
column's processing lineage or an independent source of gross emissions.

Never export numeric source emissions, model/scenario identifiers or signed
delivery URLs; all raw-source input stays within gitignored ar6-private.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import csv
import json
from pathlib import Path

WORLD_SHA = "4cf39b6b0d968e25ed389318acb1674f92146f977e9db4bfb7970f048ff73977"
V2_FILENAME = "ENGAGE_scenario_data_world_r2.0.csv"
CASE_ID = "ARC24-06"
MODEL = "POLES ENGAGE"
SCENARIO = "EN_NPi2020_400f"
YEARS = (2030,2040,2050,2060,2070)
UNIT = "Mt CO2/yr"
TOTAL = "Emissions|CO2"
AFOLU = "Emissions|CO2|AFOLU"
DEMAND = "Emissions|CO2|Energy|Demand"
SUPPLY = "Emissions|CO2|Energy|Supply"
INDUSTRY = "Emissions|CO2|Industrial Processes"
OTHER = "Emissions|CO2|Other"
COMPONENTS = (TOTAL,AFOLU,DEMAND,SUPPLY,INDUSTRY)
FOCUS = (
    TOTAL, AFOLU, "Emissions|CO2|Energy and Industrial Processes",
    DEMAND, SUPPLY, INDUSTRY, OTHER,
    "Carbon Sequestration|CCS|Fossil", "Carbon Sequestration|CCS|Biomass",
    "Carbon Sequestration|Land Use", "Carbon Sequestration|Direct Air Capture",
)
BANDS = ((Decimal("0.001"),"BELOW_0_001_PERCENT"),
         (Decimal("0.1"),"BELOW_0_1_PERCENT"),
         (Decimal("1"),"BELOW_1_PERCENT"),
         (Decimal("10"),"BELOW_10_PERCENT"))


class EngageSourceError(ValueError):
    pass


def _digest(path):
    h=sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def _decimal(s):
    if s is None or not str(s).strip():
        return None
    try:
        n=Decimal(str(s).strip())
    except InvalidOperation as exc:
        raise EngageSourceError("Source numeric observation malformed") from exc
    if not n.is_finite():
        raise EngageSourceError("Non-finite numeric observation")
    return n


def _data(path):
    """Return exact source units and years for precisely one model/scenario."""
    observations={}
    with path.open(newline="",encoding="utf-8-sig") as stream:
        reader=csv.DictReader(stream)
        columns=reader.fieldnames or []
        if len(set(columns))!=len(columns) or not {
                "Model","Scenario","Region","Variable","Unit"}.issubset(columns):
            raise EngageSourceError("Malformed original IAMC World CSV")
        cols={y: next((v for v in (str(y),f"X{y}") if v in columns),None) for y in YEARS}
        if not cols[2050]:
            raise EngageSourceError("Mandatory 2050 source column is absent")
        matching_rows=0
        for line,row in enumerate(reader,2):
            if None in row or any(v is None for v in row.values()):
                raise EngageSourceError(f"Malformed source row {line}")
            if (row["Model"],row["Scenario"],row["Region"]) != (MODEL,SCENARIO,"World"):
                continue
            matching_rows+=1
            if row["Variable"] not in FOCUS:
                continue
            key=(row["Variable"],row["Unit"])
            if key in observations:
                raise EngageSourceError("Duplicate exact source variable and unit")
            observations[key]={year: (_decimal(row[col]) if col else None)
                               for year,col in cols.items()}
    return observations,matching_rows


def _status(a,b):
    """Compare original printed decimal values; never infer true quantization."""
    if a is None or b is None:
        return "MISSING_YEAR_VALUE"
    if a == b:
        return "EXACT_REPORTED_DECIMAL"
    scale=max(Decimal(1),abs(a),abs(b))
    percent=abs(a-b)/scale*Decimal(100)
    band=next((name for bound,name in BANDS if percent < bound),"AT_LEAST_10_PERCENT")
    return "NONZERO_REPORTED_DECIMAL__"+band


def _value(observations,name,year):
    """Require exactly one original compatible Mt CO2/yr series."""
    same=[(unit,values) for (variable,unit),values in observations.items()
          if variable==name]
    if not same:
        return None,"SOURCE_VARIABLE_ABSENT"
    candidates=[values for unit,values in same if unit==UNIT]
    if len(candidates)!=1:
        return None,"MISSING_OR_AMBIGUOUS_COMPATIBLE_UNIT"
    return candidates[0].get(year),"REPORTED_VALUE" if candidates[0].get(year) is not None else "MISSING_YEAR_VALUE"


def evaluate(world, engage, packet, *, expected_world_sha256=WORLD_SHA):
    world,engage,packet=(Path(v).resolve() for v in (world,engage,packet))
    if (not all(x.is_file() for x in (world,engage,packet))
            or any("ar6-private" not in x.parts for x in (world,engage,packet))
            or len({world,engage,packet})!=3 or engage.name!=V2_FILENAME):
        raise EngageSourceError("Expected private source World CSV, named ENGAGE v2.0 CSV, and private selected case packet")
    if _digest(world)!=expected_world_sha256:
        raise EngageSourceError("World v1.1 bytes differ from registered source pin")
    source_packet=json.loads(packet.read_text(encoding="utf-8"))
    cases=source_packet.get("cases")
    if (source_packet.get("schema")!="residualpathways.ar6_canonical_selected24.private.v1"
            or source_packet.get("handling")!="LOCAL_ONLY_DO_NOT_PUBLISH"
            or source_packet.get("source_sha256")!=expected_world_sha256
            or not isinstance(cases,list) or len(cases)!=24):
        raise EngageSourceError("Unexpected private source packet")
    match=[x for x in cases if x.get("case_id")==CASE_ID]
    if len(match)!=1 or (match[0].get("model"),match[0].get("scenario"))!=(MODEL,SCENARIO):
        raise EngageSourceError("Canonical ARC24-06 identity not verified")
    ar,na=_data(world)
    en,ne=_data(engage)
    if na==0:
        raise EngageSourceError("Canonical ARC24-06 World source was not found")
    # Guard 2050 original source extract against the saved private case.
    for name,entry in match[0].get("source_observations",{}).items():
        if name not in FOCUS:continue
        values=ar.get((name,entry.get("unit")))
        if not values or values[2050]!=_decimal(entry.get("raw")):
            raise EngageSourceError("Canonical 2050 source values disagree with private packet")
    comparisons=[]
    by_status=Counter()
    derived_status=Counter()
    for year in YEARS:
        for name in FOCUS:
            a,as_=_value(ar,name,year)
            b,bs=_value(en,name,year)
            state=_status(a,b) if as_=="REPORTED_VALUE" and bs=="REPORTED_VALUE" else (
                "AR6_"+as_ if as_!="REPORTED_VALUE" else "ENGAGE_V2_"+bs)
            comparisons.append({"case_id":CASE_ID,"year":year,"variable":name,
                                "status":state})
            by_status[state]+=1
        # ENGAGE notebook uses the detailed branches, not the EIP aggregate.
        values=[];states=[]
        for name in COMPONENTS:
            v,state=_value(en,name,year)
            values.append(v);states.append(state)
        ar_other,ar_state=_value(ar,OTHER,year)
        if all(x=="REPORTED_VALUE" for x in states):
            computed=values[0]-sum(values[1:],Decimal(0))
            outcome=(_status(computed,ar_other) if ar_state=="REPORTED_VALUE"
                     else "AR6_OTHER_"+ar_state)
            derived_status[outcome]+=1
        else:
            derived_status["ENGAGE_SOURCE_COMPONENTS_INCOMPLETE"]+=1
    return {
        "schema":"residualpathways.arc24.engage_v2_vs_ar6_source_probe.v1",
        "status":("EXACT_CASE_MATCH_SOURCE_COMPARISONS_AVAILABLE" if ne
                  else "ENGAGE_V2_EXACT_MODEL_SCENARIO_NOT_FOUND"),
        "ar6_world_sha256":expected_world_sha256,
        "engage_v2_user_source_sha256":_digest(engage),
        "engage_v2_file_origin":"USER_SUPPLIED_FILENAME_AND_SHA_NOT_PUBLISHER_AUTHENTICATED",
        "ar6_source_rows_for_case":na,
        "engage_v2_source_rows_for_case":ne,
        "case_id":CASE_ID,
        "year_labels":list(YEARS),
        "exact_variables":list(FOCUS),
        "matching_basis":"IDENTICAL_SOURCE_MODEL_SCENARIO_WORLD_VARIABLE_UNIT_YEAR_ONLY",
        "source_reported_decimal_status_counts":dict(sorted(by_status.items())),
        "derived_notebook_other_status_counts":dict(sorted(derived_status.items())),
        "rows":comparisons,
        "independent_physical_gross_partition":"NOT_ESTABLISHED",
        "independent_physical_removal_partition":"NOT_ESTABLISHED",
        "ar6_source_processing_lineage":"NOT_ESTABLISHED",
        "science_review_state":"REVIEW_PENDING",
        "verified_i3":0,
        "limitations":[
            "ENGAGE Global Scenarios v2.0 is a related different source from IPCC AR6 v1.1.",
            "Source data provenance for the user-provided ENGAGE v2.0 file is not publisher-authenticated.",
            "The ENGAGE notebook explicitly computes CO2 Other; a matching derived residual is not independent physical sector evidence.",
            "Exact decimal source correspondence does not establish a common model binary, original source quantization, system-boundary completeness or atmospheric CDR.",
            "Zero and missing are distinct; other units cannot be silently converted; source observations and scenario names remain private.",
        ],
        "notebook_primary_source":"https://github.com/iiasa/ENGAGE-netzero-analysis/blob/2d2be452dceed13b9671941fe5af7094a0e12956/assessment/1_categorization.ipynb",
        "external_dataset_doi":"https://doi.org/10.5281/zenodo.5553976",
    }


def write(world,engage,packet,output,*,expected_world_sha256=WORLD_SHA):
    out=Path(output).resolve()
    if "ar6-private" in out.parts:
        raise EngageSourceError("Safe anonymous aggregate-only output must stay outside private source directory")
    result=evaluate(world,engage,packet,expected_world_sha256=expected_world_sha256)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--world",type=Path,default=Path("data/ar6-private/AR6_Scenarios_Database_World_v1.1.csv"))
    p.add_argument("--engage-v2",type=Path,default=Path("data/ar6-private/ENGAGE_scenario_data_world_r2.0.csv"))
    p.add_argument("--packet",type=Path,default=Path("data/ar6-private/canonical_selected24_packet.json"))
    p.add_argument("--output",type=Path,default=Path("results/ar6-canonical-gate/arc24_poles_engage_v2_probe_public.json"))
    args=p.parse_args()
    r=write(args.world,args.engage_v2,args.packet,args.output)
    print(r["status"])
    print("Original AR6 rows:",r["ar6_source_rows_for_case"],
          "ENGAGE v2 exact case rows:",r["engage_v2_source_rows_for_case"])
    print("Source statuses:",r["source_reported_decimal_status_counts"])
    print("Notebook-derived Other statuses:",r["derived_notebook_other_status_counts"])
    print("No physical gross/CDR scientific grade has been assigned.")


if __name__=="__main__":
    main()
