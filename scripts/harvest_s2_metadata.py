#!/usr/bin/env python3
"""Bibliographic metadata from Semantic Scholar for the items that no harvest describes.

    python3 -I scripts/harvest_s2_metadata.py

The citations shown in the review application (scripts/item_citations.py) come from the
OpenAlex corpus and from the Semantic Scholar citation harvest. The works found only in the
S2ORC full texts (stratum D) are in neither: this script asks the batch endpoint of
Semantic Scholar for them, by CorpusId, and writes, for one run stamped T:

    raw/T-s2-metadata.jsonl.gz       the records exactly as Semantic Scholar returns them
    raw/T-s2-metadata-manifest.json  the query (without key), the identifiers asked, counts

The API key, if any, is read as in harvest_s2.py and never written. Standard library only.
"""
import datetime as dt
import gzip
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from harvest_s2 import api_key, PAUSE  # noqa: E402
from item_citations import load_sources  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = "https://api.semanticscholar.org/graph/v1/paper/batch"
FIELDS = "paperId,externalIds,title,year,venue,publicationVenue,journal,publicationTypes,publicationDate,authors"


def main():
    items = [json.loads(line) for line in open(ROOT / "screening/items.jsonl", encoding="utf-8")]
    sources = load_sources()
    wanted = sorted({it["corpusid"] for it in items if it["passages"] and it.get("corpusid")
                     and not sources.find(it)})
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M")
    key = api_key()
    records = []
    for i in range(0, len(wanted), 400):
        chunk = wanted[i:i + 400]
        headers = {"User-Agent": "sosa-ssn-slr-harvest", "Content-Type": "application/json"}
        if key:
            headers["x-api-key"] = key
        req = urllib.request.Request(f"{URL}?fields={FIELDS}", method="POST", headers=headers,
                                     data=json.dumps({"ids": [f"CorpusId:{c}" for c in chunk]}).encode())
        for attempt in range(7):
            time.sleep(PAUSE * 2 ** attempt if attempt else PAUSE)   # 429 and 5xx: back off
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    records += [x for x in json.load(r) if x]
                break
            except urllib.error.HTTPError as e:
                if e.code not in (429, 500, 502, 503, 504) or attempt == 6:
                    raise
    with gzip.open(ROOT / f"raw/{stamp}-s2-metadata.jsonl.gz", "wt", encoding="utf-8") as f:
        for x in records:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    manifest = {"stamp": stamp, "source": "Semantic Scholar", "endpoint": URL, "fields": FIELDS,
                "api_key_used": bool(key), "asked": len(wanted), "received": len(records),
                "corpusids": wanted, "pause": PAUSE}
    (ROOT / f"raw/{stamp}-s2-metadata-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"raw/{stamp}-s2-metadata.jsonl.gz: {len(records)} records of {len(wanted)} asked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
