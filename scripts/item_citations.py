#!/usr/bin/env python3
"""The full citation of every item to read: screening/citations.jsonl.

    python3 -I scripts/item_citations.py

For each item of screening/items.jsonl that has passages: authors, year, title, venue,
publisher, type and DOI, from the first source that describes it:

1. the OpenAlex corpus (corpus/openalex-candidates.jsonl.gz, corpus/stratum-d-candidates.jsonl.gz),
   by OpenAlex identifier, then by DOI;
2. the Semantic Scholar citation harvest (raw/*-s2-cites-*.jsonl.gz), by CorpusId;
3. the Semantic Scholar metadata harvest (raw/*-s2-metadata.jsonl.gz,
   scripts/harvest_s2_metadata.py), by CorpusId.

Each line names its source. The review application shows the citation above the passages
(app/DESIGN.md). Bibliographic metadata only: the file is versioned. Standard library only.
"""
import glob
import gzip
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def doi_of(x):
    return (x or "").lower().removeprefix("https://doi.org/") or None


class Sources:
    def __init__(self):
        self.by_openalex, self.by_doi, self.s2 = {}, {}, {}

    def find(self, it):
        """(source, record) for an item of items.jsonl, or None."""
        if it["item"].startswith("openalex:") and it["item"][9:] in self.by_openalex:
            return "openalex", self.by_openalex[it["item"][9:]]
        if it.get("doi") and doi_of(it["doi"]) in self.by_doi:
            return "openalex", self.by_doi[doi_of(it["doi"])]
        if it.get("corpusid") in self.s2:
            return self.s2[it["corpusid"]]
        return None


def load_sources():
    s = Sources()
    for f in ("corpus/openalex-candidates.jsonl.gz", "corpus/stratum-d-candidates.jsonl.gz"):
        for line in gzip.open(ROOT / f, "rt", encoding="utf-8"):
            r = json.loads(line)
            s.by_openalex[r["openalex"]] = r
            if doi_of(r.get("doi")):
                s.by_doi.setdefault(doi_of(r["doi"]), r)
    # later harvests first: the newest record of a work wins
    for pattern, how in (("raw/*-s2-metadata.jsonl.gz", "s2-metadata"), ("raw/*-s2-cites-*.jsonl.gz", "s2-cites")):
        for f in sorted(glob.glob(str(ROOT / pattern)), reverse=True):
            for line in gzip.open(f, "rt", encoding="utf-8"):
                r = json.loads(line)
                r = r.get("citingPaper", r)
                cid = (r.get("externalIds") or {}).get("CorpusId")
                if cid and cid not in s.s2:
                    s.s2[cid] = (how, r)
    return s


def citation(it, found):
    out = {"item": it["item"], "source": None, "authors": [], "year": None, "title": it.get("title"),
           "venue": None, "publisher": None, "type": None, "doi": doi_of(it.get("doi"))}
    if not found:
        return out
    how, r = found
    out["source"] = how
    if how == "openalex":
        out.update(authors=r.get("authors") or [], year=r.get("year"), title=r.get("title") or out["title"],
                   venue=r.get("venue") or None, publisher=r.get("publisher") or None, type=r.get("type"),
                   doi=doi_of(r.get("doi")) or out["doi"])
    else:
        venue = (r.get("publicationVenue") or {}).get("name") or (r.get("journal") or {}).get("name") or r.get("venue")
        out.update(authors=[a.get("name") for a in r.get("authors") or [] if a.get("name")], year=r.get("year"),
                   title=r.get("title") or out["title"], venue=venue or None,
                   type=", ".join(r.get("publicationTypes") or []) or None,
                   doi=doi_of((r.get("externalIds") or {}).get("DOI")) or out["doi"])
    return out


def main():
    items = [json.loads(line) for line in open(ROOT / "screening/items.jsonl", encoding="utf-8")]
    sources = load_sources()
    rows = [citation(it, sources.find(it)) for it in items if it["passages"]]
    with open(ROOT / "screening/citations.jsonl", "w", encoding="utf-8") as f:
        for r in sorted(rows, key=lambda r: r["item"]):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    by = {}
    for r in rows:
        by[r["source"]] = by.get(r["source"], 0) + 1
    print(f"screening/citations.jsonl: {len(rows)} items; by source {by}; "
          f"without authors {sum(1 for r in rows if not r['authors'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
