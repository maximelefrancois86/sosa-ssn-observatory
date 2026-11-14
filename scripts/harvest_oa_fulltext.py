#!/usr/bin/env python3
"""Retrieve the open-access full texts that S2ORC does not give, for strata A and B.

    python3 -I scripts/harvest_oa_fulltext.py            # all of them (a long run)
    python3 -I scripts/harvest_oa_fulltext.py --limit 50 # the first 50, in a seeded order
    python3 -I scripts/harvest_oa_fulltext.py --population d --weak-sample 40
        # stratum D: every strong signal, and a seeded sample of the weak ones

Follows the pilot of scripts/pilot_oa_fulltext.py (results/oa-pilot.md) on every candidate of
strata A and B that has a DOI, is open access in OpenAlex, and has no S2ORC full text:

1. its locations are asked to OpenAlex (`best_oa_location`, `locations`), by batches of 50;
   the answers are kept as a stamped raw harvest;
2. each PDF URL is tried in turn, once, until one returns a file that starts with `%PDF`
   (generic User-Agent, timeout, size limit, a pause between downloads);
3. the text is extracted with `pdftotext`, and kept with the PDF in fulltext/oa-pdf/<stamp>/
   (not versioned).

Writes raw/<stamp>-openalex-locations-all.jsonl.gz and raw/<stamp>-oa-fulltext-manifest.json
(for each work: URLs tried, outcome, size, SHA-256). scripts/build_items.py reads the texts
of the last manifest as a second source of full texts. Standard library only, apart from
`pdftotext`.
"""
import argparse
import collections
import datetime as dt
import gzip
import json
import pathlib
import random
import subprocess
import sys
import time
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from harvest_openalex import api_key, get  # noqa: E402
from pilot_oa_fulltext import API, download  # noqa: E402
from strata import ROOT, load_corpus, load_seeds, stratum  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--seed", type=int, default=20261111)
    ap.add_argument("--pause", type=float, default=1.5)
    ap.add_argument("--population", choices=["ab", "d"], default="ab")
    ap.add_argument("--weak-sample", type=int, default=0, help="stratum D: weak signals drawn at random")
    args = ap.parse_args(argv)
    key = api_key()
    role = {s["key"]: s["role"] for s in load_seeds()}
    items = [json.loads(l) for l in open(ROOT / "screening/items.jsonl", encoding="utf-8")]
    have = {it["doi"] for it in items if it["doi"] and it["item"].startswith("s2orc:")}
    pool = sorted((w for w in load_corpus() if stratum(w, role) in ("A", "B") and w["doi"]
                   and w["doi"].lower() not in have and w["oa_status"] not in ("closed", "", None)),
                  key=lambda w: w["openalex"])
    if args.population == "d":  # stratum D of the OpenAlex full-text search (scripts/stratum_d.py)
        with gzip.open(ROOT / "corpus/stratum-d-candidates.jsonl.gz", "rt", encoding="utf-8") as f:
            dw = [json.loads(line) for line in f]
        dw = [dict(w, stratum_override="D") for w in dw if w["doi"] and w["doi"].lower() not in have
              and w["oa_status"] not in ("closed", "", None)]
        strong = sorted((w for w in dw if w["signal"] == "strong"), key=lambda w: w["openalex"])
        weak = sorted((w for w in dw if w["signal"] == "weak"), key=lambda w: w["openalex"])
        pool = strong + random.Random(args.seed).sample(weak, min(args.weak_sample, len(weak)))
    random.Random(args.seed).shuffle(pool)
    if args.limit:
        pool = pool[:args.limit]
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M")

    located, queries = [], []
    for i in range(0, len(pool), 50):
        ids = [w["openalex"] for w in pool[i:i + 50]]
        url = (f"{API}?filter=openalex_id:{'|'.join(ids)}&per-page=200"
               "&select=id,doi,open_access,best_oa_location,locations")
        located += get(url, key)["results"]
        queries.append(url)
    (ROOT / f"raw/{stamp}-openalex-locations-all.jsonl.gz").write_bytes(
        gzip.compress("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in located).encode(), mtime=0))
    by_id = {r["id"].rsplit("/", 1)[-1]: r for r in located}

    out = ROOT / f"fulltext/oa-pdf/{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    rows, outcomes = [], collections.Counter()
    for n, w in enumerate(pool, 1):
        r = by_id.get(w["openalex"], {})
        urls = []
        for loc in [r.get("best_oa_location") or {}] + (r.get("locations") or []):
            if loc.get("pdf_url") and loc["pdf_url"] not in urls:
                urls.append(loc["pdf_url"])
        entry = {"openalex": w["openalex"], "doi": w["doi"],
                 "stratum": w.get("stratum_override") or stratum(w, role),
                 "oa_status": w["oa_status"], "tried": []}
        if w.get("signal"):
            entry["signal"] = w["signal"]
        outcome = "no PDF URL"
        for u in urls[:4]:
            pdf = out / f"{w['openalex']}.pdf"
            res = download(u, pdf)
            entry["tried"].append({"url": u, **res})
            time.sleep(args.pause)
            if res["outcome"] == "pdf":
                txt = out / f"{w['openalex']}.txt"
                done = subprocess.run(["pdftotext", "-enc", "UTF-8", str(pdf), str(txt)], capture_output=True,
                                      timeout=180)
                ok = done.returncode == 0 and txt.exists() and txt.read_text(encoding="utf-8", errors="replace").strip()
                outcome = "text" if ok else "pdf without text"
                break
            outcome = "failed"
        entry["outcome"] = outcome
        outcomes[outcome] += 1
        rows.append(entry)
        if n % 25 == 0:
            print(f"{n}/{len(pool)} {dict(outcomes)}", file=sys.stderr, flush=True)
            manifest = {"stamp": stamp, "seed": args.seed, "pool": len(pool), "done": n,
                        "queries": [q for q in queries], "api_key_used": bool(key), "works": rows}
            (ROOT / f"raw/{stamp}-oa-fulltext-manifest.json").write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest = {"stamp": stamp, "seed": args.seed, "pool": len(pool), "done": len(rows), "complete": True,
                "population": args.population, "weak_sample": args.weak_sample,
                "queries": queries, "api_key_used": bool(key), "works": rows,
                "outcomes": dict(outcomes),
                "hosts_failed": dict(collections.Counter(urllib.parse.urlparse(e["tried"][-1]["url"]).netloc
                                                         for e in rows if e["outcome"] == "failed"))}
    (ROOT / f"raw/{stamp}-oa-fulltext-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{stamp}: {dict(outcomes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
