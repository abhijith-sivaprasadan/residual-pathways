"""Deterministic 24-case IAMC source preflight; not scientific I0-I3 review."""
from __future__ import annotations
import csv
import json
import math
from collections import Counter
from hashlib import sha256
from pathlib import Path
from .stratify import metadata_rows, sha_file

CATEGORIES = tuple(f"C{i}" for i in range(1, 9))
SIX = (
    "Emissions|CO2|Energy and Industrial Processes",
    "Emissions|CO2|AFOLU",
    "Carbon Sequestration|Land Use",
    "Carbon Sequestration|CCS|Biomass",
    "Carbon Sequestration|CCS|Fossil",
    "Carbon Sequestration|Direct Air Capture",
)
TOTAL = "Emissions|CO2"
UNIT = "Mt CO2/yr"
SEED = "ResidualPathways-RP24-v1"


class CaseAuditError(ValueError):
    pass


def metadata_population(path, sheet):
    cohort = {}
    for i, row in enumerate(metadata_rows(path, sheet_name=sheet), start=2):
        if not {"Model", "Scenario", "Category"} <= row.keys():
            raise CaseAuditError("Metadata requires Model/Scenario/Category")
        key = (row["Model"].strip(), row["Scenario"].strip())
        category = row["Category"].strip()
        if not all(key) or key in cohort or category not in CATEGORIES:
            raise CaseAuditError(f"Invalid/duplicate vetted metadata row {i}")
        cohort[key] = category
    if not cohort:
        raise CaseAuditError("Empty vetted metadata population")
    return cohort


def scan_source(path, population, names, year):
    if not set(SIX + (TOTAL,)) <= set(names):
        raise CaseAuditError("Exact required variable names not provided")
    observations = {k: {} for k in population}
    encountered = set()
    row_count = 0
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        y = str(year) if str(year) in header else f"X{year}"
        if len(header) != len(set(header)) or not {"Model", "Scenario", "Region", "Variable", "Unit", y} <= set(header):
            raise CaseAuditError("Missing/duplicate IAMC source fields")
        for line, row in enumerate(reader, start=2):
            row_count += 1
            if None in row:
                raise CaseAuditError(f"Bad CSV field count on line {line}")
            if row["Region"] != "World":
                continue
            key = (row["Model"], row["Scenario"])
            if key not in population:
                continue
            encountered.add(key)
            var = row["Variable"]
            if var not in names or not (row.get(y) or "").strip():
                continue
            try:
                value = float(row[y])
            except ValueError as exc:
                raise CaseAuditError(f"Invalid numerical source value line {line}") from exc
            if not math.isfinite(value):
                raise CaseAuditError(f"Nonfinite source value line {line}")
            if var in observations[key]:
                raise CaseAuditError("Duplicate year/model/scenario/variable source observation")
            observations[key][var] = {"value": value, "raw": row[y].strip(), "unit": row["Unit"]}
    return {k: observations[k] for k in encountered}, row_count


def score(observations):
    return sum(x in observations and observations[x]["unit"] == UNIT for x in SIX)


def tie(key):
    return sha256((SEED + "\u241f" + key[0] + "\u241f" + key[1]).encode()).hexdigest()


def choose_24(observations, population):
    picked = []
    for category in CATEGORIES:
        group = sorted((k for k in observations if population[k] == category),
                       key=lambda k: (score(observations[k]), tie(k)))
        if len(group) < 3:
            raise CaseAuditError(f"Too few source-matched scenarios for {category}")
        trio = [(group[0], "LOW"), (group[(len(group)-1)//2], "MEDIAN"), (group[-1], "HIGH")]
        if len({k for k, _ in trio}) != 3:
            raise CaseAuditError("Selected duplicate scenario")
        picked += [(k, category, role) for k, role in trio]
    assert len(picked) == 24
    return picked


def arithmetic_diagnostic(records):
    need = (TOTAL, SIX[0], SIX[1])
    if not all(n in records for n in need):
        return {"status": "NOT_COMPUTABLE_MISSING", "difference_mt": None}
    if not all(records[n]["unit"] == UNIT for n in need):
        return {"status": "NOT_COMPUTABLE_UNITS", "difference_mt": None}
    delta = records[TOTAL]["value"] - records[SIX[0]]["value"] - records[SIX[1]]["value"]
    if not math.isfinite(delta):
        raise CaseAuditError("Nonfinite arithmetic difference")
    return {"status": "ARITHMETIC_ONLY_NOT_PHYSICAL_RECONCILIATION", "difference_mt": delta}


def audit_cases(source, metadata, names, year=2050, sheet="meta_Ch3vetted_withclimate"):
    population = metadata_population(metadata, sheet)
    if len(names) != len(set(names)):
        raise CaseAuditError("Candidate variables must be distinct")
    observations, count = scan_source(source, population, set(names), year)
    selection = choose_24(observations, population)
    public_cases, private_cases = [], []
    for i, (identity, category, slot) in enumerate(selection, 1):
        obs = observations[identity]
        diag = arithmetic_diagnostic(obs)
        cid = f"RP24-{i:02d}"
        public_cases.append({
            "case_id": cid, "category": category, "slot": slot,
            "six_valid_unit_count": score(obs),
            "six_present_count": sum(v in obs for v in SIX),
            "six_wrong_unit_count": sum(v in obs and obs[v]["unit"] != UNIT for v in SIX),
            "arithmetic_diagnostic_possible": diag["difference_mt"] is not None,
            "human_review": "NOT_REVIEWED", "accounting_grade": "NOT_DETERMINED",
            "i3_verified": False, "identity_status": "BLOCKED_SEMANTICS_PRECISION",
        })
        private_cases.append({
            "case_id": cid, "model": identity[0], "scenario": identity[1],
            "category": category, "slot": slot, "year": year,
            "source_observations": obs,
            "candidate_total_minus_eip_minus_afolu": diag,
            "missing_six": [n for n in SIX if n not in obs],
            "unit_incompatible_six": [n for n in SIX if n in obs and obs[n]["unit"] != UNIT],
            "review": {
                "reviewer": None, "date": None, "official_source_verified": False,
                "model_specific_definitions_ref": None,
                "emissions_scope_sign_ref": None,
                "component_completeness_ref": None,
                "land_sink_review_ref": None,
                "fossil_ccs_vs_cdr_review_ref": None,
                "source_precision_ref": None,
                "numerical_reconciliation_review_ref": None,
                "nonoverlap_verified": False, "rounding_verified": False,
                "classification": "UNDETERMINED", "rationale": None,
            },
        })
    summary = {
        "case_count": 24,
        "per_category": dict(Counter(x["category"] for x in public_cases)),
        "six_complete_cases": sum(x["six_valid_unit_count"] == 6 for x in public_cases),
        "three_term_diagnostics_available": sum(x["arithmetic_diagnostic_possible"] for x in public_cases),
        "reviewed_cases": 0, "verified_i3_cases": 0,
    }
    public = {
        "schema_version": "residualpathways.case-preflight.v1",
        "evidence_level": "SOURCE_CHECKED_AUTOMATION_NOT_EXPERT_REVIEW",
        "source_type": "IIASA_LABELLED_PUBLIC_AR6_TEACHING_NOT_CANONICAL_VERIFIED",
        "source_sha256": sha_file(source), "metadata_sha256": sha_file(metadata),
        "year": year, "region": "World", "sheet": sheet,
        "rows_scanned": count, "metadata_cohort_size": len(population),
        "source_matched_cohort_size": len(observations),
        "selection": {"method": "EIGHT_CLASSES_LOW_MEDIAN_HIGH_BY_SIX_NAME_COMPLETENESS",
                      "seed": SEED, "probability_sample": False},
        "summary": summary, "cases": public_cases,
        "limits": [
            "Published cases have no original model/scenario identities or numerical source values",
            "Nonprobability sample cannot estimate population-level I3 frequencies",
            "Variable presence and matching units are not proof of a disjoint gross/removal partition",
            "Numeric total-minus-EIP-minus-AFOLU is not a physical identity without verified scope",
            "No individual case has completed model-specific semantic and precision review",
        ],
    }
    private = {
        "handling": "LOCAL_ONLY_DO_NOT_COMMIT_DO_NOT_UPLOAD",
        "source_sha256": public["source_sha256"],
        "metadata_sha256": public["metadata_sha256"],
        "cases": private_cases,
    }
    return public, private


def run_case_audit(source, metadata, candidate_file, public_output, private_output,
                   year=2050, sheet="meta_Ch3vetted_withclimate"):
    pub, priv = Path(public_output), Path(private_output)
    if pub.resolve() == priv.resolve():
        raise CaseAuditError("Public and private file paths must differ")
    if "results/ar6-teaching-pilot" in str(priv):
        raise CaseAuditError("Private packet must not be placed in public artifact path")
    values = json.loads(Path(candidate_file).read_text(encoding="utf-8"))
    report, packet = audit_cases(source, metadata, list(values.values()), year, sheet)
    pub.parent.mkdir(parents=True, exist_ok=True)
    priv.parent.mkdir(parents=True, exist_ok=True)
    pub.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    priv.write_text(json.dumps(packet, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return report
