#!/usr/bin/env python3
"""Scoping figures of the candidate corpus, before any screening.

    python3 -I scripts/scoping.py            # writes results/scoping.md

Reads corpus/openalex-candidates.jsonl.gz and protocol/seeds.toml. Every figure of
results/scoping.md comes from this script; none is copied by hand.
"""
import collections
import gzip
import json
import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from strata import ROOT, STRATA, load_corpus, load_seeds, seed_group, stratum as stratum_of  # noqa: E402

RISKY_DOI_PREFIXES = {"10.3390": "MDPI"}


def norm_title(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def table(rows, head):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def pct(n, d):
    return f"{100 * n / d:.1f} %" if d else "—"


def harvest_ids(stamp):
    """Work IDs per seed in the raw files of one harvest."""
    ids = {}
    for path in ROOT.glob(f"raw/{stamp}-openalex-cites-*.jsonl.gz"):
        seed = path.name[len(f"{stamp}-openalex-cites-"):-len(".jsonl.gz")]
        with gzip.open(path, "rt", encoding="utf-8") as f:
            ids[seed] = {json.loads(line)["id"] for line in f}
    return ids


def changes_since_previous(seeds):
    """How the last harvest differs from the one before it: drift of the index, new seeds."""
    manifests = sorted(ROOT.glob("raw/*-openalex-manifest.json"))
    if len(manifests) < 2:
        return []
    prev, last = (json.loads(m.read_text(encoding="utf-8")) for m in manifests[-2:])
    before, after = harvest_ids(prev["stamp"]), harvest_ids(last["stamp"])
    old_all = set().union(*before.values())
    new_all = set().union(*after.values())
    added_seeds = sorted(set(after) - set(before))
    by_new_seed_only = {i for i in new_all - old_all
                        if not any(i in after[s] for s in after if s in before)}
    L = [f"## Changes since the previous harvest (`{prev['stamp']}`)\n",
         f"- Distinct works: {len(old_all)} then {len(new_all)}: "
         f"{len(new_all - old_all)} added, {len(old_all - new_all)} gone",
         f"- Seeds added: {', '.join(added_seeds) or 'none'}; works added that cite only "
         f"added seeds: {len(by_new_seed_only)}; the others ({len(new_all - old_all) - len(by_new_seed_only)}) "
         f"come from changes in the index between the two harvests\n"]
    reported = {(m["stamp"], s["key"]): s["reported"] for m in (prev, last) for s in m["seeds"]}
    L.append(table([(s["key"], reported.get((prev["stamp"], s["key"]), "—"),
                     reported.get((last["stamp"], s["key"]), "—"))
                    for s in seeds],
                   ["seed", f"citing works, {prev['stamp']}", f"citing works, {last['stamp']}"]) + "\n")
    return L


def main():
    works = load_corpus()
    seeds = load_seeds()
    role = {s["key"]: s["role"] for s in seeds}
    manifest = sorted(ROOT.glob("raw/*-openalex-manifest.json"))[-1]
    stamp = json.loads(manifest.read_text(encoding="utf-8"))["stamp"]
    n = len(works)

    def group(w):
        return seed_group(w, role)

    F = {"harvest": stamp, "candidates": n}  # results/scoping.json, read by article_macros.py

    L = [f"# Scoping figures of the candidate corpus\n",
         f"Harvest `{stamp}` (OpenAlex, forward citations of the seeds in `protocol/seeds.toml`). "
         f"No screening yet: these are **candidates**, not included studies.\n",
         f"- Distinct candidate works: **{n}**"]
    g = collections.Counter(group(w) for w in works)
    F["seed_groups"] = dict(g)
    L.append("- By seed group: " + ", ".join(f"{k} {v} ({pct(v, n)})" for k, v in g.most_common()))
    abstracts = sum(1 for w in works if w["abstract"])
    L.append(f"- With an abstract in OpenAlex: {abstracts} ({pct(abstracts, n)})")
    dois = sum(1 for w in works if w["doi"])
    L.append(f"- With a DOI: {dois} ({pct(dois, n)})")
    retracted = sum(1 for w in works if w["is_retracted"])
    L.append(f"- Retracted: {retracted}")
    mention = re.compile(r"\b(sosa|ssn)\b", re.I)
    m_title = sum(1 for w in works if mention.search(w["title"]))
    m_abs = sum(1 for w in works if mention.search(w["title"] + " " + w["abstract"]))
    F.update(abstracts=abstracts, dois=dois, retracted=retracted, named_title=m_title,
             named_title_abstract=m_abs)
    L.append(f"- Naming SOSA or SSN in the title: {m_title} ({pct(m_title, n)}); "
             f"in the title or abstract: {m_abs} ({pct(m_abs, n)})")
    secondary = re.compile(r"\b(survey|review|state of the art|systematic|mapping study|bibliometric)\b", re.I)
    sec = sum(1 for w in works if secondary.search(w["title"]))
    L.append(f"- Likely secondary studies (survey, review, state of the art, systematic, mapping study, "
             f"bibliometric in the title): {sec} ({pct(sec, n)})")
    titles = collections.Counter(norm_title(w["title"]) for w in works)
    dup = sum(c - 1 for c in titles.values() if c > 1)
    F.update(secondary_by_title=sec, duplicate_titles=dup)
    L.append(f"- Records sharing a normalised title with another record (likely versions of one work): {dup}\n")

    def stratum(w):
        return STRATA[stratum_of(w, role)]

    L.append("## Strata (review/101; stratum D, found by full-text search, is not harvested yet)\n")
    st = collections.Counter(stratum(w) for w in works)
    oa = collections.Counter((stratum(w), w["oa_status"] or "unknown") for w in works)
    kinds = ["diamond", "gold", "hybrid", "green", "bronze", "closed", "unknown"]
    F["strata"] = {stratum_of_key: {"works": st[label], "open_access": sum(
        oa[(label, k)] for k in kinds if k not in ("closed", "unknown"))}
        for stratum_of_key, label in STRATA.items()}
    L.append(table([(s, st[s], *(oa[(s, k)] for k in kinds),
                     pct(sum(oa[(s, k)] for k in kinds if k not in ("closed", "unknown")), st[s]))
                    for s in sorted(st)],
                   ["stratum", "works", *kinds, "open access"]) + "\n")

    L.append("## Per seed\n")
    per = collections.Counter(s for w in works for s in w["seeds"])
    only = collections.Counter(w["seeds"][0] for w in works if len(w["seeds"]) == 1)
    F["seeds"] = {s["key"]: {"role": s["role"], "citing": per[s["key"]], "citing_only": only[s["key"]]}
                  for s in seeds}
    L.append(table([(s["key"], s["role"], per[s["key"]], only[s["key"]]) for s in seeds],
                   ["seed", "role", "citing works", "citing this seed only"]) + "\n")

    L.append("## By year and seed group\n")
    years = sorted({w["year"] for w in works if w["year"]})
    by = collections.Counter((w["year"], group(w)) for w in works)
    groups = ["lineage only", "lineage and 2017+", "2017+ only"]
    by_stratum = collections.Counter((w["year"], stratum_of(w, role)) for w in works if w["year"])
    F["by_year_and_stratum"] = {str(y): {k: by_stratum[(y, k)] for k in STRATA} for y in years}
    L.append(table([(y, *(by[(y, k)] for k in groups), sum(by[(y, k)] for k in groups)) for y in years],
                   ["year", *groups, "total"]) + "\n")

    def top(field, k=15, title=None, key=None):
        c = collections.Counter((key or (lambda w: w[field]))(w) or "(none)" for w in works)
        F.setdefault("top", {})[field] = c.most_common(k)
        L.append(f"## {title or field}\n")
        L.append(table([(v, c[v], pct(c[v], n)) for v, _ in c.most_common(k)], [field, "works", "share"]) + "\n")

    top("type", 12, "By OpenAlex type")
    top("language", 8, "By language")
    top("domain", 6, "By OpenAlex domain (primary topic)")
    top("field", 15, "By OpenAlex field (primary topic)")
    top("subfield", 20, "By OpenAlex subfield (primary topic)")
    top("venue", 25, "Top venues")
    top("publisher", 15, "Top publishers (host organisation)")
    risky = collections.Counter(RISKY_DOI_PREFIXES.get(w["doi"].split("/")[0], "") for w in works if w["doi"])
    L.append("## Publishers on the risk list (DOI prefix)\n")
    L.append(table([(k, v, pct(v, n)) for k, v in risky.items() if k], ["publisher", "works", "share"]) + "\n")
    cc = collections.Counter(c for w in works for c in w["countries"])
    F["countries"] = cc.most_common(15)
    F["with_countries"] = sum(1 for w in works if w["countries"])
    L.append("## Author countries (a work counts once per country)\n")
    L.append(table([(k, v, pct(v, n)) for k, v in cc.most_common(15)], ["country", "works", "share"]) + "\n")

    L.extend(changes_since_previous(seeds))

    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "scoping.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (out / "scoping.json").write_text(json.dumps(F, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"results/scoping.md: {n} works")
    return 0


if __name__ == "__main__":
    sys.exit(main())
