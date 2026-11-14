#!/usr/bin/env python3
"""Recommendations computed by script, for the review application.

    python3 -I scripts/recommend_script.py   # screening/recommendations.jsonl (source "script")

Reads screening/items.jsonl (scripts/build_items.py) and results/search-strings.csv.
For each item, recommends `engagement` when a rule settles it without reading:

- `E0` for a candidate whose body never names SOSA/SSN, neither by a term nor by name in
  prose (SOSA, SSN, Semantic Sensor Network): the seed is cited for another point
  (protocol § 5, rule checked on a random sample that is read);
- `E1` for a candidate that names SOSA/SSN only in prose, without any term, and only in
  sections whose header reads as background (introduction, background, related work, state
  of the art, literature review): a mention;
- nothing otherwise: the passages are read.

For each item with passages, it also recommends:

- `terms`: the prefixed names found in the passages;
- `version_used`: from the namespaces and names found — `ssn-xg` for the purl.oclc.org
  namespace, `ssn-2023` when a name that only the 2023 Edition declares is found,
  `sosa-ssn-2017` for the w3.org namespaces or `sosa:` names otherwise, `mixed` when the
  SSN-XG namespace and a later one are both found, `unknown` when only `ssn:` names are
  found (the prefix is the same in SSN-XG and 2017);
- `modules`: none yet (to be derived from the terms once the term-to-module table exists).

A recommendation is never a decision: the reader accepts or corrects it in the
application, which keeps both. Lines written by the model, if any, are kept: this script
replaces only the lines whose source is "script". Standard library only.
"""
import csv
import datetime as dt
import json
import re
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
VERSION = "recommend_script.py 2"
BACKGROUND = re.compile(r"introduction|background|related|state of the art|state-of-the-art|"
                        r"literature|previous work|prior work|preliminar", re.I)


def main():
    with open(ROOT / "results/search-strings.csv", encoding="utf-8", newline="") as f:
        versions = {r["string"]: set(r["versions"].split(";")) for r in csv.DictReader(f)}
    items = [json.loads(line) for line in open(ROOT / "screening/items.jsonl", encoding="utf-8")]
    path = ROOT / "screening/recommendations.jsonl"
    kept = []
    if path.exists():
        kept = [json.loads(line) for line in open(path, encoding="utf-8")
                if json.loads(line).get("source") != "script"]
    today = dt.date.today().isoformat()
    out = []
    for it in items:
        base = {"item": it["item"], "source": "script", "version": VERSION, "date": today}
        if not it["passages"]:
            out.append({**base, "question": "engagement", "value": "E0",
                        "rule": "no occurrence of SOSA/SSN in the body, not even by name"})
            continue
        if (not any(p["terms"] for p in it["passages"])
                and all(BACKGROUND.search(p["section"] or "") for p in it["passages"])):
            out.append({**base, "question": "engagement", "value": "E1",
                        "rule": "named in prose only, only in background sections"})
        found = set()
        for p in it["passages"]:
            found.update(p["found"])
        prefixed = sorted(s for s in found if ":" in s and "/" not in s)
        xg = any("purl.oclc.org" in s for s in found)
        later_ns = any("w3.org/ns/" in s for s in found) or any(s.startswith("sosa:") for s in prefixed)
        only_2023 = any(versions.get(s) == {"ssn-2023"} for s in prefixed)
        if xg and later_ns:
            version = "mixed"
        elif xg:
            version = "ssn-xg"
        elif only_2023:
            version = "ssn-2023"
        elif later_ns:
            version = "sosa-ssn-2017"
        else:
            version = "unknown"
        out.append({**base, "question": "terms", "value": prefixed})
        out.append({**base, "question": "version_used", "value": version})
    with open(path, "w", encoding="utf-8") as f:
        for r in kept + out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    # counts by stratum, for results/macros.tex (scripts/article_macros.py): recommendations, not results
    stratum = {it["item"]: it["stratum"] for it in items}
    counts = {}
    for r in out:
        if r["question"] in ("engagement", "version_used"):
            q = counts.setdefault(r["question"], {})
            q.setdefault(stratum[r["item"]], {}).setdefault(r["value"], 0)
            q[stratum[r["item"]]][r["value"]] += 1
    (ROOT / "results/recommendations.json").write_text(json.dumps(
        {"version": VERSION, "items": len(items), "by_stratum": counts}, indent=1, sort_keys=True) + "\n",
        encoding="utf-8")
    print(f"screening/recommendations.jsonl: {len(out)} script recommendations, {len(kept)} others kept")
    return 0


if __name__ == "__main__":
    sys.exit(main())
