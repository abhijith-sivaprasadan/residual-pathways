"""Dependency-free chart of reported CD-LINKS CO2; no gross/removal claim."""
from html import escape

MODELS = ("MESSAGEix-GLOBIOM 1.0", "REMIND-MAgPIE 1.7-3.0", "IMAGE 3.0.1")
COLORS = ("#185b65", "#b35c39", "#806cac")


def render_2050(rows, destination):
    scenario_names = sorted({r["scenario"] for r in rows})
    if not rows:
        return
    left, right, top, row_step = 270, 980, 105, 88
    ceiling = max(r["value"] for r in rows) * 1.08
    height = top + len(scenario_names) * row_step + 110
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1060" height="{height}" viewBox="0 0 1060 {height}">',
             '<rect width="1060" height="100%" fill="#fbfaf7"/>',
             '<text x="36" y="38" font-family="sans-serif" font-size="24" font-weight="700">Reported CO2 by model and scenario, 2050</text>',
             '<text x="36" y="63" font-family="sans-serif" font-size="13" fill="#4a5a5b">World · Mt CO2/year · CD-LINKS teaching data · not a gross/CDR decomposition</text>']
    for t in (0, 10000, 20000, 30000, 40000, 50000, 60000):
        if t > ceiling:
            continue
        x = left + (right-left)*t/ceiling
        parts += [f'<line x1="{x:.1f}" y1="{top-12}" x2="{x:.1f}" y2="{height-76}" stroke="#d4d8d5"/>',
                  f'<text x="{x:.1f}" y="{height-52}" text-anchor="middle" font-family="sans-serif" font-size="12">{t:,}</text>']
    for i, scenario in enumerate(scenario_names):
        y = top + i*row_step
        parts.append(f'<text x="35" y="{y+15}" font-family="sans-serif" font-size="13">{escape(scenario)}</text>')
        for j, model in enumerate(MODELS):
            entry = next((r for r in rows if r["scenario"] == scenario and r["model"] == model), None)
            if entry is None:
                continue
            x = left + (right-left)*entry["value"]/ceiling
            yy = y + j*16
            parts += [f'<circle cx="{x:.1f}" cy="{yy}" r="5.5" fill="{COLORS[j]}"/>',
                      f'<text x="{x+9:.1f}" y="{yy+4}" font-family="sans-serif" font-size="11" fill="#263238">{entry["value"]/1000:.1f}k</text>']
    for j, name in enumerate(MODELS):
        x = 35 + j*315
        parts += [f'<circle cx="{x}" cy="{height-20}" r="5.5" fill="{COLORS[j]}"/>',
                  f'<text x="{x+13}" y="{height-15}" font-family="sans-serif" font-size="12">{escape(name)}</text>']
    parts.append("</svg>")
    destination.write_text("\n".join(parts) + "\n", encoding="utf-8")
