#!/usr/bin/env python3
"""Stratum D: the works found by the full-text search that the citation harvest lacks.

    python3 -I scripts/stratum_d.py           # results/stratum-d.md, corpus/stratum-d-candidates.*

Reads the last full-text harvest in raw/ (scripts/harvest_fulltext_openalex.py), the
OpenAlex candidate corpus (strata A to C) and the last Semantic Scholar harvest. A work
found by the full-text search is in stratum D when it is not an OpenAlex candidate; when
Semantic Scholar says it cites a seed, it is counted apart, since it then belongs to the
citing population that OpenAlex missed. No screening: the precision of the search is
still to be measured on a sample.

Each work of stratum D gets a signal, a rule to be checked against that sample:

    strong   a namespace IRI, or a prefixed name whose local name is a compound
             (`sosa:madeBySensor`), or two different prefixed names or more
    weak     a single prefixed name made of one common word (`ssn:System`, `ssn:Condition`),
             which the search also finds as the phrase "SSN system"
    early    published before 2009, when the SSN Incubator Group started: an
             occurrence cannot be a use of SSN
"""
import collections
import csv
import gzip
import json
import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from harvest_openalex import flatten  # noqa: E402
from search_strings import COMPOUND  # noqa: E402
from strata import ROOT, load_corpus, load_seeds, stratum  # noqa: E402

SSN_START = 2009
SEMWEB = re.compile(r"\b(ontolog\w*|semantic\w*|rdf|owl|linked data|knowledge graph\w*|sparql)\b", re.I)


def norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def table(rows, head):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def pct(n, d):
    return f"{100 * n / d:.1f} %" if d else "—"


def s2_citing():
    """DOIs and normalised titles of the papers that Semantic Scholar says cite a seed."""
    manifests = sorted(ROOT.glob("raw/*-s2-manifest.json"))
    if not manifests:
        return set(), set()
    stamp = json.loads(manifests[-1].read_text(encoding="utf-8"))["stamp"]
    dois, titles = set(), set()
    for path in ROOT.glob(f"raw/{stamp}-s2-cites-*.jsonl.gz"):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                p = json.loads(line).get("citingPaper") or {}
                doi = ((p.get("externalIds") or {}).get("DOI") or "").lower()
                if doi:
                    dois.add(doi)
                if p.get("title"):
                    titles.add(norm(p["title"]))
    return dois, titles


def main():
    manifest_path = sorted(ROOT.glob("raw/*-openalex-fulltext-manifest.json"))[-1]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    stamp = manifest["stamp"]
    works, strings_of, kinds_of = {}, collections.defaultdict(set), collections.defaultdict(set)
    hits = collections.defaultdict(set)
    with gzip.open(ROOT / f"raw/{stamp}-openalex-fulltext.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in f:
            page = json.loads(line)
            for w in page["results"]:
                works.setdefault(w["id"], w)
                strings_of[w["id"]].add(page["string"])
                kinds_of[w["id"]].add(page["kind"])
                hits[page["string"]].add(w["id"])

    corpus = {f"https://openalex.org/{w['openalex']}": w for w in load_corpus()}
    role = {s["key"]: s["role"] for s in load_seeds()}
    s2_dois, s2_titles = s2_citing()

    in_corpus = {i for i in works if i in corpus}
    outside = [i for i in works if i not in corpus]

    def cites_in_s2(w):
        doi = (w.get("doi") or "").replace("https://doi.org/", "").lower()
        return (doi and doi in s2_dois) or norm(w.get("display_name")) in s2_titles

    s2_only = {i for i in outside if cites_in_s2(works[i])}
    d = [i for i in outside if i not in s2_only]
    st = collections.Counter(stratum(corpus[i], role) for i in in_corpus)
    all_st = collections.Counter(stratum(w, role) for w in corpus.values())

    def signal(i):
        if (works[i].get("publication_year") or 0) < SSN_START:
            return "early"
        found = strings_of[i]
        if "namespace" in kinds_of[i] or len(found) >= 2:
            return "strong"
        local = next(iter(found)).split(":", 1)[-1]
        return "strong" if COMPOUND.match(local) else "weak"

    sig = collections.Counter(signal(i) for i in d)

    def kind(i):
        k = kinds_of[i]
        return "both" if len(k) > 1 else ("namespace IRI only" if "namespace" in k else "prefixed names only")

    L = ["# Stratum D: works found by the full-text search of OpenAlex\n",
         f"Full-text harvest `{stamp}` ({len(manifest['queries'])} queries, strings of "
         "`results/search-strings.csv`: namespace IRIs under several spellings, prefixed "
         "names; no local names), against the OpenAlex candidate corpus of `results/scoping.md` "
         "and the last Semantic Scholar harvest; computed by `scripts/stratum_d.py`. **Not "
         "screened**: the precision of the search is not measured yet.\n",
         f"- Distinct works found: **{len(works)}**; truncated queries: "
         f"{sum(1 for q in manifest['queries'] if q['truncated'])}",
         f"- Already OpenAlex candidates: {len(in_corpus)} — "
         + ", ".join(f"{s} {st[s]} of {all_st[s]} ({pct(st[s], all_st[s])})" for s in sorted(all_st)),
         f"- Not OpenAlex candidates but citing a seed according to Semantic Scholar: {len(s2_only)}",
         f"- **Stratum D (cites no seed in either source): {len(d)}**, by signal (rule in the "
         f"script, precision to measure): strong {sig['strong']}, weak {sig['weak']}, "
         f"early {sig['early']}\n",
         "## Stratum D by what was found\n",
         table([(k, v) for k, v in collections.Counter(kind(i) for i in d).most_common()],
               ["found by", "works"]) + "\n",
         "## Stratum D by OpenAlex type\n",
         table(collections.Counter(works[i].get("type") for i in d).most_common(), ["type", "works"]) + "\n"]
    strong = {i for i in d if signal(i) == "strong"}

    def semweb(w):
        inv = w.get("abstract_inverted_index") or {}
        words = " ".join(inv) + " " + (w.get("display_name") or "") + " " + " ".join(
            k.get("display_name") or "" for k in w.get("keywords") or [])
        return bool(SEMWEB.search(words))

    cross = collections.Counter((signal(i), semweb(works[i])) for i in d)
    L += ["## Stratum D: signal against a Semantic Web term in title, abstract or keywords\n",
          "A crude indicator of relevance (ontology, semantic, RDF, OWL, linked data, knowledge "
          "graph, SPARQL), not a screening decision.\n",
          table([(s, cross[(s, True)], cross[(s, False)], pct(cross[(s, True)], cross[(s, True)] + cross[(s, False)]))
                 for s in ("strong", "weak", "early")],
                ["signal", "with a term", "without", "share with"]) + "\n"]
    L += ["## Strong signals of stratum D by year\n",
          table(sorted(collections.Counter(works[i].get("publication_year") for i in strong).items(),
                       key=lambda kv: kv[0] or 0), ["year", "works"]) + "\n"]
    rows = []
    for s, ids in sorted(hits.items(), key=lambda kv: -len(kv[1]))[:40]:
        rows.append((f"`{s}`", len(ids), sum(1 for i in ids if i in in_corpus),
                     sum(1 for i in ids if i in s2_only), sum(1 for i in ids if i in d),
                     sum(1 for i in ids if i in strong)))
    L += ["## Strings with the most works (40 first)\n",
          table(rows, ["string", "works", "OpenAlex candidates", "citing per Semantic Scholar",
                       "stratum D", "stratum D, strong"]) + "\n"]
    new23 = [q for q in manifest["queries"]
             if q["kind"] == "prefixed" and q["versions"] == "ssn-2023" and q["reported"]]
    if new23:
        L += ["## Prefixed names that only the 2023 Edition declares, found by the search\n",
              "Leads for the usage report (pilotage usage/301), not evidence: a `sosa:` name "
              "found in a work published before 2023 is more likely a term of `ssn:` written "
              "with the wrong prefix (error S1 of the codebook).\n",
              table([(f"`{q['string']}`", q["reported"],
                      ", ".join(str(y) for y in sorted(works[i].get("publication_year") or 0
                                                     for i in hits[q["string"]])))
                     for q in new23], ["string", "works", "years"]) + "\n"]
    no_hit = sum(1 for q in manifest["queries"] if q["kind"] == "prefixed" and not q["reported"])
    L.append(f"Prefixed names searched: {sum(1 for q in manifest['queries'] if q['kind'] == 'prefixed')}, "
             f"of which {no_hit} found nothing.\n")

    out = ROOT / "results"
    (out / "stratum-d.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    F = {"harvest": stamp, "queries": len(manifest["queries"]), "found": len(works),
         "in_corpus": len(in_corpus), "in_corpus_by_stratum": {k: st[k] for k in sorted(all_st)},
         "corpus_by_stratum": {k: all_st[k] for k in sorted(all_st)}, "s2_only": len(s2_only),
         "stratum_d": len(d), "signal": {k: sig[k] for k in ("strong", "weak", "early")},
         "semweb_term": {k: {"with": cross[(k, True)], "without": cross[(k, False)]}
                         for k in ("strong", "weak", "early")}}
    (out / "stratum-d.json").write_text(json.dumps(F, indent=1) + "\n", encoding="utf-8")
    rows = []
    for i in d:
        r = flatten(works[i], [])
        r["stratum"] = "D"
        r["found_by"] = sorted(strings_of[i])
        r["signal"] = signal(i)
        rows.append(r)
    rows.sort(key=lambda r: (r["year"] or 0, r["openalex"]))
    corpus_dir = ROOT / "corpus"
    # mtime=0: the same rows give the same bytes, so that a rerun leaves no spurious change
    (corpus_dir / "stratum-d-candidates.jsonl.gz").write_bytes(gzip.compress(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8"), mtime=0))
    cols = ["openalex", "doi", "year", "type", "title", "venue", "publisher", "language", "signal",
            "found_by"]
    with open(corpus_dir / "stratum-d-candidates.csv", "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(cols)
        for r in rows:
            wr.writerow([";".join(r[c]) if isinstance(r[c], list) else r[c] for c in cols])
    print(f"results/stratum-d.md: {len(works)} found, {len(d)} in stratum D")
    return 0


if __name__ == "__main__":
    sys.exit(main())
