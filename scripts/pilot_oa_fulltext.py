#!/usr/bin/env python3
"""Pilot of the retrieval of open-access full texts that S2ORC does not give.

    python3 -I scripts/pilot_oa_fulltext.py --sample 30 --seed 20261111
        # raw/T-openalex-locations.jsonl.gz, raw/T-oa-pilot-manifest.json,
        # fulltext/oa-pdf/T/<work>.pdf and .txt (not versioned), results/oa-pilot.md and .json

The candidates of strata A and B that are open access in OpenAlex but have no S2ORC full
text (results/detection.md, "Full texts still to retrieve") are the next source of full
texts. This pilot measures, on a random sample drawn with a recorded seed, what their
retrieval costs before it is done for all:

1. the locations of the sampled works are asked to OpenAlex again (the citation harvest did
   not keep them): `best_oa_location` and `locations`, with their `pdf_url`; the answers are
   kept as a stamped raw harvest;
2. the first PDF URL of each work is downloaded once, with a generic User-Agent, a timeout
   and a size limit; a file is kept only if it starts with `%PDF`; status, size and SHA-256
   are recorded in the manifest;
3. the text is extracted with `pdftotext` (poppler) and cut before the last heading that
   reads as a reference list; the occurrences of SOSA/SSN are searched in what remains, with
   the matcher of scripts/build_items.py.

The PDFs and their text are downloaded data: not versioned, never executed, read only by
`pdftotext` and by this script. Standard library only, apart from `pdftotext`.
"""
import argparse
import collections
import datetime as dt
import gzip
import hashlib
import json
import pathlib
import random
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_items import NAMES, REFS, matcher  # noqa: E402
from harvest_openalex import api_key, get  # noqa: E402
from strata import ROOT, load_corpus, load_seeds, stratum  # noqa: E402

API = "https://api.openalex.org/works"
MAX_BYTES = 60_000_000


def table(rows, head):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research text mining; SOSA/SSN review)",
                                               "Accept": "application/pdf,*/*;q=0.5"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read(MAX_BYTES + 1)
            status, ctype = r.status, r.headers.get("Content-Type", "")
    except Exception as e:
        return {"outcome": "error", "error": repr(e)[:200]}
    if len(data) > MAX_BYTES:
        return {"outcome": "too large", "status": status}
    if not data.startswith(b"%PDF"):
        return {"outcome": "not a PDF", "status": status, "content_type": ctype, "bytes": len(data)}
    path.write_bytes(data)
    return {"outcome": "pdf", "status": status, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--sample", type=int, default=30)
    ap.add_argument("--seed", type=int, default=20261111)
    args = ap.parse_args(argv)
    key = api_key()
    role = {s["key"]: s["role"] for s in load_seeds()}
    items = [json.loads(l) for l in open(ROOT / "screening/items.jsonl", encoding="utf-8")]
    have = {it["doi"] for it in items if it["doi"]}
    pool = sorted((w for w in load_corpus() if stratum(w, role) in ("A", "B") and w["doi"]
                   and w["doi"].lower() not in have and w["oa_status"] not in ("closed", "", None)),
                  key=lambda w: w["openalex"])
    sample = random.Random(args.seed).sample(pool, min(args.sample, len(pool)))
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M")

    ids = [w["openalex"] for w in sample]
    url = (f"{API}?filter=openalex_id:{'|'.join(ids)}&per-page=200"
           "&select=id,doi,open_access,best_oa_location,locations")
    located = get(url, key)["results"]
    raw = ROOT / f"raw/{stamp}-openalex-locations.jsonl.gz"
    raw.write_bytes(gzip.compress("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in located).encode(), mtime=0))
    by_id = {r["id"].rsplit("/", 1)[-1]: r for r in located}

    out = ROOT / f"fulltext/oa-pdf/{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    rx = matcher({"namespace", "prefixed", "local"})
    rows, outcomes = [], collections.Counter()
    for w in sample:
        r = by_id.get(w["openalex"], {})
        urls = []
        for loc in [r.get("best_oa_location") or {}] + (r.get("locations") or []):
            if loc.get("pdf_url") and loc["pdf_url"] not in urls:
                urls.append(loc["pdf_url"])
        entry = {"openalex": w["openalex"], "doi": w["doi"], "stratum": stratum(w, role),
                 "oa_status": w["oa_status"], "pdf_urls": urls}
        if not urls:
            entry["outcome"] = "no PDF URL"
        else:
            pdf = out / f"{w['openalex']}.pdf"
            entry.update(download(urls[0], pdf))
            entry["host"] = urllib.parse.urlparse(urls[0]).netloc
            time.sleep(2)
            if entry["outcome"] == "pdf":
                txt = out / f"{w['openalex']}.txt"
                done = subprocess.run(["pdftotext", "-enc", "UTF-8", str(pdf), str(txt)], capture_output=True,
                                      timeout=120)
                text = txt.read_text(encoding="utf-8", errors="replace") if done.returncode == 0 and txt.exists() else ""
                heads = list(REFS.finditer(text))
                body = text[:heads[-1].start()] if heads else text
                entry.update(words=len(text.split()), body_words=len(body.split()), refs_cut=bool(heads),
                             terms=len(rx.findall(body)), names=len(NAMES.findall(body)))
                if not text.strip():
                    entry["outcome"] = "no text"
        outcomes[entry["outcome"]] += 1
        rows.append(entry)

    manifest = {"stamp": stamp, "seed": args.seed, "pool": len(pool), "sample": len(sample),
                "locations_query": url.split("&api_key")[0], "api_key_used": bool(key), "works": rows}
    (ROOT / f"raw/{stamp}-oa-pilot-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                                                             encoding="utf-8")
    texts = [r for r in rows if r["outcome"] == "pdf"]
    named = [r for r in texts if r["terms"] or r["names"]]
    hosts = collections.Counter(r.get("host", "") for r in rows if r["outcome"] not in ("pdf", "no PDF URL"))
    L = ["# Pilot: open-access full texts that S2ORC does not give\n",
         f"Candidates of strata A and B with a DOI, open access in OpenAlex, without an S2ORC full text: "
         f"{len(pool)}; random sample of {len(sample)} (seed {args.seed}); locations asked to OpenAlex "
         f"(`raw/{raw.name}`), first PDF URL downloaded once; computed by `scripts/pilot_oa_fulltext.py`, "
         f"manifest `raw/{stamp}-oa-pilot-manifest.json`.\n",
         table(sorted(outcomes.items(), key=lambda kv: -kv[1]), ["outcome", "works"]) + "\n",
         f"- Text extracted: {len(texts)}; reference list found and cut: {sum(r['refs_cut'] for r in texts)}; "
         f"naming SOSA/SSN in the body: {len(named)}; with terms: {sum(1 for r in texts if r['terms'])}\n",
         "## Failed downloads by host\n",
         table(hosts.most_common(), ["host", "works"]) + "\n"]
    (ROOT / "results/oa-pilot.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (ROOT / "results/oa-pilot.json").write_text(json.dumps(
        {"pool": len(pool), "sample": len(sample), "seed": args.seed, "outcomes": dict(outcomes),
         "texts": len(texts), "refs_cut": sum(r["refs_cut"] for r in texts), "naming": len(named),
         "with_terms": sum(1 for r in texts if r["terms"])}, indent=1) + "\n", encoding="utf-8")
    print(f"results/oa-pilot.md: {dict(outcomes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
