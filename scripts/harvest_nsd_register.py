#!/usr/bin/env python3
"""Snapshot of the journal list of the Norwegian Register for Scientific Journals.

    python3 -I scripts/harvest_nsd_register.py

The register (kanalregister.hkdir.no, licence CC BY 4.0 / NLOD) gives each journal, with
its ISSNs, a level per year: 2 (leading), 1 (scientific), 0 (not scientific) or X (under
discussion). Writes, for one run stamped T:

    raw/T-nsd-journals.csv             the CSV exactly as served
    raw/T-nsd-journals-manifest.json   URL, rows, SHA-256

How the review uses it: protocol/venue-risk.toml and scripts/venue_risk.py.
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
URL = "https://kanalregister.hkdir.no/publiseringskanaler/csvliste/tidsskrift"


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "sosa-ssn-slr-harvest"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig")), delimiter=";"))
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M")
    (ROOT / f"raw/{stamp}-nsd-journals.csv").write_bytes(data)
    manifest = {"stamp": stamp, "source": "Norwegian Register for Scientific Journals", "url": URL,
                "rows": len(rows) - 1, "columns": rows[0] if rows else [],
                "sha256": hashlib.sha256(data).hexdigest()}
    (ROOT / f"raw/{stamp}-nsd-journals-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{stamp}: {len(rows) - 1} journals")
    return 0


if __name__ == "__main__":
    sys.exit(main())
