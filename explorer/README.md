# SOSA/SSN Usage Observatory

A static web application on the use of the W3C/OGC SOSA/SSN ontology: every work that cites a
publication on SOSA/SSN or writes its names, with its codes; the key figures, recomputed in
the browser; the methodology and the glossary of every code; and the knowledge graph, in a
SPARQL editor and in Sparklis. It only reads published data. It is not the screening
application (`../app/`, login-protected).

The codes are made by a language model on a codebook (Claude Sonnet 5.5 coded every work;
Claude Opus 5.5 coded a subset, and where it did, its answers are used); the modelling
patterns by Claude Opus 5.5 agents from excerpts; the name classes and simple-result forms by
script. Each code says who made it (`coded_by`, `prov:wasAttributedTo`).

## Views

| Address | Content |
|---|---|
| `#/` | overview: counts by stratum and year, engagement, data downloads |
| `#/works?…` | the works, with facets, text search, sorting, CSV export; the filters are kept in the address (`stratum=A\|B`, `year=2018-2023`, `q=…`, `p.time=resultTime-literal`, `fig=<figure key>`, `term=<IRI>`, `sort=-year`). On a wide screen the facets and the results scroll apart, each with its own scrollbar; on a phone they are stacked |
| `#/work/<id>` | one work (`openalex:W…` or `s2orc:…`): metadata, codes, and the answers with their quotations, read from the knowledge graph |
| `#/figures?theme=<slug>` or `?open=<key>` | the key figures, by theme, each recomputed from `works.json` and linked to its works |
| `#/terms` | SOSA/SSN terms (resolved IRIs) by version used; all coded works or the works that use SOSA/SSN |
| `#/methodology?g=<group>:<code>` | how the observatory is built, then the glossary; `g=` scrolls to a group or a code and marks it |
| `#/sparql`, `?ex=<n>` or `?query=…` | Sparklis on the knowledge graph, with its YASGUI view (SPARQL editor) and history; the examples of `examples.js` and the queries other pages link to open in YASGUI and run; the frame takes the height of its content, so that the page scrolls as one (`#/sparklis` leads here) |

Any set of works of `figures.json` can be listed with `#/works?fig=<key>`, key figure or not
(e.g. `#/works?fig=hyp-users`); only the key figures are shown on the key figures page.

The menu bar stays at the top of the window. Every code shown (facets, tables, work pages, key
figures) has its definition as a tooltip (`title`) and as an accessible description
(`aria-describedby`, pointing to the hidden `#defs`), and, where it is a link, leads to its
glossary entry. The footer gives the date of the data and the licence, CC BY 4.0.

## Serving it

Any static HTTP server; from this folder:

```sh
python3 -m http.server 8795        # then http://127.0.0.1:8795/
```

Opening `index.html` as a file does not work (the data are fetched). Relative paths only: the
site works under any prefix (it is published under https://ci.mines-stetienne.fr/sosa-ssn-observatory/).
The SPARQL engine, Oxigraph 0.5.13 compiled to WebAssembly, is loaded from jsDelivr
(`https://cdn.jsdelivr.net/npm/oxigraph@0.5.13/web.js`, about 4 MB) only when a view needs it;
the browser needs `DecompressionStream` and module workers (current Chrome, Firefox, Safari).

## Data

`data/` is generated, never edited by hand:

```sh
cd slr && python3 -I scripts/build_kg.py                     # with the quotations
cd slr && python3 -I scripts/build_kg.py --public DIR        # without them (what is published)
```

- `data/works.json`: one record per candidate work (strata A to D), with the codes of the
  language model (`scripts/hypothetical_findings.py`), the modelling patterns
  (`scripts/pattern_coding.py`), the name classes and simple-result forms found by script
  (`scripts/usage_patterns.py`), the flag of questionable venues (`scripts/venue_risk.py`
  rules) and `term_iris`, the terms resolved to IRIs.
- `data/figures.json`: every figure of `results/macros.tex` and every set of works the scripts
  export, with the works behind it, as a list or as a filter on `works.json`
  (`{"all": [{"field", "eq"|"ne"|"in"|"has": value}]}`), which the application evaluates. The
  key figures carry `main: true`, `label`, `group`, `order`, and may carry `sub` (a heading in
  the group), `of` (the key of the figure the share is computed on) and `code` (`[glossary
  group, code]`). Their list is `key_figures()` of `build_kg.py`.
- `data/method.json`: the glossary (`glossary`: groups of `{code, def}`, from
  `protocol/codebook.toml`, `protocol/patterns-codebook.md`, `scripts/usage_patterns.py`,
  `protocol/namespace-history.toml`, `protocol/seeds.toml`) and the facts the methodology
  states (`facts`: agreement of the second coder of the patterns…). `build_kg.py` warns about a
  code of the data that has no definition.
- `data/meta.json`: date, licence (`license`, `license_name`), number of works and triples,
  whether the quotations are included, the base IRI of the graph (`base`) and its prefixes
  (`prefixes`). The application and the SPARQL examples take their prefixes from there.
- `data/kg.ttl.gz`: the knowledge graph (Turtle, gzip): FaBiO, CiTO, PRISM, FRBR, MOD, DCTERMS,
  DCAT (the dataset node `kg:dataset`, with `dcterms:license`), FOAF, PROV-O, Web Annotation
  (`oa:TextQuoteSelector`), and the observatory's `slr:` vocabulary. Works, terms, codes,
  persons, venues and every class and property used have an `rdfs:label` (for Sparklis); see
  the docstring of `scripts/build_kg.py`.

## The SPARQL endpoint in the browser, and Sparklis

`sparklis/` is Sparklis (https://github.com/sebferre/sparklis, Apache 2.0), vendored at commit
`8a2f573` (2025-06-20): see `sparklis/VENDOR.txt` for the files, their checksums and the
changes made to `osparklis.html`; `sparklis/observatory.js` fixes the endpoint and the
settings, `sparklis/observatory.css` hides the endpoint menu, the configuration and the YASGUI
tab, and the footer says "Served with Sparklis". Sparklis is a client of a SPARQL endpoint; the endpoint is
in the browser too:

- `sw.js`, a module service worker whose scope is the site, answers the requests to `./sparql`
  (SPARQL 1.1 Protocol: `GET ?query=`, `POST` form-encoded or `application/sparql-query`) by
  running the query with Oxigraph (it imports `kg-worker.js`, which loads `data/kg.ttl.gz`
  once). SELECT and ASK give SPARQL JSON, XML, CSV or TSV by the `Accept` header; CONSTRUCT and
  DESCRIBE give Turtle, N-Triples or RDF/XML; updates are refused (403). Sparklis sends
  `POST` with `Accept: application/sparql-results+xml` and reads `responseXML`. Every other
  request goes to the network; nothing is cached.
- `#/sparklis` registers the service worker, waits until it controls the page, then opens
  `sparklis/osparklis.html?endpoint=<site>/sparql&proxy_url=&proxy=false&logging=false&short-permalink=false`
  (no third-party proxy, no logging, no URL shortener; entity and class labels from
  `rdfs:label`). The Sparklis page (`sparklis/endpoint.js`) asks the worker to load the graph
  early and keeps it alive while it is open.
- Without a controlling service worker (a browser without module service workers, a private
  window, a forced reload), `sparklis/endpoint.js` answers the same requests in the page: it
  replaces `XMLHttpRequest` for that one URL and runs the queries in `kg-worker.js`.

A service worker needs a secure context: https, or `http://127.0.0.1` / `localhost`.

## Files

`index.html`, `style.css`, `app.js` (views and routing), `examples.js` (SPARQL examples),
`kg-worker.js` (Oxigraph, as a worker and as a module of `sw.js`), `sw.js` (the endpoint),
`sparklis/` (Sparklis and `endpoint.js`). Vanilla JavaScript, no build step, no dependency
other than Oxigraph (and, in the Sparklis page, the CDN libraries Sparklis loads).

## Tests (2026-11-14)

Served with `python3 -m http.server 8795`, in headless Chromium (Playwright, `~/.venvs/grr`):
the bar stays at the top while the facets and the results scroll apart; the 171 key figures
recomputed in the browser equal the values of `figures.json`; the glossary anchors and the
tooltips; a work page with its answers from the graph; the SPARQL examples; Sparklis lists the
classes of the graph and runs a query through the service worker, and through
`sparklis/endpoint.js` with service workers blocked; the endpoint answers GET and POST in JSON,
CSV and Turtle and refuses updates; no horizontal scroll at 390 px. Then the same on the public
build. Firefox was not tested (no Playwright Firefox on this machine).

## The public version and its deployment

`make public` writes `build/public/`: the application, `sw.js` and `sparklis/`, and the data
built by `scripts/build_kg.py --public`, which leaves out the quotations of the works
(`data/meta.json` says so, and the work pages show a note). `make deploy` sends it to
ci.mines-stetienne.fr (see the `Makefile` and `deploy/`). Its regular update:
`../observatory/README.md`.
