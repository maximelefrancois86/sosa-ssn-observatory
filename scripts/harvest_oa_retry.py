#!/usr/bin/env python3
"""Third pass of the open-access retrieval: the works of strata A and B whose downloads failed.

    python3 -I scripts/harvest_oa_retry.py

The pool is every work of the complete A-and-B runs (scripts/harvest_oa_fulltext.py, then
scripts/harvest_oa_landing.py) where a download failed and that no run gave a text.
For each work, in turn, until one gives a PDF (or a text):

1. the URLs tried before, again, with the faults of the first passes corrected: non-ASCII
   paths percent-encoded, a longer timeout, one more attempt after a pause for a timeout,
   a 202 or a 5xx; an HTML page that is not a bot challenge is searched for a
   `citation_pdf_url`;
2. other sources asked by DOI: the `openAccessPdf` of Semantic Scholar (and its arXiv
   identifier), and Europe PMC (the PDF it renders, or its full-text XML).

A page that answers with a bot challenge (Anubis, reCAPTCHA, Cloudflare) is recorded as
`bot challenge` and left alone: the challenge is not solved. The User-Agent stays the one of
the first passes, which says what the client is.

Writes raw/<stamp>-oa-retry-sources.jsonl.gz (the answers of Semantic Scholar and Europe PMC),
raw/<stamp>-oa-fulltext-manifest.json (same form as the first passes, `pass`: `retry`) and the
texts in fulltext/oa-pdf/<stamp>/; scripts/build_items.py reads the texts of every complete
run. Downloaded data are only searched with regular expressions, never rendered or executed.
Standard library only, apart from `pdftotext`.
"""
import collections
import datetime as dt
import gzip
import hashlib
import html
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from harvest_oa_landing import META  # noqa: E402
from harvest_s2 import api_key as s2_key  # noqa: E402
from pilot_oa_fulltext import MAX_BYTES  # noqa: E402
from strata import ROOT  # noqa: E402

UA = "Mozilla/5.0 (research text mining; SOSA/SSN review)"
CHALLENGE = re.compile(rb"anubis|recaptcha|cf-chl|challenge-platform|just a moment\.\.\.|making sure you", re.I)
S2 = "https://api.semanticscholar.org/graph/v1/paper/batch?fields=openAccessPdf,externalIds"
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"


def iri(url):
    """The URL with its non-ASCII characters percent-encoded (urllib refuses them)."""
    p = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((p.scheme, p.netloc.encode("idna").decode() if p.netloc else "",
                                    urllib.parse.quote(p.path, safe="/%:@!$&'()*+,;="),
                                    urllib.parse.quote(p.query, safe="=&%+/:;,@!$'()*"), p.fragment))


def fetch(url, accept="application/pdf,*/*;q=0.5", tries=2):
    """(outcome dict, body bytes or None). Retries once a timeout, a 202 or a 5xx."""
    res = {}
    for attempt in range(tries):
        req = urllib.request.Request(iri(url), headers={"User-Agent": UA, "Accept": accept})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read(MAX_BYTES + 1)
                status, ctype, final = r.status, r.headers.get("Content-Type", ""), r.geturl()
        except urllib.error.HTTPError as e:
            res = {"outcome": "error", "error": f"HTTP {e.code}"}
            try:
                body = e.read(200_000)
            except Exception:
                body = b""
            if CHALLENGE.search(body):
                return {"outcome": "bot challenge", "status": e.code}, None
            if e.code >= 500 and attempt + 1 < tries:
                time.sleep(20)
                continue
            return res, None
        except Exception as e:
            res = {"outcome": "error", "error": repr(e)[:200]}
            if "timed out" in repr(e) and attempt + 1 < tries:
                time.sleep(20)
                continue
            return res, None
        if len(data) > MAX_BYTES:
            return {"outcome": "too large", "status": status}, None
        if data.startswith(b"%PDF"):
            return {"outcome": "pdf", "status": status, "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest()}, data
        if CHALLENGE.search(data[:200_000]):
            return {"outcome": "bot challenge", "status": status, "final": final}, None
        if status == 202 and attempt + 1 < tries:
            time.sleep(20)
            continue
        return {"outcome": "not a PDF", "status": status, "content_type": ctype, "bytes": len(data),
                "final": final}, data
    return res, None


def get_json(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "sosa-ssn-slr-harvest",
                                                           "Content-Type": "application/json", **(headers or {})})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(3 * 2 ** attempt)
        except OSError:
            time.sleep(3 * 2 ** attempt)
    return None


def to_text(pdf, txt):
    done = subprocess.run(["pdftotext", "-enc", "UTF-8", str(pdf), str(txt)], capture_output=True, timeout=180)
    return done.returncode == 0 and txt.exists() and txt.read_text(encoding="utf-8", errors="replace").strip()


def xml_text(xml):
    """The body of a JATS article from Europe PMC, as plain text, one paragraph per block."""
    xml = re.sub(r"(?s)<(ref-list|table-wrap|fig|xref)[ >].*?</\1>", " ", xml)
    xml = re.sub(r"</(p|title|sec|abstract)>", "\n\n", xml)
    return html.unescape(re.sub(r"<[^>]+>", "", xml)) + "\n"


def main():
    runs = []
    for m in sorted(ROOT.glob("raw/*-oa-fulltext-manifest.json")):
        man = json.loads(m.read_text(encoding="utf-8"))
        if man.get("complete") and man.get("population", "ab") == "ab" and man.get("pass") != "retry":
            runs.append(man)
    texts = {e["openalex"] for man in runs for e in man["works"] if e["outcome"] == "text"}
    failed, urls = {}, collections.defaultdict(list)
    for man in runs:
        for e in man["works"]:
            if e["outcome"] == "failed":
                failed.setdefault(e["openalex"], e)
            for t in e["tried"]:
                if t["url"] not in urls[e["openalex"]]:
                    urls[e["openalex"]].append(t["url"])
    pool = sorted((e for w, e in failed.items() if w not in texts), key=lambda e: e["openalex"])
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M")
    print(f"{stamp}: {len(pool)} works to retry", file=sys.stderr, flush=True)

    # other sources, asked once for the whole pool
    key = s2_key()
    s2 = {}
    for i in range(0, len(pool), 400):
        ids = [f"DOI:{e['doi']}" for e in pool[i:i + 400]]
        ans = get_json(S2, json.dumps({"ids": ids}).encode(), {"x-api-key": key} if key else None) or []
        for e, p in zip(pool[i:i + 400], ans):
            s2[e["openalex"]] = p
        time.sleep(2)
    epmc = {}
    for e in pool:
        q = urllib.parse.quote(f'DOI:"{e["doi"]}"')
        ans = get_json(f"{EPMC}/search?query={q}&resultType=core&format=json")
        hits = (ans or {}).get("resultList", {}).get("result", [])
        epmc[e["openalex"]] = hits[0] if hits else None
        time.sleep(0.3)
    (ROOT / f"raw/{stamp}-oa-retry-sources.jsonl.gz").write_bytes(gzip.compress("".join(
        json.dumps({"openalex": e["openalex"], "doi": e["doi"], "s2": s2.get(e["openalex"]),
                    "europepmc": epmc.get(e["openalex"])}, ensure_ascii=False) + "\n" for e in pool).encode(),
        mtime=0))

    out = ROOT / f"fulltext/oa-pdf/{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    rows, outcomes, hosts = [], collections.Counter(), collections.Counter()
    for n, e in enumerate(pool, 1):
        w = e["openalex"]
        cands = [(u, "earlier") for u in urls[w]]
        p = s2.get(w) or {}
        if (p.get("openAccessPdf") or {}).get("url"):
            cands.append((p["openAccessPdf"]["url"], "semantic scholar"))
        if (p.get("externalIds") or {}).get("ArXiv"):
            cands.append((f"https://arxiv.org/pdf/{p['externalIds']['ArXiv']}", "arxiv"))
        hit = epmc.get(w) or {}
        if hit.get("pmcid") and hit.get("isOpenAccess") == "Y":
            cands.append((f"{EPMC}/{hit['pmcid']}/fullTextXML", "europepmc xml"))
        entry = {"openalex": w, "doi": e["doi"], "stratum": e["stratum"], "oa_status": e["oa_status"],
                 "tried": []}
        outcome, seen = "failed", set()
        while cands and len(entry["tried"]) < 8:
            u, src = cands.pop(0)
            if u in seen:
                continue
            seen.add(u)
            accept = "application/xml" if src == "europepmc xml" else "application/pdf,*/*;q=0.5"
            res, data = fetch(u, accept)
            entry["tried"].append({"url": u, "source": src, **res})
            time.sleep(1.5)
            txt = out / f"{w}.txt"
            if src == "europepmc xml" and data and b"<article" in data[:5000]:
                txt.write_text(xml_text(data.decode("utf-8", errors="replace")), encoding="utf-8")
                entry["tried"][-1]["outcome"] = "xml"
                outcome = "text"
                break
            if res["outcome"] == "pdf":
                pdf = out / f"{w}.pdf"
                pdf.write_bytes(data)
                outcome = "text" if to_text(pdf, txt) else "pdf without text"
                break
            if res["outcome"] == "not a PDF" and data and "html" in res.get("content_type", ""):
                m = META.search(data[:3_000_000].decode("utf-8", errors="replace"))
                if m:
                    pdf_url = urllib.parse.urljoin(res.get("final") or u, html.unescape(m.group(1) or m.group(2)))
                    cands.insert(0, (pdf_url, "citation_pdf_url"))
        if outcome == "failed" and entry["tried"] and all(t["outcome"] == "bot challenge" for t in entry["tried"]):
            outcome = "bot challenge"
        if outcome != "text":
            for t in entry["tried"]:
                hosts[(urllib.parse.urlsplit(t["url"]).netloc, t["outcome"] if t["outcome"] != "error"
                       else t["error"][:40])] += 1
        entry["outcome"] = outcome
        outcomes[outcome] += 1
        rows.append(entry)
        if n % 25 == 0:
            print(f"{n}/{len(pool)} {dict(outcomes)}", file=sys.stderr, flush=True)
    manifest = {"stamp": stamp, "pass": "retry", "after": [m["stamp"] for m in runs], "pool": len(pool),
                "done": len(rows), "complete": True, "s2_api_key_used": bool(key), "works": rows,
                "outcomes": dict(outcomes),
                "by_source": dict(collections.Counter(next(t["source"] for t in e["tried"]
                                                           if t["outcome"] in ("pdf", "xml"))
                                                      for e in rows if e["outcome"] == "text")),
                "failures_by_host": {f"{h} {o}": c for (h, o), c in hosts.most_common()}}
    (ROOT / f"raw/{stamp}-oa-fulltext-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{stamp}: {dict(outcomes)} {manifest['by_source']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
