#!/usr/bin/env python3
"""What the Semantic Scholar harvest adds to the OpenAlex candidate corpus.

    python3 -I scripts/compare_sources.py     # writes results/sources.md

Reads the last Semantic Scholar harvest in raw/ (scripts/harvest_s2.py) and the OpenAlex
candidate corpus. A Semantic Scholar paper is the same work as an OpenAlex candidate when
their DOIs are equal, or else when their normalised titles are equal and their years differ
by one at most. Nothing is merged yet: the figures say how much a merge would add.
"""
import collections
import gzip
import json
import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from strata import ROOT, load_corpus, load_seeds  # noqa: E402


def norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def table(rows, head):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def pct(n, d):
    return f"{100 * n / d:.1f} %" if d else "—"


def main():
    manifest_path = sorted(ROOT.glob("raw/*-s2-manifest.json"))[-1]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    stamp = manifest["stamp"]
    seeds = load_seeds()
    role = {s["key"]: s["role"] for s in seeds}

    corpus = load_corpus()
    by_doi = {w["doi"].lower(): w for w in corpus if w["doi"]}
    by_title = collections.defaultdict(list)
    for w in corpus:
        by_title[norm(w["title"])].append(w)

    def match(paper):
        doi = ((paper.get("externalIds") or {}).get("DOI") or "").lower()
        if doi and doi in by_doi:
            return by_doi[doi]
        for w in by_title.get(norm(paper.get("title")), []):
            if paper.get("year") and w["year"] and abs(paper["year"] - w["year"]) <= 1:
                return w
        return None

    papers, seeds_of, contexts = {}, collections.defaultdict(set), collections.Counter()
    per_seed = []
    for entry in manifest["seeds"]:
        key = entry["key"]
        path = ROOT / f"raw/{stamp}-s2-cites-{key}.jsonl.gz"
        if not path.exists():
            per_seed.append((key, "not found", "—", "—"))
            continue
        matched = unmatched = 0
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                p = rec.get("citingPaper") or {}
                if not p.get("paperId"):
                    continue
                papers[p["paperId"]] = p
                seeds_of[p["paperId"]].add(key)
                contexts["records"] += 1
                contexts["with contexts"] += bool(rec.get("contexts"))
                if match(p):
                    matched += 1
                else:
                    unmatched += 1
        per_seed.append((key, matched + unmatched, matched, unmatched))

    new = {pid: p for pid, p in papers.items() if not match(p)}

    def stratum(pid):
        roles = {role[s] for s in seeds_of[pid]}
        if roles - {"lineage"}:
            return "A"
        return "B" if (new[pid].get("year") or 0) >= 2018 else "C"

    st = collections.Counter(stratum(pid) for pid in new)
    found = len(papers) - len(new)
    L = ["# Semantic Scholar against the OpenAlex candidate corpus\n",
         f"Semantic Scholar harvest `{stamp}`, OpenAlex corpus of `results/scoping.md`; computed by "
         "`scripts/compare_sources.py`. Same work: equal DOI, or equal normalised title within "
         "one year.\n",
         f"- Distinct citing papers in Semantic Scholar: {len(papers)}; already OpenAlex "
         f"candidates: {found} ({pct(found, len(papers))}); **not in the OpenAlex corpus: "
         f"{len(new)}**",
         f"- Of these, by the strata rule (review/101): A {st['A']}, B {st['B']}, C {st['C']}",
         f"- Citation records with citation contexts: {contexts['with contexts']} of "
         f"{contexts['records']} ({pct(contexts['with contexts'], contexts['records'])})\n",
         "## Per seed\n",
         table(per_seed, ["seed", "citing papers in Semantic Scholar", "in the OpenAlex corpus",
                          "not in it"]) + "\n"]
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "sources.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    F = {"harvest": stamp, "s2_citing": len(papers), "in_openalex": found, "not_in_openalex": len(new),
         "not_in_openalex_by_stratum": {k: st[k] for k in "ABC"},
         "citation_records": contexts["records"], "with_contexts": contexts["with contexts"],
         "per_seed": {k: {"s2": a, "in_openalex": m, "not_in_openalex": u} for k, a, m, u in per_seed}}
    (out / "sources.json").write_text(json.dumps(F, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"results/sources.md: {len(papers)} Semantic Scholar papers, {len(new)} not in OpenAlex")
    return 0


if __name__ == "__main__":
    sys.exit(main())
