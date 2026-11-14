# Changelog

One entry per release; each release has its own DOI. The date of a release is the date of
its data (`explorer/data/meta.json`).

## 1.0.0 — 2026-11-14

First release.

- The works that cite a publication on SOSA/SSN (strata A to C, OpenAlex harvest of
  2026-11-07) or write its names in their full text (stratum D), with their codes: Claude
  Opus 5.5 where it coded the work, Claude Sonnet 5.5 otherwise; the modelling patterns by
  Claude Opus 5.5 agents, with a second agent coder on a sample; names, namespaces and
  simple results by script.
- The knowledge graph (`explorer/data/kg.ttl.gz`) and the data of the web application, without
  the quotations of the works.
- The web application, with SPARQL and Sparklis in the browser, and its container.
- The monthly watch of new works (`scripts/observatory_watch.py`; first run 2026-11-14).
