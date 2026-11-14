#!/usr/bin/env python3
"""The watch of the SOSA/SSN usage observatory: the works that cite SOSA/SSN since the review.

    python3 -I scripts/observatory_watch.py      # raw/T-observatory-*.jsonl.gz and manifest,
                                                 # results/observatory-watch.{md,json}

Maxime, 2026-11-14: the explorer of the review is published as an observatory of the use of
SOSA/SSN, with a regular maintenance. This script is the part that can run unattended (a
monthly cron job, `observatory/README.md`): it asks OpenAlex for every work that cites a
seed of protocol/seeds.toml, and for every work whose full text holds a string of a text
seed, and lists those that are not candidates of the review yet. It writes its own stamped
raw files (`T-observatory-cites.jsonl.gz`, `T-observatory-textseeds.jsonl.gz`, one manifest),
which no script of the review reads: the frozen harvest of the review, its corpus and its
figures stay as they are. Taking the new works in (merge, full texts, coding by subagents,
rebuild, deployment) is done in a work session, from the list this script writes.
Standard library only; network: OpenAlex only.
"""
import datetime as dt
import gzip
import json
import pathlib
import sys
import time
import tomllib
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from harvest_openalex import API, FIELDS, api_key, get  # noqa: E402
from strata import ROOT, load_corpus, load_seeds  # noqa: E402


def pages(base, key, sink, tag):
    cursor, reported, received = "*", None, 0
    works = []
    while cursor:
        page = get(f"{base}&cursor={urllib.parse.quote(cursor)}", key)
        reported = page["meta"]["count"]
        sink.write(json.dumps({"query": tag, "meta": page["meta"], "results": page["results"]}, ensure_ascii=False) + "\n")
        works += page["results"]
        received += len(page["results"])
        cursor = page["meta"].get("next_cursor")
        if not page["results"]:
            break
        time.sleep(0.15)
    return works, reported, received


def main():
    key = api_key()
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M")
    known = {w["openalex"] for w in load_corpus()}
    with gzip.open(ROOT / "corpus/stratum-d-candidates.jsonl.gz", "rt", encoding="utf-8") as f:
        known |= {w["openalex"] for w in map(json.loads, f)}
    manifest = {"stamp": stamp, "source": "OpenAlex", "api_key_used": bool(key), "queries": []}
    new = {}
    with gzip.open(ROOT / f"raw/{stamp}-observatory-cites.jsonl.gz", "wt", encoding="utf-8") as sink:
        for s in load_seeds():
            base = f"{API}?filter=cites:{s['openalex']}&per-page=200&select={FIELDS}"
            works, rep, rec = pages(base, key, sink, s["key"])
            manifest["queries"].append({"seed": s["key"], "query": base, "reported": rep, "retrieved": rec})
            for w in works:
                oid = w["id"].rsplit("/", 1)[-1]
                if oid not in known:
                    new.setdefault(oid, {"title": w.get("display_name"), "year": w.get("publication_year"),
                                         "doi": w.get("doi"), "found_by": []})["found_by"].append(s["key"])
    seeds = tomllib.loads((ROOT / "protocol/seeds.toml").read_text(encoding="utf-8")).get("text_seed", [])
    with gzip.open(ROOT / f"raw/{stamp}-observatory-textseeds.jsonl.gz", "wt", encoding="utf-8") as sink:
        for s in seeds:
            for string in s["strings"]:
                value = '"' + string.replace('"', "") + '"'
                base = f"{API}?filter={urllib.parse.quote('fulltext.search.exact:' + value, safe=':')}&per-page=200&select={FIELDS}"
                works, rep, rec = pages(base, key, sink, f"{s['key']}: {string}")
                manifest["queries"].append({"text_seed": s["key"], "string": string, "query": base,
                                            "reported": rep, "retrieved": rec})
                for w in works:
                    oid = w["id"].rsplit("/", 1)[-1]
                    if oid not in known:
                        new.setdefault(oid, {"title": w.get("display_name"), "year": w.get("publication_year"),
                                             "doi": w.get("doi"), "found_by": []})["found_by"].append(s["key"])
    (ROOT / f"raw/{stamp}-observatory-manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    rows = sorted(new.items(), key=lambda kv: (-(kv[1]["year"] or 0), kv[0]))
    (ROOT / "results/observatory-watch.json").write_text(json.dumps(
        {"stamp": stamp, "known": len(known), "new": len(rows), "works": dict(rows)}, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8")
    by_year = {}
    for _, w in rows:
        by_year[w["year"]] = by_year.get(w["year"], 0) + 1
    L = ["# Observatory watch: works not yet in the review", "",
         f"Written by `scripts/observatory_watch.py`, run `{stamp}`. Candidates of the review (A to D): "
         f"{len(known)}. Works found now that are not candidates: **{len(rows)}** "
         f"({', '.join(f'{y}: {n}' for y, n in sorted(by_year.items(), key=lambda kv: -(kv[0] or 0)))}).", "",
         "| OpenAlex | Year | Found by | Title |", "|---|---|---|---|"]
    L += [f"| {o} | {w['year']} | {', '.join(sorted(set(w['found_by'])))} | {(w['title'] or '')[:90]} |" for o, w in rows]
    (ROOT / "results/observatory-watch.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"results/observatory-watch.md: {len(rows)} works not yet in the review (run {stamp})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
