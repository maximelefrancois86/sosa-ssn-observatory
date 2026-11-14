#!/usr/bin/env python3
"""The works that cite a seed no citation index holds: the `[[text_seed]]` of protocol/seeds.toml.

    python3 -I scripts/text_seeds.py            # the full texts held: results/text-seeds.{md,json}
    python3 -I scripts/text_seeds.py --search   # also a stamped OpenAlex full-text search
                                                # (raw/T-openalex-textseeds.jsonl.gz, manifest)

The Extensions to SSN (vocab-ssn-ext, 2020) and the drafts of the 2023 Edition are
published on w3.org only: neither OpenAlex nor Semantic Scholar has a record for them, so
the works that cite them cannot be harvested by forward citation. This script finds them
by text, in two ways:

1. In every full text held (the S2ORC records listed by a scan manifest, and the texts of
   the retrieval runs, the latest per work, wrong texts aside), **bibliography included**:
   a work cites the seed when one of its `strings` (title, URL, namespace) occurs, case and
   whitespace aside. Where in the text it occurs is recorded: in the reference list (after
   the last reference heading of a PDF text, or in a `bibentry` span of S2ORC) or in the body.
2. With `--search`, the OpenAlex `fulltext.search.exact` filter for each string, exactly as
   scripts/harvest_fulltext_openalex.py does (stamped raw harvest, never edited): the works
   it finds that are not candidates yet are new candidates, whose full text is to be found.

Writes results/text-seeds.md and .json: for each seed, the works held that cite it (by
stratum), the works that use its namespace, and, after a search, the new candidates.
Standard library only.
"""
import argparse
import collections
import datetime as dt
import gzip
import json
import pathlib
import re
import sys
import time
import tomllib
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_items import REFS  # noqa: E402
from harvest_openalex import API, FIELDS, api_key, get  # noqa: E402
from strata import ROOT, load_corpus, wrong_texts  # noqa: E402


def text_seeds():
    return tomllib.loads((ROOT / "protocol/seeds.toml").read_text(encoding="utf-8")).get("text_seed", [])


def pattern(strings):
    parts = [r"\s+".join(map(re.escape, s.split())) for s in strings]
    return re.compile("|".join(parts), re.I)


def held_texts():
    """(item, full text, start of the reference list or None) for every full text held."""
    items = {json.loads(l)["item"]: json.loads(l) for l in open(ROOT / "screening/items.jsonl", encoding="utf-8")}
    listed = set()
    for m in sorted(ROOT.glob("raw/*-s2orc-scan-manifest.json")):
        d = json.loads(m.read_text(encoding="utf-8"))
        listed.update(f"s2orc-{d['release']}/{d['stamp']}-shard-{e['index']:03d}.jsonl.gz" for e in d.get("shards", []))
    seen = set()
    for path in sorted(ROOT.glob("fulltext/s2orc-*/*.jsonl.gz")):
        if f"{path.parent.name}/{path.name}" not in listed:
            continue
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                item = f"s2orc:{rec.get('corpusid')}"
                if item in seen or item not in items:
                    continue
                seen.add(item)
                body = rec.get("body") or {}
                text = body.get("text") or ""
                bib = (body.get("annotations") or {}).get("bibentry")
                starts = [int(s["start"]) for s in json.loads(bib)] if isinstance(bib, str) and bib.startswith("[") else []
                yield item, text, (min(starts) if starts else None)
    wrong = wrong_texts()
    taken = set()
    for mpath in sorted(ROOT.glob("raw/*-oa-fulltext-manifest.json"), reverse=True):
        man = json.loads(mpath.read_text(encoding="utf-8"))
        if not man.get("complete"):
            continue
        for e in man["works"]:
            txt = ROOT / f"fulltext/oa-pdf/{man['stamp']}/{e['openalex']}.txt"
            if e["outcome"] != "text" or not txt.exists() or e["openalex"] in taken \
                    or (man["stamp"], e["openalex"]) in wrong:
                continue
            taken.add(e["openalex"])
            text = re.sub(r"-\n(?=[a-z])", "", txt.read_text(encoding="utf-8", errors="replace"))
            heads = list(REFS.finditer(text))
            yield f"openalex:{e['openalex']}", text, (heads[-1].start() if heads else None)


def search(seeds, key):
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M")
    manifest = {"stamp": stamp, "source": "OpenAlex full-text search, strings of the text seeds",
                "api_key_used": bool(key), "select": FIELDS, "queries": []}
    found = collections.defaultdict(dict)
    with gzip.open(ROOT / f"raw/{stamp}-openalex-textseeds.jsonl.gz", "wt", encoding="utf-8") as sink:
        for s in seeds:
            for string in s["strings"]:
                value = '"' + string.replace('"', "") + '"'
                flt = urllib.parse.quote(f"fulltext.search.exact:{value}", safe=":")
                base = f"{API}?filter={flt}&per-page=200&select={FIELDS}"
                cursor, reported, received, page_no = "*", None, 0, 0
                while cursor:
                    page = get(f"{base}&cursor={urllib.parse.quote(cursor)}", key)
                    reported = page["meta"]["count"]
                    sink.write(json.dumps({"seed": s["key"], "string": string, "page": page_no,
                                           "meta": page["meta"], "results": page["results"]}, ensure_ascii=False) + "\n")
                    for w in page["results"]:
                        found[s["key"]][w["id"].rsplit("/", 1)[-1]] = w
                    received += len(page["results"])
                    cursor = page["meta"].get("next_cursor")
                    page_no += 1
                    if not page["results"]:
                        break
                    time.sleep(0.15)
                manifest["queries"].append({"seed": s["key"], "string": string, "query": base,
                                            "reported": reported, "retrieved": received})
                print(f"{s['key']:<18} {string:<52} {reported:>5} reported, {received:>5} retrieved", file=sys.stderr)
    (ROOT / f"raw/{stamp}-openalex-textseeds-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return stamp


def last_search():
    mans = sorted(ROOT.glob("raw/*-openalex-textseeds-manifest.json"))
    if not mans:
        return None, {}
    stamp = json.loads(mans[-1].read_text(encoding="utf-8"))["stamp"]
    found = collections.defaultdict(dict)
    with gzip.open(ROOT / f"raw/{stamp}-openalex-textseeds.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in f:
            page = json.loads(line)
            for w in page["results"]:
                found[page["seed"]][w["id"].rsplit("/", 1)[-1]] = w
    return stamp, found


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--search", action="store_true")
    args = ap.parse_args(argv)
    seeds = text_seeds()
    if args.search:
        search(seeds, api_key())
    stamp, found = last_search()
    items = {json.loads(l)["item"]: json.loads(l) for l in open(ROOT / "screening/items.jsonl", encoding="utf-8")}
    corpus = {w["openalex"]: w for w in load_corpus()}
    with gzip.open(ROOT / "corpus/stratum-d-candidates.jsonl.gz", "rt", encoding="utf-8") as f:
        dcands = {w["openalex"]: w for w in map(json.loads, f)}
    by_doi = {it["doi"]: i for i, it in items.items() if it.get("doi")}
    pats = {s["key"]: pattern(s["strings"]) for s in seeds}
    hits = collections.defaultdict(dict)
    held = 0
    for item, text, ref_start in held_texts():
        held += 1
        for key, rx in pats.items():
            where = set()
            for m in rx.finditer(text):
                where.add("references" if ref_start is not None and m.start() >= ref_start else "body")
            if where:
                hits[key][item] = {"where": sorted(where), "stratum": items[item]["stratum"],
                                   "title": items[item]["title"], "doi": items[item].get("doi")}
    out = {"held_texts": held, "search_stamp": stamp, "seeds": {}}
    L = ["# Seeds found by text: works that cite the Extensions and the 2023 drafts", "",
         "Written by `scripts/text_seeds.py`; seeds of `[[text_seed]]` in `protocol/seeds.toml`.", "",
         f"Full texts held and scanned, bibliography included: {held}."]
    for s in seeds:
        h = hits[s["key"]]
        by_st = collections.Counter(v["stratum"] for v in h.values())
        refs = sorted(i for i, v in h.items() if "references" in v["where"])
        body_only = sorted(i for i, v in h.items() if v["where"] == ["body"])
        new = {}
        for oid, w in found.get(s["key"], {}).items():
            doi = (w.get("doi") or "").replace("https://doi.org/", "").lower() or None
            if f"openalex:{oid}" in items or (doi and doi in by_doi):
                continue
            new[oid] = {"title": w.get("display_name"), "year": w.get("publication_year"), "doi": doi,
                        "in_corpus": oid in corpus, "in_stratum_d": oid in dcands}
        out["seeds"][s["key"]] = {"held_citing": len(h), "by_stratum": dict(by_st), "in_references": len(refs),
                                  "body_only": len(body_only), "works": h, "search_new": new,
                                  "search_found": len(found.get(s["key"], {}))}
        L += ["", f"## {s['title']}", "", f"Strings: {', '.join('`' + x + '`' for x in s['strings'])}.", "",
              f"Full texts held that contain one of them: **{len(h)}** "
              f"({', '.join(f'{k} {v}' for k, v in sorted(by_st.items()))}); in the reference list "
              f"{len(refs)}, in the body only {len(body_only)}."]
        if stamp:
            L += [f"OpenAlex full-text search `{stamp}`: {len(found.get(s['key'], {}))} works, "
                  f"of which {len(new)} have no full text held "
                  f"({sum(v['in_corpus'] or v['in_stratum_d'] for v in new.values())} already candidates)."]
        L += ["", "| Work | Stratum | Where | Title |", "|---|---|---|---|"]
        L += [f"| `{i}` | {v['stratum']} | {', '.join(v['where'])} | {(v['title'] or '')[:90]} |" for i, v in sorted(h.items())]
        if new:
            L += ["", "Found by the search, no full text held:", "", "| OpenAlex | Year | Candidate | Title |", "|---|---|---|---|"]
            L += [f"| {o} | {v['year']} | {'yes' if v['in_corpus'] or v['in_stratum_d'] else 'no'} | {(v['title'] or '')[:90]} |"
                  for o, v in sorted(new.items())]
    (ROOT / "results/text-seeds.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (ROOT / "results/text-seeds.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for k, v in out["seeds"].items():
        print(f"{k}: {v['held_citing']} held texts cite it ({v['in_references']} in references); "
              f"search {v['search_found']} found, {len(v['search_new'])} without a text held")
    return 0


if __name__ == "__main__":
    sys.exit(main())
