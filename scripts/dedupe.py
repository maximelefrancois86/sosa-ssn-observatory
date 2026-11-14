#!/usr/bin/env python3
"""Probable duplicates of the candidate corpus: versions of one work under several records.

    python3 -I scripts/dedupe.py      # corpus/duplicates.csv, results/duplicates.md and .json

Two records of the OpenAlex candidate corpus are taken for versions of one work when their
normalised titles are equal (accents, case and punctuation removed; titles of fewer than four
words are left alone) and their years differ by one at most. In each cluster the record kept
is the most complete version (protocol § 4): a journal article before a conference paper,
before a chapter, a thesis, a report, a preprint; then the one with a DOI; then the most cited.
The others are linked to it. Nothing is removed from the corpus: the clusters are a
proposal, applied when the reference harvest is frozen (pilotage review/102), and a stratum
can change when versions that cite different seeds are merged, which is counted.
Standard library only.
"""
import collections
import csv
import json
import re
import sys
import unicodedata
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from strata import ROOT, load_corpus, load_seeds, stratum  # noqa: E402

RANK = {"article": 0, "review": 0, "data-paper": 0, "conference-paper": 1, "conference-abstract": 1,
        "book-chapter": 2, "book": 2, "dissertation": 3, "report": 4, "preprint": 5}


def norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def table(rows, head):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def main():
    works = load_corpus()
    role = {s["key"]: s["role"] for s in load_seeds()}
    by_title = collections.defaultdict(list)
    for w in works:
        t = norm(w["title"])
        if len(t.split()) >= 4:
            by_title[t].append(w)
    clusters = []
    for t, ws in by_title.items():
        if len(ws) < 2:
            continue
        ws = sorted(ws, key=lambda w: (w["year"] or 0))
        group = [ws[0]]
        for w in ws[1:]:  # split a title shared by works far apart in time
            if w["year"] and group[-1]["year"] and w["year"] - group[-1]["year"] > 1:
                if len(group) > 1:
                    clusters.append(group)
                group = [w]
            else:
                group.append(w)
        if len(group) > 1:
            clusters.append(group)

    def key(w):
        return (RANK.get(w["type"], 6), 0 if w["doi"] else 1, -int(w["cited_by_count"] or 0), w["openalex"])

    rows, changed = [], collections.Counter()
    for i, group in enumerate(sorted(clusters, key=lambda g: norm(g[0]["title"])), 1):
        kept = min(group, key=key)
        seeds = sorted({s for w in group for s in w["seeds"]})
        merged = stratum({"seeds": seeds, "year": kept["year"]}, role)
        if merged != stratum(kept, role):
            changed[(stratum(kept, role), merged)] += 1
        for w in group:
            rows.append({"cluster": i, "openalex": w["openalex"], "kept": w is kept, "type": w["type"],
                         "year": w["year"], "doi": w["doi"], "venue": w["venue"],
                         "stratum": stratum(w, role), "stratum_merged": merged, "title": w["title"]})
    with open(ROOT / "corpus/duplicates.csv", "w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["cluster"])
        wr.writeheader()
        wr.writerows(rows)
    removed = sum(1 for r in rows if not r["kept"])
    after = collections.Counter()
    gone = {r["openalex"] for r in rows if not r["kept"]}
    merged_stratum = {r["openalex"]: r["stratum_merged"] for r in rows if r["kept"]}
    for w in works:
        if w["openalex"] not in gone:
            after[merged_stratum.get(w["openalex"], stratum(w, role))] += 1
    types = collections.Counter(tuple(sorted(r["type"] for r in rows if r["cluster"] == c))
                                for c in {r["cluster"] for r in rows})
    L = ["# Probable duplicates of the candidate corpus\n",
         "Equal normalised titles (four words or more), years one apart at most; computed by "
         "`scripts/dedupe.py`, clusters in `corpus/duplicates.csv`. A proposal: nothing is removed "
         "from the corpus before the reference harvest is frozen.\n",
         f"- Clusters: **{len(clusters)}**, {len(rows)} records; records that would be linked to another: "
         f"**{removed}**; candidates after the merge: {len(works) - removed} (of {len(works)})",
         f"- After the merge, by stratum: " + ", ".join(f"{k} {after[k]}" for k in sorted(after)),
         f"- Clusters whose merged stratum differs from that of the kept record: "
         f"{sum(changed.values())}" + (" (" + ", ".join(f"{a} to {b}: {n}" for (a, b), n in changed.items()) + ")"
                                       if changed else "") + "\n",
         "## Clusters by the types of their records\n",
         table([(" + ".join(t), n) for t, n in types.most_common()], ["types", "clusters"]) + "\n"]
    (ROOT / "results/duplicates.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (ROOT / "results/duplicates.json").write_text(json.dumps(
        {"clusters": len(clusters), "records": len(rows), "linked": removed, "after": len(works) - removed,
         "after_by_stratum": dict(sorted(after.items())),
         "stratum_changes": {f"{a}>{b}": n for (a, b), n in changed.items()}}, indent=1) + "\n", encoding="utf-8")
    print(f"results/duplicates.md: {len(clusters)} clusters, {removed} records to link")
    return 0


if __name__ == "__main__":
    sys.exit(main())
