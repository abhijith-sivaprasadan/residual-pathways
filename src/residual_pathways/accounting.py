"""Quantization-aware arithmetic gate, not independent scientific validation."""
from __future__ import annotations
from decimal import Decimal, InvalidOperation, getcontext
getcontext().prec = 32
METHOD = "accounting.v3.provisional.1"
UNIT = "Mt CO2/yr"
FLAGS = ("exhaustive_positive_partition", "nonoverlapping_components",
         "same_gas_region_year_boundary", "verified_source_definitions",
         "fossil_ccs_excluded_from_removal", "land_net_gross_separated")

class AccountingError(ValueError):
    pass

def num(value, name):
    if value is None or isinstance(value, bool):
        raise AccountingError(f"{name}: missing/bool value is forbidden")
    try:
        v=Decimal(str(value))
    except (InvalidOperation, ValueError) as e:
        raise AccountingError(f"{name}: invalid number") from e
    if not v.is_finite():
        raise AccountingError(f"{name}: nonfinite")
    return v

def check_accounting(case, *, material_multiplier="1"):
    """Always separately assert semantics, source quantization and materiality."""
    if not isinstance(case,dict):
        raise AccountingError("Case must be an object")
    b=case.get("boundary")
    if not isinstance(b,dict) or any(b.get(x) is None for x in ("model","scenario","region","year","gas","sector_scope")):
        raise AccountingError("Exact source dimensions are required")
    if b["gas"] != "CO2" or type(b["year"]) is not int:
        raise AccountingError("CO2 gas and integer year only")
    net=case.get("net")
    positive=case.get("positive_components")
    removals=case.get("atmospheric_removals")
    if not isinstance(net,dict) or not isinstance(positive,list) or not isinstance(removals,list) or not positive or not removals:
        raise AccountingError("Explicit nonempty positive and removal partitions required")
    items=[net]+positive+removals
    if any(not isinstance(x,dict) for x in items):
        raise AccountingError("Each component must be an object")
    ids=[x.get("id") for x in items]
    if any(not isinstance(x,str) or not x for x in ids) or len(set(ids)) != len(ids):
        raise AccountingError("Distinct source IDs are mandatory")
    values=[]
    quant=[]
    source_precision_known=True
    for x in items:
        if x.get("unit") != UNIT:
            raise AccountingError("Explicit common Mt CO2/yr unit required")
        v=num(x.get("value"),x["id"])
        if x is not net and v<0:
            raise AccountingError("Positive components and atmospheric removals must be nonnegative")
        if x in removals and x.get("kind") == "fossil_ccs_capture":
            raise AccountingError("Fossil CCS is not atmospheric removal")
        values.append(v)
        if x.get("quantization_mt") is None:
            source_precision_known=False
        else:
            q=num(x["quantization_mt"],"quantization")
            if q <= 0 or not str(x.get("quantization_source_url") or "").startswith("https://"):
                source_precision_known=False
            quant.append(q)
    sem=case.get("semantic_review")
    semantic_pass=(isinstance(sem,dict) and all(sem.get(x) is True for x in FLAGS)
        and isinstance(sem.get("reviewer"),str) and bool(sem["reviewer"].strip())
        and isinstance(sem.get("source_definition_refs"),list)
        and bool(sem["source_definition_refs"])
        and all(isinstance(x,str) and x.startswith(("https://","doi:")) for x in sem["source_definition_refs"]))
    gross=sum(values[1:1+len(positive)],Decimal(0))
    cdr=sum(values[1+len(positive):],Decimal(0))
    net_value=values[0]
    residual=net_value-(gross-cdr)
    abs_error=abs(residual)
    eps_numeric=Decimal("1e-9")*max(Decimal(1),sum(map(abs,values),Decimal(0)))
    eps_round=Decimal("0.5")*sum(quant,Decimal(0)) if source_precision_known else None
    eps_source=eps_round+eps_numeric if eps_round is not None else None
    eps_material=max(Decimal("0.1"),Decimal("0.0001")*abs(net_value))
    min_nonzero=min((abs(x) for x in values[1:] if x!=0),default=None)
    if min_nonzero is not None and min_nonzero<10:
        eps_material=min(eps_material,Decimal("0.01")*min_nonzero)
    mult=num(material_multiplier,"material_multiplier")
    if mult<=0 or mult>10:
        raise AccountingError("Material sensitivity outside (0,10]")
    eps_material*=mult
    gates={"semantic_pass":bool(semantic_pass),
           "source_precision_known":source_precision_known,
           "source_precision_pass":eps_source is not None and abs_error<=eps_source,
           "materiality_pass":abs_error<=eps_material,
           "provenance_pass":bool(case.get("source_sha256")) and
                             str(case.get("source_document_url") or "").startswith("https://")}
    all_pass=all(gates.values())
    return {"method":METHOD,"boundary":b,"unit":UNIT,
            "reported_net_mt":str(net_value),"gross_positive_mt":str(gross),
            "atmospheric_removal_mt":str(cdr),"residual_mt":str(residual),
            "abs_error_mt":str(abs_error),"epsilon_round_mt":str(eps_round) if eps_round is not None else None,
            "epsilon_numeric_mt":str(eps_numeric),
            "epsilon_source_mt":str(eps_source) if eps_source is not None else None,
            "epsilon_material_mt":str(eps_material),"gates":gates,
            "failure_codes":[k for k,passed in gates.items() if not passed],
            "classification":"PENDING_INDEPENDENT_REVIEW" if all_pass else "NOT_I3",
            "scientific_warning":"Self-reported flags and source URLs are not independent authentication or review."}

def sensitivity(case):
    return {label:check_accounting(case,material_multiplier=value)
        for label,value in (("strict_half","0.5"),("registered","1"),("loose_double","2"))}
