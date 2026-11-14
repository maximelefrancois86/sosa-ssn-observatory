#!/usr/bin/env python3
"""The coding of the modelling patterns (protocol/patterns-codebook.md), from excerpts.

    python3 -I scripts/pattern_coding.py prepare --batches 8   # excerpts in batches, manifest in raw/
    python3 -I scripts/pattern_coding.py ingest                # results/pattern-coding.{md,json}

`prepare` takes the works that use SOSA/SSN (engagement E3 to E5 by the strongest model
that coded the work from its full text, scripts/hypothetical_findings.py) and those whose
text writes a SOSA/SSN name (results/usage-patterns.json), less the seeds and the texts a
model took for another work. For each, the excerpts: the passages of the body within 300
characters of a SOSA/SSN name, namespace or distinctive local name, merged, at most 10,000
characters, cut at the passage boundaries. They go to screening/patterns/STAMP/batch-K.jsonl
(passages of downloaded papers: not versioned); raw/STAMP-patterns-manifest.json records the
codebook's hash, the works of each batch and the hash of each excerpt.

The coders (pilotage review/105, the ladder: Claude agents of a Claude Code session, model
named in the manifest) write one line per work to raw/STAMP-patterns-coded-K.jsonl, as
protocol/patterns-codebook.md says.

`ingest` reads every coded batch of the latest stamp, checks each quotation against the
excerpts (case, whitespace and hyphenation aside), and counts the works per value of each
question: among the works where the question is shown (values other than `not-shown`),
and by engagement and year. These are recommendations, not decisions of the readers. It
also writes what the review application shows (app/DESIGN.md, protocol/patterns-codebook.toml):
screening/pattern-recommendations.jsonl, one line per (work, question `patterns.<id>`), source
"model", with the coder's quotations as evidence; and screening/pattern-population.jsonl, the
works of the population with `writes_names` (the text writes a SOSA/SSN name), for which the
application asks the questions whatever the engagement. Standard library only.
"""
import argparse
import collections
import datetime as dt
import gzip
import hashlib
import json
import pathlib
import re
import sys
import tomllib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from strata import ROOT, load_seeds  # noqa: E402

CODEBOOK = ROOT / "protocol/patterns-codebook.md"
ANCHOR = re.compile(
    r"(sosa|ssn|ssn-system|ssn-ext)\s?:\s?[A-Za-z]|w3\.org/ns/(sosa|ssn)|purl\.oclc\.org/NET/ssnx|"
    r"\b(observedProperty|madeBySensor|hasFeatureOfInterest|hasSimpleResult|hasResult|isHostedBy|hosts|"
    r"actsOnProperty|madeByActuator|ObservableProperty|ActuatableProperty|FeatureOfInterest|phenomenonTime|"
    r"resultTime|isPropertyOf|hasProperty|usedProcedure|isSampleOf|ObservationCollection|hasMember|"
    r"hasSubSystem|deployedSystem|deployedOnPlatform)\b")
WINDOW, CAP = 300, 10000
QUESTIONS = ["property_individuals", "property_source", "punning", "system_individuals", "result_form",
             "unit_placement", "time", "hosting", "location", "grouping", "feature_typing", "other"]


def sha(t):
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def excerpts(body):
    spans = []
    for m in ANCHOR.finditer(body):
        s, e = max(0, m.start() - WINDOW), min(len(body), m.end() + WINDOW)
        if spans and s <= spans[-1][1]:
            spans[-1][1] = e
        else:
            spans.append([s, e])
    out, n = [], 0
    for s, e in spans:
        chunk = " ".join(body[s:e].split())
        if n + len(chunk) > CAP:
            break
        out.append(chunk)
        n += len(chunk)
    return "\n[…]\n".join(out)


def population(parts=False):
    """The works whose modelling choices are coded: engagement E3 to E5 from the full text, or a
    text that writes a SOSA/SSN name; less the seeds and the texts that are not the work. With
    `parts`, also the two sets (use, writers)."""
    import hypothetical_findings as hf
    answers, not_work, _ = hf.ladder_answers()
    use = {i for i, a in answers.items() if a.get("engagement", {}).get("value") in ("E3", "E4", "E5")
           and a["engagement"].get("basis", "full text") != "abstract"}
    up = json.loads((ROOT / "results/usage-patterns.json").read_text(encoding="utf-8"))
    writers = {x["item"] for v in up["names"]["by_class"].values() for x in v["list"]}
    its = hf.items()
    seed_ids = {x["openalex"] for x in load_seeds()}
    seed_dois = {x["doi"].lower() for x in load_seeds() if x.get("doi")}
    keep = {i for i in use | writers if i not in not_work and i[9:] not in seed_ids
            and (its.get(i, {}).get("doi") or "").lower() not in seed_dois}
    eng = {i: answers.get(i, {}).get("engagement", {}).get("value") for i in keep}
    if parts:
        return keep, eng, its, hf, use, writers
    return keep, eng, its, hf


def app_files(coded, manifest):
    """What the review application shows: the coders' answers as recommendations (source
    "model", question `patterns.<id>`), and the population, with `writes_names`."""
    kinds = {q["id"]: q["kind"] for q in tomllib.loads(
        (ROOT / "protocol/patterns-codebook.toml").read_text(encoding="utf-8"))["question"]}
    stamp = manifest["stamp"]
    recs = []
    for item, r in sorted(coded.items()):
        for q in QUESTIONS:
            a = r["answers"].get(q)
            if not a:
                continue
            vals = a.get("values") or ["not-shown"]
            recs.append({"item": item, "source": "model",
                         "version": f"{r.get('coder') or manifest.get('coder')}, patterns codebook "
                                    f"{manifest['codebook_sha256'][:12]}",
                         "date": stamp[:10], "run": stamp, "question": f"patterns.{q}",
                         "value": vals if kinds[q] == "many" else vals[0],
                         "justification": a.get("note", ""), "evidence": a.get("quotes", []),
                         "evidence_found": a.get("quotes_found", []), "basis": "excerpts",
                         "uncertain": q in r.get("uncertain", [])})
    with open(ROOT / "screening/pattern-recommendations.jsonl", "w", encoding="utf-8") as f:
        f.write("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in recs))
    keep, _, _, _, use, writers = population(parts=True)
    with open(ROOT / "screening/pattern-population.jsonl", "w", encoding="utf-8") as f:
        for i in sorted(keep):
            f.write(json.dumps({"item": i, "writes_names": i in writers, "uses": i in use, "coded": i in coded}) + "\n")
    return len(recs), len(keep)


def prepare(args):
    keep, eng, its, hf = population()
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M")
    out_dir = ROOT / f"screening/patterns/{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    works = []
    with gzip.open(ROOT / "screening/bodies.jsonl.gz", "rt", encoding="utf-8") as f:
        for d in map(json.loads, f):
            if d["item"] in keep:
                ex = excerpts(d["body"])
                if ex:
                    works.append({"item": d["item"], "title": its.get(d["item"], {}).get("title"),
                                  "engagement": eng.get(d["item"]), "excerpts": ex})
    works.sort(key=lambda w: sha(w["item"]))
    batches = [[] for _ in range(args.batches)]
    sizes = [0] * args.batches
    for w in sorted(works, key=lambda w: -len(w["excerpts"])):  # balance the sizes
        k = sizes.index(min(sizes))
        batches[k].append(w)
        sizes[k] += len(w["excerpts"])
    manifest = {"stamp": stamp, "codebook": str(CODEBOOK.relative_to(ROOT)), "codebook_sha256": sha(CODEBOOK.read_text(encoding="utf-8")),
                "window": WINDOW, "cap": CAP, "coder": args.coder, "works": len(works), "batches": []}
    for k, b in enumerate(batches, 1):
        with open(out_dir / f"batch-{k}.jsonl", "w", encoding="utf-8") as f:
            for w in b:
                f.write(json.dumps(w, ensure_ascii=False) + "\n")
        manifest["batches"].append({"batch": k, "works": [{"item": w["item"], "excerpts_sha256": sha(w["excerpts"])} for w in b],
                                    "characters": sum(len(w["excerpts"]) for w in b)})
    (ROOT / f"raw/{stamp}-patterns-manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{stamp}: {len(works)} works in {args.batches} batches of {min(sizes)}–{max(sizes)} characters; {out_dir}")


def second(args):
    """screening/patterns/STAMP/batch-R1.jsonl: the N first works of the latest run in an order
    fixed by a seeded hash, with the same excerpts, for a second coder who does not see the
    first coding; the answers go to raw/STAMP-patterns-coded-R1.jsonl, and `ingest` measures the
    agreement of the two codings (results/pattern-coding.md)."""
    manifest = json.loads(sorted(ROOT.glob("raw/*-patterns-manifest.json"))[-1].read_text(encoding="utf-8"))
    stamp = manifest["stamp"]
    works = [json.loads(l) for p in sorted((ROOT / f"screening/patterns/{stamp}").glob("batch-[0-9]*.jsonl"))
             for l in open(p, encoding="utf-8")]
    works.sort(key=lambda w: sha(args.seed + w["item"]))
    pick = works[:args.n]
    with open(ROOT / f"screening/patterns/{stamp}/batch-R1.jsonl", "w", encoding="utf-8") as f:
        for w in pick:
            f.write(json.dumps(w, ensure_ascii=False) + "\n")
    second_manifest = {"stamp": stamp, "seed": args.seed, "n": len(pick),
                       "works": [{"item": w["item"], "excerpts_sha256": sha(w["excerpts"])} for w in pick]}
    (ROOT / f"raw/{stamp}-patterns-second-manifest.json").write_text(
        json.dumps(second_manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"batch R1 of {stamp}: {len(pick)} works")


def kappa(pairs):
    n = len(pairs)
    if not n:
        return None
    po = sum(a == b for a, b in pairs) / n
    ca, cb = collections.Counter(a for a, _ in pairs), collections.Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in ca) / n / n
    return (po - pe) / (1 - pe) if pe < 1 else None


def norm(t):
    t = re.sub(r"-\s+", "", t or "")
    return re.sub(r"\W+", "", t.lower())


def ingest(args):
    mans = sorted(ROOT.glob("raw/*-patterns-manifest.json"))
    manifest = json.loads(mans[-1].read_text(encoding="utf-8"))
    stamp = manifest["stamp"]
    exc = {}
    for p in sorted((ROOT / f"screening/patterns/{stamp}").glob("batch-*.jsonl")):
        for w in map(json.loads, open(p, encoding="utf-8")):
            exc[w["item"]] = w
    coded, quotes_ok, quotes_n = {}, 0, 0
    for p in sorted(ROOT.glob(f"raw/{stamp}-patterns-coded-[0-9]*.jsonl")):
        for line in open(p, encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            if r["item"] not in exc:
                continue
            body = norm(exc[r["item"]]["excerpts"])
            for q, a in r["answers"].items():
                a["quotes_found"] = [bool(norm(x)) and norm(x) in body for x in a.get("quotes", [])]
                quotes_ok += sum(a["quotes_found"])
                quotes_n += len(a["quotes_found"])
            coded[r["item"]] = r
    second_path = ROOT / f"raw/{stamp}-patterns-coded-R1.jsonl"
    agreement, agree_lines = {}, []
    if second_path.exists():
        sec = {r["item"]: r for r in (json.loads(l) for l in open(second_path, encoding="utf-8") if l.strip())}
        for q in QUESTIONS[:-1]:
            pairs, jac = [], []
            for i, r2 in sec.items():
                if i not in coded:
                    continue
                a = set(coded[i]["answers"].get(q, {}).get("values") or ["not-shown"])
                b = set(r2["answers"].get(q, {}).get("values") or ["not-shown"])
                pairs.append(("|".join(sorted(a)), "|".join(sorted(b))))
                jac.append(len(a & b) / len(a | b))
            k = kappa(pairs)
            agreement[q] = {"n": len(pairs), "exact": sum(x == y for x, y in pairs), "kappa": k,
                            "jaccard": sum(jac) / len(jac) if jac else None}
        agree_lines = ["", "## Agreement of a second, independent coder", "",
              f"{len(sec)} works drawn by a seeded hash (raw/{stamp}-patterns-coded-R1.jsonl).", "",
              "| Question | Works | Same set of values | Cohen's kappa | Mean Jaccard |", "|---|---|---|---|---|"]
        for q, v in agreement.items():
            agree_lines.append(f"| {q} | {v['n']} | {v['exact']} | {v['kappa']:.2f} | {v['jaccard']:.2f} |"
                               if v["kappa"] is not None else f"| {q} | {v['n']} | {v['exact']} | — | {v['jaccard']:.2f} |")
    import hypothetical_findings as hf
    by_id, by_doi = hf.work_meta()
    its = hf.items()

    def year(i):
        w = by_id.get(i[9:]) if i.startswith("openalex:") else None
        w = w or by_doi.get((its.get(i, {}).get("doi") or "").lower(), {})
        return w.get("year")

    out = {"stamp": stamp, "coder": manifest.get("coder"), "works_prepared": manifest["works"], "works_coded": len(coded),
           "quotes": quotes_n, "quotes_found": quotes_ok, "questions": {}}
    L = ["# Modelling patterns of the works that use SOSA/SSN", "",
         f"Written by `scripts/pattern_coding.py ingest` from run `{stamp}` "
         f"(codebook `protocol/patterns-codebook.md`, coder: {manifest.get('coder')}). Recommendations, not "
         "decisions of the readers.", "",
         f"Works prepared: {manifest['works']}; coded: {len(coded)}; quotations found in the excerpts: "
         f"{quotes_ok} of {quotes_n} ({100 * quotes_ok / max(1, quotes_n):.1f} %)."]
    out["agreement"] = agreement
    L += agree_lines
    for q in QUESTIONS[:-1]:
        c, shown, unsure = collections.Counter(), set(), set()
        lists = collections.defaultdict(list)
        for i, r in coded.items():
            a = r["answers"].get(q, {})
            vals = a.get("values") or ["not-shown"]
            if any(v != "not-shown" for v in vals):
                shown.add(i)
            for v in vals:
                c[v] += 1
                lists[v].append(i)
            if q in r.get("uncertain", []):
                unsure.add(i)
        out["questions"][q] = {"shown": len(shown), "uncertain": len(unsure), "counts": dict(c),
                               "works": {v: sorted(x) for v, x in lists.items()}}
        L += ["", f"## {q}", "", f"Shown in {len(shown)} of the {len(coded)} works coded; the coder hesitated on {len(unsure)}.", "",
              "| Value | Works | Share of the works where it is shown |", "|---|---|---|"]
        for v, n in c.most_common():
            share = "" if v == "not-shown" else f"{100 * n / max(1, len(shown)):.0f} %"
            L.append(f"| {v} | {n} | {share} |")
    # property individuals by year
    by_year = collections.defaultdict(collections.Counter)
    for i, r in coded.items():
        for v in r["answers"].get("property_individuals", {}).get("values", []):
            if v != "not-shown" and year(i):
                by_year[int(year(i))][v] += 1
    out["property_individuals_by_year"] = {y: dict(c) for y, c in sorted(by_year.items())}
    others = [(i, r["answers"].get("other", {}).get("values", [""])[0]) for i, r in coded.items()]
    others = [(i, t) for i, t in others if t and t.lower() not in ("none", "not-shown")]
    out["other"] = [{"item": i, "text": t} for i, t in others]
    L += ["", "## other (free text)", ""] + [f"- `{i}`: {t}" for i, t in sorted(others)]
    from article_macros import num, pct
    M = {"coded": num(len(coded)), "prepared": num(manifest["works"]),
         "quotes-found-pct": pct(quotes_ok, quotes_n, 1)}
    for q, v in out["questions"].items():
        qk = q.replace("_", "-")
        M[f"{qk}-shown"] = num(v["shown"])
        M[f"{qk}-shown-pct"] = pct(v["shown"], len(coded), 0)
        for val, n in v["counts"].items():
            vk = re.sub(r"[^a-z0-9]+", "-", val.lower()).strip("-")
            M[f"{qk}-{vk}"] = num(n)
            if val != "not-shown":
                M[f"{qk}-{vk}-pct"] = pct(n, v["shown"], 0)
    for q, v in agreement.items():
        qk = q.replace("_", "-")
        M[f"{qk}-second-n"] = num(v["n"])
        if v["kappa"] is not None:
            M[f"{qk}-second-kappa"] = f"{v['kappa']:.2f}"
        M[f"{qk}-second-same-pct"] = pct(v["exact"], v["n"], 0)
    out["macros"] = M
    (ROOT / "results/pattern-coding.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (ROOT / "results/pattern-coding.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"results/pattern-coding.md: {len(coded)} works coded of {manifest['works']}; quotations found {quotes_ok}/{quotes_n}")
    n_recs, n_pop = app_files(coded, manifest)
    print(f"screening/pattern-recommendations.jsonl: {n_recs} recommendations; "
          f"screening/pattern-population.jsonl: {n_pop} works")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--batches", type=int, default=8)
    p.add_argument("--coder", default="claude-opus-5-5 (Claude Code agents)")
    sub.add_parser("ingest")
    p2 = sub.add_parser("second", help="a seeded sample of the works, for a second, independent coder")
    p2.add_argument("--n", type=int, default=60)
    p2.add_argument("--seed", default="patterns-second-2026-11-14")
    args = ap.parse_args(argv)
    return {"prepare": prepare, "ingest": ingest, "second": second}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
