#!/usr/bin/env python3
"""A local page to fetch by hand the full texts that the scripts could not get.

    python3 -I scripts/download_desk.py      # fulltext/manual/index.html and one page per platform
                                             # (ieee.html, sciencedirect.html…), not versioned

The works listed: candidates of strata A and B with a DOI, no S2ORC text and no text from
any retrieval run, that a reader of the school can open (access checked on 2026-11-12):
- every work published on IEEE Xplore, ScienceDirect, the ACM Digital Library or theses.fr,
  open access or not;
- the open-access works of the publishers outside the subscription table (MDPI, preprint
  servers, university presses…), whose DOI leads to the text;
- the works of the other subscription platforms (SpringerLink, Wiley…), which the school
  cannot read, only when OpenAlex knows a copy elsewhere (a repository, HAL), and with the
  links of that copy only: the open-access flag alone is not enough (Maxime, 2026-11-12: a
  "green" Springer chapter with no known copy could not be opened).
The rest is counted, not listed.

Order: stratum A before B, and within each, the works whose title or abstract names SOSA/SSN
first, then by year, most recent first. Each row gives direct links: the IEEE Xplore PDF
(stamp.jsp, from the article number the DOI leads to), the ScienceDirect PDF (pdfft, from the
PII), the ACM PDF; for open access, the PDF and landing pages that OpenAlex knows, and the
DOI. Where the IEEE and ScienceDirect DOIs lead is asked once to the doi.org handle API and
kept in fulltext/manual/doi-targets.json. A person clicks, the publisher's page or PDF opens,
the PDF is saved anywhere (the Downloads folder is fine): scripts/ingest_manual.py then finds
which work each PDF is. The ticks of the page are kept in the browser only.
"""
import collections
import csv
import gzip
import html
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from closed_access import PLATFORM  # noqa: E402
from strata import ROOT, load_corpus, load_seeds, stratum, wrong_texts  # noqa: E402

NAMES = re.compile(r"\b(?:SOSA|SSN(?:-XG)?|[Ss]emantic [Ss]ensor [Nn]etwork(?:s)?(?: [Oo]ntology)?)\b")
NOT_COPIES = re.compile(r"springer|wiley|tandfonline|taylorfrancis|igi-global|sagepub|iospress|degruyter|"
                        r"spiedigitallibrary|emerald|worldscientific|ascelibrary|eurekaselect|cambridge\.org|"
                        r"inderscience|theiet|aiaa|jove\.com|iop\.org|scopus\.com|doaj\.org|doabooks", re.I)
READABLE = {"IEEE Xplore", "IBM (IEEE Xplore)", "ScienceDirect (Elsevier)", "ACM Digital Library",
            "theses.fr (ABES): French theses, no subscription"}


def texts_so_far():
    """OpenAlex ids with a text from a retrieval run, and DOIs with an S2ORC text."""
    got, wrong = set(), wrong_texts()
    for m in ROOT.glob("raw/*-oa-fulltext-manifest.json"):
        man = json.loads(m.read_text(encoding="utf-8"))
        if man.get("complete"):
            got |= {e["openalex"] for e in man["works"] if e["outcome"] == "text"
                    and (man["stamp"], e["openalex"]) not in wrong
                    and (ROOT / f"fulltext/oa-pdf/{man['stamp']}/{e['openalex']}.txt").exists()}
    items = [json.loads(l) for l in open(ROOT / "screening/items.jsonl", encoding="utf-8")]
    s2orc = {it["doi"].lower() for it in items if it["doi"] and it["item"].startswith("s2orc:")}
    return got, s2orc


def links_from_openalex():
    """For each work: the PDF and landing URLs of its OpenAlex locations (last harvest)."""
    out = collections.defaultdict(list)
    for path in sorted(ROOT.glob("raw/*-openalex-locations-all.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                w = r["id"].rsplit("/", 1)[-1]
                urls = []
                for loc in [r.get("best_oa_location") or {}] + (r.get("locations") or []):
                    for k in ("pdf_url", "landing_page_url"):
                        u = loc.get(k)
                        if u and "doi.org/" not in u and u not in urls:
                            urls.append(u)
                out[w] = urls
    return out


def main():
    role = {s["key"]: s["role"] for s in load_seeds()}
    got, s2orc = texts_so_far()
    platform = {}
    with open(ROOT / "results/closed-access.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            platform[row["openalex"]] = row["platform"]
    links = links_from_openalex()
    rows, skipped = [], collections.Counter()
    for w in load_corpus():
        st = stratum(w, role)
        if st not in ("A", "B") or not w["doi"] or w["doi"].lower() in s2orc or w["openalex"] in got:
            continue
        closed = w["oa_status"] in ("closed", "", None)
        plat = platform.get(w["openalex"]) or PLATFORM.get(w["doi"].split("/")[0], "open-access publisher")
        found = links.get(w["openalex"], [])
        if plat in READABLE or plat == "open-access publisher":
            shown = found[:3]
        else:  # a subscription platform the school cannot read: only a copy elsewhere helps
            shown = [u for u in found if not NOT_COPIES.search(u)][:3]
            if closed or not shown:
                skipped[f"{plat}{'' if closed else ' (open access, no copy known)'}"] += 1
                continue
            plat = f"copy elsewhere ({plat.split(' (')[0]})"
        if plat in READABLE and not closed:
            plat += ", open access"
        if plat == "open-access publisher" and closed:
            skipped["closed, publisher unknown"] += 1
            continue
        named = bool(NAMES.search(f"{w['title']} {w.get('abstract') or ''}"))
        rows.append({"w": w, "stratum": st, "named": named, "platform": plat, "links": shown})
    rows.sort(key=lambda r: (r["stratum"], not r["named"], -(int(r["w"]["year"]) if str(r["w"]["year"]).isdigit()
                                                               else 0)))
    by = collections.Counter(r["platform"] for r in rows)
    skipped_txt = ", ".join(f"{k} {v}" for k, v in skipped.most_common())
    out = ROOT / "fulltext/manual"
    out.mkdir(parents=True, exist_ok=True)
    targets = resolve(rows, out / "doi-targets.json")
    groups = collections.defaultdict(list)
    for r in rows:
        groups[family(r["platform"])].append(r)
    nav = " · ".join(f'<a href="{f}.html">{FAMILIES[f]} ({len(groups[f])})</a>' for f in FAMILIES if groups[f])
    for f, rs in groups.items():
        (out / f"{f}.html").write_text(render(rs, FAMILIES[f], nav, targets), encoding="utf-8")
    (out / "index.html").write_text(render(rows, "all platforms", nav, targets,
                                           f"Not listed (no access): {skipped_txt}."), encoding="utf-8")
    print(f"{out}: {len(rows)} works ({', '.join(f'{f} {len(g)}' for f, g in groups.items())}; "
          f"★ {sum(r['named'] for r in rows)}); not listed: {skipped_txt}")
    return 0


FAMILIES = {"ieee": "IEEE Xplore", "sciencedirect": "ScienceDirect", "acm": "ACM", "theses": "theses.fr",
            "open": "open-access publishers", "copies": "copies elsewhere"}


def family(plat):
    for key, f in (("IEEE", "ieee"), ("ScienceDirect", "sciencedirect"), ("ACM", "acm"), ("theses.fr", "theses"),
                   ("copy elsewhere", "copies")):
        if key in plat:
            return f
    return "open"


def resolve(rows, cache_path):
    """Where the DOIs of IEEE Xplore and ScienceDirect lead (doi.org handle API, not the
    publishers): the IEEE article number and the ScienceDirect PII give direct PDF links."""
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    for r in rows:
        doi = r["w"]["doi"]
        if doi in cache or family(r["platform"]) not in ("ieee", "sciencedirect"):
            continue
        try:
            req = urllib.request.Request(f"https://doi.org/api/handles/{urllib.parse.quote(doi, safe='/')}",
                                         headers={"User-Agent": "sosa-ssn-slr-harvest"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                vals = json.load(resp).get("values", [])
            cache[doi] = next((v["data"]["value"] for v in vals if v.get("type") == "URL"), "")
        except Exception:
            cache[doi] = ""
        time.sleep(0.2)
    cache_path.write_text(json.dumps(cache, indent=1), encoding="utf-8")
    return cache


def direct(r, targets):
    """Direct links for a row: (label, url) pairs."""
    w, f = r["w"], family(r["platform"])
    target = targets.get(w["doi"], "")
    if f == "ieee":
        m = re.search(r"arnumber=(\d+)|/document/(\d+)", target)
        if m:
            n = m.group(1) or m.group(2)
            return [("PDF", f"https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={n}"),
                    ("page", f"https://ieeexplore.ieee.org/document/{n}")]
    if f == "sciencedirect":
        m = re.search(r"/pii/(S?[0-9X]+)", target, re.I)
        if m:
            return [("PDF", f"https://www.sciencedirect.com/science/article/pii/{m.group(1)}/pdfft"),
                    ("page", f"https://www.sciencedirect.com/science/article/pii/{m.group(1)}")]
    if f == "acm":
        return [("PDF", f"https://dl.acm.org/doi/pdf/{w['doi']}"), ("page", f"https://dl.acm.org/doi/{w['doi']}")]
    links = [("PDF" if ".pdf" in u.lower() or "/document" in u or "download" in u.lower() else "page", u)
             for u in r["links"]]
    if f != "copies":
        links.append(("DOI", f"https://doi.org/{w['doi']}"))
    return links


def render(rows, name, nav, targets, note=""):
    esc = html.escape
    by = collections.Counter(r["platform"] for r in rows)
    trs = []
    for i, r in enumerate(rows, 1):
        w = r["w"]
        links = " ".join(f'<a href="{esc(u)}" target="_blank" rel="noopener">{label}</a>'
                         for label, u in direct(r, targets))
        trs.append(
            f'<tr data-id="{w["openalex"]}"><td><input type="checkbox" aria-label="done"></td><td>{i}</td>'
            f'<td>{r["stratum"]}{"&nbsp;★" if r["named"] else ""}</td><td>{esc(str(w["year"]))}</td>'
            f'<td class="t">{esc(w["title"])}<div class="v">{esc(w["venue"] or "")} · {w["openalex"]}</div></td>'
            f'<td>{esc(r["platform"])}</td><td class="l">{links}</td></tr>')
    return PAGE.format(name=esc(name), n=len(rows), nav=nav, rows="\n".join(trs),
                       counts=esc(", ".join(f"{k} {v}" for k, v in by.most_common())), note=esc(note))


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Full texts: {name}</title>
<style>
:root {{ --bg:#fbfaf7; --fg:#1d1d1b; --mute:#6b6a65; --line:#e3e1da; --accent:#2b5fab; --done:#eef3e8; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#1a1a19; --fg:#ecebe6; --mute:#9d9b94; --line:#34332f;
  --accent:#86aef0; --done:#22301c; }} }}
body {{ background:var(--bg); color:var(--fg); font:14px/1.45 system-ui, sans-serif; margin:0; padding:16px; }}
h1 {{ font-size:20px; margin:0 0 6px; }} p {{ margin:4px 0; color:var(--mute); max-width:70em; }}
nav a, td.l a {{ color:var(--accent); margin-right:8px; white-space:nowrap; }}
.bar {{ position:sticky; top:0; background:var(--bg); padding:8px 0; border-bottom:1px solid var(--line); z-index:1; }}
table {{ border-collapse:collapse; width:100%; margin-top:8px; }}
td {{ border-bottom:1px solid var(--line); padding:5px 6px; vertical-align:top; }}
td.t {{ width:55%; }} .v {{ color:var(--mute); font-size:12px; }}
tr.done {{ background:var(--done); }} tr.done td.t {{ color:var(--mute); }}
</style></head><body>
<div class="bar"><h1>Full texts to fetch, {name}: <span id="left">{n}</span> left of {n}</h1>
<nav><a href="index.html">all</a> · {nav}</nav>
<p>Click PDF (or the page): the row greys at once (untick it to undo). Save the PDF anywhere (Téléchargements is fine, no renaming).
Then tell the agent, who runs <code>scripts/ingest_manual.py</code>: it matches each PDF to its work by DOI or
title; a PDF it does not recognise can be renamed with the W… id of its row.
★ = SOSA/SSN named in the title or abstract. Order: stratum A first, ★ first, recent first.</p>
<p>{counts}. {note}</p>
<label><input type="checkbox" id="hide"> hide ticked rows</label></div>
<table><tbody>
{rows}
</tbody></table>
<script>
const KEY = "slr-desk-done";
let done = {{}};
try {{ done = JSON.parse(localStorage.getItem(KEY) || "{{}}"); }} catch (e) {{}}
const rows = [...document.querySelectorAll("tr[data-id]")];
function paint() {{
  const hide = document.getElementById("hide").checked;
  let left = 0;
  for (const tr of rows) {{
    const d = !!done[tr.dataset.id];
    tr.classList.toggle("done", d);
    tr.querySelector("input").checked = d;
    tr.style.display = d && hide ? "none" : "";
    left += d ? 0 : 1;
  }}
  document.getElementById("left").textContent = left;
}}
function mark(tr, value) {{
  done[tr.dataset.id] = value;
  try {{ localStorage.setItem(KEY, JSON.stringify(done)); }} catch (err) {{}}
  paint();
}}
for (const tr of rows) {{
  tr.querySelector("input").addEventListener("change", e => mark(tr, e.target.checked));
  // a click on any link of the row (left or middle button) greys the row; untick to undo
  for (const a of tr.querySelectorAll("a")) {{
    a.addEventListener("click", () => mark(tr, true));
    a.addEventListener("auxclick", e => {{ if (e.button === 1) mark(tr, true); }});
  }}
}}
document.getElementById("hide").addEventListener("change", paint);
paint();
</script></body></html>
"""


if __name__ == "__main__":
    sys.exit(main())
