#!/usr/bin/env python3
"""Snapshot of the lists of predatory publishers and journals of predatoryjournals.org.

    python3 -I scripts/harvest_venue_lists.py

The site (https://www.predatoryjournals.org/the-list/publishers and …/journals) embeds two
public Google Sheets; this script downloads them as CSV through the sheets' query
endpoint and writes, for one run stamped T (local time, YYYY-MM-DDTHHMM):

    raw/T-predatoryjournals-publishers.csv   the sheet exactly as served
    raw/T-predatoryjournals-journals.csv
    raw/T-predatoryjournals-manifest.json    URLs, rows, SHA-256

The lists are opinions of the site's maintainers, dated by the snapshot; how the review
uses them is in protocol/protocol.md (section 4) and protocol/venue-risk.toml.
Standard library only.
"""
import csv
import datetime as dt
import hashlib
import io
import json
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
LISTS = {
    "publishers": ("https://www.predatoryjournals.org/the-list/publishers",
                   "1BHM4aJljhbOAzSpkX1kXDUEvy6vxREZu5WJaDH6M1Vk"),
    "journals": ("https://www.predatoryjournals.org/the-list/journals",
                 "1Qa1lAlSbl7iiKddYINNsDB4wxI7uUA4IVseeLnCc5U4"),
}
SHEET = "https://docs.google.com/spreadsheets/d/{}/gviz/tq?tqx=out:csv"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "sosa-ssn-slr-harvest"})
    with urllib.request.urlopen(req, timeout=60) as r:
        if "text/csv" not in r.headers.get("Content-Type", ""):
            raise RuntimeError(f"{url}: not CSV ({r.headers.get('Content-Type')})")
        return r.read()


def main():
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M")
    (ROOT / "raw").mkdir(exist_ok=True)
    manifest = {"stamp": stamp, "source": "predatoryjournals.org", "lists": []}
    for name, (page, sheet) in LISTS.items():
        url = SHEET.format(sheet)
        data = fetch(url)
        rows = list(csv.reader(io.StringIO(data.decode("utf-8"))))
        (ROOT / f"raw/{stamp}-predatoryjournals-{name}.csv").write_bytes(data)
        manifest["lists"].append({"name": name, "page": page, "query": url, "rows": len(rows),
                                  "sha256": hashlib.sha256(data).hexdigest()})
        print(f"{name:<11} {len(rows):>5} rows", file=sys.stderr)
    (ROOT / f"raw/{stamp}-predatoryjournals-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(stamp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
