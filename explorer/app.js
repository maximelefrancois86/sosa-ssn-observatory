// The SOSA/SSN Usage Observatory: works, codes, key figures, terms, methodology and glossary,
// and the knowledge graph in SPARQL and in Sparklis. Vanilla JS, no build step. Data from
// data/ (slr/scripts/build_kg.py): works.json, figures.json, method.json, meta.json, kg.ttl.gz.
import { EXAMPLES, prefixBlock } from "./examples.js";

const DATA = "data/";
const TITLE = "SOSA/SSN Usage Observatory";
const S = { works: [], byId: new Map(), figures: [], figByKey: new Map(), facets: [], years: [0, 0], meta: {}, gloss: new Map(), glossary: [] };
let PREFIXES = "";   // the PREFIX block of the queries, from meta.json (start())

/* ---------- utilities ---------- */
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const fmt = (n) => Number(n).toLocaleString("en-US");
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const fold = (s) => String(s ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const NONE = "(none)";
const NOT_CODED = "not coded";
const live = (msg) => { const el = $("#live"); if (el) el.textContent = msg; };

function workIri(id) {
  const i = id.indexOf(":");
  const kind = id.slice(0, i), x = id.slice(i + 1);
  return kind === "openalex" ? `https://openalex.org/${x}` : `https://api.semanticscholar.org/CorpusID:${x}`;
}
function idFromIri(u) {
  if (u.startsWith("https://openalex.org/W")) return "openalex:" + u.slice(21);
  if (u.startsWith("https://api.semanticscholar.org/CorpusID:")) return "s2orc:" + u.slice(41);
  return null;
}
const workHref = (id) => "#/work/" + encodeURIComponent(id);

/* ---------- the glossary (method.json) ---------- */
// every code shown has a tooltip (title) with its definition, an accessible description
// (aria-describedby: a hidden element of #defs), and, where it is a link, links to its entry
const slug = (s) => String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const glossId = (group, code) => `g-${slug(group)}${code === undefined ? "" : "--" + slug(code)}`;
const defId = (group, code) => "d" + glossId(group, code).slice(1);
const glossHref = (group, code) => `#/methodology?g=${encodeURIComponent(group)}${code === undefined ? "" : ":" + encodeURIComponent(code)}`;
function def(group, code) {
  const g = S.gloss.get(group);
  return g ? g.get(String(code)) : undefined;
}
// attributes of an element that shows a code: title and accessible description
function defAttrs(group, code) {
  const d = def(group, code);
  return d ? ` title="${esc(code + ": " + d)}" aria-describedby="${defId(group, code)}"` : "";
}
// a code as a link to its glossary entry (or as plain text when it has no entry)
function codeLink(group, code, text = code, cls = "code") {
  if (code === null || code === undefined || code === "") return "";
  if (!def(group, code)) return `<span class="${cls}">${esc(text)}</span>`;
  return `<a class="${cls}" href="${glossHref(group, code)}"${defAttrs(group, code)}>${esc(text)}</a>`;
}
const codeList = (group, a) => (a && a.length ? a.map((x) => codeLink(group, x)).join(" ") : '<span class="muted">none</span>');
function installDefs() {
  const box = document.createElement("div");
  box.id = "defs";
  box.hidden = true;
  box.innerHTML = S.glossary.map((g) => g.entries.map((e) => `<span id="${defId(g.id, e.code)}">${esc(e.def)}</span>`).join("")).join("");
  document.body.append(box);
}

const NS = [
  ["sosa:", "http://www.w3.org/ns/sosa/"], ["ssn-system:", "http://www.w3.org/ns/ssn/systems/"],
  ["ssn:", "http://www.w3.org/ns/ssn/"], ["ssnx:", "http://purl.oclc.org/NET/ssnx/ssn#"],
];
function shortTerm(u) {
  for (const [p, ns] of NS) if (u.startsWith(ns)) return p + u.slice(ns.length);
  return u;
}

// the integer a printed figure states, or null (a percentage, a date, a list…)
function printedCount(v) {
  const s = v.replace(/\{,\}/g, "").replace(/,/g, "").replace(/\\,/g, "").trim();
  return /^\d+$/.test(s) ? Number(s) : null;
}

function download(name, text, type = "text/csv") {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], { type: type + ";charset=utf-8" }));
  a.download = name;
  document.body.append(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
}
const csvCell = (v) => {
  const s = Array.isArray(v) ? v.join("; ") : v === null || v === undefined ? "" : String(v);
  return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
};
const csv = (head, rows) => [head.map(csvCell).join(","), ...rows.map((r) => r.map(csvCell).join(","))].join("\r\n") + "\r\n";

/* ---------- the filter language of figures.json ---------- */
function same(a, b) {
  if (a === b) return true;
  if (typeof a === "object" || typeof b === "object") return JSON.stringify(a) === JSON.stringify(b);
  return false;
}
function cond(w, c) {
  const v = w[c.field] ?? null;
  if ("eq" in c) return same(v, c.eq);
  if ("ne" in c) return !same(v, c.ne);
  if ("in" in c) return c.in.some((x) => same(v, x));
  if ("has" in c) return Array.isArray(v) && v.includes(c.has);
  return false;
}
const matches = (w, f) => (f.all || []).every((c) => cond(w, c));

/* ---------- facets ---------- */
const PATTERN_Q = {
  property_individuals: "Property individuals", property_source: "Property source", punning: "Punning",
  system_individuals: "System individuals", result_form: "Result form", unit_placement: "Unit placement",
  time: "Time", hosting: "Hosting", location: "Location", grouping: "Grouping", feature_typing: "Feature typing",
};
const MODEL_NAME = { "claude-sonnet-5-5": "Claude Sonnet 5.5", "claude-opus-5-5": "Claude Opus 5.5", "claude-opus-5-5-agent": "Claude Opus 5.5 agents" };
const ENG_ORDER = ["E0", "E1", "E2", "E3", "E4", "E5", "unknown", NOT_CODED];
const ENG_LABEL = {
  E0: "E0 not about SOSA/SSN", E1: "E1 mention", E2: "E2 discussion", E3: "E3 data",
  E4: "E4 ontology reuse", E5: "E5 contribution", unknown: "unknown", [NOT_CODED]: NOT_CODED,
};
const STRATUM_LABEL = {
  A: "A cites a 2017+ seed", B: "B lineage seeds only, 2018+", C: "C lineage seeds only, before 2018",
  D: "D found in full texts, cites no seed",
};
const yn = (b) => (b ? "yes" : "no");
function facetDefs() {
  const F = [
    { key: "stratum", label: "Stratum", gloss: "strata", get: (w) => [w.stratum ?? NONE], order: ["A", "B", "C", "D"], labels: STRATUM_LABEL, open: true },
    { key: "engagement", label: "Engagement (model)", gloss: "engagement", get: (w) => [w.engagement ?? NOT_CODED], order: ENG_ORDER, labels: ENG_LABEL, open: true },
    { key: "type", label: "Type", get: (w) => [w.type || NONE] },
    { key: "version_used", label: "Version used (model)", gloss: "version", get: (w) => [w.version_used ?? NONE] },
    { key: "modules", label: "Modules (model)", gloss: "modules", get: (w) => w.modules },
    { key: "domain", label: "Domain (model)", gloss: "domain", get: (w) => [w.domain ?? NONE] },
    { key: "result_pattern", label: "Result pattern (model)", gloss: "result_pattern", get: (w) => w.result_pattern },
    { key: "value_properties", label: "Value properties (model)", gloss: "value_properties", get: (w) => w.value_properties },
    { key: "errors", label: "Error codes (model)", gloss: "errors", get: (w) => w.errors },
    { key: "names", label: "Name classes (script)", gloss: "names", get: (w) => w.names },
    { key: "simple_results", label: "Simple-result forms (script)", gloss: "simple_forms", get: (w) => w.simple_results },
    { key: "seeds", label: "Seeds cited", gloss: "seeds", get: (w) => w.seeds },
    { key: "text_seeds", label: "Text seeds named", gloss: "seeds", get: (w) => w.text_seeds },
    { key: "fulltext", label: "Full text held", get: (w) => [yn(w.fulltext)], order: ["yes", "no"] },
    { key: "basis", label: "Coded from", gloss: "coding", get: (w) => [w.basis ?? NOT_CODED] },
    { key: "coded_by", label: "Coded by", gloss: "coding", get: (w) => [w.coded_by ?? NOT_CODED] },
    { key: "engagement_uncertain", label: "Engagement marked uncertain", get: (w) => [yn(w.engagement_uncertain)], order: ["yes", "no"] },
    { key: "not_the_work", label: "Text held is another work", get: (w) => [yn(w.not_the_work)], order: ["yes", "no"] },
    { key: "flagged_venue", label: "Venue flagged (predatoryjournals.org)", get: (w) => [yn(w.flagged_venue)], order: ["yes", "no"] },
  ];
  for (const [q, label] of Object.entries(PATTERN_Q)) {
    F.push({ key: "p." + q, label, group: "Modelling patterns (agents)", gloss: "pattern-" + q, get: (w) => (w.patterns && w.patterns[q]) || [] });
  }
  return F;
}

/* ---------- the knowledge graph (worker) ---------- */
const KG = { worker: null, ready: null, seq: 0, pending: new Map(), listeners: new Set(), last: null };
function kgProgress(msg) {
  KG.last = msg;
  for (const fn of KG.listeners) fn(msg);
}
function kgCall(msg) {
  const id = ++KG.seq;
  return new Promise((resolve, reject) => {
    KG.pending.set(id, { resolve, reject });
    KG.worker.postMessage({ ...msg, id });
  });
}
function kgLoad() {
  if (KG.ready) return KG.ready;
  try {
    KG.worker = new Worker(new URL("kg-worker.js", import.meta.url), { type: "module" });
  } catch (e) {
    return Promise.reject(new Error("This browser cannot run module workers: " + e.message));
  }
  KG.worker.onmessage = (e) => {
    const m = e.data;
    if (m.type === "progress") return kgProgress(m);
    const p = KG.pending.get(m.id);
    if (!p) return;
    KG.pending.delete(m.id);
    if (m.type === "error") p.reject(new Error(m.message));
    else p.resolve(m);
  };
  KG.worker.onerror = (e) => {
    const err = new Error("The SPARQL engine could not start (" + (e.message || "network or CDN error") + ").");
    for (const p of KG.pending.values()) p.reject(err);
    KG.pending.clear();
    kgProgress({ stage: "error", message: err.message });
    KG.ready = null;
  };
  kgProgress({ stage: "engine" });
  KG.ready = kgCall({ type: "load", url: new URL(DATA + "kg.ttl.gz", location.href).href }).then((m) => {
    kgProgress({ stage: "ready", ...m });
    return m;
  }, (err) => {
    kgProgress({ stage: "error", message: err.message });
    KG.ready = null;
    throw err;
  });
  return KG.ready;
}
async function sparql(query) {
  await kgLoad();
  return kgCall({ type: "query", query });
}
function kgStatusText(m) {
  if (!m) return "";
  const mb = (n) => (n / 1048576).toFixed(1);
  switch (m.stage) {
    case "engine": return "Loading the SPARQL engine (Oxigraph 0.5.13, WebAssembly, about 4 MB)…";
    case "download": return m.total ? `Downloading the knowledge graph: ${mb(m.received)} of ${mb(m.total)} MB…` : `Downloading the knowledge graph: ${mb(m.received)} MB…`;
    case "decompress": return "Decompressing the knowledge graph…";
    case "parse": return `Loading the triples into Oxigraph (${mb(m.size)} MB of Turtle)…`;
    case "ready": return `Knowledge graph ready: ${fmt(m.triples)} triples (parsed in ${(m.ms / 1000).toFixed(1)} s).`;
    case "error": return "Error: " + m.message;
    default: return "";
  }
}
// show the loading state of the graph in an element, as long as it is in the page
function bindKgStatus(el) {
  const fn = (m) => {
    if (!el.isConnected) return KG.listeners.delete(fn);
    el.textContent = kgStatusText(m);
    el.classList.toggle("err", m.stage === "error");
  };
  KG.listeners.add(fn);
  if (KG.last) fn(KG.last);
}

/* ---------- routing ---------- */
function parseHash() {
  const raw = location.hash.replace(/^#\/?/, "");
  const qi = raw.indexOf("?");
  const path = qi < 0 ? raw : raw.slice(0, qi);
  const params = new URLSearchParams(qi < 0 ? "" : raw.slice(qi + 1));
  const parts = path.split("/").map((p) => { try { return decodeURIComponent(p); } catch { return p; } });
  const view = parts[0] === "sparklis" ? "sparql" : parts[0];   // the former Sparklis page is the SPARQL page
  return { view: view || "overview", arg: parts.slice(1).join("/"), params };
}
const VIEWS = { overview: viewOverview, works: viewWorks, work: viewWork, figures: viewKeyFigures, terms: viewTerms,
  methodology: viewMethodology, sparql: viewSparql };
let mounted = null;   // {view, update?}
function route() {
  const r = parseHash();
  const fn = VIEWS[r.view] || viewOverview;
  document.body.dataset.view = VIEWS[r.view] ? r.view : "overview";
  for (const a of $$("nav a")) {
    const on = a.dataset.view === r.view || (r.view === "work" && a.dataset.view === "works");
    a.classList.toggle("on", on);
    if (on) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
    const nav = a.parentElement;   // a phone: the menu scrolls sideways; show the current view
    if (on && nav.scrollWidth > nav.clientWidth) nav.scrollLeft = Math.max(0, a.offsetLeft - nav.offsetLeft - 16);
  }
  if (mounted && mounted.view === r.view && mounted.update && mounted.arg === r.arg) {
    mounted.update(r);
    return;
  }
  const main = $("#main");
  main.innerHTML = "";
  mounted = { view: r.view, arg: r.arg };
  const res = fn(main, r);
  if (res && res.update) mounted.update = res.update;
  window.scrollTo(0, 0);
}
// change the hash without a new history entry and without re-mounting the view
function replaceHash(h) {
  history.replaceState(null, "", h);
}

/* ---------- overview ---------- */
function viewOverview(main) {
  document.title = TITLE;
  const W = S.works;
  const by = (f) => W.reduce((m, w) => m.set(f(w), (m.get(f(w)) || 0) + 1), new Map());
  const strata = by((w) => w.stratum);
  const coded = W.filter((w) => w.engagement !== null).length;
  const full = W.filter((w) => w.fulltext).length;
  const keys = S.figures.filter((f) => f.main && f.set);
  main.innerHTML = `
  <h1>${TITLE}</h1>
  <div class="prose">
    <p>How is the W3C/OGC Semantic Sensor Network ontology (SSN), with its core SOSA, used? The observatory follows the
    works that cite the publications on SOSA/SSN (strata A to C), and the works whose full text writes SOSA/SSN names
    without citing them (stratum D), with what is known of each work's relation to SOSA/SSN: how deeply it engages
    with it, which version, modules and terms it uses, how it models observations and results, and the errors in
    the names it writes.</p>
    <p class="note"><strong>About the codes.</strong> The codes (engagement, version, modules, terms, results, errors,
    domains…) are made by a language model on a codebook, from the full text or the abstract: Claude Sonnet 5.5 coded
    every work; Claude Opus 5.5 coded a subset, and where it did, its answers are used. The modelling patterns are
    coded by Claude Opus 5.5 agents from excerpts of the full texts. The name classes and simple-result forms are found
    by script in the texts. Each code says who made it; the <a href="#/methodology">methodology</a> says how, and its
    glossary defines every code.</p>
  </div>
  <div class="cards">
    <div class="card"><a href="#/works"><div class="big">${fmt(W.length)}</div>candidate works</a></div>
    ${["A", "B", "C", "D"].map((s) => `<div class="card"><a href="#/works?stratum=${s}"${defAttrs("strata", s)}><div class="big">${fmt(strata.get(s) || 0)}</div><span class="st st-${s}">${s}</span> ${esc(STRATUM_LABEL[s].slice(2))}</a></div>`).join("")}
    <div class="card"><a href="#/works?fulltext=yes"><div class="big">${fmt(full)}</div>full texts held</a></div>
    <div class="card"><a href="#/works?engagement=${ENG_ORDER.slice(0, 7).map(encodeURIComponent).join("|")}"><div class="big">${fmt(coded)}</div>works coded by the language model</a></div>
    <div class="card"><a href="#/figures"><div class="big">${fmt(keys.length)}</div>key figures, recomputed in your browser</a></div>
  </div>
  <div class="grid2">
    <section aria-labelledby="h-years">
      <h2 id="h-years">Works by year and stratum</h2>
      <ul class="legend" aria-hidden="true">${["A", "B", "C", "D"].map((s) => `<li><span class="sw sw-${s}"></span>${s}</li>`).join("")}</ul>
      <div id="year-chart"></div>
      <details><summary>Table of this chart</summary><div class="table-wrap" id="year-table"></div></details>
    </section>
    <section aria-labelledby="h-eng">
      <h2 id="h-eng">Engagement with SOSA/SSN</h2>
      <p class="muted small">Deepest engagement coded by the language model for each work (all strata). <a href="${glossHref("engagement")}">The codes</a>.</p>
      <ul class="hbars" id="eng-bars"></ul>
    </section>
  </div>
  <h2>Views</h2>
  <ul class="prose">
    <li><a href="#/works">Works</a>: the table of all works, with facets, search, sorting, CSV export; the filters are kept in the address, to share a view.</li>
    <li><a href="#/figures">Key figures</a>: the main figures of the observatory by theme, each recomputed from the data and linked to its works.</li>
    <li><a href="#/terms">Terms</a>: the SOSA/SSN terms the works use, by version used.</li>
    <li><a href="#/methodology">Methodology</a>: how the observatory is built, and the glossary of every code.</li>
    <li><a href="#/sparql">SPARQL</a>: the knowledge graph (codes, citations, artefacts), explored in the browser with Sparklis, a query builder in natural language, or queried in SPARQL in its YASGUI view, with examples.</li>
  </ul>
  <h2>Data</h2>
  <ul class="prose">
    <li><a href="${DATA}works.json" download>works.json</a>: one record per work, with its codes.</li>
    <li><a href="${DATA}figures.json" download>figures.json</a>: the figures, with the works or the filter behind each count.</li>
    <li><a href="${DATA}method.json" download>method.json</a>: the glossary of the codes.</li>
    <li><a href="${DATA}kg.ttl.gz" download>kg.ttl.gz</a>: the knowledge graph, Turtle, gzip (FaBiO, CiTO, MOD, PROV-O, Web Annotation, DCAT, and the observatory's <code>slr:</code> vocabulary).</li>
  </ul>
  ${S.meta.quotations === false ? '<p class="muted small">This version does not publish the quotations of the works.</p>' : ""}`;
  yearChart($("#year-chart"), $("#year-table"));
  const eng = by((w) => w.engagement ?? NOT_CODED);
  const max = Math.max(...ENG_ORDER.map((e) => eng.get(e) || 0));
  $("#eng-bars").innerHTML = ENG_ORDER.map((e) => {
    const n = eng.get(e) || 0;
    return `<li><a href="#/works?engagement=${encodeURIComponent(e)}"${defAttrs("engagement", e)}>${esc(ENG_LABEL[e])}</a>
      <div class="track" aria-hidden="true"><div class="fill" style="width:${(100 * n / max).toFixed(1)}%"></div></div>
      <span class="n">${fmt(n)}</span></li>`;
  }).join("");
}

function yearChart(box, tableBox) {
  const W = S.works.filter((w) => w.year);
  const lo = Math.max(2005, Math.min(...W.map((w) => w.year))), hi = Math.max(...W.map((w) => w.year));
  const years = [];
  for (let y = lo; y <= hi; y++) years.push(y);
  const ST = ["A", "B", "C", "D"];
  const cnt = new Map(years.map((y) => [y, Object.fromEntries(ST.map((s) => [s, 0]))]));
  let before = 0;
  for (const w of W) {
    if (w.year < lo) { before++; continue; }
    if (cnt.has(w.year) && ST.includes(w.stratum)) cnt.get(w.year)[w.stratum]++;
  }
  const tot = (y) => ST.reduce((a, s) => a + cnt.get(y)[s], 0);
  const maxv = Math.max(...years.map(tot));
  const step = maxv > 300 ? 100 : maxv > 120 ? 50 : 20;
  const top = Math.ceil(maxv / step) * step;
  const Wd = 560, Ht = 260, L = 34, B = 22, T = 8, R = 4;
  const bw = (Wd - L - R) / years.length;
  const y = (v) => T + (Ht - T - B) * (1 - v / top);
  let svg = `<svg class="chart" viewBox="0 0 ${Wd} ${Ht}" role="img" aria-label="Stacked bars: works per year of publication, by stratum, ${lo} to ${hi}">`;
  for (let v = 0; v <= top; v += step) svg += `<line class="grid" x1="${L}" x2="${Wd - R}" y1="${y(v)}" y2="${y(v)}"/><text x="${L - 4}" y="${y(v) + 4}" text-anchor="end">${v}</text>`;
  years.forEach((yr, i) => {
    const x = L + i * bw + 1;
    let acc = 0;
    const c = cnt.get(yr);
    const segs = ST.filter((s) => c[s]);
    segs.forEach((s, k) => {
      const v = c[s];
      const y0 = y(acc), y1 = y(acc + v);
      const hgt = Math.max(0, y0 - y1 - (k < segs.length - 1 ? 1 : 0));
      svg += `<rect class="seg" x="${x.toFixed(1)}" y="${y1.toFixed(1)}" width="${(bw - 2).toFixed(1)}" height="${hgt.toFixed(1)}" rx="${k === segs.length - 1 ? 2 : 0}" fill="var(--s-${s.toLowerCase()})" data-tip="${yr}, stratum ${s}: ${v} works"/>`;
      acc += v;
    });
    if ((yr % 5 === 0) || i === 0 || (i === years.length - 1 && yr % 5 >= 2)) svg += `<text x="${(x + bw / 2 - 1).toFixed(1)}" y="${Ht - 6}" text-anchor="middle">${yr}</text>`;
    svg += `<a href="#/works?year=${yr}-${yr}" aria-label="${yr}: ${tot(yr)} works"><rect x="${(L + i * bw).toFixed(1)}" y="${T}" width="${bw.toFixed(1)}" height="${Ht - T - B}" fill="transparent" data-tip="${yr}: ${tot(yr)} works (A ${c.A}, B ${c.B}, C ${c.C}, D ${c.D})"/></a>`;
  });
  svg += "</svg>";
  box.innerHTML = svg + (before ? `<p class="muted small">Not shown: ${before} works dated before ${lo}.</p>` : "");
  tooltips(box);
  tableBox.innerHTML = `<table><thead><tr><th>Year</th>${ST.map((s) => `<th class="num">${s}</th>`).join("")}<th class="num">Total</th></tr></thead><tbody>${years.map((yr) => `<tr><td><a href="#/works?year=${yr}-${yr}">${yr}</a></td>${ST.map((s) => `<td class="num">${cnt.get(yr)[s]}</td>`).join("")}<td class="num">${tot(yr)}</td></tr>`).join("")}</tbody></table>`;
}
function tooltips(root) {
  let tip = null;
  root.addEventListener("pointermove", (e) => {
    const t = e.target.closest("[data-tip]");
    if (!t) { if (tip) tip.hidden = true; return; }
    if (!tip) { tip = document.createElement("div"); tip.className = "tip"; document.body.append(tip); }
    tip.hidden = false;
    tip.textContent = t.dataset.tip;
    const x = Math.min(e.clientX + 12, window.innerWidth - tip.offsetWidth - 8);
    tip.style.left = x + "px";
    tip.style.top = (e.clientY + 14) + "px";
  });
  root.addEventListener("pointerleave", () => { if (tip) tip.hidden = true; });
}

/* ---------- works ---------- */
const SORTS = {
  title: (w) => fold(w.title), year: (w) => w.year ?? -1, stratum: (w) => w.stratum ?? "~", type: (w) => w.type || "~",
  engagement: (w) => w.engagement ?? "~", version_used: (w) => w.version_used ?? "~", domain: (w) => w.domain ?? "~",
};
const COLS = [
  ["title", "Title"], ["year", "Year"], ["stratum", "Str."], ["type", "Type"], ["engagement", "Eng."],
  ["version_used", "Version used"], ["domain", "Domain"],
];
const openFacets = new Set();

function readWorksState(params) {
  const sel = {};
  for (const f of S.facets) {
    const v = params.get(f.key);
    if (v) sel[f.key] = new Set(v.split("|"));
  }
  let year = [null, null];
  const y = params.get("year");
  if (y) {
    const m = y.match(/^(\d{4})?-(\d{4})?$/);
    if (m) year = [m[1] ? +m[1] : null, m[2] ? +m[2] : null];
  }
  return { sel, year, q: params.get("q") || "", fig: params.get("fig"), term: params.get("term"), sort: params.get("sort") || "-year" };
}
function worksHash(st) {
  const p = new URLSearchParams();
  if (st.q) p.set("q", st.q);
  if (st.fig) p.set("fig", st.fig);
  if (st.term) p.set("term", st.term);
  if (st.year[0] !== null || st.year[1] !== null) p.set("year", `${st.year[0] ?? ""}-${st.year[1] ?? ""}`);
  for (const f of S.facets) if (st.sel[f.key] && st.sel[f.key].size) p.set(f.key, [...st.sel[f.key]].join("|"));
  if (st.sort && st.sort !== "-year") p.set("sort", st.sort);
  const s = p.toString().replace(/%7C/g, "|");
  return "#/works" + (s ? "?" + s : "");
}
function evaluate(st) {
  const words = fold(st.q).split(/\s+/).filter(Boolean);
  const fig = st.fig ? S.figByKey.get(st.fig) : null;
  const active = S.facets.filter((f) => st.sel[f.key] && st.sel[f.key].size);
  const counts = new Map(S.facets.map((f) => [f.key, new Map()]));
  const bump = (f, w) => { const m = counts.get(f.key); for (const v of w._f[f.key]) m.set(v, (m.get(v) || 0) + 1); };
  const rows = [];
  for (const w of S.works) {
    if (fig && !(fig.set && fig.set.has(w.id))) continue;
    if (st.term && !w.term_iris.includes(st.term)) continue;
    if (st.year[0] !== null && !(w.year >= st.year[0])) continue;
    if (st.year[1] !== null && !(w.year <= st.year[1])) continue;
    if (words.length && !words.every((t) => w._text.includes(t))) continue;
    let failed = null, nf = 0;
    for (const f of active) {
      const sel = st.sel[f.key];
      if (!w._f[f.key].some((v) => sel.has(v))) { nf++; failed = f; if (nf > 1) break; }
    }
    if (nf === 0) { rows.push(w); for (const f of S.facets) bump(f, w); }
    else if (nf === 1) bump(failed, w);
  }
  const desc = st.sort.startsWith("-");
  const key = SORTS[st.sort.replace(/^-/, "")] || SORTS.year;
  rows.sort((a, b) => {
    const x = key(a), y = key(b);
    const c = x < y ? -1 : x > y ? 1 : 0;
    return (desc ? -c : c) || (a.title < b.title ? -1 : 1);
  });
  return { rows, counts };
}

function viewWorks(main, r) {
  document.title = "Works · " + TITLE;
  let st = readWorksState(r.params);
  let shown = 100;
  let result = null;
  main.innerHTML = `
  <h1>Works</h1>
  <div class="works-layout">
    <aside class="facets" aria-label="Filters"><details class="all" open><summary>Filters</summary><div id="facet-box"></div></details></aside>
    <section>
      <div class="toolbar">
        <label class="visually-hidden" for="q">Search titles, authors and venues</label>
        <input type="search" id="q" placeholder="Search titles, authors, venues…" value="${esc(st.q)}" autocomplete="off">
        <span class="count" id="count" aria-live="polite"></span>
        <button type="button" id="csv">Export CSV</button>
        <button type="button" id="reset">Clear filters</button>
      </div>
      <ul class="chips" id="chips" aria-label="Active filters"></ul>
      <div class="results" id="results-pane" tabindex="0" aria-label="Results">
        <div class="table-wrap"><table class="works"><thead><tr id="thead"></tr></thead><tbody id="tbody"></tbody></table></div>
        <div class="more" id="more"></div>
      </div>
    </section>
  </div>`;
  if (matchMedia("(max-width: 860px)").matches) $("details.all", main).open = false;

  const go = (next, replace = false) => {
    const h = worksHash(next);
    if (replace) { replaceHash(h); update({ params: new URLSearchParams(h.split("?")[1] || "") }); }
    else location.hash = h;
  };
  let timer = null;
  $("#q").addEventListener("input", (e) => {
    clearTimeout(timer);
    timer = setTimeout(() => go({ ...st, q: e.target.value.trim() }, true), 200);
  });
  $("#reset").addEventListener("click", () => go({ sel: {}, year: [null, null], q: "", fig: null, term: null, sort: st.sort }));
  $("#csv").addEventListener("click", () => exportWorks(result.rows));
  $("#facet-box").addEventListener("change", (e) => {
    const t = e.target;
    if (t.dataset.facet) {
      const sel = { ...st.sel };
      const set = new Set(sel[t.dataset.facet] || []);
      t.checked ? set.add(t.value) : set.delete(t.value);
      sel[t.dataset.facet] = set;
      go({ ...st, sel });
    } else if (t.dataset.year) {
      const year = [...st.year];
      const v = t.value.trim();
      year[+t.dataset.year] = /^\d{4}$/.test(v) ? +v : null;
      go({ ...st, year });
    }
  });
  $("#facet-box").addEventListener("toggle", (e) => {
    const d = e.target;
    const k = d.dataset && d.dataset.key;
    if (!k) return;
    if (d.open) { openFacets.add(k); openFacets.delete("!" + k); }
    else { openFacets.delete(k); openFacets.add("!" + k); }
  }, true);
  $("#chips").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-drop]");
    if (!b) return;
    const [kind, k, v] = JSON.parse(b.dataset.drop);
    const next = { ...st, sel: { ...st.sel } };
    if (kind === "facet") { const s = new Set(next.sel[k]); s.delete(v); next.sel[k] = s; }
    else if (kind === "year") next.year = [null, null];
    else next[kind] = kind === "q" ? "" : null;
    go(next);
  });
  $("#thead").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-sort]");
    if (!b) return;
    const k = b.dataset.sort;
    const sort = st.sort === k ? "-" + k : st.sort === "-" + k ? k : (k === "year" ? "-year" : k);
    go({ ...st, sort }, true);
  });
  $("#more").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-more]");
    if (!b) return;
    shown = b.dataset.more === "all" ? Infinity : shown + 200;
    renderRows();
  });

  function renderRows() {
    const rows = result.rows;
    const n = Math.min(shown, rows.length);
    const frag = [];
    for (let i = 0; i < n; i++) {
      const w = rows[i];
      const by = [w.authors.slice(0, 3).join(", ") + (w.authors.length > 3 ? " et al." : ""), w.venue].filter(Boolean).join(" · ");
      frag.push(`<tr><td class="title"><a href="${workHref(w.id)}">${esc(w.title || "(no title)")}</a>${by ? `<div class="by">${esc(by)}</div>` : ""}</td>
        <td class="num">${w.year ?? ""}</td><td>${w.stratum ? codeLink("strata", w.stratum, w.stratum, `st st-${w.stratum}`) : ""}</td>
        <td>${esc(w.type)}</td><td>${w.engagement ? codeLink("engagement", w.engagement) + (w.engagement_uncertain ? '<span class="muted" title="marked uncertain by the model">?</span>' : "") : ""}</td>
        <td>${codeLink("version", w.version_used)}</td><td>${codeLink("domain", w.domain)}</td></tr>`);
    }
    $("#tbody").innerHTML = frag.join("") || `<tr><td colspan="7" class="muted">No work matches these filters.</td></tr>`;
    $("#more").innerHTML = rows.length > n
      ? `<span class="muted">Showing ${fmt(n)} of ${fmt(rows.length)}.</span><button type="button" data-more="200">Show 200 more</button><button type="button" data-more="all">Show all</button>`
      : rows.length > 100 ? `<span class="muted">Showing all ${fmt(rows.length)}.</span>` : "";
  }

  function renderFacets(counts) {
    const box = $("#facet-box");
    const focusId = document.activeElement && box.contains(document.activeElement) ? document.activeElement.id : null;
    const html = [];
    html.push(`<details class="facet" data-key="year" ${st.year[0] !== null || st.year[1] !== null || openFacets.has("year") ? "open" : ""}><summary>Year</summary>
      <div class="range"><label for="y0">From</label><input id="y0" type="number" inputmode="numeric" min="${S.years[0]}" max="${S.years[1]}" placeholder="${S.years[0]}" value="${st.year[0] ?? ""}" data-year="0">
      <label for="y1">to</label><input id="y1" type="number" inputmode="numeric" min="${S.years[0]}" max="${S.years[1]}" placeholder="${S.years[1]}" value="${st.year[1] ?? ""}" data-year="1"></div></details>`);
    let group = null;
    S.facets.forEach((f, fi) => {
      if (f.group !== group) {
        if (group) html.push("</details>");
        group = f.group;
        if (group) {
          const anyOpen = S.facets.some((g) => g.group === group && ((st.sel[g.key] && st.sel[g.key].size) || openFacets.has(g.key)));
          html.push(`<details class="facet-group" data-key="group:${esc(group)}" ${anyOpen || openFacets.has("group:" + group) ? "open" : ""}><summary>${esc(group)}</summary>`);
        }
      }
      const sel = st.sel[f.key] || new Set();
      const c = counts.get(f.key);
      const vals = [...new Set([...f.universe, ...sel])];
      if (f.order) vals.sort((a, b) => (f.order.indexOf(a) + 1 || 99) - (f.order.indexOf(b) + 1 || 99) || String(a).localeCompare(b));
      else vals.sort((a, b) => (c.get(b) || 0) - (c.get(a) || 0) || f.total.get(b) - f.total.get(a) || String(a).localeCompare(b));
      const open = sel.size || openFacets.has(f.key) || (f.open && !openFacets.has("!" + f.key));
      const help = f.gloss ? ` <a class="gl" href="${glossHref(f.gloss)}" title="Definitions: ${esc(f.label)}" aria-label="Definitions of the values of ${esc(f.label)}">?</a>` : "";
      html.push(`<details class="facet" data-key="${esc(f.key)}" ${open ? "open" : ""}><summary>${esc(f.label)}${sel.size ? ` <span class="sel">(${sel.size})</span>` : ""}${help}</summary><ul>`);
      vals.forEach((v, i) => {
        const n = c.get(v) || 0;
        const id = `f${fi}-${i}`;
        html.push(`<li class="${n ? "" : "zero"}"><label for="${id}"><input type="checkbox" id="${id}" data-facet="${esc(f.key)}" value="${esc(v)}" ${sel.has(v) ? "checked" : ""}>
          <span class="v"${f.gloss ? defAttrs(f.gloss, v) : ""}>${esc((f.labels && f.labels[v]) || v)}</span><span class="c">${fmt(n)}</span></label></li>`);
      });
      html.push("</ul></details>");
    });
    if (group) html.push("</details>");
    box.innerHTML = html.join("");
    if (focusId && document.getElementById(focusId)) document.getElementById(focusId).focus();
  }

  function renderChips() {
    const chips = [];
    const chip = (label, drop) => chips.push(`<li class="chip"><span>${label}</span><button type="button" aria-label="Remove this filter" data-drop='${esc(JSON.stringify(drop))}'>×</button></li>`);
    if (st.fig) {
      const f = S.figByKey.get(st.fig);
      chip(f ? `${f.label ? "Key figure" : "Set"}: ${esc(figLabel(f))}` : `Set <code>${esc(publicKey(st.fig))}</code> (unknown)`, ["fig"]);
    }
    if (st.term) chip(`Term <code>${esc(shortTerm(st.term))}</code>`, ["term"]);
    if (st.q) chip(`Text “${esc(st.q)}”`, ["q"]);
    if (st.year[0] !== null || st.year[1] !== null) chip(`Year ${st.year[0] ?? "…"}–${st.year[1] ?? "…"}`, ["year"]);
    for (const f of S.facets) for (const v of st.sel[f.key] || []) chip(`${esc(f.label)}: <span${f.gloss ? defAttrs(f.gloss, v) : ""}>${esc((f.labels && f.labels[v]) || v)}</span>`, ["facet", f.key, v]);
    $("#chips").innerHTML = chips.join("");
  }

  function update(rr) {
    st = readWorksState(rr.params);
    if ($("#q") !== document.activeElement) $("#q").value = st.q;
    result = evaluate(st);
    shown = 100;
    const pane = $("#results-pane");
    if (pane) pane.scrollTop = 0;
    $("#count").textContent = `${fmt(result.rows.length)} of ${fmt(S.works.length)} works`;
    live(`${result.rows.length} works`);
    $("#thead").innerHTML = COLS.map(([k, label]) => {
      const aria = st.sort === k ? "ascending" : st.sort === "-" + k ? "descending" : "none";
      return `<th scope="col" aria-sort="${aria}" class="${k === "year" ? "num" : ""}"><button type="button" class="sort" data-sort="${k}">${label}</button></th>`;
    }).join("");
    renderChips();
    renderFacets(result.counts);
    renderRows();
  }
  update(r);
  return { update };
}

function exportWorks(rows) {
  const qs = Object.keys(PATTERN_Q);
  const head = ["id", "url", "title", "year", "type", "authors", "venue", "publisher", "doi", "stratum", "seeds", "text_seeds",
    "countries", "flagged_venue", "fulltext", "not_the_work", "coded_by", "basis", "engagement", "engagement_uncertain",
    "version_used", "modules", "terms", "term_iris", "result_pattern", "value_properties", "domain", "subdomain", "companions",
    "gaps", "errors", "names", "simple_results", ...qs.map((q) => "pattern_" + q)];
  const out = rows.map((w) => head.map((k) => k === "url" ? workIri(w.id) : k.startsWith("pattern_") ? (w.patterns[k.slice(8)] || []) : w[k]));
  download(`sosa-ssn-works-${rows.length}.csv`, csv(head, out));
}

/* ---------- one work ---------- */
const CODE_FIELDS = [
  ["engagement", "Engagement"], ["version_used", "Version used", "version"], ["modules", "Modules", "modules"], ["terms", "Terms (as written)"],
  ["result_pattern", "Result pattern", "result_pattern"], ["value_properties", "Value properties", "value_properties"],
  ["errors", "Error codes", "errors"], ["domain", "Domain", "domain"], ["subdomain", "Subdomain"],
  ["companions", "Companion vocabularies"], ["gaps", "Gaps reported"],
];
// the glossary group of the answers of the knowledge graph, by question
const Q_GLOSS = { engagement: "engagement", engagement_also: "engagement", version_used: "version", modules: "modules",
  result_pattern: "result_pattern", value_properties: "value_properties", errors: "errors", domain: "domain" };
// a figure's readable name: its label (key figures), or its key without internal prefixes
const publicKey = (k) => String(k).replace(/^hyp-/, "");
const figLabel = (f) => f.label || `${publicKey(f.key)} (${fmt(f.n ?? 0)} works)`;
function viewWork(main, r) {
  const w = S.byId.get(r.arg);
  if (!w) {
    main.innerHTML = `<h1>Work not found</h1><p>No work has the id <code>${esc(r.arg)}</code>. <a href="#/works">All works</a>.</p>`;
    return;
  }
  document.title = (w.title || w.id).slice(0, 60) + " · " + TITLE;
  const iri = workIri(w.id);
  const src = w.id.startsWith("openalex:") ? `<a href="${esc(iri)}" rel="noopener">OpenAlex ${esc(w.id.slice(9))}</a>` : `<a href="${esc(iri)}" rel="noopener">Semantic Scholar CorpusID ${esc(w.id.slice(6))}</a>`;
  const list = (a) => (a && a.length ? a.map((x) => `<code>${esc(x)}</code>`).join(" ") : '<span class="muted">none</span>');
  const val = (v, g) => Array.isArray(v) ? (g ? codeList(g, v) : list(v)) : v === null || v === undefined || v === "" ? '<span class="muted">—</span>' : g ? codeLink(g, v) : esc(v);
  const figs = S.figures.filter((f) => f.main && f.set && f.set.has(w.id)).sort((a, b) => a.order - b.order);
  const pats = Object.entries(w.patterns || {});
  main.innerHTML = `
  <p class="small"><a href="#/works">← Works</a></p>
  <h1>${esc(w.title || "(no title)")}</h1>
  <p>${esc(w.authors.join(", "))}${w.authors.length >= 12 ? " et al." : ""}</p>
  <dl class="kv">
    <dt>Year</dt><dd>${w.year ?? "—"}</dd>
    <dt>Type</dt><dd>${esc(w.type || "—")}</dd>
    <dt>Venue</dt><dd>${esc(w.venue || "—")}${w.publisher ? ` <span class="muted">(${esc(w.publisher)})</span>` : ""}${w.flagged_venue ? ' <span class="tag">venue flagged by predatoryjournals.org</span>' : ""}</dd>
    <dt>Links</dt><dd>${w.doi ? `<a href="https://doi.org/${esc(w.doi)}" rel="noopener">doi:${esc(w.doi)}</a> · ` : ""}${src}</dd>
    <dt>Stratum</dt><dd>${codeLink("strata", w.stratum, w.stratum, `st st-${esc(w.stratum)}`)} ${esc(STRATUM_LABEL[w.stratum] ? STRATUM_LABEL[w.stratum].slice(2) : "")}</dd>
    <dt>Seeds cited</dt><dd id="seeds">${codeList("seeds", w.seeds)}${w.text_seeds.length ? ` · names ${codeList("seeds", w.text_seeds)}` : ""}</dd>
    <dt>Countries</dt><dd>${esc(w.countries.join(", ") || "—")}</dd>
    <dt>Full text</dt><dd>${w.fulltext ? "held" : "not held"}${w.text_item && w.text_item !== w.id ? ` (as <code>${esc(w.text_item)}</code>)` : ""}${w.not_the_work ? ' · <strong>the text held is another work</strong>: its codes are not counted' : ""}</dd>
  </dl>
  <h2>Codes</h2>
  ${w.engagement === null ? '<p class="muted">The language model did not code this work.</p>' : `
  <p class="muted small">Coded by ${codeLink("coding", w.coded_by, MODEL_NAME[w.coded_by] || w.coded_by)} from the ${codeLink("coding", w.basis)}.</p>
  <div class="table-wrap"><table class="codes"><tbody>
    ${CODE_FIELDS.map(([k, label, g]) => `<tr><td>${label}</td><td>${k === "engagement" ? codeLink("engagement", w.engagement, ENG_LABEL[w.engagement] || w.engagement) + (w.engagement_uncertain ? ' <span class="tag">uncertain</span>' : "") : val(w[k], g)}</td></tr>`).join("")}
  </tbody></table></div>`}
  ${w.names.length || w.simple_results.length ? `<h3>Found by script in the text</h3><dl class="kv"><dt>Name classes</dt><dd>${codeList("names", w.names)}</dd><dt>Simple-result forms</dt><dd>${codeList("simple_forms", w.simple_results)}</dd></dl>` : ""}
  ${pats.length ? `<h3>Modelling patterns <span class="muted small">(coded by Claude Opus 5.5 agents from excerpts)</span></h3><dl class="kv">${pats.map(([q, v]) => `<dt><a href="${glossHref("pattern-" + q)}">${esc(PATTERN_Q[q] || q)}</a></dt><dd>${codeList("pattern-" + q, v)}</dd>`).join("")}</dl>` : ""}
  ${figs.length ? `<h3>Key figures that count this work</h3><ul>${figs.map((f) => `<li><a href="#/figures?open=${encodeURIComponent(f.key)}">${esc(f.label)}</a> <span class="muted small">(${esc(f.group)}: ${fmt(f.n)} works)</span></li>`).join("")}</ul>` : ""}
  <h2>Answers and quotations</h2>
  ${S.meta.quotations === false ? '<p class="note">This version does not publish the quotations of the works: the answers are shown without their evidence.</p>' : ""}
  <p class="muted small">From the knowledge graph: each answer with the agent it is attributed to (<code>prov:wasAttributedTo</code>) and the passages quoted as evidence (<code>oa:TextQuoteSelector</code>). <a href="#/sparql?query=${encodeURIComponent(workQuery(iri))}">See the query</a>.</p>
  <p class="status" id="kg-status" role="status"></p>
  <div id="kg-answers"></div>`;
  if (w.engagement === null && !pats.length) {
    $("#kg-status").textContent = "No coded answer in the knowledge graph for this work.";
    return;
  }
  bindKgStatus($("#kg-status"));
  loadAnswers(w, iri).catch((e) => {
    const s = $("#kg-status");
    if (s) { s.textContent = "Could not query the knowledge graph: " + e.message; s.classList.add("err"); }
  });
}
function workQuery(iri) {
  return `${PREFIXES}
# every answer coded for one work, with its agent and its quotations
SELECT ?kind ?question ?value ?agent ?basis ?quote WHERE {
  VALUES ?work { <${iri}> }
  ?c slr:about ?work ; a ?kind ; slr:question ?question ; prov:wasAttributedTo ?agent .
  OPTIONAL { ?c slr:value ?value }
  OPTIONAL { ?c slr:basis ?basis }
  OPTIONAL { ?c slr:evidence/oa:exact ?quote }
}`;
}
async function loadAnswers(w, iri) {
  const base = `${PREFIXES}\n`;
  const [codes, quotes, seeds] = await Promise.all([
    sparql(`${base}SELECT ?c ?kind ?q ?agent ?basis (GROUP_CONCAT(?v; separator="\\u001f") AS ?values) WHERE {
      ?c slr:about <${iri}> ; a ?kind ; slr:question ?q ; prov:wasAttributedTo ?agent .
      OPTIONAL { ?c slr:value ?v } OPTIONAL { ?c slr:basis ?basis } } GROUP BY ?c ?kind ?q ?agent ?basis`),
    sparql(`${base}SELECT ?c ?quote WHERE { ?c slr:about <${iri}> ; slr:evidence/oa:exact ?quote }`),
    sparql(`${base}SELECT ?key ?title WHERE { <${iri}> cito:cites ?s . ?s slr:seedKey ?key ; dcterms:title ?title }`),
  ]);
  const B = (m) => m.json.results.bindings;
  const q = new Map();
  for (const b of B(quotes)) {
    const k = b.c.value;
    if (!q.has(k)) q.set(k, []);
    q.get(k).push(b.quote.value);
  }
  const rows = B(codes).map((b) => ({
    pattern: b.kind.value.endsWith("PatternCoding"),
    q: b.q.value.replace(/^.*#[qp]-/, ""),
    agent: b.agent.value.replace(/^.*\/agent\//, ""),
    basis: b.basis ? b.basis.value : "",
    values: b.values && b.values.value ? b.values.value.split("\u001f") : [],
    quotes: q.get(b.c.value) || [],
  }));
  const order = ["engagement", "engagement_also", "version_used", "modules", "terms", "extensions", "result_pattern", "value_properties", "errors", "artefacts", "domain", "subdomain", "companions", "gaps"];
  rows.sort((a, b) => (a.pattern - b.pattern) || ((order.indexOf(a.q) + 1 || 99) - (order.indexOf(b.q) + 1 || 99)) || a.q.localeCompare(b.q));
  const st = $("#kg-status");
  if (!st) return;
  st.textContent = `${rows.length} answers, ${B(quotes).length} quotations.`;
  $("#kg-answers").innerHTML = rows.length ? `<div class="table-wrap"><table class="codes"><thead><tr><th scope="col">Question</th><th scope="col">Answer and quotations</th><th scope="col">Coded by</th></tr></thead><tbody>${rows.map((r) => `
    <tr><td>${esc(r.pattern ? (PATTERN_Q[r.q] || r.q) : r.q.replace(/_/g, " "))}${r.pattern ? '<div class="who">pattern</div>' : ""}</td>
    <td>${r.values.length ? r.values.map((v) => `<div>${r.pattern ? codeLink("pattern-" + r.q, v) : Q_GLOSS[r.q] ? codeLink(Q_GLOSS[r.q], v) : esc(v)}</div>`).join("") : '<span class="muted">no value</span>'}
      ${r.quotes.map((t) => `<blockquote class="quote">“${esc(t)}”</blockquote>`).join("")}</td>
    <td class="who">${codeLink("coding", r.agent, MODEL_NAME[r.agent] || r.agent)}${r.basis ? `<br>from the ${esc(r.basis)}` : ""}</td></tr>`).join("")}</tbody></table></div>` : "";
  const sb = B(seeds);
  if (sb.length && $("#seeds")) {
    $("#seeds").innerHTML = `<ul>${sb.map((b) => `<li>${codeLink("seeds", b.key.value)}: ${esc(b.title.value)}</li>`).join("")}</ul>`;
  }
}

/* ---------- key figures ---------- */
const CODE_GLOSS = (c) => (c && c.length === 2 ? codeLink(c[0], c[1]) + " " : "");
function viewKeyFigures(main, r) {
  document.title = "Key figures · " + TITLE;
  const figs = S.figures.filter((f) => f.main && f.set).sort((a, b) => a.order - b.order);
  const ko = figs.filter((f) => f.ok === false);
  const groups = new Map();
  for (const f of figs) {
    if (!groups.has(f.group)) groups.set(f.group, []);
    groups.get(f.group).push(f);
  }
  const share = (f) => {
    const of = f.of && S.figByKey.get(f.of);
    if (!of || !of.n) return '<td class="num"></td>';
    const x = f.n / of.n;
    return `<td class="num share" title="${esc(`${fmt(f.n)} of ${fmt(of.n)}: ${figLabel(of)}`)}">${(100 * x).toFixed(x && x < 0.1 ? 1 : 0)} %<span class="bar" aria-hidden="true"><span style="width:${(100 * x).toFixed(1)}%"></span></span></td>`;
  };
  const row = (f) => `<tr id="fig-${esc(f.key)}" data-key="${esc(f.key)}" data-n="${f.n}" data-value="${esc(f.value)}">
    <td class="label">${CODE_GLOSS(f.code)}${esc(f.label)}${f.ok === false ? ` <span class="mark ko" title="figures.json says ${esc(f.value)}">differs from figures.json: ${esc(f.value)}</span>` : ""}</td>
    <td class="num"><button type="button" class="linkish count-btn" data-fig="${esc(f.key)}" aria-expanded="false" aria-label="${esc(`List the ${fmt(f.n)} works: ${f.label}`)}">${fmt(f.n)}</button></td>${share(f)}</tr>`;
  const table = (list) => `<div class="table-wrap"><table class="kf"><thead><tr><th scope="col">Figure</th><th scope="col" class="num">Works</th><th scope="col" class="num">Share</th></tr></thead><tbody>${list.map(row).join("")}</tbody></table></div>`;
  const section = ([g, list]) => {
    const subs = new Map();
    for (const f of list) {
      const k = f.sub || "";
      if (!subs.has(k)) subs.set(k, []);
      subs.get(k).push(f);
    }
    return `<section class="kf-group" id="kf-${slug(g)}" aria-labelledby="kfh-${slug(g)}"><h2 id="kfh-${slug(g)}">${esc(g)}</h2>
      ${[...subs].map(([sub, l]) => (sub ? `<h3>${esc(sub)}</h3>` : "") + table(l)).join("")}</section>`;
  };
  main.innerHTML = `
  <h1>Key figures</h1>
  <div class="prose">
  <p>The main figures of the observatory, by theme. Each counts works and is recomputed in your browser from
  <a href="${DATA}works.json" download>works.json</a> (with the filter or the list of works that
  <a href="${DATA}figures.json" download>figures.json</a> gives for it). The share is that of the figure named in its
  tooltip. Click a count to list its works, then open them in the works table to filter them further or export them.
  Every code has its definition in its tooltip and in the <a href="#/methodology">glossary</a>.</p>
  <p class="small ${ko.length ? "status err" : "muted"}">${ko.length ? `${ko.length} of the ${fmt(figs.length)} figures differ from the value of figures.json.` : `All ${fmt(figs.length)} figures recomputed here equal the values of figures.json.`}</p>
  </div>
  <nav class="toc" aria-label="Themes"><ul>${[...groups.keys()].map((g) => `<li><a href="#/figures?theme=${slug(g)}">${esc(g)}</a></li>`).join("")}</ul></nav>
  <div id="fig-box">${[...groups].map(section).join("")}</div>`;
  const box = $("#fig-box");
  function toggle(btn, force) {
    const tr = btn.closest("tr");
    const next = tr.nextElementSibling;
    if (next && next.classList.contains("fig-works")) {
      if (force) return;
      next.remove();
      btn.setAttribute("aria-expanded", "false");
      return;
    }
    const f = S.figByKey.get(btn.dataset.fig);
    const ws = [...f.set].map((id) => S.byId.get(id)).filter(Boolean).sort((a, b) => (b.year ?? 0) - (a.year ?? 0) || a.title.localeCompare(b.title));
    const extra = document.createElement("tr");
    extra.className = "fig-works";
    extra.innerHTML = `<td colspan="3"><p class="small"><a href="#/works?fig=${encodeURIComponent(f.key)}">Open these ${fmt(ws.length)} works in the works table</a> (facets, CSV).</p>
      <ol>${ws.map((w) => `<li><a href="${workHref(w.id)}">${esc(w.title || w.id)}</a> <span class="muted small">${w.year ?? ""} · ${esc(w.stratum)}${w.engagement ? " · " + esc(w.engagement) : ""}</span></li>`).join("")}</ol></td>`;
    tr.after(extra);
    btn.setAttribute("aria-expanded", "true");
  }
  box.addEventListener("click", (e) => {
    const b = e.target.closest("button[data-fig]");
    if (b) toggle(b);
  });
  function update(rr) {
    const p = rr.params;
    const open = p.get("open"), theme = p.get("theme");
    if (open) {
      const tr = document.getElementById("fig-" + open);
      if (tr) { toggle($("button[data-fig]", tr), true); tr.scrollIntoView({ block: "center" }); }
    } else if (theme) {
      const sec = document.getElementById("kf-" + theme);
      if (sec) sec.scrollIntoView({ block: "start" });
    }
  }
  update(r);
  return { update };
}
/* ---------- terms ---------- */
const VERSIONS = ["sosa-ssn-2017", "ssn-xg", "ssn-2023", "mixed", "unknown"];
const USERS = { stratum: "A|B|D", engagement: "E3|E4|E5", basis: "full text", not_the_work: "no" };
function viewTerms(main, r) {
  document.title = "Terms · " + TITLE;
  const p = r.params;
  main.innerHTML = `
  <h1>SOSA/SSN terms used</h1>
  <div class="prose">
  <p>The terms each work uses, as coded by the language model, resolved to IRIs: <code>ssn:</code> is
  the SSN-XG namespace (<code>ssnx:</code> here) for a work that uses SSN-XG or for a name only SSN-XG declares.
  Counts are numbers of works, by the <a href="${glossHref("version")}">version the work uses</a>. Click a term or a count to list the works.</p>
  </div>
  <div class="toolbar">
    <label for="tpop">Works</label>
    <select id="tpop">
      <option value="all">all coded works</option>
      <option value="users" ${p.get("pop") === "users" ? "selected" : ""}>works that use SOSA/SSN: E3–E5, full text, strata A, B, D</option>
    </select>
    <label class="visually-hidden" for="tq">Filter terms</label>
    <input type="search" id="tq" placeholder="Filter terms…" value="${esc(p.get("q") || "")}">
    <span class="count" id="tcount" aria-live="polite"></span>
  </div>
  <div class="table-wrap"><table><thead><tr id="thead"></tr></thead><tbody id="tbody"></tbody></table></div>
  <p class="muted small" id="tnote"></p>`;
  let sort = p.get("sort") || "-total";
  function render() {
    const users = $("#tpop").value === "users";
    const words = fold($("#tq").value).split(/\s+/).filter(Boolean);
    const params = new URLSearchParams();
    if (users) params.set("pop", "users");
    if ($("#tq").value.trim()) params.set("q", $("#tq").value.trim());
    if (sort !== "-total") params.set("sort", sort);
    replaceHash("#/terms" + (params.toString() ? "?" + params : ""));
    const pop = S.works.filter((w) => users
      ? ["A", "B", "D"].includes(w.stratum) && ["E3", "E4", "E5"].includes(w.engagement) && w.basis === "full text" && !w.not_the_work
      : w.engagement !== null);
    const T = new Map();
    for (const w of pop) {
      for (const t of w.term_iris) {
        if (!T.has(t)) T.set(t, { iri: t, short: shortTerm(t), total: 0 });
        const e = T.get(t);
        e.total++;
        const v = w.version_used ?? NONE;
        e[v] = (e[v] || 0) + 1;
      }
    }
    const unresolved = pop.filter((w) => w.terms.some((x) => x !== "unknown") && !w.term_iris.length).length;
    let rows = [...T.values()].filter((e) => words.every((t) => fold(e.short).includes(t)));
    const k = sort.replace(/^-/, ""), desc = sort.startsWith("-");
    rows.sort((a, b) => {
      const x = k === "term" ? a.short : a[k] || 0, y = k === "term" ? b.short : b[k] || 0;
      const c = x < y ? -1 : x > y ? 1 : 0;
      return (desc ? -c : c) || a.short.localeCompare(b.short);
    });
    const cols = [["term", "Term"], ["total", "Works"], ...VERSIONS.map((v) => [v, v]), [NONE, "no version coded"]];
    $("#thead").innerHTML = cols.map(([c, label]) => {
      const aria = sort === c ? "ascending" : sort === "-" + c ? "descending" : "none";
      return `<th scope="col" class="${c === "term" ? "" : "num"}" aria-sort="${aria}"><button type="button" class="sort" data-sort="${esc(c)}"${defAttrs("version", c)}>${esc(label)}</button></th>`;
    }).join("");
    const base = users ? Object.entries(USERS).map(([a, b]) => `&${a}=${encodeURIComponent(b).replace(/%7C/g, "|")}`).join("") : "";
    const link = (e, v, n) => {
      if (!n) return '<span class="muted">·</span>';
      const ver = v ? `&version_used=${encodeURIComponent(v)}` : "";
      return `<a href="#/works?term=${encodeURIComponent(e.iri)}${base}${ver}">${fmt(n)}</a>`;
    };
    $("#tbody").innerHTML = rows.map((e) => `<tr><td><a href="#/works?term=${encodeURIComponent(e.iri)}${base}"><code>${esc(e.short)}</code></a></td>
      <td class="num"><strong>${link(e, null, e.total)}</strong></td>${VERSIONS.map((v) => `<td class="num">${link(e, v, e[v])}</td>`).join("")}<td class="num">${link(e, NONE, e[NONE])}</td></tr>`).join("");
    $("#tcount").textContent = `${fmt(rows.length)} terms, ${fmt(pop.length)} works`;
    $("#tnote").textContent = unresolved ? `${unresolved} of these works name terms that could not be resolved to a SOSA/SSN IRI (unknown prefix): see their work pages.` : "";
  }
  $("#thead").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-sort]");
    if (!b) return;
    const c = b.dataset.sort;
    sort = sort === "-" + c ? c : sort === c ? "-" + c : (c === "term" ? c : "-" + c);
    render();
  });
  $("#tpop").addEventListener("change", render);
  let timer = null;
  $("#tq").addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(render, 150); });
  render();
}

/* ---------- SPARQL ---------- */
// the prefixes shown in the results: those of meta.json ("slr" first: its namespace is inside "kg")
let PFX = [];
function setPrefixes(prefixes) {
  PREFIXES = prefixBlock(prefixes);
  const keep = ["slr", "kg", "fabio", "cito", "mod", "xsd", "dcterms", "dcat", "prov", "oa", "rdfs", "owl"];
  PFX = [...keep.filter((p) => prefixes[p]).map((p) => [p + ":", prefixes[p]]), ...NS];
}
function term(t) {
  if (!t) return "";
  if (t.type === "uri") {
    const id = idFromIri(t.value);
    const w = id && S.byId.get(id);
    if (w) return `<a href="${workHref(id)}" title="${esc(t.value)}">${esc(w.title || id)}</a>`;
    for (const [p, ns] of PFX) if (t.value.startsWith(ns)) return /^https?:/.test(t.value) && !["slr:", "kg:", "xsd:"].includes(p) ? `<a href="${esc(t.value)}" rel="noopener"><code>${esc(p + t.value.slice(ns.length))}</code></a>` : `<code>${esc(p + t.value.slice(ns.length))}</code>`;
    return /^https?:/.test(t.value) ? `<a href="${esc(t.value)}" rel="noopener">${esc(t.value)}</a>` : esc(t.value);
  }
  if (t.type === "bnode") return `<code>_:${esc(t.value)}</code>`;
  const dt = t.datatype && !/#(string|integer)$/.test(t.datatype) ? ` <span class="lit-meta">^^${esc(t.datatype.replace("http://www.w3.org/2001/XMLSchema#", "xsd:"))}</span>` : "";
  const lang = t["xml:lang"] ? ` <span class="lit-meta">@${esc(t["xml:lang"])}</span>` : "";
  return esc(t.value) + dt + lang;
}

/* ---------- footer ---------- */
function footer() {
  const el = $("#site-footer");
  if (!el) return;
  const d = S.meta.date || (S.meta.generated || "").slice(0, 10);
  const when = d ? new Date(d + "T12:00:00Z").toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" }) : "";
  el.innerHTML = `<p>${when ? `Data of ${esc(when)}. ` : ""}Licence <a rel="license" href="${esc(S.meta.license || "https://creativecommons.org/licenses/by/4.0/")}">${esc(S.meta.license_name || "CC BY 4.0")}</a>.</p>`;
}

/* ---------- methodology and glossary ---------- */
function viewMethodology(main, r) {
  document.title = "Methodology · " + TITLE;
  const W = S.works;
  const count = (f) => W.filter(f).length;
  const st = (x) => count((w) => w.stratum === x);
  const coded = count((w) => w.engagement !== null);
  const byOpus = count((w) => w.coded_by === "claude-opus-5-5");
  const full = count((w) => w.fulltext);
  const fullCoded = count((w) => w.engagement !== null && w.basis === "full text");
  const seeds = (S.glossary.find((g) => g.id === "seeds") || { entries: [] }).entries;
  const P = (S.facts && S.facts.patterns) || {};
  const decided = S.facts && S.facts.decision_all_terms_in_sosa;
  const toc = S.glossary.map((g) => `<li><a href="${glossHref(g.id)}">${esc(g.title)}</a></li>`).join("");
  main.innerHTML = `
  <h1>Methodology</h1>
  <div class="prose method">
  <p>How the observatory is built, in short. The counts below are computed in your browser from the data; every code has
  its entry in the <a href="#/methodology?g=glossary">glossary</a>.</p>
  <h2 id="m-seeds">1. Seeds</h2>
  <p>The observatory starts from <em>seeds</em>: the publications on SOSA/SSN whose citing works it collects. Each has a
  role: <strong>core</strong> (the publications that describe SOSA/SSN, 2017 and later), <strong>lineage</strong> (the
  earlier SSN of the W3C Incubator Group, its design pattern, and the ontology for observations and sampling features
  whose sampling part became SOSA's), or <strong>variant</strong> (another record of a core publication). Two more,
  the <em>text seeds</em>, are W3C documents that no citation index holds: the Extensions to SSN and the drafts of the
  2023 Edition; their citing works are found by their titles, URLs and namespaces in the full texts.</p>
  <ul class="seeds">${seeds.map((e) => `<li>${codeLink("seeds", e.code)}: ${esc(e.def)}</li>`).join("")}</ul>
  <h2 id="m-sources">2. Sources</h2>
  <p><strong>OpenAlex</strong> gives the works that cite a seed and their bibliographic records, and its full-text
  search finds works that write SOSA/SSN names and namespaces. <strong>Semantic Scholar</strong> gives its own list of
  the works that cite the seeds, compared with OpenAlex's, and completes the records. <strong>S2ORC</strong>, the corpus
  of open-access full texts of Semantic Scholar, is scanned for the texts of the candidates and for SOSA/SSN names; the
  <strong>open-access PDFs</strong> that OpenAlex locates give the other full texts.</p>
  <h2 id="m-strata">3. Strata A to D</h2>
  <p>Each candidate work is in one <a href="${glossHref("strata")}">stratum</a>:
  ${["A", "B", "C", "D"].map((x) => `${codeLink("strata", x, x, `st st-${x}`)} ${esc(def("strata", x) || "")} (<a href="#/works?stratum=${x}">${fmt(st(x))} works</a>)`).join("; ")}.</p>
  <h2 id="m-texts">4. Full texts</h2>
  <p>The full text of <a href="#/works?fulltext=yes">${fmt(full)} works</a> is held, from S2ORC or from an open-access
  PDF. Its bibliography is cut before coding, so that a citation alone is not read as a use of SOSA/SSN.</p>
  <h2 id="m-coding">5. Coding by a language model</h2>
  <p>A language model reads each work of strata A, B and D (its full text, or its abstract when no full text could be
  obtained) and answers the questions of a codebook (<code>slr/protocol/codebook.md</code>, in machine form
  <code>codebook.toml</code>), with the instructions of <code>slr/protocol/model-prompt.md</code>:
  <a href="${glossHref("engagement")}">engagement</a> E0 to E5, <a href="${glossHref("version")}">version used</a>,
  <a href="${glossHref("modules")}">modules</a>, terms, extensions, <a href="${glossHref("result_pattern")}">result patterns</a>,
  <a href="${glossHref("value_properties")}">value properties</a>, <a href="${glossHref("errors")}">errors</a>,
  <a href="${glossHref("domain")}">domain</a>, companion vocabularies, artefacts and gaps. Each answer comes with up to three
  quotations copied exactly from the text, which a script checks against it, and a short justification.
  Claude Sonnet 5.5 coded every work; Claude Opus 5.5 coded a subset, and where it did, its answers are used
  (${fmt(byOpus)} of the ${fmt(coded)} coded works; ${fmt(fullCoded)} were coded from the full text).</p>
  <h2 id="m-patterns">6. Modelling patterns</h2>
  <p>Where SOSA/SSN leaves a modelling choice open (generic or feature-specific properties, systems as individuals or as
  types, simple literals or quantity values…), a second codebook (<code>slr/protocol/patterns-codebook.md</code>) asks
  which choice the work makes. Claude Opus 5.5 agents code it from <em>excerpts</em> of the full texts, the passages
  around the SOSA/SSN names, for the works that use SOSA/SSN or write its names${P.coded ? ` (${fmt(P.coded)} works)` : ""};
  a choice the excerpts do not show is <code>not-shown</code>. Each answer quotes the excerpts${P.quotes ? `, and a script
  found ${fmt(P.quotes_found)} of the ${fmt(P.quotes)} quotations in them` : ""}. A second, independent coder coded
  ${P.second_coder_works ? `${fmt(P.second_coder_works)} works drawn at random` : "a sample"}; the agreement
  ${P.kappa_min != null ? `(Cohen's kappa from ${P.kappa_min} to ${P.kappa_max} across the ${P.questions} questions)` : ""} is in
  <code>slr/results/pattern-coding.md</code>.</p>
  <h2 id="m-scripts">7. Readings by script</h2>
  <p>Scripts read the full texts for what a rule can decide (<code>slr/scripts/usage_patterns.py</code>): each prefixed
  name of SOSA/SSN a text writes is put in a <a href="${glossHref("names")}">name class</a>, from the terms of each version,
  the namespaces the work declares, and the dates at which terms entered the <code>sosa:</code> namespace
  (<code>slr/protocol/namespace-history.toml</code>${decided ? `; the Working Group decided on ${esc(decided)} that every term goes into <code>sosa:</code>` : ""});
  each value of <code>sosa:hasSimpleResult</code> a text writes gets a <a href="${glossHref("simple_forms")}">form</a> (its
  datatype, a plain string, a bare number, a query variable). These count what the text shows: a work that uses a
  datatype without printing it is not counted.</p>
  <h2 id="m-graph">8. The knowledge graph</h2>
  <p>Everything is published as a knowledge graph (<a href="${DATA}kg.ttl.gz" download>kg.ttl.gz</a>, Turtle): works
  (FaBiO, with their OpenAlex or Semantic Scholar IRIs), citations (CiTO), the versions of SOSA/SSN and the artefacts the
  works publish (MOD), each code with the agent it is attributed to (PROV-O) and its quotations (Web Annotation), under
  the licence <a href="${esc(S.meta.license || "")}">${esc(S.meta.license_name || "")}</a>. It can be queried in
  <a href="#/sparql">SPARQL</a> or explored with Sparklis, both in the browser (<a href="#/sparql">SPARQL</a> page):
  <a href="https://github.com/oxigraph/oxigraph" rel="noopener">Oxigraph</a> compiled to WebAssembly answers the queries, and
  <a href="https://github.com/sebferre/sparklis" rel="noopener">Sparklis</a> (Sébastien Ferré, Apache 2.0; Ferré,
  <em>Semantic Web</em> 8(3), 2017) builds them in natural language.
  ${S.meta.quotations === false ? "This version leaves out the quotations of the works." : ""}</p>
  </div>
  <h2 id="g-glossary">Glossary</h2>
  <nav class="toc" aria-label="Glossary sections"><ul>${toc}</ul></nav>
  <div class="glossary">${S.glossary.map((g) => `
    <section id="${glossId(g.id)}" aria-labelledby="${glossId(g.id)}-h"><h3 id="${glossId(g.id)}-h">${esc(g.title)}</h3>
    <p class="muted small">${esc(g.intro || "")}</p>
    <dl class="gloss">${g.entries.map((e) => `<dt id="${glossId(g.id, e.code)}"><code>${esc(e.code)}</code></dt><dd>${esc(e.def)}</dd>`).join("")}</dl></section>`).join("")}
  </div>`;
  function update(rr) {
    const g = rr.params.get("g");
    for (const el of $$(".gloss dt.hl, .gloss dd.hl", main)) el.classList.remove("hl");
    if (!g) return;
    const i = g.indexOf(":");
    const el = g === "glossary" ? $("#g-glossary") : document.getElementById(i < 0 ? glossId(g) : glossId(g.slice(0, i), g.slice(i + 1)));
    if (!el) return;
    if (el.tagName === "DT") { el.classList.add("hl"); el.nextElementSibling.classList.add("hl"); }
    requestAnimationFrame(() => el.scrollIntoView({ block: i < 0 ? "start" : "center" }));
  }
  update(r);
  return { update };
}

/* ---------- Sparklis ---------- */
// Sparklis (sparklis/, vendored) in a frame, on the in-browser SPARQL endpoint ./sparql: the
// service worker sw.js answers it (or, without one, sparklis/endpoint.js in the frame)
async function endpointReady() {
  const sw = navigator.serviceWorker;
  if (!sw || !window.isSecureContext) return "page";
  try {
    const reg = await sw.register("sw.js", { type: "module", scope: "./" });
    await Promise.race([sw.ready, new Promise((res) => setTimeout(res, 8000))]);
    if (!reg.active) return "page";
    if (!sw.controller) {   // the first visit: the worker takes this page at activation
      await Promise.race([new Promise((res) => sw.addEventListener("controllerchange", res, { once: true })), new Promise((res) => setTimeout(res, 3000))]);
    }
    return "service worker";
  } catch (e) {
    console.warn("No service worker for the SPARQL endpoint:", e);
    return "page";
  }
}
function sparklisUrl() {
  const endpoint = new URL("sparql", location.href.split("#")[0]).href;
  const p = new URLSearchParams({
    title: TITLE, endpoint, proxy_url: "", proxy: "false", logging: "false", "short-permalink": "false", lang: "en",
    entity_lexicon_select: "http://www.w3.org/2000/01/rdf-schema#label",
    concept_lexicons_select: "http://www.w3.org/2000/01/rdf-schema#label",
  });
  return "sparklis/osparklis.html?" + p.toString();
}
// The one query page (Maxime, 2026-11-14: the SPARQL and Sparklis tabs merged, since Sparklis
// has a YASGUI view): Sparklis in a frame, with its Sparklis, YASGUI and History views; the
// examples of examples.js, and the queries that other pages link to (#/sparql?query=… or
// ?ex=n), open in its YASGUI view and run there.
function viewSparql(main, r) {
  document.title = "SPARQL · " + TITLE;
  const p = r.params;
  const ex = +(p.get("ex") || 0);
  const given = p.get("query") || (ex >= 1 && ex <= EXAMPLES.length ? PREFIXES + "\n" + EXAMPLES[ex - 1].query : "");
  main.innerHTML = `
  <h1>SPARQL</h1>
  <div class="prose">
  <p>The knowledge graph of the observatory, explored with <a href="https://github.com/sebferre/sparklis" rel="noopener">Sparklis</a>,
  a query builder in natural language, or queried in SPARQL in its YASGUI view. Both run in your browser, on
  <a href="https://github.com/oxigraph/oxigraph" rel="noopener">Oxigraph</a> compiled to WebAssembly: loading the graph takes a
  few seconds, and no query leaves your browser. Works are FaBiO expressions with their OpenAlex or Semantic Scholar IRI;
  each code is an <code>slr:Coding</code> or <code>slr:PatternCoding</code> with <code>slr:about</code>, <code>slr:question</code>,
  <code>slr:value</code> and <code>prov:wasAttributedTo</code>${S.meta.quotations === false ? "" : ", and <code>slr:evidence</code> → <code>oa:exact</code> quotations"};
  the citation of SOSA/SSN is a <code>cito:Citation</code>.</p>
  <p>Download: <a href="${DATA}kg.ttl.gz" download>kg.ttl.gz</a> (the graph, Turtle, gzip) ·
  <a href="${DATA}works.json" download>works.json</a> (the works and their codes) ·
  <a href="${DATA}figures.json" download>figures.json</a> (the key figures) ·
  <a href="${DATA}method.json" download>method.json</a> (the glossary) — licence
  <a href="${esc(S.meta.license || "")}">${esc(S.meta.license_name || "")}</a>.</p>
  </div>
  <div class="sparql-bar">
    <label for="ex">Example queries</label>
    <select id="ex"><option value="0">Choose an example: it opens in the SPARQL editor (YASGUI) and runs</option>
      ${EXAMPLES.map((e, i) => `<option value="${i + 1}" ${!p.get("query") && i + 1 === ex ? "selected" : ""}>${i + 1}. ${esc(e.title)}</option>`).join("")}</select>
    <span class="sparklis-status muted small" id="sparklis-status" role="status">Loading the knowledge graph in your browser…</span>
  </div>
  <div class="sparklis-frame" id="sparklis-box"></div>`;
  let frame = null;
  endpointReady().then(() => {
    const box = $("#sparklis-box");
    if (!box) return;
    frame = document.createElement("iframe");
    frame.title = "Sparklis and YASGUI, on the knowledge graph of the observatory";
    frame.src = sparklisUrl();
    frame.addEventListener("load", () => {
      fitFrame(frame);
      const st = $("#sparklis-status");
      if (st) st.textContent = "";
      if (given) openInYasgui(given);
    }, { once: true });
    box.append(frame);
  });
  $("#ex").addEventListener("change", (e) => {
    const i = +e.target.value;
    if (!i) return;
    replaceHash("#/sparql?ex=" + i);
    openInYasgui(PREFIXES + "\n" + EXAMPLES[i - 1].query);
  });
  // the frame as tall as the Sparklis page, which then never scrolls by itself: the page of the
  // observatory scrolls, down to the footers (Maxime, 2026-11-14: the inner scroll of the frame
  // went back up to the query and the footer could not be reached)
  function fitFrame(f) {
    const doc = f.contentDocument;
    if (!doc || !doc.body) return;
    doc.documentElement.style.overflow = "hidden";
    // the height of the content (not of the frame's viewport, which would never let it shrink)
    const fit = () => {
      const b = doc.body, cs = doc.defaultView.getComputedStyle(b);
      f.style.height = Math.ceil(b.getBoundingClientRect().height + parseFloat(cs.marginTop) + parseFloat(cs.marginBottom)) + "px";
    };
    new ResizeObserver(fit).observe(doc.body);
    fit();
  }
  // the YASQE editor of Sparklis's YASGUI view is a CodeMirror instance (same origin)
  async function openInYasgui(query) {
    if (!frame) return;
    const doc = frame.contentDocument;
    if (!doc) return;
    const button = doc.getElementById("button-yasgui-view");
    if (button) button.click();
    for (let k = 0; k < 60; k++) {
      const el = doc.querySelector("#sparklis-yasgui .CodeMirror");
      if (el && el.CodeMirror && typeof el.CodeMirror.query === "function") {
        el.CodeMirror.setValue(query);
        el.CodeMirror.query();
        return;
      }
      await new Promise((res) => setTimeout(res, 250));
    }
    const st = $("#sparklis-status");
    if (st) st.textContent = "The SPARQL editor did not start: reload the page.";
  }
}

/* ---------- start ---------- */
async function start() {
  try {
    const get = (name) => fetch(DATA + name).then((r) => { if (!r.ok) throw new Error(name + ": HTTP " + r.status); return r.json(); });
    const [wj, fj, meta, method] = await Promise.all([get("works.json"), get("figures.json"), get("meta.json"), get("method.json")]);
    S.works = wj.works;
    S.meta = meta;
    if (!meta.prefixes) throw new Error("meta.json gives no prefixes: rebuild the data (scripts/build_kg.py).");
    setPrefixes(meta.prefixes);
    S.glossary = method.glossary || [];
    S.facts = method.facts || {};
    for (const g of S.glossary) S.gloss.set(g.id, new Map(g.entries.map((e) => [String(e.code), e.def])));
    installDefs();
    footer();
    S.facets = facetDefs();
    const byText = new Map();
    let lo = Infinity, hi = -Infinity;
    for (const w of S.works) {
      S.byId.set(w.id, w);
      if (w.text_item) byText.set(w.text_item, w.id);
      w.term_iris = w.term_iris || [];
      w._text = fold([w.title, w.authors.join(" "), w.venue, w.publisher, w.doi].join(" "));
      w._f = {};
      for (const f of S.facets) w._f[f.key] = f.get(w);
      if (w.year) { lo = Math.min(lo, w.year); hi = Math.max(hi, w.year); }
    }
    S.years = [lo, hi];
    for (const f of S.facets) {
      f.total = new Map();
      for (const w of S.works) for (const v of w._f[f.key]) f.total.set(v, (f.total.get(v) || 0) + 1);
      f.universe = [...f.total.keys()];
    }
    S.figures = fj.figures;
    for (const f of S.figures) {
      S.figByKey.set(f.key, f);
      if (f.filter) f.set = new Set(S.works.filter((w) => matches(w, f.filter)).map((w) => w.id));
      else if (f.works) f.set = new Set(f.works.map((i) => (S.byId.has(i) ? i : byText.get(i))).filter(Boolean));
      if (f.set) {
        f.n = f.set.size;
        const printed = printedCount(f.value);
        f.ok = printed === null ? null : printed === f.n;
        if (f.works && f.set.size !== new Set(f.works).size) f.unresolved = new Set(f.works).size - f.set.size;
      }
    }
  } catch (e) {
    $("#main").innerHTML = `<h1>The data could not be loaded</h1><p class="status err">${esc(e.message)}</p>
      <p>Serve this folder over HTTP (for instance <code>python3 -m http.server</code>) rather than opening the file directly.</p>`;
    return;
  }
  const bar = $("header.top");
  const measure = () => document.documentElement.style.setProperty("--header-h", Math.ceil(bar.getBoundingClientRect().height) + "px");
  if (window.ResizeObserver) new ResizeObserver(measure).observe(bar);
  measure();
  window.addEventListener("hashchange", route);
  route();
}
start();
