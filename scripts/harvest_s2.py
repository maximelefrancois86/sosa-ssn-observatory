#!/usr/bin/env python3
"""Forward-citation harvest from Semantic Scholar: every paper that cites a seed.

    python3 -I scripts/harvest_s2.py

Each seed of protocol/seeds.toml is looked up by its `s2` paper ID when it has one, else
by DOI, else by exact title match; the paper found is recorded in the manifest, and a
title that does not match the seed's stops the run. Writes, for one run stamped T:

    raw/T-s2-cites-<seed>.jsonl.gz   the citation records exactly as Semantic Scholar returns
                                      them, with the citation contexts and intents
    raw/T-s2-manifest.json           seeds, papers found, query URLs (without key), counts

The API key, if any, is read from $S2_API_KEY or from the line `S2_API_Key: …` of
~/.secrets/keys.md and sent in the x-api-key header; it is never written anywhere.
Requests are spaced by two seconds. Standard library only.
"""
import datetime as dt
import gzip
import json
import os
import pathlib
import re
import sys
import time
import tomllib
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://api.semanticscholar.org/graph/v1"
PAPER_FIELDS = "paperId,title,year,citationCount,externalIds"
CITING_FIELDS = ("contexts,intents,isInfluential,paperId,externalIds,title,year,venue,"
                 "publicationVenue,publicationTypes,publicationDate,isOpenAccess,openAccessPdf,"
                 "authors,abstract,citationCount")
PAUSE = 2.0


def api_key():
    if os.environ.get("S2_API_KEY"):
        return os.environ["S2_API_KEY"]
    keys = pathlib.Path.home() / ".secrets" / "keys.md"
    if keys.exists():
        for line in keys.read_text(encoding="utf-8").splitlines():
            name, _, value = line.partition(":")
            if name.strip().strip("-* `") == "S2_API_Key" and value.strip():
                return value.strip().strip("`")
    return None


def get(url, key, tries=6):
    headers = {"User-Agent": "sosa-ssn-slr-harvest"}
    if key:
        headers["x-api-key"] = key
    for attempt in range(tries):
        time.sleep(PAUSE)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if attempt == tries - 1:
                raise RuntimeError(f"{url}: {e}") from None
            time.sleep(PAUSE * 2 ** attempt)  # 429 and 5xx: back off
        except OSError as e:
            if attempt == tries - 1:
                raise RuntimeError(f"{url}: {e}") from None
            time.sleep(PAUSE * 2 ** attempt)


def norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def resolve(seed, key):
    """The Semantic Scholar paper of a seed, and the URL that found it."""
    if seed.get("s2"):
        url = f"{API}/paper/{seed['s2']}?fields={PAPER_FIELDS}"
    elif seed.get("doi"):
        url = f"{API}/paper/DOI:{urllib.parse.quote(seed['doi'])}?fields={PAPER_FIELDS}"
    else:
        url = f"{API}/paper/search/match?" + urllib.parse.urlencode(
            {"query": seed["title"], "fields": PAPER_FIELDS})
    found = get(url, key)
    if found and "data" in found:
        found = found["data"][0] if found["data"] else None
    return found, url


def harvest(paper_id, key):
    base = f"{API}/paper/{paper_id}/citations?fields={CITING_FIELDS}&limit=1000"
    rows, offset = [], 0
    while offset is not None:
        page = get(f"{base}&offset={offset}", key)
        rows.extend(page.get("data") or [])
        offset = page.get("next")
    return base, rows


def main():
    seeds = tomllib.loads((ROOT / "protocol" / "seeds.toml").read_text(encoding="utf-8"))["seed"]
    key = api_key()
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M")
    (ROOT / "raw").mkdir(exist_ok=True)
    manifest = {"stamp": stamp, "source": "Semantic Scholar", "api_key_used": bool(key),
                "fields": CITING_FIELDS, "seeds": []}
    for s in seeds:
        paper, lookup = resolve(s, key)
        entry = {**s, "lookup": lookup}
        if not paper:
            entry.update(found=None, reported=0, retrieved=0)
            print(f"{s['key']:<24} not found", file=sys.stderr)
        else:
            a, b = norm(paper.get("title")), norm(s["title"])
            if not (a.startswith(b[:40]) or b.startswith(a[:40])):
                raise SystemExit(f"{s['key']}: Semantic Scholar found {paper.get('title')!r}")
            query, rows = harvest(paper["paperId"], key)
            with gzip.open(ROOT / f"raw/{stamp}-s2-cites-{s['key']}.jsonl.gz", "wt", encoding="utf-8") as f:
                for row in rows:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
            entry.update(found={k: paper.get(k) for k in ("paperId", "title", "year")},
                         query=query, reported=paper.get("citationCount"), retrieved=len(rows))
            print(f"{s['key']:<24} {paper.get('citationCount'):>5} reported, {len(rows):>5} retrieved",
                  file=sys.stderr)
        manifest["seeds"].append(entry)
    (ROOT / f"raw/{stamp}-s2-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(stamp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
