#!/usr/bin/env python3
"""Forward-citation harvest from OpenAlex: every work that cites a seed of protocol/seeds.toml.

    python3 -I scripts/harvest_openalex.py            # harvest, then merge
    python3 -I scripts/harvest_openalex.py --merge-only raw/2026-11-07T1030

Writes, for one run stamped T (local time, YYYY-MM-DDTHHMM):

    raw/T-openalex-cites-<seed>.jsonl.gz   the works exactly as OpenAlex returns them
    raw/T-openalex-manifest.json           seeds, query URLs (without key), counts
    corpus/openalex-candidates.jsonl.gz    one line per distinct work, with the seeds it cites
    corpus/openalex-candidates.csv         the same, flat, for screening

The API key, if any, is read from $OPENALEX_API_KEY or from the line
`OpenAlex_API_Key: …` of ~/.secrets/keys.md. It is never written anywhere.
Standard library only.
"""
import argparse
import csv
import datetime as dt
import gzip
import json
import os
import pathlib
import sys
import time
import tomllib
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://api.openalex.org/works"
FIELDS = ("id,doi,display_name,publication_year,publication_date,type,language,"
          "primary_location,authorships,cited_by_count,abstract_inverted_index,"
          "primary_topic,keywords,open_access,referenced_works_count,ids,is_retracted")


def api_key():
    if os.environ.get("OPENALEX_API_KEY"):
        return os.environ["OPENALEX_API_KEY"]
    keys = pathlib.Path.home() / ".secrets" / "keys.md"
    if keys.exists():
        for line in keys.read_text(encoding="utf-8").splitlines():
            name, _, value = line.partition(":")
            if name.strip().strip("-* `") == "OpenAlex_API_Key" and value.strip():
                return value.strip().strip("`")
    return None


def get(url, key, tries=5):
    full = url + (f"&api_key={urllib.parse.quote(key)}" if key else "")
    for attempt in range(tries):
        try:
            req = urllib.request.Request(full, headers={"User-Agent": "sosa-ssn-slr-harvest"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # network or 429: back off, then give up
            if attempt == tries - 1:
                raise RuntimeError(f"{url}: {e}") from None
            time.sleep(2 ** attempt)


def harvest(seed, key):
    base = f"{API}?filter=cites:{seed['openalex']}&per-page=200&select={FIELDS}"
    works, cursor, reported = [], "*", None
    while cursor:
        page = get(f"{base}&cursor={urllib.parse.quote(cursor)}", key)
        reported = page["meta"]["count"]
        works.extend(page["results"])
        cursor = page["meta"].get("next_cursor")
        if not page["results"]:
            break
        time.sleep(0.15)
    return base, reported, works


def abstract(inv):
    if not inv:
        return ""
    pos = {}
    for word, places in inv.items():
        for p in places:
            pos[p] = word
    return " ".join(pos[i] for i in sorted(pos))


def flatten(w, seeds):
    loc = w.get("primary_location") or {}
    src = loc.get("source") or {}
    topic = w.get("primary_topic") or {}
    countries = sorted({c for a in w.get("authorships") or [] for c in a.get("countries") or []})
    return {
        "openalex": w["id"].rsplit("/", 1)[-1],
        "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
        "title": w.get("display_name") or "",
        "year": w.get("publication_year"),
        "type": w.get("type"),
        "language": w.get("language"),
        "venue": src.get("display_name") or "",
        "venue_type": src.get("type") or "",
        "publisher": src.get("host_organization_name") or "",
        "landing_page": loc.get("landing_page_url") or "",
        "authors": [((a.get("author") or {}).get("display_name") or "") for a in w.get("authorships") or []],
        "countries": countries,
        "cited_by_count": w.get("cited_by_count"),
        "is_retracted": w.get("is_retracted"),
        "oa_status": (w.get("open_access") or {}).get("oa_status"),
        "domain": ((topic.get("domain") or {}).get("display_name")) or "",
        "field": ((topic.get("field") or {}).get("display_name")) or "",
        "subfield": ((topic.get("subfield") or {}).get("display_name")) or "",
        "topic": topic.get("display_name") or "",
        "keywords": [k.get("display_name") for k in w.get("keywords") or []],
        "abstract": abstract(w.get("abstract_inverted_index")),
        "seeds": sorted(seeds),
    }


def merge(stamp):
    by_id, seeds_of = {}, {}
    for path in sorted(ROOT.glob(f"raw/{stamp}-openalex-cites-*.jsonl.gz")):
        seed = path.name[len(f"{stamp}-openalex-cites-"):-len(".jsonl.gz")]
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                w = json.loads(line)
                by_id.setdefault(w["id"], w)
                seeds_of.setdefault(w["id"], set()).add(seed)
    rows = [flatten(w, seeds_of[i]) for i, w in by_id.items()]
    rows.sort(key=lambda r: (r["year"] or 0, r["openalex"]))
    out = ROOT / "corpus"
    out.mkdir(exist_ok=True)
    # mtime=0: the same rows give the same bytes (a --merge-only rebuild leaves no spurious change)
    (out / "openalex-candidates.jsonl.gz").write_bytes(gzip.compress(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8"), mtime=0))
    cols = ["openalex", "doi", "year", "type", "title", "venue", "publisher", "language",
            "domain", "field", "cited_by_count", "seeds"]
    with open(out / "openalex-candidates.csv", "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(cols)
        for r in rows:
            wr.writerow([";".join(r[c]) if isinstance(r[c], list) else r[c] for c in cols])
    return len(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--merge-only", metavar="STAMP", help="merge an earlier run, e.g. 2026-11-07T1030")
    ap.add_argument("--seed", action="append", help="harvest only this seed key (repeatable)")
    args = ap.parse_args(argv)

    if args.merge_only:
        print(f"{merge(args.merge_only)} distinct works")
        return 0

    seeds = tomllib.loads((ROOT / "protocol" / "seeds.toml").read_text(encoding="utf-8"))["seed"]
    if args.seed:
        seeds = [s for s in seeds if s["key"] in args.seed]
    key = api_key()
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M")
    (ROOT / "raw").mkdir(exist_ok=True)
    manifest = {"stamp": stamp, "source": "OpenAlex", "api_key_used": bool(key),
                "select": FIELDS, "seeds": []}
    for s in seeds:
        url, reported, works = harvest(s, key)
        with gzip.open(ROOT / f"raw/{stamp}-openalex-cites-{s['key']}.jsonl.gz", "wt", encoding="utf-8") as f:
            for w in works:
                f.write(json.dumps(w, ensure_ascii=False) + "\n")
        manifest["seeds"].append({**s, "query": url, "reported": reported, "retrieved": len(works)})
        print(f"{s['key']:<24} {reported:>5} reported, {len(works):>5} retrieved", file=sys.stderr)
    (ROOT / f"raw/{stamp}-openalex-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{merge(stamp)} distinct works ({stamp})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
