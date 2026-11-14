// The knowledge graph in a worker: Oxigraph (WebAssembly) loads kg.ttl.gz and answers SPARQL
// queries, so that neither the loading nor a long query freezes the page.
// Oxigraph 0.5.13 (npm, published 2026-10-22), web build from jsDelivr.
//
// Two uses: a module worker of the application and of the Sparklis page (messages "load" and
// "query"), and a module imported by the service worker sw.js (the in-browser SPARQL endpoint),
// which calls loadStore() and runQuery() itself.
import init, * as oxigraph from "https://cdn.jsdelivr.net/npm/oxigraph@0.5.13/web.js";

const RESULTS = {
  json: "application/sparql-results+json", xml: "application/sparql-results+xml",
  csv: "text/csv", tsv: "text/tab-separated-values",
};
const GRAPHS = { turtle: "text/turtle", ntriples: "application/n-triples", rdfxml: "application/rdf+xml" };

// the query form, after the prologue (PREFIX/BASE) and comments
export function queryForm(q) {
  const body = q.replace(/#[^\n]*/g, " ").replace(/\b(PREFIX|BASE)\s+[^<]*<[^>]*>/gi, " ");
  const m = body.match(/\b(SELECT|ASK|CONSTRUCT|DESCRIBE|INSERT|DELETE|LOAD|CLEAR|DROP|CREATE|ADD|MOVE|COPY|WITH)\b/i);
  return m ? m[1].toUpperCase() : "SELECT";
}
export const isUpdate = (form) => !["SELECT", "ASK", "CONSTRUCT", "DESCRIBE"].includes(form);

// Fetches kg.ttl.gz, decompresses it and loads it into a new store.
export async function loadStore(url, say = () => {}) {
  say("engine");
  await init();
  say("download", { received: 0 });
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  const total = Number(res.headers.get("content-length")) || 0;
  const reader = res.body.getReader();
  const chunks = [];
  let received = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    received += value.length;
    say("download", { received, total });
  }
  const bytes = new Uint8Array(received);
  let off = 0;
  for (const c of chunks) { bytes.set(c, off); off += c.length; }
  say("decompress");
  // a server may already have decoded the gzip (Content-Encoding): look at the magic number
  let text;
  if (bytes[0] === 0x1f && bytes[1] === 0x8b) {
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
    text = await new Response(stream).text();
  } else {
    text = new TextDecoder().decode(bytes);
  }
  say("parse", { size: text.length });
  const t0 = performance.now();
  const store = new oxigraph.Store();
  store.load(text, { format: "text/turtle" });
  return { store, triples: store.size, ms: Math.round(performance.now() - t0) };
}

// Runs a read-only query; `format` is a key of RESULTS (SELECT, ASK) or of GRAPHS (CONSTRUCT,
// DESCRIBE), or a media type. Returns {form, type, text}.
export function runQuery(store, query, format) {
  const form = queryForm(query);
  if (isUpdate(form)) throw new Error("This knowledge graph is read only: SPARQL updates are not accepted.");
  const graph = form === "CONSTRUCT" || form === "DESCRIBE";
  const table = graph ? GRAPHS : RESULTS;
  const type = table[format] || (Object.values(table).includes(format) ? format : Object.values(table)[0]);
  return { form, type, text: store.query(query, { results_format: type }) };
}

let store = null;
let loading = null;

// the protocol of the module worker (not in the service worker, which has its own messages)
const inServiceWorker = typeof ServiceWorkerGlobalScope !== "undefined" && self instanceof ServiceWorkerGlobalScope;
if (!inServiceWorker) {
  const say = (stage, detail = {}) => postMessage({ type: "progress", stage, ...detail });
  onmessage = async (e) => {
    const msg = e.data;
    try {
      if (msg.type === "load") {
        if (!loading) loading = loadStore(msg.url, say).then((r) => { store = r.store; return r; });
        const { triples, ms } = await loading;
        postMessage({ type: "ready", id: msg.id, triples, ms });
      } else if (msg.type === "query") {
        if (!store) await loading;
        const t0 = performance.now();
        if (msg.format) {   // a raw result in a given format (the Sparklis page)
          const r = runQuery(store, msg.query, msg.format);
          postMessage({ type: "result", id: msg.id, ...r, ms: Math.round(performance.now() - t0) });
          return;
        }
        const r = runQuery(store, msg.query, "json");
        const ms = Math.round(performance.now() - t0);
        if (r.form === "CONSTRUCT" || r.form === "DESCRIBE") postMessage({ type: "result", id: msg.id, form: r.form, turtle: r.text, ms });
        else postMessage({ type: "result", id: msg.id, form: r.form, json: JSON.parse(r.text), ms });
      }
    } catch (err) {
      if (msg.type === "load") loading = null;
      postMessage({ type: "error", id: msg.id, message: String(err && err.message ? err.message : err) });
    }
  };
}
