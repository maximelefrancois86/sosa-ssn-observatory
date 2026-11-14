#!/usr/bin/env python3
"""Full-text search of OpenAlex for the strings of SOSA/SSN (stratum D, pilotage review/101).

    python3 -I scripts/harvest_fulltext_openalex.py            # namespaces and prefixed names
    python3 -I scripts/harvest_fulltext_openalex.py --kinds namespace

Reads results/search-strings.csv (scripts/search_strings.py). For each string, queries the
`fulltext.search` filter of OpenAlex, which searches titles, abstracts and the full texts
OpenAlex holds:

- a namespace IRI is searched under several spellings (with `www.`, without it, with
  `http://`), each both exact (`fulltext.search.exact`) and stemmed (`fulltext.search`),
  because OpenAlex tokenises URLs in ways it does not document;
- a prefixed name (`sosa:Observation`) is searched exact only; the colon is a word
  separator there, so `sosa:Observation` also finds the phrase "SOSA observation".

Local names are not searched yet: their precision is to be measured first (protocol § 3).
Writes, for one run stamped T (local time):

    raw/T-openalex-fulltext.jsonl.gz       one line per page returned: the query, the page
                                           metadata and the works, exactly as returned
    raw/T-openalex-fulltext-manifest.json  queries (without key), counts reported and
                                           received, truncation

The full texts are not in the OpenAlex snapshot: this harvest, with its date, is the only
record of what the search found. At most MAX_PER_QUERY works are kept per query; the
manifest says when a query was truncated. Standard library only.
"""
import argparse
import csv
import datetime as dt
import gzip
import json
import pathlib
import sys
import time
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from harvest_openalex import API, FIELDS, api_key, get  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAX_PER_QUERY = 2000


def spellings(namespace):
    """The spellings under which a namespace IRI (given without its scheme) is searched."""
    bare = namespace[4:] if namespace.startswith("www.") else namespace
    host_first = bare.split("/")[0]
    out = [bare, f"http://{bare}"]
    if host_first == "w3.org":
        out += [f"www.{bare}", f"http://www.{bare}"]
    return out


def queries(kinds):
    with open(ROOT / "results/search-strings.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        if r["kind"] not in kinds:
            continue
        if r["kind"] == "namespace":
            for s in spellings(r["string"]):
                for mode in ("exact", "stemmed"):
                    out.append({"string": r["string"], "searched": s, "kind": r["kind"],
                                "mode": mode, "versions": r["versions"]})
        elif r["kind"] == "prefixed":
            out.append({"string": r["string"], "searched": r["string"], "kind": r["kind"],
                        "mode": "exact", "versions": r["versions"]})
    return out


def run(q, key, sink):
    name = "fulltext.search.exact" if q["mode"] == "exact" else "fulltext.search"
    value = '"' + q["searched"].replace('"', "") + '"'
    flt = urllib.parse.quote(f"{name}:{value}", safe=":")
    base = f"{API}?filter={flt}&per-page=200&select={FIELDS}"
    cursor, reported, received, page_no = "*", None, 0, 0
    while cursor and received < MAX_PER_QUERY:
        page = get(f"{base}&cursor={urllib.parse.quote(cursor)}", key)
        reported = page["meta"]["count"]
        sink.write(json.dumps({**q, "page": page_no, "meta": page["meta"],
                               "results": page["results"]}, ensure_ascii=False) + "\n")
        received += len(page["results"])
        cursor = page["meta"].get("next_cursor")
        page_no += 1
        if not page["results"]:
            break
        time.sleep(0.15)
    return base, reported, received


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--kinds", nargs="+", default=["namespace", "prefixed"],
                    choices=["namespace", "prefixed"])
    args = ap.parse_args(argv)
    key = api_key()
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M")
    qs = queries(set(args.kinds))
    manifest = {"stamp": stamp, "source": "OpenAlex full-text search", "api_key_used": bool(key),
                "select": FIELDS, "max_per_query": MAX_PER_QUERY, "queries": []}
    (ROOT / "raw").mkdir(exist_ok=True)
    with gzip.open(ROOT / f"raw/{stamp}-openalex-fulltext.jsonl.gz", "wt", encoding="utf-8") as sink:
        for i, q in enumerate(qs, 1):
            base, reported, received = run(q, key, sink)
            manifest["queries"].append({**q, "query": base, "reported": reported, "retrieved": received,
                                        "truncated": bool(reported and received < reported)})
            print(f"{i:>4}/{len(qs)} {q['mode']:<7} {q['searched']:<45} {reported:>6} reported, "
                  f"{received:>5} retrieved", file=sys.stderr)
    (ROOT / f"raw/{stamp}-openalex-fulltext-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(stamp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
