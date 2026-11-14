#!/usr/bin/env python3
"""Take in the PDFs fetched by hand from the page of scripts/download_desk.py.

    python3 -I scripts/ingest_manual.py                     # ~/Downloads, ~/Téléchargements, fulltext/manual/inbox
    python3 -I scripts/ingest_manual.py --from ~/somewhere  # another folder
    python3 -I scripts/ingest_manual.py --tidy              # then move the PDFs taken in to
                                                            # fulltext/manual/taken/
    python3 -I scripts/ingest_manual.py --since 2026-11-12  # PDFs modified since that day
                                       # (default: since the page was first written, less an hour)
    python3 -I scripts/ingest_manual.py --ocr-again W3122945518 W3212446860
                                       # read again by OCR PDFs already taken in, whose text
                                       # layer turned out garbled

Each PDF of the folders (not their subfolders) is turned into text with `pdftotext` (by OCR,
`pdftoppm` then `tesseract`, when its text layer is garbled or matches nothing), then
matched to a work still without a full text: by a DOI printed on its first page, else by the
OpenAlex id in its file name (W…, shown on the page: rename a PDF that is not recognised), else
by the title of the work found in its first pages (normalised; a title of four or five words
must be on the first page), else, for titles of six words and more, by the share of the
title's word pairs found there (at least 0.7, and 0.2 ahead of the next work). A PDF already
taken in (same SHA-256) is skipped. A PDF that matches
no work is left alone and listed; the folders are only read, unless --tidy is given. A PDF that
matches is copied, with its text, to fulltext/oa-pdf/<stamp>/<openalex>.pdf and .txt.

Writes raw/<stamp>-oa-fulltext-manifest.json (`pass`: `manual`, the file name and SHA-256 of
each PDF), read by scripts/build_items.py like the other runs; the latest run that holds a
work gives its text, so a run of --ocr-again supersedes the garbled text without touching
the earlier manifest. The PDFs are downloaded data: only `pdftotext`, `pdftoppm` and
`tesseract` read them. Standard library only, apart from these.
"""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from download_desk import texts_so_far  # noqa: E402
from strata import ROOT, load_corpus, load_seeds, stratum  # noqa: E402

DOI = re.compile(r"10\.\d{4,9}/[^\s\"<>]+", re.I)


def norm(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


STOP = {"the", "and", "of", "to", "in", "a", "is", "for", "on", "with", "that", "are", "by", "this", "as"}


def garbled(text):
    """True when the text layer is unreadable (fonts without a Unicode map): few common words."""
    words = re.findall(r"[a-z]+", text[:8000].lower())
    return len(words) < 50 or sum(w in STOP for w in words) / len(words) < 0.04


def ocr(pdf, work):
    """The text of a PDF by OCR (pdftoppm, then tesseract), for a PDF whose text layer is garbled."""
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    subprocess.run(["pdftoppm", "-r", "200", "-gray", "-l", "40", "-png", str(pdf), str(work / "p")],
                   capture_output=True, timeout=900)
    pages = []
    for png in sorted(work.glob("p-*.png")):
        done = subprocess.run(["tesseract", str(png), "-", "-l", "eng"], capture_output=True, timeout=300)
        pages.append(done.stdout.decode("utf-8", errors="replace"))
    shutil.rmtree(work, ignore_errors=True)
    return "\f".join(pages)


def find_work(text, name, by_doi, by_id, by_title, title_pairs):
    """(work, how) for the text of a PDF, or (None, "")."""
    head = text[:20000]
    for d in DOI.findall(head[:5000]):  # the first page: further on, the DOIs are references
        d = d.lower().rstrip(".,;)")
        if d in by_doi:
            return by_doi[d], "doi"
    ids = re.findall(r"W\d{6,}", name)
    if ids and ids[0] in by_id:
        return by_id[ids[0]], "file name"
    nh = norm(head[:8000])
    for t, w in by_title:
        if t in (nh if len(t.split()) >= 6 else nh[:1500]):
            return w, "title"
    # a title reworded or cut: share of its word pairs found in the first pages
    pairs_head = set(zip(nh.split(), nh.split()[1:]))
    scored = sorted(((len(tp & pairs_head) / len(tp), w) for tp, w in title_pairs), key=lambda x: -x[0])
    if scored and scored[0][0] >= 0.7 and (len(scored) < 2 or scored[0][0] - scored[1][0] >= 0.2):
        return scored[0][1], f"title pairs {scored[0][0]:.2f}"
    return None, ""


def ocr_again(ids):
    """A new manual run with the OCR text of PDFs already taken in, for texts found garbled
    after the fact (a shifted font encoding that the test of the time missed). The PDF is the
    copy kept in fulltext/oa-pdf/<stamp>/ by the latest manual run that holds the work, so the
    SHA-256 is the same; the OCR text must still name the work (find_work), or it is left alone."""
    runs = sorted((json.loads(m.read_text(encoding="utf-8")) for m in ROOT.glob("raw/*-oa-fulltext-manifest.json")),
                  key=lambda m: m["stamp"], reverse=True)
    corpus = {w["openalex"]: w for w in load_corpus()}
    role = {s["key"]: s["role"] for s in load_seeds()}
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M")
    for suffix in "bcdefghij":
        if not (ROOT / f"raw/{stamp}-oa-fulltext-manifest.json").exists():
            break
        stamp = stamp[:15] + suffix
    out = ROOT / f"fulltext/oa-pdf/{stamp}"
    rows, unmatched = [], []
    for oa in ids:
        before = next(((m, e) for m in runs if m.get("pass") == "manual" for e in m["works"]
                       if e["openalex"] == oa and e["outcome"] == "text"), None)
        if not before or oa not in corpus:
            unmatched.append(f"{oa}: no manual text taken in for this work")
            continue
        m, e = before
        pdf = ROOT / f"fulltext/oa-pdf/{m['stamp']}/{oa}.pdf"
        if not pdf.exists() or hashlib.sha256(pdf.read_bytes()).hexdigest() != e["tried"][0]["sha256"]:
            unmatched.append(f"{oa}: the PDF of run {m['stamp']} is missing or changed")
            continue
        text = ocr(pdf, ROOT / "fulltext/manual/ocr-tmp")
        w = corpus[oa]
        nt = norm(w["title"])
        match, how = find_work(text, pdf.name, {(w["doi"] or "").lower(): w}, {}, [(nt, w)],
                               [(set(zip(nt.split(), nt.split()[1:])), w)])
        if not match:
            unmatched.append(f"{oa}: the OCR text does not name the work")
            continue
        out.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(pdf, out / f"{oa}.pdf")
        (out / f"{oa}.txt").write_text(text, encoding="utf-8")
        rows.append({"openalex": oa, "doi": w["doi"], "stratum": stratum(w, role), "oa_status": w["oa_status"],
                     "outcome": "text", "matched_by": how, "ocr": True, "ocr_again_of": m["stamp"],
                     "tried": e["tried"]})
    if rows:
        manifest = {"stamp": stamp, "pass": "manual", "pool": len(ids), "done": len(rows), "complete": True,
                    "pdfs_read": len(ids), "works": rows, "outcomes": {"text": len(rows)}, "unmatched": unmatched}
        (ROOT / f"raw/{stamp}-oa-fulltext-manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{stamp}: {len(rows)} texts read again by OCR, {len(unmatched)} left alone")
    for u in unmatched:
        print("  ", u)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--from", dest="folders", action="append", type=pathlib.Path)
    ap.add_argument("--since", help="YYYY-MM-DD: only PDFs modified from that day on")
    ap.add_argument("--tidy", action="store_true",
                    help="move the PDFs taken in (this run or before) and their second copies "
                         "to fulltext/manual/taken/")
    ap.add_argument("--ocr-again", nargs="+", metavar="OPENALEX",
                    help="read again by OCR the PDFs already taken in for these works")
    args = ap.parse_args(argv)
    if args.ocr_again:
        return ocr_again(args.ocr_again)
    folders = args.folders or [pathlib.Path.home() / "Downloads", pathlib.Path.home() / "Téléchargements",
                               ROOT / "fulltext/manual/inbox"]
    desk = ROOT / "fulltext/manual/index.html"
    # by default, the PDFs saved since the page was first written: older downloads are not read
    first = ROOT / "fulltext/manual/.first"
    if desk.exists() and not first.exists():
        first.write_text(str(desk.stat().st_mtime))
    since = (dt.datetime.fromisoformat(args.since).timestamp() if args.since
             else float(first.read_text()) - 3600 if first.exists() else 0)

    role = {s["key"]: s["role"] for s in load_seeds()}
    got, s2orc = texts_so_far()
    manual = {e["openalex"] for m in ROOT.glob("raw/*-oa-fulltext-manifest.json")
              for e in json.loads(m.read_text(encoding="utf-8")).get("works", [])
              if json.loads(m.read_text(encoding="utf-8")).get("pass") == "manual"}
    # the works still without a text, and those taken in by hand (to recognise a second copy)
    todo = [w for w in load_corpus() if stratum(w, role) in ("A", "B") and w["doi"]
            and w["doi"].lower() not in s2orc and (w["openalex"] not in got or w["openalex"] in manual)]
    by_doi = {w["doi"].lower().rstrip("."): w for w in todo}
    by_id = {w["openalex"]: w for w in todo}
    by_title = [(norm(w["title"]), w) for w in todo if len(norm(w["title"]).split()) >= 4]
    # word pairs only for titles of six words and more: a short generic title ("The Internet of
    # Everything") is found in the text of many other papers
    title_pairs = [(set(zip(t.split(), t.split()[1:])), w) for t, w in by_title if len(t.split()) >= 6]
    taken = {t["sha256"] for m in ROOT.glob("raw/*-oa-fulltext-manifest.json")
             for e in json.loads(m.read_text(encoding="utf-8")).get("works", [])
             if json.loads(m.read_text(encoding="utf-8")).get("pass") == "manual" for t in e["tried"]}

    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M")
    for suffix in "bcdefghij":  # two runs in the same minute must not overwrite each other
        if not (ROOT / f"raw/{stamp}-oa-fulltext-manifest.json").exists():
            break
        stamp = stamp[:15] + suffix
    out = ROOT / f"fulltext/oa-pdf/{stamp}"
    tmp = ROOT / "fulltext/manual/tmp.txt"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    rows, unmatched, seen, to_move = [], [], set(), []
    pdfs = sorted(p for d in folders if d.is_dir() for p in d.iterdir()
                  if p.is_file() and p.suffix.lower() == ".pdf" and p.stat().st_mtime >= since)
    for pdf in pdfs:
        if hashlib.sha256(pdf.read_bytes()).hexdigest() in taken:
            unmatched.append(f"{pdf.name}: already taken in")
            to_move.append(pdf)
            continue
        done = subprocess.run(["pdftotext", "-enc", "UTF-8", str(pdf), str(tmp)], capture_output=True, timeout=180)
        text = tmp.read_text(encoding="utf-8", errors="replace") if done.returncode == 0 and tmp.exists() else ""
        ocred = False
        if garbled(text):
            text, ocred = ocr(pdf, ROOT / "fulltext/manual/ocr-tmp"), True
        if not text.strip():
            unmatched.append(f"{pdf.name}: no text")
            continue
        match, how = find_work(text, pdf.name, by_doi, by_id, by_title, title_pairs)
        if not match and not ocred:  # a text layer garbled in a way the test misses: OCR, then again
            text_ocr = ocr(pdf, ROOT / "fulltext/manual/ocr-tmp")
            match, how = find_work(text_ocr, pdf.name, by_doi, by_id, by_title, title_pairs)
            if match:
                text, ocred = text_ocr, True
        if not match:
            unmatched.append(f"{pdf.name}: no work still without a text (already taken in, or not a candidate)")
            continue
        if match["openalex"] in manual:
            unmatched.append(f"{pdf.name}: second PDF of {match['openalex']}, taken in before")
            to_move.append(pdf)
            continue
        if match["openalex"] in seen:
            unmatched.append(f"{pdf.name}: second PDF of {match['openalex']}")
            to_move.append(pdf)
            continue
        seen.add(match["openalex"])
        out.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(pdf, out / f"{match['openalex']}.pdf")
        (out / f"{match['openalex']}.txt").write_text(text, encoding="utf-8")
        data = pdf.read_bytes()
        rows.append({"openalex": match["openalex"], "doi": match["doi"], "stratum": stratum(match, role),
                     "oa_status": match["oa_status"], "outcome": "text", "matched_by": how, "ocr": ocred,
                     "tried": [{"file": pdf.name, "folder": str(pdf.parent), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}]})
    tmp.unlink(missing_ok=True)
    to_move += [pdf for pdf in pdfs if any(r["tried"][0]["file"] == pdf.name and r["tried"][0]["folder"] == str(pdf.parent)
                                            for r in rows)]
    if args.tidy:
        dest = ROOT / "fulltext/manual/taken"
        dest.mkdir(parents=True, exist_ok=True)
        for pdf in dict.fromkeys(to_move):
            target = dest / pdf.name
            n = 1
            while target.exists():
                target = dest / f"{pdf.stem} ({n}){pdf.suffix}"
                n += 1
            shutil.move(str(pdf), target)
        print(f"{len(dict.fromkeys(to_move))} PDFs moved to {dest}")
    if rows:
        manifest = {"stamp": stamp, "pass": "manual", "pool": len(todo), "done": len(rows), "complete": True,
                    "pdfs_read": len(pdfs), "works": rows,
                    "outcomes": {"text": len(rows)}, "unmatched": unmatched}
        (ROOT / f"raw/{stamp}-oa-fulltext-manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(pdfs)} PDFs read, {len(rows)} matched "
          f"({sum(r['matched_by'] == 'doi' for r in rows)} by DOI, {sum(r['matched_by'].startswith('title') for r in rows)} "
          f"by title, {sum(r['matched_by'] == 'file name' for r in rows)} by file name), {len(unmatched)} left alone")
    for u in unmatched:
        print("  ", u)
    return 0


if __name__ == "__main__":
    sys.exit(main())
