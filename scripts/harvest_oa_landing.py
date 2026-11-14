#!/usr/bin/env python3
"""Second pass of the open-access retrieval: the PDF announced by the landing pages.

    python3 -I scripts/harvest_oa_landing.py

For every work of the last complete run of scripts/harvest_oa_fulltext.py that gave no text
(no PDF location in OpenAlex, or every download failed), the landing pages are read: the DOI
resolver, then the landing pages of the OpenAlex locations kept in the raw harvest. A page
that declares `<meta name="citation_pdf_url" content="...">` (the Highwire tags that
publishers and repositories expose for indexers) gives a PDF URL, downloaded once as in the
first pass. The HTML is downloaded data: it is only searched with a regular expression,
never rendered or executed.

Writes raw/<stamp>-oa-fulltext-manifest.json (same form as the first pass, with `pass`:
`landing pages`) and the texts in fulltext/oa-pdf/<stamp>/; scripts/build_items.py reads
the texts of every complete run. Standard library only, apart from `pdftotext`.
"""
import collections
import datetime as dt
import gzip
import html
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pilot_oa_fulltext import download  # noqa: E402
from strata import ROOT  # noqa: E402

META = re.compile(r"""<meta\s+[^>]*name=["']citation_pdf_url["'][^>]*content=["']([^"']+)["']"""
                  r"""|<meta\s+[^>]*content=["']([^"']+)["'][^>]*name=["']citation_pdf_url["']""", re.I)
UA = "Mozilla/5.0 (research text mining; SOSA/SSN review)"


def page(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*;q=0.5"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            if "html" not in (r.headers.get("Content-Type") or ""):
                return None, r.geturl()
            return r.read(3_000_000).decode("utf-8", errors="replace"), r.geturl()
    except Exception:
        return None, url


def main():
    runs = [m for m in sorted(ROOT.glob("raw/*-oa-fulltext-manifest.json"))
            if json.loads(m.read_text(encoding="utf-8")).get("complete")
            and json.loads(m.read_text(encoding="utf-8")).get("pass", "locations") == "locations"
            and json.loads(m.read_text(encoding="utf-8")).get("population", "ab") == "ab"]
    first = json.loads(runs[-1].read_text(encoding="utf-8"))
    located = {}
    with gzip.open(ROOT / f"raw/{first['stamp']}-openalex-locations-all.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            located[r["id"].rsplit("/", 1)[-1]] = r
    todo = [e for e in first["works"] if e["outcome"] != "text"]
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M")
    out = ROOT / f"fulltext/oa-pdf/{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    rows, outcomes = [], collections.Counter()
    for n, e in enumerate(todo, 1):
        r = located.get(e["openalex"], {})
        landings = [f"https://doi.org/{e['doi']}"] + [loc["landing_page_url"] for loc in r.get("locations") or []
                                                       if loc.get("landing_page_url")]
        seen, entry = set(), {"openalex": e["openalex"], "doi": e["doi"], "stratum": e["stratum"],
                              "oa_status": e["oa_status"], "pages": [], "tried": []}
        outcome = "no citation_pdf_url"
        for lp in landings[:4]:
            if lp in seen:
                continue
            seen.add(lp)
            text, final = page(lp)
            time.sleep(1.0)
            m = META.search(text or "")
            entry["pages"].append({"url": lp, "final": final, "meta": bool(m)})
            if not m:
                continue
            pdf_url = urllib.parse.urljoin(final, html.unescape(m.group(1) or m.group(2)))
            pdf = out / f"{e['openalex']}.pdf"
            res = download(pdf_url, pdf)
            entry["tried"].append({"url": pdf_url, **res})
            time.sleep(1.0)
            if res["outcome"] == "pdf":
                txt = out / f"{e['openalex']}.txt"
                done = subprocess.run(["pdftotext", "-enc", "UTF-8", str(pdf), str(txt)], capture_output=True,
                                      timeout=180)
                ok = done.returncode == 0 and txt.exists() and txt.read_text(encoding="utf-8", errors="replace").strip()
                outcome = "text" if ok else "pdf without text"
                break
            outcome = "failed"
        entry["outcome"] = outcome
        outcomes[outcome] += 1
        rows.append(entry)
        if n % 25 == 0:
            print(f"{n}/{len(todo)} {dict(outcomes)}", file=sys.stderr, flush=True)
    manifest = {"stamp": stamp, "pass": "landing pages", "after": first["stamp"], "pool": len(todo),
                "done": len(rows), "complete": True, "works": rows, "outcomes": dict(outcomes)}
    (ROOT / f"raw/{stamp}-oa-fulltext-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{stamp}: {dict(outcomes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
