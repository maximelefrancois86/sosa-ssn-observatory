#!/usr/bin/env python3
"""Candidates in questionable venues: the predatoryjournals.org lists, and the levels of
the Norwegian Register for Scientific Journals.

    python3 -I scripts/venue_risk.py          # writes results/venue-risk.md

Reads protocol/venue-risk.toml (which snapshots, which aliases and DOI prefixes), the
snapshots in raw/, the candidate corpus, and the ISSNs of the works in the raw harvest. Flagged works stay in the corpus; the figures say how many there are.
Standard library only; the lists are downloaded data, parsed as CSV and nothing else.
"""
import collections
import csv
import gzip
import json
import pathlib
import re
import sys
import tomllib
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from strata import ROOT, load_corpus, load_seeds, stratum  # noqa: E402


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\([^)]*\)", " ", s).replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def read_list(stamp, name):
    path = ROOT / f"raw/{stamp}-predatoryjournals-{name}.csv"
    with open(path, encoding="utf-8", newline="") as f:
        return {norm(row[-1]): row[-1] for row in csv.reader(f) if row and row[-1].strip()}


def table(rows, head):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def pct(n, d):
    return f"{100 * n / d:.1f} %" if d else "—"


def issns_of_works():
    """OpenAlex ID -> ISSNs of the source, from the raw files of the last OpenAlex harvest."""
    manifest = sorted(ROOT.glob("raw/*-openalex-manifest.json"))[-1]
    stamp = json.loads(manifest.read_text(encoding="utf-8"))["stamp"]
    out = {}
    for path in ROOT.glob(f"raw/{stamp}-openalex-cites-*.jsonl.gz"):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                w = json.loads(line)
                src = (w.get("primary_location") or {}).get("source") or {}
                issns = set(src.get("issn") or []) | ({src["issn_l"]} if src.get("issn_l") else set())
                out[w["id"].rsplit("/", 1)[-1]] = issns
    return out


def register_section(cfg, works, role, flag, st, F):
    """Level of each candidate's journal in the Norwegian register, in its year of publication."""
    reg = cfg.get("register")
    if not reg:
        return []
    with open(ROOT / f"raw/{reg['harvest']}-nsd-journals.csv", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    level_cols = {int(k.rsplit(" ", 1)[1]): k for k in rows[0] if k.startswith("Niv")}
    by_issn = {}
    for r in rows:
        for k in ("Print ISSN", "Online ISSN"):
            if r.get(k):
                by_issn[r[k].strip()] = r
    issns = issns_of_works()
    first, last = min(level_cols), max(level_cols)
    levels = collections.Counter()
    low = {}
    for w in works:
        ids = issns.get(w["openalex"], set())
        row = next((by_issn[i] for i in sorted(ids) if i in by_issn), None)  # sorted: deterministic
        if not ids:
            lv = "no ISSN"
        elif row is None:
            lv = "not in the register"
        else:
            year = min(max(w["year"] or last, first), last)
            lv = row[level_cols[year]].strip() or "no level that year"
        levels[lv] += 1
        if lv in ("0", "X"):
            low[w["openalex"]] = lv
    n = len(works)
    lst = collections.Counter(stratum(w, role) for w in works if w["openalex"] in low)
    both = sum(1 for i in low if i in flag)
    F["register"] = {"snapshot": reg["harvest"], "levels": dict(levels), "low": len(low),
                     "low_by_stratum": dict(lst), "low_and_flagged": both,
                     "low_and_flagged_works": sorted(i for i in low if i in flag),
                     "low_works": {i: lv for i, lv in sorted(low.items())}}
    order = ["2", "1", "0", "X", "no level that year", "not in the register", "no ISSN"]
    return ["## Norwegian Register for Scientific Journals\n",
            f"Snapshot `{reg['harvest']}` ({len(rows)} journals); level of the journal in the year "
            "of publication, matched by ISSN (ISSNs from the raw OpenAlex harvest). Level 0: not "
            "considered scientific; X: under discussion.\n",
            table([(lv, levels[lv], pct(levels[lv], n)) for lv in order if levels[lv]],
                  ["level", "works", "share of candidates"]) + "\n",
            table([(s, st[s], lst[s], pct(lst[s], st[s])) for s in sorted(st)],
                  ["stratum", "candidates", "level 0 or X", "share"]) + "\n",
            f"Level 0 or X and also flagged by predatoryjournals.org: {both} of {len(low)}.\n"]


def main():
    cfg = tomllib.loads((ROOT / "protocol/venue-risk.toml").read_text(encoding="utf-8"))
    stamp = cfg["list"]["harvest"]
    publishers, journals = read_list(stamp, "publishers"), read_list(stamp, "journals")
    alias = {norm(k): v for k, v in cfg.get("publisher_alias", {}).items()}
    prefixes = cfg.get("doi_prefix", {})
    for entry in list(alias.values()) + list(prefixes.values()):
        if norm(entry) not in publishers:
            raise SystemExit(f"venue-risk.toml names {entry!r}, which is not in the list")

    def listed_publisher(w):
        p = norm(w["publisher"])
        if p in publishers:
            return publishers[p], "publisher"
        if p in alias:
            return alias[p], "publisher"
        prefix = (w["doi"] or "").split("/")[0]
        if not p and prefix in prefixes:
            return prefixes[prefix], "DOI prefix"
        return None, None

    works = load_corpus()
    role = {s["key"]: s["role"] for s in load_seeds()}
    flag, by_pub, journal_only, to_check = {}, collections.Counter(), collections.Counter(), collections.Counter()
    for w in works:
        pub, how = listed_publisher(w)
        jour = journals.get(norm(w["venue"])) if w["venue"] else None
        if pub:
            flag[w["openalex"]] = how
            by_pub[pub] += 1
        elif jour and not w["publisher"]:
            flag[w["openalex"]] = "journal"
            journal_only[jour] += 1
        elif jour:
            to_check[(w["venue"], w["publisher"])] += 1

    n = len(works)
    st = collections.Counter(stratum(w, role) for w in works)
    fst = collections.Counter(stratum(w, role) for w in works if w["openalex"] in flag)
    L = ["# Candidates in questionable venues\n",
         "## The predatoryjournals.org lists\n",
         f"Snapshot `{stamp}` of the lists (publishers: {len(publishers)}, journals: "
         f"{len(journals)}), rules in `protocol/venue-risk.toml`, computed by "
         "`scripts/venue_risk.py`. Flagged works stay in the corpus.\n",
         f"- Flagged: **{len(flag)}** of {n} candidates ({pct(len(flag), n)}): "
         f"{sum(1 for v in flag.values() if v == 'publisher')} by publisher name, "
         f"{sum(1 for v in flag.values() if v == 'DOI prefix')} by DOI prefix and "
         f"{sum(1 for v in flag.values() if v == 'journal')} by journal name, "
         "when OpenAlex gives no publisher\n",
         "## By stratum\n",
         table([(s, st[s], fst[s], pct(fst[s], st[s])) for s in sorted(st)],
               ["stratum", "candidates", "flagged", "share"]) + "\n",
         "## By listed publisher\n",
         table([(k, v, pct(v, n)) for k, v in by_pub.most_common()],
               ["publisher (list entry)", "works", "share of candidates"]) + "\n"]
    if journal_only:
        L += ["## By listed journal, when OpenAlex gives no publisher\n",
              table([(k, v) for k, v in journal_only.most_common()], ["journal (list entry)", "works"]) + "\n"]
    if to_check:
        L += ["## Journal names on the list, publisher known and not listed (not flagged; to check)\n",
              table([(v, p, c) for (v, p), c in to_check.most_common()], ["venue", "publisher", "works"]) + "\n"]

    F = {"snapshot": stamp, "candidates": n, "flagged": len(flag),  # results/venue-risk.json
         "flagged_by_stratum": dict(fst), "by_publisher": dict(by_pub.most_common())}
    L += register_section(cfg, works, role, flag, st, F)

    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "venue-risk.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (out / "venue-risk.json").write_text(json.dumps(F, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"results/venue-risk.md: {len(flag)} of {n} flagged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
