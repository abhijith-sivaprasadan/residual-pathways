"""Reproduce formal AR6 C1–C8 reporting-coverage findings, table and SVG figures.

Input must be the immutable candidate release JSON plus independently pinned
SHA-256. Outputs are descriptive reporting-presence aggregates, NOT physical
emissions, deployment, model-family frequencies, or I0/I3 judgements.
stdlib-only, offline, deterministic; source time series are never read.
"""
from __future__ import annotations

import argparse
import csv
from hashlib import sha256
from html import escape
import json
from pathlib import Path

CANDIDATE_SHA = "489a07276556fdb63774297fbb79fe78ed04ffec831ce05a22d4a338629168ba"
TAG = "ar6-coverage-only-v0.1.0-candidate"
YEAR = 2050
CATEGORIES = [f"C{i}" for i in range(1, 9)]
YEARS = [2030, 2050, 2070, 2100]
FOCUS = (
    "Emissions|CO2", "Emissions|CO2|AFOLU",
    "Carbon Sequestration|CCS|Biomass",
    "Carbon Sequestration|CCS|Fossil",
    "Carbon Sequestration|Land Use",
    "Carbon Sequestration|Direct Air Capture",
    "Carbon Sequestration|Enhanced Weathering",
)
SHORT = {
    "Emissions|CO2": "Net CO2",
    "Emissions|CO2|Energy": "Energy CO2",
    "Emissions|CO2|AFOLU": "AFOLU CO2",
    "Carbon Sequestration|CCS|Fossil": "Fossil CCS",
    "Carbon Sequestration|CCS|Biomass": "Biomass CCS",
    "Carbon Sequestration|Direct Air Capture": "Direct air capture",
    "Emissions|CH4": "Methane",
    "Emissions|N2O": "Nitrous oxide",
    "Emissions|CO2|Energy and Industrial Processes": "Energy + industry CO2",
    "Carbon Sequestration|Land Use": "Land-use sequestration",
    "Carbon Sequestration|Enhanced Weathering": "Enhanced weathering",
}
BLUE = "#246eb3"
INK = "#1b3351"
PALE = "#eaf0f6"
FONT = "font-family='Arial, Helvetica, sans-serif'"


class FindingsError(ValueError):
    pass


def _xml(v):
    return escape(str(v), quote=True)


def load_candidate(path: Path, *, expected_sha256=CANDIDATE_SHA):
    raw = path.read_bytes()
    digest = sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise FindingsError("The source bytes are not the pinned AR6 candidate")
    data = json.loads(raw)
    if (data.get("schema") != "residualpathways.coverage-only.v1"
            or data.get("science_review_state") != "REVIEW_PENDING"
            or data.get("i3_verified") != 0
            or data.get("physical_accounting") != "NOT_ESTABLISHED"
            or data.get("cohort_size") != 1202
            or data.get("years") != YEARS
            or data.get("categories") != CATEGORIES
            or len(data.get("variables", [])) != 11):
        raise FindingsError("Candidate scope / science-status gate failed")
    expected = {(cat, y, v) for cat in CATEGORIES for y in YEARS for v in data["variables"]}
    lookup = {}
    for r in data["records"]:
        if set(r) != {"category", "year", "variable", "denominator", "reporting", "model_labels",
                      "scenario_fraction", "model_label_balanced_fraction", "units"}:
            raise FindingsError("Unrecognized or identifying source record field")
        key = (r["category"], r["year"], r["variable"])
        if key in lookup or key not in expected:
            raise FindingsError("Invalid or duplicate aggregate")
        if (type(r["denominator"]) is not int or type(r["reporting"]) is not int
                or not 0 <= r["reporting"] <= r["denominator"]
                or abs(r["scenario_fraction"] - r["reporting"] / r["denominator"]) > 1e-9):
            raise FindingsError("Count and fraction mismatch")
        lookup[key] = r
    if set(lookup) != expected:
        raise FindingsError("Incomplete aggregate cross-product")
    for yr in YEARS:
        sizes = {cat: lookup[(cat,yr,data["variables"][0])]["denominator"] for cat in CATEGORIES}
        if sum(sizes.values()) != data["cohort_size"]:
            raise FindingsError("Category denominators do not reconcile")
        for cat in CATEGORIES:
            if any(lookup[(cat,yr,v)]["denominator"] != sizes[cat] for v in data["variables"]):
                raise FindingsError("Within-category denominator mismatch")
    return data, lookup, digest


def summaries(data, lookup, year=YEAR):
    n = data["cohort_size"]
    overall = {v: sum(lookup[(cat,year,v)]["reporting"] for cat in CATEGORIES)
               for v in data["variables"]}
    categories = {
        cat: {"n": lookup[(cat,year,data["variables"][0])]["denominator"],
              "models": lookup[(cat,year,data["variables"][0])]["model_labels"],
              **{v: lookup[(cat,year,v)]["reporting"] for v in data["variables"]}}
        for cat in CATEGORIES
    }
    for v in data["variables"]:
        for yr in YEARS:
            current = sum(lookup[(cat,yr,v)]["reporting"] for cat in CATEGORIES)
            if current != overall[v]:
                raise FindingsError("Year-specific counts differ: do not state time-invariance")
    return n, overall, categories


def bar_svg(data, overall, n):
    height = 72 + 11 * 34 + 46
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="980" height="{height}" viewBox="0 0 980 {height}" role="img" aria-label="Reported presence by variable, World C1–C8, 2050">',
             "<rect width='980' height='100%' fill='white'/>",
             f"<text x='22' y='32' fill='{INK}' font-size='22' font-weight='bold' {FONT}>Variable reporting coverage · World (2050)</text>",
             f"<text x='22' y='53' fill='#5a6e83' font-size='13' {FONT}>1,202 climate-vetted model–scenario records · data presence, not deployment</text>"]
    for i, v in enumerate(data["variables"]):
        k = overall[v]; p = 100*k/n; y = 88 + i*34
        lines += [
            f"<text x='22' y='{y+12}' fill='{INK}' font-size='13' {FONT}>{_xml(SHORT[v])}</text>",
            f"<rect x='255' y='{y}' width='540' height='16' rx='3' fill='{PALE}'/>",
            f"<rect x='255' y='{y}' width='{540*k/n:.2f}' height='16' rx='3' fill='{BLUE}'/>",
            f"<text x='815' y='{y+13}' fill='{INK}' font-size='13' {FONT}>{p:.1f}% ({k:,})</text>",
        ]
    lines.append(f"<text x='22' y='{height-20}' fill='#5a6e83' font-size='12' {FONT}>Exact source-variable names are used in the archived machine-readable table. Zero counts as present.</text>")
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def heatmap_svg(lookup):
    labels = [SHORT[v] for v in FOCUS]
    width, height = 1100, 102 + len(labels)*48 + 62
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Reporting percentages by climate category and variable, 2050">',
             "<rect width='1100' height='100%' fill='white'/>",
             f"<text x='20' y='30' fill='{INK}' font-size='21' font-weight='bold' {FONT}>Cross-category reporting availability · 2050</text>"]
    for i, cat in enumerate(CATEGORIES):
        x = 350 + i*89
        count = lookup[(cat,YEAR,FOCUS[0])]["denominator"]
        lines.append(f"<text x='{x+34}' y='70' text-anchor='middle' fill='{INK}' font-size='14' {FONT}>{cat}</text>")
        lines.append(f"<text x='{x+34}' y='87' text-anchor='middle' fill='#748599' font-size='11' {FONT}>n={count}</text>")
    for j, v in enumerate(FOCUS):
        y = 103 + j*48
        lines.append(f"<text x='20' y='{y+26}' fill='{INK}' font-size='13' {FONT}>{_xml(labels[j])}</text>")
        for i,cat in enumerate(CATEGORIES):
            x=350+i*89
            r=lookup[(cat,YEAR,v)]
            p=r["reporting"]/r["denominator"]*100
            # Opacity carries the reporting fraction; printed percentage remains legible.
            opacity=0.10+0.75*p/100
            lines.append(f"<rect x='{x}' y='{y}' width='76' height='37' rx='4' fill='{BLUE}' fill-opacity='{opacity:.3f}'/>")
            lines.append(f"<text x='{x+38}' y='{y+24}' text-anchor='middle' fill='{INK}' font-weight='bold' font-size='12' {FONT}>{p:.1f}%</text>")
    lines.append(f"<text x='20' y='{height-18}' fill='#5a6e83' font-size='12' {FONT}>Each cell is k / n for that category; category samples are unequal and not independent model families.</text>")
    lines.append("</svg>")
    return "\n".join(lines)+"\n"


def weighting_svg(lookup):
    v="Carbon Sequestration|Land Use"
    height=430
    lines=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1030" height="{height}" viewBox="0 0 1030 {height}" role="img" aria-label="Scenario versus exact model label balanced land sequestration reporting fractions">',
           "<rect width='1030' height='100%' fill='white'/>",
           f"<text x='20' y='29' font-size='21' fill='{INK}' font-weight='bold' {FONT}>Weighting sensitivity · land-use sequestration reporting (2050)</text>",
           f"<text x='20' y='52' fill='#5a6e83' font-size='13' {FONT}>Scenario-weighted vs mean within exact model labels; neither is model-family weighting</text>"]
    for i,cat in enumerate(CATEGORIES):
        r=lookup[(cat,YEAR,v)];y=74+i*39
        a=r["scenario_fraction"];b=r["model_label_balanced_fraction"]
        lines += [
            f"<text x='20' y='{y+18}' font-size='13' fill='{INK}' {FONT}>{cat}</text>",
            f"<rect x='73' y='{y}' width='{550*a:.2f}' height='11' fill='{BLUE}'/>",
            f"<rect x='73' y='{y+14}' width='{550*b:.2f}' height='11' fill='#d18443'/>",
            f"<text x='650' y='{y+19}' font-size='13' fill='{INK}' {FONT}>{100*a:.1f}%  /  {100*b:.1f}%  (Δ {100*(b-a):+.1f} pp)</text>"
        ]
    lines.append(f"<rect x='20' y='{height-28}' width='12' height='10' fill='{BLUE}'/><text x='40' y='{height-18}' font-size='12' fill='{INK}' {FONT}>Scenario-weighted</text>")
    lines.append(f"<rect x='207' y='{height-28}' width='12' height='10' fill='#d18443'/><text x='227' y='{height-18}' font-size='12' fill='{INK}' {FONT}>Exact model-label-balanced</text>")
    lines.append("</svg>")
    return "\n".join(lines)+"\n"


def manuscript(data, lookup, digest, n, overall, categories):
    pct = lambda k, d: f"{100*k/d:.1f}%"
    lines = [
        "# Reported variable availability across climate-vetted AR6 scenarios",
        "",
        "**Research findings — empirical descriptive analysis, candidate v0.1.0; 24 October 2026.**",
        "",
        "## Data and estimand",
        "",
        f"The frozen [AR6 World coverage-only candidate](https://github.com/abhijith-sivaprasadan/residual-pathways/tree/{TAG}) contains "
        f"{n:,} source-matched, climate-vetted World `Model + Scenario` records classified C1–C8. "
        "For each of 11 **exactly named** IAMC variables, a case is counted as *reporting* when it has an explicitly reported, "
        "finite numeric observation for a specified year, including zero. A blank entry is missing, not a zero. "
        "The numerator counts reporting pairs and the denominator is all matched pairs in the category; "
        "the fractions describe **reporting prevalence in this assessed ensemble**, not probabilities over future worlds, "
        "technology deployment, net emissions magnitudes or CDR effectiveness.",
        "",
        "The pre-specified years are 2030, 2050, 2070 and 2100; each year contains 88 category–variable aggregates. "
        "The source cohort has 1,202 distinct model–scenario pairs and 352 records overall. "
        "Climate categories are descriptive strata and are not balanced experimental treatments.",
        "",
        "## Main results",
        "",
        f"Overall, **net CO₂, CH₄ and N₂O** were explicitly reported in every matched scenario ({n:,}/{n:,}, 100%). "
        f"The reporting fractions were **{pct(overall['Emissions|CO2|AFOLU'],n)}** "
        f"({overall['Emissions|CO2|AFOLU']:,}/{n:,}) for net AFOLU CO₂; "
        f"**{pct(overall['Carbon Sequestration|CCS|Biomass'],n)}** "
        f"({overall['Carbon Sequestration|CCS|Biomass']:,}/{n:,}) for biomass CCS; "
        f"**{pct(overall['Carbon Sequestration|CCS|Fossil'],n)}** "
        f"({overall['Carbon Sequestration|CCS|Fossil']:,}/{n:,}) for fossil CCS; "
        f"**{pct(overall['Carbon Sequestration|Land Use'],n)}** "
        f"({overall['Carbon Sequestration|Land Use']:,}/{n:,}) for land-use sequestration; "
        f"**{pct(overall['Carbon Sequestration|Direct Air Capture'],n)}** "
        f"({overall['Carbon Sequestration|Direct Air Capture']:,}/{n:,}) for direct air capture; and "
        f"**{pct(overall['Carbon Sequestration|Enhanced Weathering'],n)}** "
        f"({overall['Carbon Sequestration|Enhanced Weathering']:,}/{n:,}) for enhanced weathering.",
        "",
        "![Aggregate reporting by variable](figures/ar6_world_variable_coverage.svg)",
        "",
        "*Figure 1.* Scenario-level reporting prevalence across the 1,202 climate-vetted World pairs, shown for 2050. "
        "The archived dataset has the same count for each selected variable at each of the four specified years. "
        "Presence is not activity; a reported numerical zero counts as reporting.",
        "",
        "## Differences by climate category",
        "",
        "Categories vary markedly in size, so raw reporting counts must not be compared without denominators. "
        "The table lists four high-interest source labels with source-native reporting counts in 2050; values are exact-name observations.",
        "",
        "| Category | n | DAC reported | Land sequestration reported | Enhanced weathering reported | Biomass CCS reported |",
        "| :--- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for cat in CATEGORIES:
        row=categories[cat];den=row["n"]
        def cell(name):
            k=row[name];return f"{k}/{den} ({pct(k,den)})"
        lines.append(f"| {cat} | {den} | {cell('Carbon Sequestration|Direct Air Capture')} | "
                     f"{cell('Carbon Sequestration|Land Use')} | "
                     f"{cell('Carbon Sequestration|Enhanced Weathering')} | "
                     f"{cell('Carbon Sequestration|CCS|Biomass')} |")
    dac="Carbon Sequestration|Direct Air Capture"
    eh="Carbon Sequestration|Enhanced Weathering"
    dac_rates={c:categories[c][dac]/categories[c]["n"] for c in CATEGORIES}
    eh_rates={c:categories[c][eh]/categories[c]["n"] for c in CATEGORIES}
    hi_dac=max(CATEGORIES,key=lambda x:dac_rates[x]);lo_dac=min(CATEGORIES,key=lambda x:dac_rates[x])
    hi_ew=max(CATEGORIES,key=lambda x:eh_rates[x]);lo_ew=min(CATEGORIES,key=lambda x:eh_rates[x])
    lines += [
        "",
        f"DAC reporting was highest in {hi_dac} ({categories[hi_dac][dac]}/{categories[hi_dac]['n']}, {pct(categories[hi_dac][dac],categories[hi_dac]['n'])}) "
        f"and lowest in {lo_dac} ({categories[lo_dac][dac]}/{categories[lo_dac]['n']}, {pct(categories[lo_dac][dac],categories[lo_dac]['n'])}). "
        f"Enhanced weathering reporting was highest in {hi_ew} ({categories[hi_ew][eh]}/{categories[hi_ew]['n']}, {pct(categories[hi_ew][eh],categories[hi_ew]['n'])}) "
        f"and lowest in {lo_ew} ({categories[lo_ew][eh]}/{categories[lo_ew]['n']}, {pct(categories[lo_ew][eh],categories[lo_ew]['n'])}). "
        "These are descriptive category-level differences, **not causal climate-category effects**.",
        "",
        "![Reporting by climate category](figures/ar6_category_coverage_heatmap.svg)",
        "",
        "*Figure 2.* Category-specific coverage percentages for seven selected exact source variable labels (2050). "
        "C1–C8 are not equal-sized groups, and the heatmap does not measure deployment, tonnes of removal or scientific identifiability.",
        "",
        "## Year and weighting robustness",
        "",
        "For each of the 11 candidate variables, the number of matched source scenarios reporting a value was "
        "**identical at 2030, 2050, 2070 and 2100**. This is a property of the selected availability screen and year fields; "
        "it is **not** evidence of constant emissions trajectories or unchanged technology deployment. "
        "The record should not be interpreted as 4 × 1,202 independent scenarios.",
        "",
        "The optional alternative estimator gives every **exactly matched model label** equal weight after calculating "
        "within-label reporting fractions. It is not independent model-family weighting. The observed category-wise gaps "
        "between this estimator and scenario-weighted prevalence show sensitivity to how models with multiple scenarios "
        "are represented; they must not be treated as uncertainty intervals or independent replicated trials.",
        "",
        "![Scenario versus model-label weighting](figures/ar6_weighting_contrast.svg)",
        "",
        "*Figure 3.* Scenario-level versus exact-model-label-balanced prevalence of land sequestration reporting. "
        "Differences are measured in percentage points and do not quantify family-level uncertainty.",
        "",
        "## Scientific interpretation and limitations",
        "",
        "- This is **reporting availability**. A named sequestration term may represent capture or a non-additive proxy; "
        "fossil point-source CCS is **not** atmospheric CDR. A DAC value of zero is not missing and does not imply DAC deployment.",
        "- `Emissions|CO2|AFOLU` is signed net land-sector CO₂, not gross land carbon uptake. "
        "Adding AFOLU, land sequestration, biomass CCS and DAC terms risks nested or overlapping accounting.",
        "- Source-specific positive-emissions and atmospheric-removal partitions have not been documented or physically "
        "reconciled. All classifications remain `REVIEW_PENDING`, `physical_accounting=NOT_ESTABLISHED`, **I3 verified = 0**. "
        "This is **not** a conclusion that zero true cases are eligible for I3.",
        "- Scenario pairs share modelling assumptions and sometimes whole model families. "
        "No probability-sample uncertainty, inferential confidence intervals, causal effects or model-family-independent frequencies are supported.",
        "- The original-named World and metadata file hashes were locally checked; the workbook identity-joined "
        "`Model + Scenario` records match the earlier redistribution, but non-cohort worksheet differences and "
        "independent authentication of the publisher download receipt remain open.",
        "- The low non-reporting cells of 1–3 in six category-variable combinations recur across years. "
        "They were screened and documented before the author approved publication of aggregate-only outputs.",
        "",
        "## Reproducibility and credit",
        "",
        f"- Pinned aggregate [candidate source tag](https://github.com/abhijith-sivaprasadan/residual-pathways/tree/{TAG}); "
        f"commit `e64156b7429441836d1fa3b1879d40d9aa814bb0`, artifact SHA-256 `{digest}`.",
        "- Regenerate this paper, tabulation and all SVG figures with `python -m residual_pathways.coverage_findings --check-input atlas/data/coverage_release.json --output-dir docs/research/coverage_20261024`.",
        "- Original dataset: Byers, E. et al. (2022), AR6 Scenarios Database v1.1, IAMC / IIASA, "
        "[version DOI](https://doi.org/10.5281/zenodo.7197970); "
        "[IIASA recommended citation](https://data.ene.iiasa.ac.at/ar6/static/About.html) "
        "and [AR6-specific adapted license](https://data.ene.iiasa.ac.at/ar6/static/License/Legal.html). "
        "Independent derived analysis, no IIASA/IPCC endorsement.",
        "- For climate-category definitions see IPCC AR6 WGIII Annex III and IIASA scenario metadata. "
        "This manuscript reports source-derived descriptive coverage findings only, and has not undergone independent peer review.",
        "",
    ]
    return "\n".join(lines)


def build(input_path: Path, output_dir: Path, *, expected_sha256=CANDIDATE_SHA):
    data, lookup, digest = load_candidate(input_path, expected_sha256=expected_sha256)
    n, overall, cats = summaries(data,lookup)
    output_dir.mkdir(parents=True,exist_ok=True)
    figures = output_dir / "figures"
    figures.mkdir(parents=True,exist_ok=True)
    paths = {
        "results": output_dir / "ar6_reporting_coverage_results.md",
        "table": output_dir / "ar6_presence_table.csv",
        "fig1": figures / "ar6_world_variable_coverage.svg",
        "fig2": figures / "ar6_category_coverage_heatmap.svg",
        "fig3": figures / "ar6_weighting_contrast.svg",
    }
    paths["results"].write_text(manuscript(data,lookup,digest,n,overall,cats),encoding="utf-8")
    paths["fig1"].write_text(bar_svg(data,overall,n),encoding="utf-8")
    paths["fig2"].write_text(heatmap_svg(lookup),encoding="utf-8")
    paths["fig3"].write_text(weighting_svg(lookup),encoding="utf-8")
    with paths["table"].open("w",encoding="utf-8",newline="") as file:
        w=csv.writer(file)
        w.writerow(["category","year","variable","eligible","reporting","reporting_percent",
                    "exact_model_labels","model_label_balanced_percent"])
        for yr in YEARS:
            for cat in CATEGORIES:
                for v in data["variables"]:
                    r=lookup[(cat,yr,v)]
                    w.writerow([cat,yr,v,r["denominator"],r["reporting"],
                        f'{100*r["scenario_fraction"]:.6f}',r["model_labels"],
                        f'{100*r["model_label_balanced_fraction"]:.6f}'])
    return paths


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check-input",type=Path,default=Path("atlas/data/coverage_release.json"))
    p.add_argument("--output-dir",type=Path,default=Path("docs/research/coverage_20261024"))
    p.add_argument("--expected-sha256",default=CANDIDATE_SHA)
    a=p.parse_args()
    result=build(a.check_input,a.output_dir,expected_sha256=a.expected_sha256)
    for name,path in result.items():
        print(f"{name}: {path}")


if __name__=="__main__":
    main()
