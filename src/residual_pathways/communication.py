"""Generate derivative-only figure and source-linked research/policy brief."""
from __future__ import annotations
import csv
import json
from hashlib import sha256
from pathlib import Path

def write_communication(root,output):
    root=Path(root)
    raw=(root/"data/derived/ar6_teaching_2050_summary.json").read_bytes()
    source=json.loads(raw)
    register=list(csv.DictReader((root/"data/derived/rp24_case_register.csv").open(newline="")))
    gas=list(csv.DictReader((root/"data/derived/n2o_metric_sensitivity_2050.csv").open(newline="")))
    classes=source["category_coverage"]
    if (len(classes)!=8 or sum(x["n"] for x in classes)!=1202 or
            sum(x["eip_afolu_land_beccs_dac_fossilccs"] for x in classes)!=261 or
            len(register)!=24 or len(gas)!=8):
        raise ValueError("Changed source summary must be revalidated before communication")
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    width,height=910,540
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
         '<title id="title">AR6 teaching source: category-level CO2 reporting candidates</title>',
         '<desc id="desc">Bars represent vetted cohort size, direct-air capture reporting, and six candidate co-reporting counts at 2050. They are not verified gross emissions.</desc>',
         '<rect width="100%" height="100%" fill="#ffffff"/>',
         '<text x="25" y="34" font-size="21" font-family="sans-serif" fill="#182c44">Reporting completeness — AR6 teaching source, 2050</text>',
         '<text x="25" y="58" font-size="12" font-family="sans-serif" fill="#395067">Not canonical AR6 v1.1; reporting presence only, not I3 accounting</text>']
    plot_left=200
    max_value=max(x["n"] for x in classes)
    labels=[("Vetted scenarios","n","#77849b"),
            ("DAC variable reported","dac","#3178a7"),
            ("Six candidate variables reported","eip_afolu_land_beccs_dac_fossilccs","#146b55")]
    for idx,cat in enumerate(classes):
        y=90+idx*51
        svg.append(f'<text x="25" y="{y+19}" font-size="14" font-family="sans-serif" fill="#24374d">{cat["category"]}</text>')
        for k,(_,field,fill) in enumerate(labels):
            value=cat[field]
            bar_y=y+k*11
            bar_w=round(540*value/max_value,1)
            svg.append(f'<rect x="{plot_left}" y="{bar_y}" width="{bar_w}" height="9" fill="{fill}"/>')
            svg.append(f'<text x="{plot_left+bar_w+6}" y="{bar_y+8}" font-size="10" font-family="sans-serif">{value}</text>')
    for n,(label,_,fill) in enumerate(labels):
        x=25+n*290
        svg.append(f'<rect x="{x}" y="515" width="13" height="10" fill="{fill}"/>')
        svg.append(f'<text x="{x+19}" y="524" font-size="11" font-family="sans-serif" fill="#24374d">{label}</text>')
    svg.append('</svg>')
    chart=out/"reporting_funnel.svg";chart.write_text("\n".join(svg)+"\n")
    total=source["vetted_totals"]
    policy=[
        "# Research brief — what the AR6 teaching-source reporting audit can establish","",
        "**Independent exploratory research, 23 October 2026. Not affiliated with or endorsed by IIASA/IPCC. Not the canonical World v1.1 assessment.**","",
        "## Main result",
        f"Of {total['scenarios']:,} climate-vetted Model×Scenario cases matched to the independently published World teaching release, "
        f"{total['reported_dac']:,} report a 2050 DAC variable and {total['co_report_eip_afolu_land_beccs_dac_fossilccs']:,} "
        "co-report the six named EIP, AFOLU, land, BECCS, fossil CCS and DAC candidate variables.",
        "Co-reporting **does not establish an exhaustive emissions/removals partition**. Fossil CCS is avoided source emissions, "
        "not atmospheric removal. Nested net AFOLU and energy-industrial series cannot be reconstructed as positive gross CO2 without source review.","",
        "## Sampling and reliability",
        f"The registered purposive forensic pilot selected {len(register)} contrasting scenarios across eight climate categories, "
        "with seven reporting all six candidate variables; 19 permit a three-term arithmetic diagnostic. "
        "None has completed model-specific scientific review. Zero verified I3 findings is a review-status statement, not a claim of true non-identifiability.",
        "Separate annual coverage tests cover 2030, 2050, 2070 and 2100. Model-label-balanced reporting rates are diagnostics, not probabilities or climate projections.","",
        "## Non-CO2 assessment-method finding",
        "The original 2021 and corrected 2025 IPCC AR6 N2O GWP100 values are 273 and 267. For fixed reported N2O mass, "
        "the CO2-equivalent number changes by −2.20% solely because the metric changed. The source does not support a complete methane-source split, "
        "so no unsupported all-gas CO2e total is reported.","",
        "## What a decision-maker should conclude",
        "Published reporting coverage varies by source variables and climate category. Comparisons of residual positive emissions or carbon removals "
        "require an explicit accounting boundary, exclusion log, source definitions, precision audit and independent scientific review. "
        "This exploratory software study **does not estimate a technology's effect on real-world emissions**.","",
        "## Reproduce and verify",
        "Source data: IIASA-labelled teaching World release, Zenodo 20056332. The named v1.1 metadata source was independently republished and "
        "has not been authenticated against a canonical IIASA download. Reproducible source scripts, source hashes, exclusion protocol and "
        "real-data GitHub Actions are provided in the ResidualPathways repository. No substantial restricted source rows are republished.","",
        "Reference: https://zenodo.org/records/20056332",
        "Reference: https://zenodo.org/records/7197970",
        "Reference: https://www.ipcc.ch/report/ar6/wg3/chapter/chapter-12/",
        "Reference: https://www.ipcc.ch/report/ar6/wg1/about/errata/",
        ""
    ]
    (out/"policy_brief.md").write_text("\n".join(policy))
    manifest={"schema_version":"derived-communication.v1","source_aggregate_sha256":sha256(raw).hexdigest(),
              "source_world_sha256":source["world_source"]["sha256"],
              "source_metadata_sha256":source["metadata_source"]["sha256"],
              "policy_brief_sha256":sha256((out/"policy_brief.md").read_bytes()).hexdigest(),
              "figure_sha256":sha256(chart.read_bytes()).hexdigest(),
              "source_status":"AR6_TEACHING_PILOT_NOT_CANONICAL_V1_1",
              "scientific_claims":"COVERAGE_AND_METRIC_COMPARISON_ONLY_NO_I3"}
    (out/"communication_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    return manifest
