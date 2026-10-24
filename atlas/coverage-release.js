/* Optional, checksum-checked four-year reporting data. No fallback fabrication. */
const byId = id => document.getElementById(id);
const clean = x => String(x).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const pct = value => (100 * value).toFixed(1) + "%";
let release = null;

async function loadCoverageRelease() {
  const status = byId("coverage-release-status");
  try {
    const [res, checksum] = await Promise.all([
      fetch("./data/coverage_release.json", {cache:"no-store"}),
      fetch("./data/coverage_release.json.sha256", {cache:"no-store"})
    ]);
    if (res.status === 404 && checksum.status === 404) {
      status.textContent = "Four-year coverage-only bundle not yet published. The original 2050 chart below is a separate snapshot, not a certified four-year release.";
      return;
    }
    if (!res.ok || !checksum.ok) throw new Error("Missing file or checksum; refusing partial release");
    const raw = await res.arrayBuffer();
    const expected = (await checksum.text()).trim().split(/\s+/)[0];
    if (!/^[a-f0-9]{64}$/.test(expected)) throw new Error("Invalid SHA-256 sidecar");
    if (!crypto?.subtle) throw new Error("Browser SHA-256 unavailable on this origin");
    const digest = [...new Uint8Array(await crypto.subtle.digest("SHA-256", raw))].map(x => x.toString(16).padStart(2,"0")).join("");
    if (digest !== expected) throw new Error("Coverage bundle failed SHA-256 check");
    const data = JSON.parse(new TextDecoder().decode(raw));
    if (data.schema !== "residualpathways.coverage-only.v1" || data.science_review_state !== "REVIEW_PENDING" ||
        data.i3_verified !== 0 || data.physical_accounting !== "NOT_ESTABLISHED" ||
        data.categories.length !== 8 || data.years.length !== 4 ||
        data.records.length !== data.categories.length * data.years.length * data.variables.length)
      throw new Error("Coverage bundle failed scientific and shape validation");
    release = data;
    status.textContent = "Coverage-only candidate " + data.version + " · " + data.cohort_size + " World model–scenario records · local source hashes checked · publisher receipt and scientific review outstanding. SHA-256 " + digest.slice(0, 16) + "…";
    const controls = byId("coverage-release-controls");
    controls.hidden = false;
    byId("release-year").innerHTML = data.years.map(y => '<option value="' + y + '"' + (y === 2050 ? " selected" : "") + '>' + y + '</option>').join("");
    byId("release-variable").innerHTML = data.variables.map((v,i) => '<option value="' + i + '">' + clean(v) + '</option>').join("");
    byId("release-year").addEventListener("change", renderCoverageRelease);
    byId("release-variable").addEventListener("change", renderCoverageRelease);
    byId("release-weighting").addEventListener("change", renderCoverageRelease);
    renderCoverageRelease();
  } catch (e) {
    status.textContent = "Four-year bundle unavailable or failed verification (" + e.message + "). No unverified data are displayed.";
  }
}

function renderCoverageRelease() {
  if (!release) return;
  const year = Number(byId("release-year").value);
  const variable = release.variables[Number(byId("release-variable").value)];
  const weight = byId("release-weighting").value;
  const rows = release.records.filter(r => r.year === year && r.variable === variable);
  if (rows.length !== 8) {
    byId("release-chart").textContent = "Incomplete coverage records: no visualization.";
    return;
  }
  byId("release-chart").innerHTML = rows.map(r => {
    const fraction = weight === "model" ? r.model_label_balanced_fraction : r.scenario_fraction;
    const descriptor = weight === "model" ? "equal average by exact model label" : r.reporting + " / " + r.denominator + " scenarios";
    return '<div class="bar-row"><span class="bar-label">' + clean(r.category) + '</span>' +
      '<div class="track" role="img" aria-label="' + clean(r.category + " " + pct(fraction) + ", " + descriptor) +
      '"><span style="width:' + (fraction * 100).toFixed(2) + '%"></span></div>' +
      '<span class="bar-value">' + pct(fraction) + '</span></div>';
  }).join("");
  const counts = rows.reduce((acc,r) => ({n:acc.n+r.denominator,reported:acc.reported+r.reporting}), {n:0,reported:0});
  byId("release-detail").textContent = counts.reported + " of " + counts.n + " scenarios explicitly report " + variable +
    " in " + year + ". The model-label view is descriptive, not model-family weighted. Neither view is an I3 accounting estimate.";
}

document.addEventListener("DOMContentLoaded", loadCoverageRelease);
