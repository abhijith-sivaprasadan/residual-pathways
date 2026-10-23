"""Reject silent zero filling and IAMC semi-hierarchy aggregation."""
from __future__ import annotations
import math

class UnsafeAggregation(ValueError):
    pass

def approved_partition_sum(observations, expected_components, *, approval):
    """Explicit exact-source component list; no missing imputation or parent-child assumptions.

    Observations map source variable to {value,unit,region,year}; approvals are
    externally reviewed inputs, not generated from a pipe-delimited name.
    """
    if not isinstance(approval,dict) or approval.get("nonoverlap_reviewed") is not True or approval.get("exhaustive_reviewed") is not True:
        raise UnsafeAggregation("An independently reviewed exhaustive/nonoverlap mapping is required")
    if not approval.get("reference_url"):
        raise UnsafeAggregation("Source definition reference required")
    if not isinstance(expected_components,(list,tuple)) or not expected_components:
        raise UnsafeAggregation("Nonempty predeclared components required")
    if len(expected_components)!=len(set(expected_components)):
        raise UnsafeAggregation("Duplicate component IDs")
    if not all(comp in observations for comp in expected_components):
        raise UnsafeAggregation("Missing source components are not zero")
    chosen=[observations[comp] for comp in expected_components]
    if any(not isinstance(x,dict) for x in chosen):
        raise UnsafeAggregation("Each observation must have source fields")
    identifiers={(x.get("unit"),x.get("region"),x.get("year")) for x in chosen}
    if len(identifiers)!=1 or any(None in ident for ident in identifiers):
        raise UnsafeAggregation("Unit/region/year mismatch")
    vals=[]
    for x in chosen:
        raw=x.get("value")
        if raw is None or isinstance(raw,bool):
            raise UnsafeAggregation("Missing and bool numerical values not permitted")
        try:value=float(raw)
        except (TypeError,ValueError) as exc:
            raise UnsafeAggregation("Invalid numerical source value") from exc
        if not math.isfinite(value):
            raise UnsafeAggregation("Nonfinite numerical source value")
        vals.append(value)
    return {"source_variables":list(expected_components),
            "unit":chosen[0]["unit"],"region":chosen[0]["region"],"year":chosen[0]["year"],
            "sum":math.fsum(vals),
            "status":"APPROVED_MAP_ARITHMETIC_ONLY_NOT_INDEPENDENT_SOURCE_VERIFICATION"}

def guard_semihierarchy(parent,children):
    """Warn if any child is nested in another requested child; never auto-approve."""
    names=[parent]+list(children)
    if len(set(names))!=len(names):
        raise UnsafeAggregation("Duplicate parent/child variable")
    for i,a in enumerate(names):
        for b in names[i+1:]:
            if a.startswith(b+"|") or b.startswith(a+"|"):
                raise UnsafeAggregation("Nested semi-hierarchical IAMC names require explicit non-overlap review")
    return True
