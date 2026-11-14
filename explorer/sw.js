// The in-browser SPARQL endpoint of the observatory: a module service worker whose scope is the
// site. It answers the requests to ./sparql (SPARQL 1.1 Protocol: GET ?query=, POST
// application/x-www-form-urlencoded or application/sparql-query) by running the query with
// Oxigraph on data/kg.ttl.gz, loaded once (kg-worker.js), and leaves every other request to the
// network. Results: SPARQL JSON (default), XML, CSV or TSV for SELECT and ASK, chosen by the
// Accept header; Turtle, N-Triples or RDF/XML for CONSTRUCT and DESCRIBE. Read only.
// Sparklis (sparklis/) uses it with POST and Accept: application/sparql-results+xml.
import { loadStore, runQuery, queryForm, isUpdate } from "./kg-worker.js";

const SCOPE = new URL(self.registration.scope);
const ENDPOINT = new URL("sparql", SCOPE).pathname;
const GRAPH = new URL("data/kg.ttl.gz", SCOPE).href;
let loading = null;

const store = () => {
  if (!loading) loading = loadStore(GRAPH).catch((e) => { loading = null; throw e; });
  return loading.then((r) => r.store);
};

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));
// the Sparklis page sends "warm" when it opens and "keepalive" while it is open, so that the
// graph is loaded early and the worker is not stopped (and the graph lost) between two clicks
self.addEventListener("message", (e) => {
  if (e.data && e.data.type === "warm") e.waitUntil(store().catch(() => {}));
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (url.origin !== SCOPE.origin || url.pathname !== ENDPOINT) return;
  e.respondWith(answer(e.request, url));
});

const HEADERS = { "Access-Control-Allow-Origin": "*", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" };
const reply = (status, body, type) => new Response(body, { status, headers: { ...HEADERS, "Content-Type": type + "; charset=utf-8" } });

// the first media type of the Accept header (by quality) that the query form can give
function negotiate(accept, graph) {
  const offers = graph
    ? { "text/turtle": "turtle", "application/x-turtle": "turtle", "application/n-triples": "ntriples", "text/plain": "ntriples", "application/rdf+xml": "rdfxml" }
    : { "application/sparql-results+json": "json", "application/json": "json", "application/sparql-results+xml": "xml",
        "application/xml": "xml", "text/xml": "xml", "text/csv": "csv", "text/tab-separated-values": "tsv" };
  const ranges = (accept || "").split(",").map((part, i) => {
    const [type, ...params] = part.trim().toLowerCase().split(";");
    const q = params.map((p) => p.trim()).find((p) => p.startsWith("q="));
    return { type: type.trim(), q: q ? Number(q.slice(2)) : 1, i };
  }).filter((r) => r.type && r.q > 0).sort((a, b) => b.q - a.q || a.i - b.i);
  for (const r of ranges) if (offers[r.type]) return offers[r.type];
  return graph ? "turtle" : "json";
}

async function answer(request, url) {
  try {
    let query = null;
    if (request.method === "GET" || request.method === "HEAD") {
      query = url.searchParams.get("query");
    } else if (request.method === "POST") {
      const type = (request.headers.get("content-type") || "").toLowerCase();
      const body = await request.text();
      if (type.startsWith("application/sparql-query")) query = body;
      else if (type.startsWith("application/sparql-update") || new URLSearchParams(body).has("update")) {
        return reply(403, "This knowledge graph is read only: SPARQL updates are not accepted.\n", "text/plain");
      } else query = new URLSearchParams(body).get("query");
    } else if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: { ...HEADERS, Allow: "GET, POST, OPTIONS", "Access-Control-Allow-Methods": "GET, POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type, Accept" } });
    } else {
      return reply(405, "Method not allowed: use GET or POST.\n", "text/plain");
    }
    if (!query) {
      return reply(400, "The SPARQL endpoint of the SOSA/SSN Usage Observatory, in your browser: send a query with ?query= or POST.\n", "text/plain");
    }
    const form = queryForm(query);
    if (isUpdate(form)) return reply(403, "This knowledge graph is read only: SPARQL updates are not accepted.\n", "text/plain");
    const s = await store();
    const r = runQuery(s, query, negotiate(request.headers.get("accept"), form === "CONSTRUCT" || form === "DESCRIBE"));
    return reply(200, request.method === "HEAD" ? null : r.text, r.type);
  } catch (err) {
    const msg = String(err && err.message ? err.message : err);
    // a syntax error or an unsupported feature is the client's: 400; a failed load is ours: 500
    return reply(/HTTP \d|fetch|WebAssembly|wasm/i.test(msg) ? 500 : 400, msg + "\n", "text/plain");
  }
}
