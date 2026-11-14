#!/usr/bin/env python3
"""The term lists of SSN-XG, SOSA/SSN 2017 and the SSN 2023 Edition, read from git.

    ~/.venvs/ldpy/bin/python -I scripts/term_inventory.py     # needs rdflib
    ... --sdw ../../sdw --sdw-rev gh-pages --sosa ../../sdw-sosa-ssn --sosa-rev gh-pages

Writes results/terms.csv (one row per version and term) and results/terms.md (counts).
Files are read with `git show <rev>:<path>`, never from a working tree, so that the
inventory names the commit it describes. A term is an IRI of a SOSA/SSN namespace typed
as a class, a property or an individual, and declared by the file (it carries
rdfs:isDefinedBy, rdfs:label or skos:definition there).
"""
import argparse
import collections
import csv
import pathlib
import subprocess
import sys

from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS, SKOS

ROOT = pathlib.Path(__file__).resolve().parent.parent
NAMESPACES = ("http://purl.oclc.org/NET/ssnx/ssn#", "http://www.w3.org/ns/sosa/",
              "http://www.w3.org/ns/ssn/systems/", "http://www.w3.org/ns/ssn/")
KINDS = {OWL.Class: "class", OWL.ObjectProperty: "object property",
         OWL.DatatypeProperty: "datatype property", OWL.AnnotationProperty: "annotation property",
         RDF.Property: "property", OWL.NamedIndividual: "individual", SKOS.Concept: "individual"}


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout


def namespace(iri):
    return next((ns for ns in NAMESPACES if iri.startswith(ns)), None)


def terms_of(repo, rev, paths, version):
    rows = []
    for path in paths:
        g = Graph()
        g.parse(data=git(repo, "show", f"{rev}:{path}"), format="turtle")
        for s in set(g.subjects(RDF.type, None)):
            if not isinstance(s, URIRef) or not namespace(str(s)):
                continue
            if not any((s, p, None) in g for p in (RDFS.isDefinedBy, RDFS.label, SKOS.definition)):
                continue
            kinds = [KINDS[t] for t in g.objects(s, RDF.type) if t in KINDS]
            if not kinds:
                continue
            kind = next((k for k in kinds if k not in ("property", "individual")), kinds[0])
            rows.append({"version": version, "file": path, "namespace": namespace(str(s)),
                         "term": str(s), "kind": kind,
                         "deprecated": "yes" if (s, OWL.deprecated, None) in g else "",
                         "defined_by": str(g.value(s, RDFS.isDefinedBy) or "")})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--sdw", type=pathlib.Path, default=ROOT.parent.parent / "sdw")
    ap.add_argument("--sdw-rev", default="gh-pages")
    ap.add_argument("--sosa", type=pathlib.Path, default=ROOT.parent.parent / "sdw-sosa-ssn")
    ap.add_argument("--sosa-rev", default="gh-pages")
    a = ap.parse_args(argv)

    sdw_commit = git(a.sdw, "log", "-1", "--format=%h %ad", "--date=short", a.sdw_rev).strip()
    sosa_commit = git(a.sosa, "log", "-1", "--format=%h %ad", "--date=short", a.sosa_rev).strip()
    rows = terms_of(a.sdw, a.sdw_rev, ["ssn/integrated/ssnx.ttl"], "ssn-xg")
    rows += terms_of(a.sdw, a.sdw_rev, [f"ssn/integrated/{f}.ttl" for f in ("sosa", "ssn", "ssn-system")],
                     "sosa-ssn-2017")
    files_2023 = [p for p in git(a.sosa, "ls-tree", "-r", "--name-only", a.sosa_rev,
                                 "ssn/rdf/ontology/core/", "ssn/rdf/ontology/extensions/").split()
                  if p.endswith(".ttl")]
    rows += terms_of(a.sosa, a.sosa_rev, files_2023, "ssn-2023")

    # A term declared in several files of one version counts once, under its first file.
    seen, unique = set(), []
    for r in rows:
        if (r["version"], r["term"]) not in seen:
            seen.add((r["version"], r["term"]))
            unique.append(r)
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    with open(out / "terms.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(unique[0]))
        w.writeheader()
        w.writerows(sorted(unique, key=lambda r: (r["version"], r["term"])))

    L = ["# SOSA/SSN terms by version\n",
         f"`w3c/sdw` at `{sdw_commit}` (SSN-XG and 2017), `w3c/sdw-sosa-ssn` at `{sosa_commit}` "
         "(2023 Edition). Computed by `scripts/term_inventory.py`; the list is `results/terms.csv`.\n",
         "| version | namespace | terms | of which deprecated |", "|---|---|---|---|"]
    c = collections.Counter((r["version"], r["namespace"]) for r in unique)
    d = collections.Counter((r["version"], r["namespace"]) for r in unique if r["deprecated"])
    for (v, ns), k in sorted(c.items()):
        L.append(f"| {v} | `{ns}` | {k} | {d[(v, ns)]} |")
    tot = collections.Counter(r["version"] for r in unique)
    L += ["", "Totals: " + ", ".join(f"{v} {k}" for v, k in sorted(tot.items())) + "."]
    L += ["", "| version | file | terms |", "|---|---|---|"]
    for (v, p), k in sorted(collections.Counter((r["version"], r["file"]) for r in unique).items()):
        L.append(f"| {v} | `{p}` | {k} |")
    old = {r["term"] for r in unique if r["version"] == "sosa-ssn-2017"}
    new = {r["term"] for r in unique if r["version"] == "ssn-2023"}
    L += ["", f"- Terms of 2017 still declared in 2023: {len(old & new)}",
          f"- Terms of 2017 no longer declared in 2023 (moved or removed): {len(old - new)}",
          f"- Terms of 2023 absent from 2017: {len(new - old)}"]
    (out / "terms.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"results/terms.csv: {len(unique)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
