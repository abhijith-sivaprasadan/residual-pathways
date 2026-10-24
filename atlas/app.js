const $ = (selector, base = document) => base.querySelector(selector);
const $$ = (selector, base = document) => [...base.querySelectorAll(selector)];
const fmt = n => Number(n).toLocaleString("en-US", { maximumFractionDigits: 1 });
const percent = (n, d) => d ? 100 * n / d : 0;
const esc = x => String(x).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");
const coverFields = {
  dac: ["dac", "Direct air capture"],
  six: ["all_six_candidate_presence", "Six candidate variables together"],
  eipLand: ["eip_afolu_land_beccs_dac", "Energy/industry, AFOLU, land, BECCS & DAC"],
  sixPlus: ["eip_afolu_land_beccs_dac_fossilccs", "Previous set + fossil CCS"],
  co2: ["co2", "Reported net CO₂"]
};
const sectionLabels = { overview: "Overview", coverage: "Scenario coverage", models: "Model comparison", gases: "Non-CO₂ metrics", experiments: "Controlled modelling", innovations: "Innovation gaps", operations: "Research operations", methods: "Methods & sources" };
const state = { data: null, metric: "dac", view: "overview" };
function finite(value) { const n = Number(value); if (!Number.isFinite(n)) throw new Error("Invalid numeric source value"); return n; }
function kpi(title, value, note, alert=false) {
  return '<div class="kpi"><div class="kpi-head"><span>' + esc(title) + '</span><span class="kpi-icon">↗</span></div><strong' + (alert ? ' class="alert"' : '') + '>' + esc(value) + '</strong><p>' + esc(note) + '</p></div>';
}
function metricRow(name, value, denominator, mode="percentage") {
  const v=finite(value), d=finite(denominator), p=percent(v,d);
  return '<div class="bar-row"><span class="bar-label">' + esc(name) + '</span><div class="track" role="img" aria-label="' + esc(name) + ', ' + fmt(v) + ' of ' + fmt(d) + ' reported"><span style="width:' + Math.min(100,Math.max(0,p)).toFixed(2) + '%"></span></div><span class="bar-value">' + (mode==="count" ? fmt(v) : p.toFixed(1)+"%") + '</span></div>';
}
function go(view) {
  if (!sectionLabels[view]) view="overview";
  state.view=view;
  $$("section.view").forEach(panel => panel.hidden = panel.id !== view);
  $$(".nav").forEach(btn => { const active=btn.dataset.go === view;btn.classList.toggle("active",active);if(active)btn.setAttribute("aria-current","page");else btn.removeAttribute("aria-current");});
  $("#crumb").textContent = sectionLabels[view];
  if (location.hash !== "#"+view) history.replaceState(null,"","#"+view);
  window.scrollTo({top:0,behavior:"instant"});
}
function totalsCheck(d) {
  if(d.schema!=="residualpathways.atlas.public.v1" || d.categories.length!==8 ||
     d.categories.reduce((s,x)=>s+finite(x.n),0)!==finite(d.totals.scenarios) ||
     d.comparison.rows.length!==18 || d.n2o.length!==8 || d.totals.verifiedI3!==0)
     throw new Error("Dashboard manifest failed provenance/count checks");
}
function renderHeadlines(d) {
  $("#hero-stats").innerHTML =
    kpi("Climate-vetted",fmt(d.totals.scenarios),"World · 2050 · eight categories") +
    kpi("Reported DAC",fmt(d.totals.dac),"Scenarios with explicit DAC value") +
    kpi("Six-variable presence",fmt(d.totals.six),"Reporting co-presence only") +
    kpi("Physical I3 verified","0","Unreviewed source partitions",true);
}
function renderCoverage(d) {
  const metric=coverFields[state.metric], key=metric[0], cats=d.categories;
  $("#overview-bars").innerHTML=cats.map(c=>metricRow(c.category,c[key],c.n)).join("");
  $("#coverage-bars").innerHTML=cats.map(c=>metricRow(c.category,c[key],c.n,$("#coverage-mode").value)).join("");
  const total=cats.reduce((s,c)=>s+finite(c[key]),0);
  $("#coverage-title").textContent=metric[1]+" by category";
  $("#coverage-big").textContent=fmt(total);
  $("#coverage-description").textContent=metric[1]+" · "+percent(total,d.totals.scenarios).toFixed(1)+"%";
  $("#coverage-progress").style.width=percent(total,d.totals.scenarios).toFixed(2)+"%";
  $("#coverage-table").innerHTML=cats.map(c=>{
    const v=finite(c[key]);
    return '<tr><td><strong>'+esc(c.category)+'</strong></td><td class="num">'+fmt(c.n)+'</td><td class="num">'+fmt(v)+'</td><td class="num">'+fmt(c.n-v)+'</td><td class="num"><strong>'+percent(v,c.n).toFixed(1)+'%</strong></td></tr>';
  }).join("");
  $$("#overview-switch [data-metric]").forEach(x=>x.classList.toggle("on",x.dataset.metric===state.metric));
  const vars=Object.entries(d.variableCounts).sort((a,b)=>finite(b[1])-finite(a[1]));
  $("#variables").innerHTML=vars.map(([name,count])=>'<div class="var-item"><span>'+esc(name)+'<br><small>'+esc(d.units[name]||"Original unit not recorded")+'</small></span><strong>'+fmt(count)+'</strong></div>').join("");
}
function setMetric(metric) {
  if(!coverFields[metric])return;
  state.metric=metric; $("#coverage-metric").value=metric;renderCoverage(state.data);
}
function downloadCsv(name,head,rows) {
  const safe=v=>{let str=String(v??"");if(/^[=+@]/.test(str))str="'"+str;return '"'+str.replaceAll('"','""')+'"';};
  const csv=[head,...rows].map(row=>row.map(safe).join(",")).join("\r\n")+"\r\n";
  const url=URL.createObjectURL(new Blob([csv],{type:"text/csv;charset=utf-8"}));
  const link=document.createElement("a");link.href=url;link.download=name;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function showRecordBars(id,records,unitFn) {
  const max=Math.max(1,...records.map(x=>Math.abs(finite(x.value))));
  $(id).innerHTML=records.map(x=>{
    const val=finite(x.value),width=(Math.abs(val)/max*100).toFixed(2);
    return '<div class="record"><span class="rec-name">'+esc(x.name)+'</span><div class="rec-track" role="img" aria-label="'+esc(x.name)+": "+fmt(val)+'"><span style="width:'+width+'%"></span></div><span class="rec-value">'+esc(unitFn(val))+'</span></div>';
  }).join("");
}
function renderModels(d) {
  const selected=$("#scenario-select").value;
  const rows=d.comparison.rows.filter(x=>x.scenario===selected);
  $("#model-title").textContent=selected || "Select a scenario";
  showRecordBars("#model-chart",rows.map(x=>({name:x.model,value:x.value})),value=>fmt(value));
}
function renderGases(d) {
  $("#n2o-stats").innerHTML=
    kpi("Original GWP100","273","IPCC AR6 WGI 2021")+
    kpi("Corrected GWP100","267","October 2025 errata")+
    kpi("Metric-only difference","−2.20%","Mass values unchanged")+
    kpi("Vetted cohorts",fmt(d.totals.scenarios),"Reported N₂O in 2050");
  const max=Math.max(...d.n2o.map(x=>finite(x.meanOriginal)));
  $("#n2o-chart").innerHTML=d.n2o.map(x=>{
    const original=finite(x.meanOriginal),corrected=finite(x.meanCorrected);
    return '<div class="n2o-row"><b>'+esc(x.category)+'</b><div class="n2o-pair" role="img" aria-label="'+esc(x.category)+': original '+fmt(original)+', corrected '+fmt(corrected)+' Mt CO₂e per year"><span style="width:'+(100*original/max).toFixed(2)+'%"></span><span class="second" style="width:'+(100*corrected/max).toFixed(2)+'%"></span></div><small>'+fmt(corrected)+'</small></div>';
  }).join("");
}
function renderExperiment(d) {
  const w=d.westeros;
  $("#experiment-stats").innerHTML=
    kpi("Baseline",fmt(w.baselineObjective),"Saved native objective")+
    kpi("No-cap control",fmt(w.controlObjective),"Emissions bookkeeping only")+
    kpi("With CO₂ cap",fmt(w.cappedObjective),"Same underlying model inputs")+
    kpi("Objective change","+"+finite(w.objectiveDeltaPct).toFixed(2)+"%","Educational model only");
  showRecordBars("#experiment-chart",[{name:"Original baseline",value:w.baselineObjective},{name:"CO₂ accounting; no cap",value:w.controlObjective},{name:"CO₂ accounting + cap",value:w.cappedObjective}],value=>fmt(value));
}
function renderOperations(d) {
  const rows=d.operations.milestones,counts={};
  for(const x of rows)counts[x.status]=(counts[x.status]||0)+1;
  $("#operation-stats").innerHTML=
    kpi("Total milestones",rows.length,"Author-reported workstream")+
    kpi("Done & tested",counts.DONE_TESTED||0,"Repository implementation state")+
    kpi("In progress",counts.IN_PROGRESS||0,"Open research/engineering tasks")+
    kpi("External review",counts.NEEDS_EXTERNAL_REVIEW||0,"Independent action not recorded",true);
  const selected=$("#operation-filter").value;
  $("#operation-table").innerHTML=rows.filter(x=>selected==="all"||x.status===selected).map(x=>
    '<tr><td><strong>'+esc(x.id)+'</strong></td><td>'+esc(x.name)+'</td><td><span class="status-pill '+esc(x.status)+'">'+esc(x.status.replaceAll("_"," "))+'</span></td></tr>'
  ).join("");
}
function renderInnovations(d) {
  const sector=$("#innovation-sector").value,search=$("#innovation-search").value.trim().toLocaleLowerCase();
  const rows=d.innovations.filter(x=>(sector==="all"||x.sector===sector)
    && (x.title+" "+x.mechanism+" "+x.sector).toLocaleLowerCase().includes(search));
  $("#innovation-count").textContent=rows.length+" / "+d.innovations.length+" research hypotheses";
  $("#innovation-list").innerHTML=rows.map(x=>{
    const safeSource=/^https:\/\/(www\.)?ipcc\.ch\//.test(x.source)?x.source:"https://www.ipcc.ch/";
    return '<article class="card innovation-card"><div class="innovation-top"><span>'+esc(x.id)+' / '+esc(x.sector.toUpperCase())+'</span><span class="status-pill">UNTESTED HYPOTHESIS</span></div><h2>'+esc(x.title)+'</h2><p>'+esc(x.mechanism)+'</p><div class="innovation-caution"><strong>Interpretation constraint</strong><span>'+esc(x.caution)+'</span></div><a href="'+esc(safeSource)+'" target="_blank" rel="noopener noreferrer" class="linklike">SOURCE CONTEXT ↗</a></article>';
  }).join("")||'<div class="notice">No matching hypotheses. Change the sector or search terms.</div>';
}
function renderMethods(d) {
  const items=[
    ["Input",d.provenance.coverageSource],["World SHA256",d.provenance.coverageSha256],
    ["Coverage cohort",fmt(d.totals.scenarios)+" climate-vetted World records"],["Data status","Public teaching-labelled source with locally reported official-file byte match; portal origin unverified"],
    ["Source year","2050"],["I3 status","0 independently verified cases"]
  ];
  $("#source-list").innerHTML=items.map(([k,v])=>'<dt>'+esc(k)+'</dt><dd>'+esc(v)+'</dd>').join("");
}
async function init(){
  try {
    const response=await fetch("./data/atlas.json",{cache:"no-store"});
    if(!response.ok)throw new Error("No atlas data: HTTP "+response.status);
    const d=await response.json();totalsCheck(d);state.data=d;
    $("#snapshot").textContent="DATA SNAPSHOT · "+d.date;
    renderHeadlines(d);
    renderGases(d);renderExperiment(d);renderOperations(d);renderMethods(d);
    $("#innovation-sector").innerHTML='<option value="all">All research domains</option>'+[...new Set(d.innovations.map(x=>x.sector))].sort().map(x=>'<option value="'+esc(x)+'">'+esc(x)+'</option>').join("");
    renderInnovations(d);
    $("#scenario-select").innerHTML=d.comparison.scenarios.map(x=>'<option value="'+esc(x)+'">'+esc(x)+'</option>').join("");
    renderModels(d);renderCoverage(d);
    $$("[data-go]").forEach(button=>button.addEventListener("click",()=>go(button.dataset.go)));
    $$("#overview-switch [data-metric]").forEach(button=>button.addEventListener("click",()=>setMetric(button.dataset.metric)));
    $("#coverage-metric").addEventListener("change",e=>setMetric(e.target.value));
    $("#coverage-mode").addEventListener("change",()=>renderCoverage(d));
    $("#scenario-select").addEventListener("change",()=>renderModels(d));
    $("#operation-filter").addEventListener("change",()=>renderOperations(d));
    $("#innovation-sector").addEventListener("change",()=>renderInnovations(d));
    $("#innovation-search").addEventListener("input",()=>renderInnovations(d));
    $("#coverage-download").addEventListener("click",()=>{
      const [key,label]=coverFields[state.metric];
      downloadCsv("ar6-world-2050-reporting-"+state.metric+".csv",["category","vetted_scenarios","reported","not_reported","reporting_share_percent","field"],
        d.categories.map(x=>[x.category,x.n,x[key],x.n-x[key],percent(x[key],x.n).toFixed(3),label]));
    });
    $("#scenario-download").addEventListener("click",()=>{
      const selected=$("#scenario-select").value;
      downloadCsv("cdlinks-"+selected+"-2050-net-co2.csv",["model","scenario","region","year","unit","reported_net_co2"],
        d.comparison.rows.filter(x=>x.scenario===selected).map(x=>[x.model,x.scenario,"World",2050,"Mt CO2/yr",x.value]));
    });
    window.addEventListener("hashchange",()=>go(location.hash.slice(1)));
    go(location.hash.slice(1)||"overview");
  }catch(err){console.error("Atlas initialization failed",err);$("#load-error").hidden=false;$("#load-error").textContent="Dashboard data could not be loaded or passed integrity checks. Check atlas/data/atlas.json and serve the atlas over HTTP."; }
}
init();