#!/usr/bin/env python3
"""Detection in the full texts: the passages where SOSA/SSN occurs, as items to read.

    python3 -I scripts/build_items.py        # screening/items.jsonl, results/detection.md

Reads the full texts kept by scripts/scan_s2orc.py (fulltext/, not versioned), the
strings of results/search-strings.csv, the OpenAlex candidate corpus and the last
Semantic Scholar harvest. For every full text, finds the occurrences of the namespace
IRIs, prefixed names and distinctive local names in the **body** (the bibliography is
apart in S2ORC), and the names of the ontology in prose (SOSA, SSN, Semantic Sensor
Network), and keeps each paragraph that holds one, with its section header.

- A work with occurrences becomes an item of `screening/items.jsonl`: identifiers,
  stratum, passages, word counts. The review application shows it (app/DESIGN.md).
- A candidate with no occurrence in its body, not even the name of the ontology, is
  listed too, with `passages: []`: the protocol codes it E0 by script (the seed is cited
  for another point), a rule checked on a random sample.

The body of each full text, without its bibliography, goes to
`screening/bodies.jsonl.gz`, read by scripts/model_code.py. The passages and bodies are
text from downloaded papers: they go to `screening/`, which is not versioned either, and are shown as text only. `results/detection.md` gives the counts
and the measured lengths that replace the assumptions of protocol/budget.toml.
Standard library only.
"""
import collections
import csv
import gzip
import json
import pathlib
import re
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from strata import ROOT, load_corpus, load_seeds, stratum, wrong_texts  # noqa: E402


def table(rows, head):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def pct(n, d):
    return f"{100 * n / d:.1f} %" if d else "—"


def spans(annotations, name):
    raw = (annotations or {}).get(name)
    if not raw:
        return []
    items = json.loads(raw) if isinstance(raw, str) else raw
    return sorted((int(a["start"]), int(a["end"])) for a in items or [])


def matcher(kinds):
    with open(ROOT / "results/search-strings.csv", encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["kind"] in kinds and r["distinctive"] == "yes"]
    alts = []
    for r in sorted(rows, key=lambda r: len(r["string"]), reverse=True):
        s = re.escape(r["string"])
        if r["kind"] == "local":
            alts.append(r"(?<![A-Za-z0-9_:/#])" + s + r"(?![A-Za-z0-9_])")
        elif r["kind"] == "prefixed":
            alts.append(s + r"(?![A-Za-z0-9_])")
        else:
            alts.append(s)
    return re.compile("|".join(alts))


# a heading that opens a reference list, in a text extracted from a PDF
REFS = re.compile(r"^\s*(?:\d+\.?\s*)?(references|bibliography|literature cited|works cited|"
                  r"r\s?e\s?f\s?e\s?r\s?e\s?n\s?c\s?e\s?s)\s*$", re.I | re.M)
NAMES = re.compile(r"\b(?:SOSA|SSN(?:-XG)?|[Ss]emantic [Ss]ensor [Nn]etwork(?:s)?(?: [Oo]ntology)?)\b")


def s2_index():
    """Seeds cited per Semantic Scholar corpus id and per DOI, from the last S2 harvest."""
    m = sorted(ROOT.glob("raw/*-s2-manifest.json"))[-1]
    stamp = json.loads(m.read_text(encoding="utf-8"))["stamp"]
    by_id, by_doi, year = collections.defaultdict(set), collections.defaultdict(set), {}
    for path in ROOT.glob(f"raw/{stamp}-s2-cites-*.jsonl.gz"):
        seed = path.name[len(f"{stamp}-s2-cites-"):-len(".jsonl.gz")]
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                p = json.loads(line).get("citingPaper") or {}
                ext = p.get("externalIds") or {}
                if ext.get("CorpusId"):
                    by_id[int(ext["CorpusId"])].add(seed)
                    year[int(ext["CorpusId"])] = p.get("year")
                if ext.get("DOI"):
                    by_doi[ext["DOI"].lower()].add(seed)
    return by_id, by_doi, year


def main():
    role = {s["key"]: s["role"] for s in load_seeds()}
    corpus = {w["doi"].lower(): w for w in load_corpus() if w["doi"]}
    s2_by_id, s2_by_doi, s2_year = s2_index()
    rx = matcher({"namespace", "prefixed", "local"})

    def stratum_of(cid, doi, year):
        if doi and doi in corpus:
            return stratum(corpus[doi], role), "openalex"
        seeds = s2_by_id.get(cid) or s2_by_doi.get(doi)
        if seeds:
            return stratum({"seeds": sorted(seeds), "year": year or s2_year.get(cid)}, role), "semantic scholar"
        return "D", "full-text search"

    # Only the shard files that a manifest lists as scanned: a failed or interrupted attempt
    # leaves a partial file behind, which no manifest lists.
    listed = set()
    for m in sorted(ROOT.glob("raw/*-s2orc-scan-manifest.json")):
        d = json.loads(m.read_text(encoding="utf-8"))
        listed.update(f"s2orc-{d['release']}/{d['stamp']}-shard-{e['index']:03d}.jsonl.gz"
                      for e in d.get("shards", []))
    records, seen = [], set()
    for path in sorted(ROOT.glob("fulltext/s2orc-*/*.jsonl.gz")):
        if f"{path.parent.name}/{path.name}" not in listed:
            continue
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                if rec.get("corpusid") in seen:
                    continue
                seen.add(rec.get("corpusid"))
                records.append(rec)

    items, lengths, passage_words = [], [], []
    bodies = {}  # item -> body text without the bibliography, for scripts/model_code.py
    by_stratum = collections.Counter()
    with_occ = collections.Counter()
    with_terms = collections.Counter()
    for rec in records:
        body = rec.get("body") or {}
        text = body.get("text") or ""
        ann = body.get("annotations") or {}
        doi = ((rec.get("openaccessinfo") or {}).get("externalids") or {}).get("DOI")
        doi = doi.lower() if doi else None
        st, via = stratum_of(rec.get("corpusid"), doi, None)
        paragraphs = spans(ann, "paragraph") or [(0, len(text))]
        headers = spans(ann, "section_header")
        passages = []
        for start, end in paragraphs:
            chunk = text[start:end]
            found = collections.Counter(rx.findall(chunk))
            names = collections.Counter(NAMES.findall(chunk))
            if not (found or names):
                continue
            section = ""
            for hs, he in headers:
                if hs <= start:
                    section = text[hs:he]
                else:
                    break
            passages.append({"section": section.strip(), "start": start, "end": end,
                             "text": chunk, "found": dict(found + names), "terms": bool(found)})
        words = len(text.split())
        lengths.append(words)
        by_stratum[st] += 1
        if passages:
            with_occ[st] += 1
            passage_words.append(sum(len(p["text"].split()) for p in passages))
            with_terms[st] += any(p["terms"] for p in passages)
        bodies[f"s2orc:{rec.get('corpusid')}"] = text
        items.append({"item": f"s2orc:{rec.get('corpusid')}", "corpusid": rec.get("corpusid"),
                      "source": "s2orc",
                      "doi": doi, "title": rec.get("title"), "stratum": st, "stratum_from": via,
                      "url": (rec.get("openaccessinfo") or {}).get("url"),
                      "body_words": words, "passages": passages})
    # second source: the open-access PDFs retrieved by scripts/harvest_oa_fulltext.py (last
    # complete manifest); the text is cut before the last reference-list heading, and split
    # into paragraphs on blank lines; there are no section headers
    oa = {"works": 0, "refs_cut": 0, "by_stratum": collections.Counter(), "naming": collections.Counter(),
          "with_terms": collections.Counter(), "lengths": [], "passage_words": [], "cut_at": [],
          "signal": collections.Counter()}  # stratum D: (signal, texts | naming | with terms)
    by_openalex = {w["openalex"]: w for w in load_corpus()}
    with gzip.open(ROOT / "corpus/stratum-d-candidates.jsonl.gz", "rt", encoding="utf-8") as f:
        d_titles = {w["openalex"]: w["title"] for w in map(json.loads, f)}
    # every complete run, the latest first, one text per work (a later pass retries failures)
    oa_manifests = [m for m in sorted(ROOT.glob("raw/*-oa-fulltext-manifest.json"), reverse=True)
                    if json.loads(m.read_text(encoding="utf-8")).get("complete")]
    oa_stamp = ", ".join(m.name.split("-oa-fulltext")[0] for m in sorted(oa_manifests)) or None
    taken = set()
    wrong = wrong_texts()
    for mpath in oa_manifests:
        man = json.loads(mpath.read_text(encoding="utf-8"))
        for e in man["works"]:
            txt = ROOT / f"fulltext/oa-pdf/{man['stamp']}/{e['openalex']}.txt"
            if e["outcome"] != "text" or not txt.exists() or e["openalex"] in taken \
                    or (man["stamp"], e["openalex"]) in wrong:
                continue
            taken.add(e["openalex"])
            text = re.sub(r"-\n(?=[a-z])", "", txt.read_text(encoding="utf-8", errors="replace"))
            heads = list(REFS.finditer(text))
            body = text[:heads[-1].start()] if heads else text
            if heads:  # where the reference list starts, as a share of the text: a check of the cut
                oa["cut_at"].append(heads[-1].start() / max(1, len(text)))
            passages = []
            for para in re.split(r"\n\s*\n", body):
                chunk = " ".join(para.split())
                found = collections.Counter(rx.findall(chunk))
                names = collections.Counter(NAMES.findall(chunk))
                if found or names:
                    passages.append({"section": "", "start": None, "end": None, "text": chunk,
                                     "found": dict(found + names), "terms": bool(found)})
            w = by_openalex.get(e["openalex"])
            st = stratum(w, role) if w else e["stratum"]
            words = len(body.split())
            oa["works"] += 1
            oa["refs_cut"] += bool(heads)
            oa["by_stratum"][st] += 1
            oa["lengths"].append(words)
            if passages:
                oa["naming"][st] += 1
                oa["passage_words"].append(sum(len(p_["text"].split()) for p_ in passages))
                oa["with_terms"][st] += any(p_["terms"] for p_ in passages)
            if e.get("signal"):
                oa["signal"][(e["signal"], "texts")] += 1
                oa["signal"][(e["signal"], "naming")] += bool(passages)
                oa["signal"][(e["signal"], "with terms")] += any(p_["terms"] for p_ in passages)
            bodies[f"openalex:{e['openalex']}"] = body
            items.append({"item": f"openalex:{e['openalex']}", "corpusid": None, "source": "oa-pdf",
                          "doi": (e["doi"] or "").lower() or None, "title": w["title"] if w else d_titles.get(e["openalex"], ""),
                          "stratum": st, "stratum_from": "openalex", "url": e["tried"][-1].get("url") or f"https://doi.org/{e['doi']}",
                          "body_words": words, "refs_cut": bool(heads), "passages": passages})

    out = ROOT / "screening"
    out.mkdir(exist_ok=True)
    with open(out / "items.jsonl", "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    with gzip.open(out / "bodies.jsonl.gz", "wt", encoding="utf-8") as f:
        for item, body in bodies.items():
            f.write(json.dumps({"item": item, "body": body}, ensure_ascii=False) + "\n")

    def q(values, p):
        return round(statistics.quantiles(values, n=100)[p - 1]) if len(values) > 1 else "—"

    L = ["# Detection of SOSA/SSN in the full texts\n",
         "Full texts of S2ORC kept by `scripts/scan_s2orc.py` (shards scanned: see the last "
         "`raw/*-s2orc-scan-manifest.json`), occurrences of the namespace IRIs, prefixed names "
         "and distinctive local names of `results/search-strings.csv` in the body only; computed "
         "by `scripts/build_items.py`. Not screened.\n",
         f"- Full texts: {len(records)}; naming SOSA/SSN in the body (terms or names in "
         f"prose): {sum(with_occ.values())}; with terms (IRIs, prefixed or local names): "
         f"{sum(with_terms.values())}\n",
         table([(s, by_stratum[s], with_occ[s], with_terms[s], pct(with_occ[s], by_stratum[s]))
                for s in sorted(by_stratum)],
               ["stratum", "full texts", "naming SOSA/SSN", "with terms", "share naming"]) + "\n",
         "## Measured lengths (words)\n",
         table([("body of a full text", q(lengths, 25), round(statistics.median(lengths)) if lengths else "—",
                 q(lengths, 75)),
                ("passages of a work with occurrences", q(passage_words, 25),
                 round(statistics.median(passage_words)) if passage_words else "—", q(passage_words, 75))],
               ["what", "first quartile", "median", "third quartile"]) + "\n"]
    (ROOT / "results/detection.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    # what is left to retrieve: candidates of strata A and B without an S2ORC full text
    # (matched by DOI), by open-access status in OpenAlex
    have = {it["doi"] for it in items if it["doi"] and it["source"] == "s2orc"}
    have_oa = {it["doi"] for it in items if it["doi"] and it["source"] == "oa-pdf"}
    gap = collections.Counter()
    for w in corpus.values():
        st_w = stratum(w, role)
        if st_w not in ("A", "B"):
            continue
        oa_ = "open access" if w["oa_status"] not in ("closed", "", None) else "closed or unknown"
        gap[(st_w, "S2ORC full text" if w["doi"].lower() in have else oa_)] += 1
        if w["doi"].lower() in have_oa:
            gap[(st_w, "open-access PDF text")] += 1
    no_doi = collections.Counter(stratum(w, role) for w in load_corpus() if not w["doi"]
                                 and stratum(w, role) in ("A", "B"))
    L += ["## Full texts still to retrieve (strata A and B)\n",
          "Candidates with a DOI, by whether S2ORC gives their full text (matched by DOI) and, if "
          "not, by their open-access status in OpenAlex. Candidates without a DOI are counted apart.\n",
          table([(s_, gap[(s_, "S2ORC full text")], gap[(s_, "open access")], gap[(s_, "open-access PDF text")],
                  gap[(s_, "closed or unknown")], no_doi[s_]) for s_ in ("A", "B")],
                ["stratum", "S2ORC full text", "open access, not in S2ORC", "of which PDF text retrieved",
                 "closed or unknown", "no DOI"]) + "\n"]
    if oa["works"]:
        L += ["## Second source: open-access PDFs (scripts/harvest_oa_fulltext.py)\n",
              f"Retrieval `{oa_stamp}`: {oa['works']} texts extracted with pdftotext; reference list found and "
              f"cut in {oa['refs_cut']}; paragraphs split on blank lines, no section headers (so no E1 by "
              "script). Counted apart from S2ORC.\n",
              table([(s_, oa["by_stratum"][s_], oa["naming"][s_], oa["with_terms"][s_],
                      pct(oa["naming"][s_], oa["by_stratum"][s_])) for s_ in sorted(oa["by_stratum"])],
                    ["stratum", "full texts", "naming SOSA/SSN", "with terms", "share naming"]) + "\n",
              (table([(sg, oa["signal"][(sg, "texts")], oa["signal"][(sg, "naming")], oa["signal"][(sg, "with terms")])
                      for sg in sorted({sg for sg, _ in oa["signal"]})],
                     ["stratum D signal", "texts", "naming SOSA/SSN", "with terms"]) + "\n") if oa["signal"] else "",
              table([("body of a full text", q(oa["lengths"], 25),
                      round(statistics.median(oa["lengths"])) if oa["lengths"] else "—", q(oa["lengths"], 75)),
                     ("passages of a work with occurrences", q(oa["passage_words"], 25),
                      round(statistics.median(oa["passage_words"])) if oa["passage_words"] else "—",
                      q(oa["passage_words"], 75))],
                    ["what", "first quartile", "median", "third quartile"]) + "\n"]

    # what S2ORC adds to stratum D: works naming SOSA/SSN that cite no seed, against the
    # stratum D of the OpenAlex full-text search (corpus/stratum-d-candidates.jsonl.gz)
    with gzip.open(ROOT / "corpus/stratum-d-candidates.jsonl.gz", "rt", encoding="utf-8") as f:
        openalex_d = {(json.loads(line)["doi"] or "").lower() for line in f} - {""}
    d_named = [it for it in items if it["stratum"] == "D" and it["passages"] and it["source"] == "s2orc"]
    d_new = [it for it in d_named if not (it["doi"] and it["doi"] in openalex_d)]
    # the works of stratum D found by S2ORC, with or without an OpenAlex counterpart: the
    # second source of stratum D, next to corpus/stratum-d-candidates.* (scripts/stratum_d.py)
    with open(ROOT / "corpus/stratum-d-s2orc.csv", "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["corpusid", "doi", "title", "in_openalex_stratum_d", "found"])
        for it in sorted(d_named, key=lambda it: it["corpusid"] or 0):
            found = sorted({k for p_ in it["passages"] for k in p_["found"]})
            wr.writerow([it["corpusid"], it["doi"] or "", it["title"] or "",
                         bool(it["doi"] and it["doi"] in openalex_d), ";".join(found)])
    L += ["## What S2ORC adds to stratum D\n",
          f"Works naming SOSA/SSN in the body that cite no seed: {len(d_named)}; of these, already "
          f"in the stratum D of the OpenAlex full-text search (same DOI): {len(d_named) - len(d_new)}; "
          f"**new: {len(d_new)}**; new and with terms (IRIs, prefixed or local names): "
          f"{sum(1 for it in d_new if any(p['terms'] for p in it['passages']))}.\n"]
    (ROOT / "results/detection.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    def quartiles(values):
        if len(values) < 2:
            return {}
        qs = statistics.quantiles(values, n=4)
        return {"q1": qs[0], "median": statistics.median(values), "q3": qs[2], "mean": statistics.mean(values)}

    F = {"shard_files": len(listed), "full_texts": len(records),
         "with_occurrences": sum(with_occ.values()), "with_terms": sum(with_terms.values()),
         "by_stratum": {k: {"full_texts": by_stratum[k], "naming": with_occ[k], "with_terms": with_terms[k]}
                        for k in sorted(by_stratum)},
         "body_words": quartiles(lengths), "passage_words": quartiles(passage_words),
         "oa_pdf": {"stamp": oa_stamp, "works": oa["works"], "refs_cut": oa["refs_cut"],
                    "by_stratum": {k: {"full_texts": oa["by_stratum"][k], "naming": oa["naming"][k],
                                       "with_terms": oa["with_terms"][k]} for k in sorted(oa["by_stratum"])},
                    "body_words": quartiles(oa["lengths"]), "passage_words": quartiles(oa["passage_words"]),
                    "cut_at": quartiles(oa["cut_at"]),
                    "stratum_d_by_signal": {sg: {k: oa["signal"][(sg, k)] for k in ("texts", "naming", "with terms")}
                                            for sg in sorted({sg for sg, _ in oa["signal"]})},
                    "cut_before_half": sum(1 for x in oa["cut_at"] if x < 0.5)},
         "to_retrieve": {s_: {"s2orc": gap[(s_, "S2ORC full text")], "open_access": gap[(s_, "open access")],
                              "oa_pdf_text": gap[(s_, "open-access PDF text")],
                              "closed": gap[(s_, "closed or unknown")], "no_doi": no_doi[s_]} for s_ in ("A", "B")},
         "stratum_d_named": len(d_named), "stratum_d_new": len(d_new),
         "stratum_d_new_with_terms": sum(1 for it in d_new if any(p["terms"] for p in it["passages"]))}
    (ROOT / "results/detection.json").write_text(json.dumps(F, indent=1) + "\n", encoding="utf-8")
    print(f"screening/items.jsonl: {len(items)} items; results/detection.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
