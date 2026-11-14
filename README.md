# SOSA/SSN Usage Observatory

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24223888.svg)](https://doi.org/10.5281/zenodo.24223888)

An observatory of how the W3C/OGC Semantic Sensor Network ontology (SSN) and its core, SOSA,
are used in the scientific literature. It covers every work that cites a publication on
SOSA/SSN, and every work whose full text writes SOSA/SSN names or namespaces. For each work it
records how the work relates to SOSA/SSN: how deeply it engages with the ontology, the version
and modules it uses, the terms, how it represents results and values, the errors it makes
with names and namespaces, its domain, the vocabularies it uses alongside, the artefacts it
publishes, the gaps it reports, and its modelling choices (property and system individuals,
punning, result form, units, time, hosting, location, grouping…).

- **Web application**: https://ci.mines-stetienne.fr/sosa-ssn-observatory/ (works with facets,
  key figures recomputed in the browser, methodology and glossary, SPARQL and Sparklis on the
  knowledge graph, all in the browser)
- **Persistent identifier**: https://w3id.org/sosa-ssn-observatory
- **Repository**: https://github.com/maximelefrancois86/sosa-ssn-observatory
- **DOI**: [10.5281/zenodo.24223888](https://doi.org/10.5281/zenodo.24223888) (all releases; each release has its own DOI on Zenodo)
- **Maintainer**: Maxime Lefrançois, Mines Saint-Étienne
  ([ORCID 0000-0001-9814-8991](https://orcid.org/0000-0001-9814-8991))

This repository holds the code, the instructions to rebuild the observatory, and its data:
the knowledge graph, the data of the web application, and the harvests, codes and figures
it is built from. **It holds no full text**: no PDF, no text extracted from a work, and no
quotation of a work (see [What is not here](#what-is-not-here)).

## This release

Data of 2026-11-14, release 1.0.0:

| | |
|---|---|
| works | 3,067 (A: 940, B: 653, C: 816, D: 658) |
| works with a full text (used for the coding, not distributed) | 1,492 |
| works coded by a language model | 1,493 (1,345 from the full text, 148 from the abstract only) |
| triples of the public knowledge graph | 205,715 |

The figures above are computed from `explorer/data/works.json` and `explorer/data/meta.json`
by the export script that produced this release.

**What the codes are.** The codes are made by language models, by agents and by scripts, on
a codebook fixed before coding; each code says who made it (`coded_by` in `works.json`,
`prov:wasAttributedTo` in the graph). For each work, the codes are those of Claude Opus 5.5
where it coded the work, otherwise those of Claude Sonnet 5.5, which coded every work. The
modelling patterns are coded by Claude Opus 5.5 agents from excerpts of the full texts, with
a second, independent agent coder on a sample (the agreement is in
`results/pattern-coding.json`). Names, namespaces and simple results are read by script. No
person has checked the codes yet: they are recommendations, to be used as such.

### Strata

| stratum | the work… |
|---|---|
| A | cites a publication on SOSA/SSN of 2017 or later (a core seed) |
| B | cites only the earlier SSN publications (lineage seeds), published in 2018 or later |
| C | cites only the earlier SSN publications, published before 2018 (not coded) |
| D | cites no seed: found by the SOSA/SSN names and namespaces in its full text |

The seeds are in `protocol/seeds.toml`; the codebooks in `protocol/codebook.toml`,
`protocol/codebook.md` and `protocol/patterns-codebook.md`; the glossary of every code is
also in `explorer/data/method.json` and on the Methodology page of the application.

## Structure

The folders keep the layout the scripts expect (every script resolves its paths from the
root of the repository).

| Path | Content | Licence |
|---|---|---|
| `scripts/` | the pipeline, standard-library Python 3.12, run with `python3 -I` | MIT |
| `protocol/` | seeds, codebooks, the instructions given to the models, parameters | CC BY 4.0 |
| `raw/` | harvests as the sources returned them (stamped), and the runs of the models and agents, without the quotations | CC BY 4.0 (OpenAlex records: CC0) |
| `corpus/` | the candidate works merged from the OpenAlex harvests, without abstracts | CC BY 4.0 (from CC0 records) |
| `screening/` | the works with a text (`items.jsonl`, without passages), their citations, the codes as recommendations (`recommendations.jsonl`, without quotations) | CC BY 4.0 |
| `results/` | the figures computed by the scripts (`*.json`, `*.md`, `macros.tex`, `figures/*.csv`) | CC BY 4.0 |
| `explorer/` | the web application (static, vanilla JavaScript) and its container | MIT |
| `explorer/data/` | the data of the application: `kg.ttl.gz` (the knowledge graph), `works.json`, `figures.json`, `method.json`, `meta.json` | CC BY 4.0 |
| `explorer/sparklis/` | Sparklis, vendored (`VENDOR.txt`) | Apache 2.0 |

### The data of the application

- `explorer/data/kg.ttl.gz`: the knowledge graph (Turtle, gzip). Vocabularies: SPAR (FaBiO for
  the types of works, CiTO for the citations, with a `cito:Citation` per work characterised
  by its engagement, PRISM, FRBR), MOD 3.2 (the versions of SOSA/SSN and the artefacts the
  works publish, `mod:reliesOn`), DCTERMS, DCAT (the dataset, with its licence), FOAF,
  PROV-O (who made each code), and a small vocabulary of the observatory (`slr:`), with
  labels. SOSA/SSN terms keep their own IRIs. Base IRI:
  `https://ci.mines-stetienne.fr/sosa-ssn-observatory/kg/`.
- `explorer/data/works.json`: one record per work: bibliographic data, stratum, seeds cited,
  full text held or not, and the codes.
- `explorer/data/figures.json`: every figure, with the works behind it (as a list, or as a
  filter on `works.json` that the application evaluates).
- `explorer/data/method.json`: the glossary of the codes and the facts the methodology states.
- `explorer/data/meta.json`: date, licence, number of works and triples, base IRI, prefixes.

The fields are described in `explorer/README.md`.

## What is not here

The observatory is built from the full texts of the works, which are not ours to publish.
This repository leaves out:

- the full texts (PDFs, S2ORC records, extracted text, `fulltext/`, `screening/bodies.jsonl.gz`)
  and the requests sent to the models (`screening/model/`), which contain them;
- the passages and quotations of the works: `passages` of `screening/items.jsonl`;
  `justification` and `evidence` of each answer of the models (in
  `raw/*-model-results.jsonl.gz` and `screening/recommendations.jsonl`, kept with empty values
  so that the scripts still read the files; `evidence_found` is emptied with them), and the
  `evidence` of each error the models report; `quotes` and `note` of the pattern codes
  (`raw/*-patterns-coded-*.jsonl`); `quote` of the simple results found by script
  (`results/usage-patterns.json`, whose Markdown report is left out); any reasoning block of
  the models' answers;
- the abstracts: `abstract` of the corpus, `abstract_inverted_index` of the OpenAlex records;
  and the affiliation strings of the OpenAlex authorships as printed in the papers
  (`raw_affiliation_strings`, `raw_affiliation_string`), which often hold e-mail addresses;
- the Semantic Scholar harvests (`harvest_s2.py`, `harvest_s2_metadata.py`), whose records
  carry abstracts and citation contexts (passages of the citing works) and come under the
  Semantic Scholar API licence: rebuild them with your own key;
- the third-party lists of questionable venues and the Norwegian register of journals
  (`harvest_venue_lists.py`, `harvest_nsd_register.py` download them again);
- everything about the human screening of the companion systematic review (readers,
  decisions); only its reading queue (`screening/queue.jsonl`: which works form the
  calibration and blind samples) is kept, because the nested samples of the models follow it.

The quotations are in the private build of the observatory only.

## Reproducing the observatory

Requirements: Python 3.12 (standard library only, except `term_inventory.py`, which needs
`rdflib`); `git`; for PDFs taken in by hand, `pdftotext`, `pdftoppm` and `tesseract`; for the
coding, Claude Code (or an Anthropic API key). Keys are read from environment variables
(`OPENALEX_API_KEY`, optional; `S2_API_KEY`, for Semantic Scholar and S2ORC;
`ELSEVIER_API_KEY`, for the Elsevier text-mining API; `ANTHROPIC_API_KEY`, for the Message
Batches API) and are never written anywhere. Every script states what it reads and writes
in its docstring. Scripts that read downloaded data run with `python3 -I`.

The comments of the scripts refer to decision records (`pilotage review/105`…) of a private
project log; they explain why a choice was made and are not needed to run anything.

### 1. Harvest the candidate works

```sh
python3 -I scripts/harvest_openalex.py          # works citing the seeds: raw/T-openalex-*, merged into corpus/
python3 -I scripts/harvest_openalex.py --merge-only 2026-11-07T1337   # or rebuild corpus/ from the harvest of this release
python3 -I scripts/scoping.py                   # results/scoping.md
python3 -I scripts/dedupe.py                    # results/duplicates.md: versions of one work
python3 -I scripts/harvest_s2.py                # Semantic Scholar citations (S2_API_KEY)
python3 -I scripts/compare_sources.py           # results/sources.md
python3 -I scripts/harvest_venue_lists.py       # the predatoryjournals.org lists (snapshot)
python3 -I scripts/harvest_nsd_register.py      # the Norwegian register of journals (snapshot)
python3 -I scripts/venue_risk.py                # results/venue-risk.md (protocol/venue-risk.toml names the snapshots)
python -I scripts/term_inventory.py --sdw PATH --sosa PATH   # results/terms.csv: the terms of every version (rdflib;
                                                # clones of w3c/sdw and w3c/sdw-sosa-ssn)
python3 -I scripts/namespace_history.py --repo PATH   # results/namespace-history.json (clone of w3c/sdw-sosa-ssn)
python3 -I scripts/search_strings.py            # results/search-strings.csv: the names and IRIs to search
python3 -I scripts/harvest_fulltext_openalex.py # works whose full text holds those strings (stratum D)
python3 -I scripts/stratum_d.py                 # corpus/stratum-d-candidates.*, results/stratum-d.md
```

### 2. Obtain the full texts (yourself)

The full texts are not distributed: obtain them under the terms that apply to you (open
access, your institution's subscriptions, text-and-data-mining agreements). The scripts
below help, and record what they did in stamped manifests in `raw/`; the texts themselves go
to `fulltext/`, which is never versioned.

```sh
python3 -I scripts/scan_s2orc.py --shards all --skip-done   # S2ORC full texts (S2_API_KEY, Datasets API)
python3 -I scripts/harvest_oa_fulltext.py       # open-access PDFs that S2ORC lacks
python3 -I scripts/harvest_oa_landing.py        # second pass: citation_pdf_url of the landing pages
python3 -I scripts/harvest_oa_retry.py          # third pass, and other sources (Semantic Scholar, Europe PMC)
python3 -I scripts/oa_retry_report.py           # what is left to fetch by hand
python3 -I scripts/closed_access.py             # the closed-access works, by platform
python3 -I scripts/download_desk.py             # a local page to fetch the rest by hand in a browser
python3 -I scripts/ingest_manual.py             # take in the PDFs fetched by hand (pdftotext, OCR)
python3 -I scripts/harvest_elsevier_tdm.py      # Elsevier text-mining API, if your institution is entitled
python3 -I scripts/build_items.py               # screening/items.jsonl and bodies.jsonl.gz (local): the texts, without bibliography
```

`download_desk.py` encodes the subscriptions of one institution (its table of platforms):
adapt it to yours. `protocol/wrong-texts.toml` lists texts found to be another work.

### 3. Readings by script

```sh
python3 -I scripts/recommend_script.py          # engagement E0/E1 when a rule settles it
python3 -I scripts/harvest_s2_metadata.py       # Semantic Scholar metadata of the items no other harvest describes
python3 -I scripts/item_citations.py            # screening/citations.jsonl
python3 -I scripts/text_seeds.py                # works that cite the text seeds (Extensions, 2023 Edition)
python3 -I scripts/usage_patterns.py            # names and namespaces written, simple-result forms
```

### 4. Coding by model agents

Each work is coded on the codebook (`protocol/codebook.toml`, `protocol/codebook.md`, the
instructions of `protocol/model-prompt.md`) by an isolated Claude Code subagent: one subagent
per work, given nothing but the system prompt, the text of the work and the JSON schema of
the answer, which it writes to `answer.json`.

```sh
python3 -I scripts/model_code.py prepare --model sonnet --set all   # requests and manifest (raw/STAMP-model-*)
python3 -I scripts/agent_run.py export STAMP     # screening/model/STAMP/agents/<id>/: system.md, work.md, schema.json
# one isolated Claude Code subagent per folder (Claude Sonnet 5.5): it reads the three files
# and writes answer.json; then, for each:
python3 -I scripts/agent_run.py check STAMP <id> # is answer.json valid against the schema?
python3 -I scripts/agent_run.py collect STAMP --agent-model sonnet   # raw/STAMP-model-results.jsonl.gz, -agents.json
python3 -I scripts/model_code.py prepare --model opus --set all --sample 339   # Claude Opus 5.5, on a nested seeded sample
python3 -I scripts/model_code.py prepare --model sonnet --set abstracts      # the works with an abstract only
python3 -I scripts/model_code.py ingest          # screening/recommendations.jsonl, results/model-coding.md
python3 -I scripts/model_code.py compare         # results/model-comparison.md: the two models on the works they share
```

For each work, the codes used are those of Claude Opus 5.5 where it coded the work, otherwise
those of Claude Sonnet 5.5. `--sample N` takes the N first works in an order fixed by a
seeded hash (`--seed`, default `model-ladder-2026-11-13`), the works of the companion
review's blind sample first (`screening/queue.jsonl`), so that the part coded by one model
is nested in the part coded by the other. `model_code.py submit STAMP` and `fetch STAMP` send the same
requests to the Anthropic Message Batches API instead; the manifest of each run in `raw/`
records the model, the parameters, the hash of the system prompt and of each text, and how
the run was made.

The modelling patterns (`protocol/patterns-codebook.md`) are coded the same way, by Claude
Opus 5.5 agents, in batches, from excerpts of the texts:

```sh
python3 -I scripts/pattern_coding.py prepare --batches 8   # batches of excerpts (screening/patterns/STAMP/, local)
python3 -I scripts/pattern_show.py STAMP K       # what the agent of batch K reads; --check: what is coded
python3 -I scripts/pattern_coding.py ingest      # results/pattern-coding.md, with the second coder's agreement
```

### 5. Figures and the knowledge graph

```sh
python3 -I scripts/hypothetical_findings.py      # results/hypothetical-findings.json: the figures, from the codes
python3 -I scripts/article_macros.py             # results/macros.tex: every figure, with the file it comes from
python3 -I scripts/build_kg.py --public explorer/build/public/data   # the graph and the data, without quotations
make -C explorer public                          # the same, and the site in explorer/build/public/
```

`build_kg.py` without `--public` writes a private build with the quotations to
`explorer/data/`: never publish it. The data of `explorer/data/` in this repository are the
public build.

### What runs from this repository alone

Without the full texts: `harvest_openalex.py --merge-only`, `scoping.py`, `dedupe.py`,
`observatory_watch.py`, the web application, and any SPARQL query on the graph. The steps
from `build_items.py` on need the full texts.

## Running the web application

From the root of the repository, with the data of this release:

```sh
python3 -I explorer/deploy/serve.py --root explorer --host 127.0.0.1 --port 8000
# then http://127.0.0.1:8000/
```

(or `python3 -m http.server 8000` from `explorer/`). Use `127.0.0.1` or `localhost`: the
SPARQL endpoint runs in a service worker, which needs a secure context. The SPARQL engine,
Oxigraph, is loaded from jsDelivr when a view needs it.

With the container (a standard-library static server; the site is mounted read only):

```sh
docker build -t sosa-ssn-observatory explorer/deploy
docker run --rm -p 127.0.0.1:8115:8000 -v "$PWD/explorer:/site:ro" sosa-ssn-observatory
# then http://127.0.0.1:8115/
```

`explorer/deploy/compose.yaml` and `explorer/deploy/sosa-ssn-observatory.conf` are the
deployment of the public instance (a container behind Apache); `make -C explorer deploy`
installs it on that server.

## Maintenance: the monthly watch

```sh
python3 -I scripts/observatory_watch.py          # results/observatory-watch.md
```

On the first day of each month, `observatory_watch.py` asks OpenAlex for the works that cite
a seed and for the works whose full text holds a string of a text seed, and lists those that
are not in the observatory yet, in raw files of its own (`raw/T-observatory-*`). The new
works are then taken in by the steps above (harvest, full texts, readings, coding, graph),
and a new release is made. Each release has its own DOI; the changes are in `CHANGELOG.md`.

## Licences

- **Code** (`scripts/`, `explorer/` except `explorer/data/` and `explorer/sparklis/`): MIT,
  `LICENSE`.
- **Data** (`protocol/`, `raw/`, `corpus/`, `screening/`, `results/`, `explorer/data/`):
  Creative Commons Attribution 4.0 International (CC BY 4.0), `LICENSE-DATA`.
- **Third-party parts**:
  - the OpenAlex records (`raw/*-openalex-*`, `raw/*-observatory-*`, and the bibliographic data
    taken from them) are CC0 (https://openalex.org); the abstracts are left out;
  - the bibliographic data of the works known only to Semantic Scholar (titles, authors,
    venues, years, identifiers, in `screening/citations.jsonl`, `corpus/stratum-d-s2orc.csv`,
    `explorer/data/`) come from the Semantic Scholar Academic Graph and S2ORC (ODC-BY 1.0):
    attribution to Semantic Scholar, https://www.semanticscholar.org;
  - `explorer/sparklis/`: Sparklis by Sébastien Ferré (IRISA, Université de Rennes),
    Apache License 2.0 (`explorer/sparklis/LICENSE`); the changes made to it are listed in
    `explorer/sparklis/VENDOR.txt`;
  - the SOSA/SSN term IRIs and the term lists (`results/terms.csv`) are read from the W3C
    specifications (W3C Software and Document License).

## How to cite

Until the DOI of this release is minted, cite the repository and the web application:

> Maxime Lefrançois. *SOSA/SSN Usage Observatory* (release 1.0.0, data of 2026-11-14).
> Mines Saint-Étienne. https://ci.mines-stetienne.fr/sosa-ssn-observatory/ —
> DOI: [10.5281/zenodo.24223888](https://doi.org/10.5281/zenodo.24223888) (concept DOI; cite the DOI of the release you used, given on its Zenodo record).

The paper describing the resource (submitted to the Resources track of ESWC 2027):

> Maxime Lefrançois. *The SOSA/SSN Usage Observatory* (title to be confirmed). To appear.

`CITATION.cff` has the same information in machine-readable form.
