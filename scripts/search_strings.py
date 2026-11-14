#!/usr/bin/env python3
"""The strings that the full-text search (stratum D) and the detection in full texts look for.

    python3 -I scripts/search_strings.py      # writes results/search-strings.csv

Reads results/terms.csv (scripts/term_inventory.py). One row per string:

    namespace   a namespace IRI without its scheme, e.g. w3.org/ns/sosa
    prefixed    a prefixed name with the usual prefix of its namespace, e.g. sosa:Observation
    local       a local name distinctive enough to be searched alone, e.g. madeBySensor

A local name is distinctive when it is a compound (camelCase: several words run together),
like `ObservableProperty` or `hasSimpleResult`; a single word (`Observation`, `System`) is
too common to be searched without its prefix, and is listed with `distinctive = no`.
Whether the distinctive local names are kept for stratum D depends on their precision,
measured on a sample (pilotage review/101).
"""
import collections
import csv
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
NAMESPACES = {  # namespace IRI → (searched string, usual prefix)
    "http://purl.oclc.org/NET/ssnx/ssn#": ("purl.oclc.org/NET/ssnx/ssn", "ssn"),
    "http://www.w3.org/ns/sosa/": ("w3.org/ns/sosa", "sosa"),
    "http://www.w3.org/ns/ssn/": ("w3.org/ns/ssn", "ssn"),
    "http://www.w3.org/ns/ssn/systems/": ("w3.org/ns/ssn/systems", "ssn-system"),
}
COMPOUND = re.compile(r"^[a-z]+[A-Z]|^[A-Z][a-z]+[A-Z]")


def main():
    with open(ROOT / "results/terms.csv", encoding="utf-8", newline="") as f:
        terms = list(csv.DictReader(f))
    rows = collections.defaultdict(lambda: {"versions": set(), "kind": "", "distinctive": ""})
    for t in terms:
        ns = t["namespace"]
        if ns not in NAMESPACES:
            raise SystemExit(f"unknown namespace {ns}")
        searched, prefix = NAMESPACES[ns]
        local = t["term"][len(ns):]
        for string, kind, distinctive in (
                (searched, "namespace", "yes"),
                (f"{prefix}:{local}", "prefixed", "yes"),
                (local, "local", "yes" if COMPOUND.match(local) else "no")):
            row = rows[string]
            row["versions"].add(t["version"])
            row["kind"], row["distinctive"] = kind, distinctive
    out = ROOT / "results/search-strings.csv"
    with open(out, "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["string", "kind", "distinctive", "versions"])
        for string, row in sorted(rows.items(), key=lambda kv: (kv[1]["kind"], kv[0].lower())):
            wr.writerow([string, row["kind"], row["distinctive"], ";".join(sorted(row["versions"]))])
    count = collections.Counter((r["kind"], r["distinctive"]) for r in rows.values())
    print(f"results/search-strings.csv: " + ", ".join(f"{k} {d}: {n}" for (k, d), n in sorted(count.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
