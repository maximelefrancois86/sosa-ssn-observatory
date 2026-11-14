#!/usr/bin/env python3
"""The figures of the papers, as LaTeX macros: nothing in a paper is typed by hand.

    python3 -I scripts/article_macros.py     # results/macros.tex, results/figures/*.csv

Reads the machine-readable outputs of the other scripts (results/*.json, written next to
their Markdown reports, and results/terms.csv) and writes one `\\slrdef{key}{value}` line
per figure, with the file it comes from. The papers load `results/macros.tex` and write
`\\slr{key}`; an unknown key prints in bold as `??key??` and warns, so that a missing or
renamed figure shows in the PDF instead of passing silently.

A figure missing from its source (a script not run yet) is left out, with a comment.
Standard library only.
"""
import csv
import datetime as dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]


def num(n):
    """An integer with thousands separators, as the papers print it: 2,304."""
    return f"{round(n):,}"


def pct(n, d, digits=1):
    return f"{100 * n / d:.{digits}f}\\%" if d else "--"


def date(stamp):
    """2026-11-07T1337 or 2026-11-07 -> 7 November 2026."""
    d = dt.date.fromisoformat(stamp[:10])
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def tex_escape(s):
    return (s.replace("\\", "\\textbackslash{}").replace("&", "\\&").replace("%", "\\%")
            .replace("_", "\\_").replace("#", "\\#"))


class Macros:
    def __init__(self):
        self.lines, self.keys = [], set()

    def source(self, rel):
        self.lines.append(f"\n% --- {rel}")

    def add(self, key, value):
        if key in self.keys:
            raise SystemExit(f"duplicate key {key}")
        self.keys.add(key)
        self.lines.append(f"\\slrdef{{{key}}}{{{value}}}")

    def missing(self, rel):
        self.lines.append(f"\n% --- {rel}: missing, run the script that writes it")


def load(name):
    p = RESULTS / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main():
    m = Macros()

    s = load("scoping.json")
    if s:
        m.source("results/scoping.json (scripts/scoping.py)")
        n = s["candidates"]
        st = s["strata"]
        m.add("harvest", s["harvest"])
        m.add("harvest-date", date(s["harvest"]))
        m.add("seeds", num(len(s["seeds"])))
        m.add("candidates", num(n))
        for k in "ABC":
            m.add(f"stratum-{k.lower()}", num(st[k]["works"]))
            m.add(f"stratum-{k.lower()}-oa-pct", pct(st[k]["open_access"], st[k]["works"]))
            m.add(f"stratum-{k.lower()}-closed", num(st[k]["works"] - st[k]["open_access"]))
        m.add("strata-ab", num(st["A"]["works"] + st["B"]["works"]))
        m.add("lineage-only", num(st["B"]["works"] + st["C"]["works"]))
        m.add("abstracts-pct", pct(s["abstracts"], n))
        m.add("dois-pct", pct(s["dois"], n))
        m.add("named-title", num(s["named_title"]))
        m.add("named-title-abstract", num(s["named_title_abstract"]))
        m.add("named-title-abstract-pct", pct(s["named_title_abstract"], n, 0))
        m.add("secondary-by-title", num(s["secondary_by_title"]))
        m.add("duplicate-titles", num(s["duplicate_titles"]))
        m.add("retracted", num(s["retracted"]))
        for key, v in s["seeds"].items():
            m.add(f"seed-{key}", num(v["citing"]))
            m.add(f"seed-{key}-only", num(v["citing_only"]))
        types = dict(s["top"]["type"])
        for t in ("article", "conference-paper", "dissertation", "book-chapter", "preprint", "review"):
            if t in types:
                m.add(f"type-{t}-pct", pct(types[t], n, 0))
        venues = [(v, c) for v, c in s["top"]["venue"] if v != "(none)"]
        for i, (v, c) in enumerate(venues[:10], 1):
            m.add(f"venue-{i}-name", tex_escape(v))
            m.add(f"venue-{i}", num(c))
        m.add("venue-none", num(dict(s["top"]["venue"]).get("(none)", 0)))
        for k, v in s.get("seed_groups", {}).items():
            m.add("group-" + k.replace(" ", "-").replace("+", "plus"), num(v))
        if "countries" in s:
            m.add("with-countries", num(s["with_countries"]))
            m.add("with-countries-pct", pct(s["with_countries"], n, 0))
            for i, (c, v) in enumerate(s["countries"][:10], 1):
                m.add(f"country-{i}-name", c)
                m.add(f"country-{i}", num(v))
                m.add(f"country-{i}-pct", pct(v, s["with_countries"], 0))
        m.add("publisher-none", num(dict(s["top"]["publisher"]).get("(none)", 0)))
        m.add("publisher-none-pct", pct(dict(s["top"]["publisher"]).get("(none)", 0), n, 0))
        langs = dict(s["top"]["language"])
        m.add("language-en-pct", pct(langs.get("en", 0), n))
        fields = dict(s["top"]["field"])
        m.add("field-cs-pct", pct(fields.get("Computer Science", 0), n, 0))
        years = sorted(int(y) for y in s["by_year_and_stratum"])
        m.add("first-year", str(years[0]))
        m.add("last-year", str(years[-1]))
        fig = RESULTS / "figures"
        fig.mkdir(exist_ok=True)
        with open(fig / "candidates-by-year.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["year", "A", "B", "C"])
            for y in years:
                row = s["by_year_and_stratum"][str(y)]
                w.writerow([y, row["A"], row["B"], row["C"]])
    else:
        m.missing("results/scoping.json")

    v = load("venue-risk.json")
    if v:
        m.source("results/venue-risk.json (scripts/venue_risk.py)")
        m.add("venue-list-date", date(v["snapshot"]))
        m.add("flagged", num(v["flagged"]))
        m.add("flagged-pct", pct(v["flagged"], v["candidates"]))
        mdpi = next((c for p, c in v["by_publisher"].items() if "MDPI" in p), 0)
        m.add("flagged-mdpi", num(mdpi))
        m.add("flagged-mdpi-pct", pct(mdpi, v["candidates"]))
        if s:
            for k in "ABC":
                m.add(f"flagged-{k.lower()}-pct", pct(v["flagged_by_stratum"].get(k, 0), s["strata"][k]["works"]))
        r = v.get("register")
        if r:
            m.add("register-date", date(r["snapshot"]))
            m.add("register-low", num(r["low"]))
            m.add("register-low-and-flagged", num(r["low_and_flagged"]))
            if r.get("low_and_flagged_works"):  # the works themselves, cited as primary studies
                m.add("register-low-and-flagged-studies",
                      "\\study{" + ",".join(r["low_and_flagged_works"]) + "}")
    else:
        m.missing("results/venue-risk.json")

    c = load("sources.json")
    if c:
        m.source("results/sources.json (scripts/compare_sources.py)")
        m.add("s2-harvest-date", date(c["harvest"]))
        m.add("s2-citing", num(c["s2_citing"]))
        m.add("s2-in-openalex", num(c["in_openalex"]))
        m.add("s2-new", num(c["not_in_openalex"]))
        for k in "ABC":
            m.add(f"s2-new-{k.lower()}", num(c["not_in_openalex_by_stratum"][k]))
        m.add("s2-new-ab", num(c["not_in_openalex_by_stratum"]["A"] + c["not_in_openalex_by_stratum"]["B"]))
        m.add("s2-contexts-pct", pct(c["with_contexts"], c["citation_records"], 0))
        if s:
            m.add("openalex-not-in-s2", num(s["candidates"] - c["in_openalex"]))
    else:
        m.missing("results/sources.json")

    d = load("stratum-d.json")
    if d:
        m.source("results/stratum-d.json (scripts/stratum_d.py)")
        m.add("fulltext-harvest-date", date(d["harvest"]))
        m.add("fulltext-queries", num(d["queries"]))
        m.add("fulltext-found", num(d["found"]))
        m.add("fulltext-in-corpus", num(d["in_corpus"]))
        for k, n_k in d["in_corpus_by_stratum"].items():
            m.add(f"fulltext-recall-{k.lower()}-pct", pct(n_k, d["corpus_by_stratum"][k]))
        m.add("fulltext-s2-only", num(d["s2_only"]))
        m.add("stratum-d", num(d["stratum_d"]))
        for k in ("strong", "weak", "early"):
            m.add(f"stratum-d-{k}", num(d["signal"][k]))
            x = d["semweb_term"][k]
            m.add(f"stratum-d-{k}-semweb-pct", pct(x["with"], x["with"] + x["without"], 0))
    else:
        m.missing("results/stratum-d.json")

    t = load("detection.json")
    manifests = sorted(ROOT.glob("raw/*-s2orc-scan-manifest.json"))
    if manifests:
        m.source("raw/*-s2orc-scan-manifest.json (scripts/scan_s2orc.py)")
        scanned, total, release = set(), None, None
        for p in manifests:
            mf = json.loads(p.read_text(encoding="utf-8"))
            scanned.update(e["file"] for e in mf.get("shards", []))
            total, release = mf["shards_in_release"], mf["release"]
        m.add("s2orc-release", date(release))
        m.add("s2orc-shards", num(total))
        m.add("s2orc-shards-scanned", num(len(scanned)))
    if t:
        m.source("results/detection.json (scripts/build_items.py)")
        m.add("s2orc-full-texts", num(t["full_texts"]))
        m.add("s2orc-naming", num(t["with_occurrences"]))
        m.add("s2orc-naming-pct", pct(t["with_occurrences"], t["full_texts"], 0))
        m.add("s2orc-with-terms", num(t["with_terms"]))
        m.add("s2orc-not-naming", num(t["full_texts"] - t["with_occurrences"]))
        ab = [x for k, x in t["by_stratum"].items() if k in ("A", "B")]
        m.add("s2orc-ab-full-texts", num(sum(x["full_texts"] for x in ab)))
        m.add("s2orc-ab-naming", num(sum(x["naming"] for x in ab)))
        m.add("s2orc-ab-not-naming", num(sum(x["full_texts"] - x["naming"] for x in ab)))
        m.add("s2orc-ab-with-terms", num(sum(x["with_terms"] for x in ab)))
        for k, x in t["by_stratum"].items():
            m.add(f"s2orc-{k.lower()}-full-texts", num(x["full_texts"]))
            m.add(f"s2orc-{k.lower()}-naming", num(x["naming"]))
            m.add(f"s2orc-{k.lower()}-naming-pct", pct(x["naming"], x["full_texts"], 0))
            m.add(f"s2orc-{k.lower()}-with-terms", num(x["with_terms"]))
            if s and k in s["strata"]:
                m.add(f"s2orc-{k.lower()}-coverage-pct", pct(x["full_texts"], s["strata"][k]["works"], 0))
        for what in ("body", "passage"):
            q = t[f"{what}_words"]
            if q:
                for k in ("q1", "median", "q3", "mean"):
                    if k in q:
                        m.add(f"s2orc-{what}-{k}", num(q[k]))
        if t["body_words"] and t["passage_words"]:
            m.add("s2orc-reading-ratio", num(t["body_words"]["mean"] / t["passage_words"]["mean"]))
        for k, x in t.get("to_retrieve", {}).items():
            for what in ("s2orc", "open_access", "oa_pdf_text", "closed", "no_doi"):
                if what in x:
                    m.add(f"retrieve-{k.lower()}-{what.replace('_', '-')}", num(x[what]))
        oa = t.get("oa_pdf") or {}
        if oa.get("works"):
            m.add("oa-full-texts", num(oa["works"]))
            ab_ = [x for k, x in oa["by_stratum"].items() if k in ("A", "B")]
            m.add("oa-ab-full-texts", num(sum(x["full_texts"] for x in ab_)))
            m.add("oa-ab-naming", num(sum(x["naming"] for x in ab_)))
            m.add("oa-ab-with-terms", num(sum(x["with_terms"] for x in ab_)))
            m.add("oa-refs-cut", num(oa["refs_cut"]))
            m.add("oa-naming", num(sum(x["naming"] for x in oa["by_stratum"].values())))
            m.add("oa-with-terms", num(sum(x["with_terms"] for x in oa["by_stratum"].values())))
            for k, x in oa["by_stratum"].items():
                m.add(f"oa-{k.lower()}-full-texts", num(x["full_texts"]))
                m.add(f"oa-{k.lower()}-naming", num(x["naming"]))
                m.add(f"oa-{k.lower()}-naming-pct", pct(x["naming"], x["full_texts"], 0))
                m.add(f"oa-{k.lower()}-with-terms", num(x["with_terms"]))
            for what in ("body", "passage"):
                q = oa.get(f"{what}_words") or {}
                if q:
                    m.add(f"oa-{what}-median", num(q["median"]))
                    m.add(f"oa-{what}-mean", num(q["mean"]))
            for sg, x in (oa.get("stratum_d_by_signal") or {}).items():
                for k, v in x.items():
                    m.add(f"oa-d-{sg}-{k.replace(' ', '-')}", num(v))
            if oa.get("cut_at"):
                m.add("oa-cut-at-median-pct", pct(oa["cut_at"]["median"], 1, 0))
                m.add("oa-cut-before-half", num(oa["cut_before_half"]))
        m.add("s2orc-d-named", num(t["stratum_d_named"]))
        m.add("s2orc-d-new", num(t["stratum_d_new"]))
        m.add("s2orc-d-new-with-terms", num(t["stratum_d_new_with_terms"]))
    else:
        m.missing("results/detection.json")

    r = load("recommendations.json")
    if r:
        m.source("results/recommendations.json (scripts/recommend_script.py): recommendations, not decisions")
        eng = r["by_stratum"].get("engagement", {})
        for code in ("E0", "E1"):
            m.add(f"rec-{code.lower()}", num(sum(x.get(code, 0) for x in eng.values())))
            for k, x in eng.items():
                m.add(f"rec-{code.lower()}-{k.lower()}", num(x.get(code, 0)))
        ver = r["by_stratum"].get("version_used", {})
        for v_ in ("ssn-xg", "sosa-ssn-2017", "ssn-2023", "mixed", "unknown"):
            m.add(f"rec-version-{v_}", num(sum(x.get(v_, 0) for x in ver.values())))
    else:
        m.missing("results/recommendations.json")

    budget_toml = ROOT / "protocol/budget.toml"
    if budget_toml.exists():
        import tomllib
        cfg = tomllib.loads(budget_toml.read_text(encoding="utf-8"))["budget"]
        m.source("protocol/budget.toml (parameters of the protocol)")
        if "calibration_sample" in cfg:
            m.add("calibration-sample", num(cfg["calibration_sample"]))
        m.add("second-reader-pct", pct(cfg.get("second_reader_share", 0), 1, 0))

    b = load("reading-budget.json")
    if b:
        m.source("results/reading-budget.json (scripts/reading_budget.py)")
        m.add("budget-hours", num(b["hours"]))
        m.add("budget-reading-hours", num(b["reading_hours"]))
        m.add("budget-reading-pct", pct(b["reading_share"], 1, 0))
        for k in ("low", "mid", "high"):
            m.add(f"budget-wpm-{k}", num(b["wpm"][k]))
        m.add("budget-words-mid", num(b["readable_words"]["mid"]))
        m.add("budget-ta-words", num(b["title_abstract_words"]))
        m.add("budget-ta-hours-mid", num(b["title_abstract_hours"]["mid"]))
        m.add("budget-full-text-words", num(b["full_text_words"]))
        m.add("budget-passage-words", num(b["passage_words"]))
        m.add("budget-full-texts-mid", num(b["full_texts_fit"]["mid"]))
        m.add("budget-passage-works-mid", num(b["works_by_passages_fit"]["mid"]))
        m.add("budget-passage-works-after-ta-mid", num(b["works_by_passages_fit_after_ta"]["mid"]))
        for k, v in b["per_record_minutes"].items():
            m.add(f"budget-minutes-{k.replace('_', '-')}", f"{v:g}")
    else:
        m.missing("results/reading-budget.json")

    terms = RESULTS / "terms.csv"
    if terms.exists():
        m.source("results/terms.csv (scripts/term_inventory.py)")
        with open(terms, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        by_version = {}
        for r in rows:
            by_version.setdefault(r["version"], []).append(r)
        short = {"http://www.w3.org/ns/sosa/": "sosa", "http://www.w3.org/ns/ssn/": "ssn",
                 "http://www.w3.org/ns/ssn/systems/": "system",
                 "http://purl.oclc.org/NET/ssnx/ssn#": "ssnx"}
        label = {"sosa-ssn-2017": "2017", "ssn-2023": "2023", "ssn-xg": "xg"}
        for version, rs in by_version.items():
            v_ = label.get(version, version)
            m.add(f"terms-{v_}", num(len(rs)))
            for ns in sorted({r["namespace"] for r in rs}):
                sub = [r for r in rs if r["namespace"] == ns]
                m.add(f"terms-{v_}-{short.get(ns, ns)}", num(len(sub)))
                m.add(f"terms-{v_}-{short.get(ns, ns)}-deprecated", num(sum(1 for r in sub if r["deprecated"])))
            if version == "ssn-2023":
                for file in sorted({r["file"] for r in rs}):
                    stem = file.rsplit("/", 1)[-1].removesuffix(".ttl")
                    m.add(f"terms-2023-file-{stem}", num(sum(1 for r in rs if r["file"] == file)))
        t17 = {r["term"] for r in by_version.get("sosa-ssn-2017", [])}
        t23 = {r["term"] for r in by_version.get("ssn-2023", [])}
        for file in sorted({r["file"] for r in by_version.get("ssn-2023", [])}):
            stem = file.rsplit("/", 1)[-1].removesuffix(".ttl")
            m.add(f"terms-2023-file-{stem}-new", num(sum(1 for r in by_version["ssn-2023"]
                                                          if r["file"] == file and r["term"] not in t17)))
        local = lambda t: t.rstrip("/#").rsplit("/", 1)[-1].rsplit("#", 1)[-1]
        names17 = {local(t) for t in t17}
        moved = {t for t in t23 - t17 if local(t) in names17}
        m.add("terms-moved", num(len(moved)))
        m.add("terms-brand-new", num(len(t23 - t17 - moved)))
        m.add("terms-kept", num(len(t17 & t23)))
        ns_of = {r["term"]: r["namespace"] for r in by_version.get("sosa-ssn-2017", [])}
        for ns, short_ns in short.items():
            kept_ns = {t for t in t17 & t23 if ns_of[t] == ns}
            dropped_ns = {t for t in t17 - t23 if ns_of[t] == ns}
            if kept_ns or dropped_ns:
                m.add(f"terms-kept-{short_ns}", num(len(kept_ns)))
                m.add(f"terms-dropped-{short_ns}", num(len(dropped_ns)))
        m.add("terms-dropped", num(len(t17 - t23)))
        m.add("terms-new", num(len(t23 - t17)))
        terms_md = (RESULTS / "terms.md").read_text(encoding="utf-8").split("\n", 3)[2]
        m.add("terms-revisions", tex_escape(terms_md.split(". Computed")[0].replace("`", "")))
    else:
        m.missing("results/terms.csv")

    u = load("usage-gaps.json")
    if u:
        m.source("results/usage-gaps.json (scripts/usage_gaps.py)")
        m.add("usage-revision", tex_escape(u["revision"]))
        m.add("usage-datasets", num(u["datasets_defined"]))
        m.add("usage-rows", num(u["rows"]))
        m.add("usage-rows-new", num(u["rows_new"]))
        m.add("usage-rows-under-two", num(u["rows_under_two"]))
        m.add("usage-rows-none", num(u["rows_none"]))
        m.add("usage-rows-one", num(u["rows_one"]))
        if "terms_no_row" in u:
            m.add("usage-terms-no-row", num(u["terms_no_row"]))
            for k, n_k in u["terms_no_row_by_file"].items():
                m.add(f"usage-terms-no-row-{k.removesuffix('.ttl')}", num(n_k))
    else:
        m.missing("results/usage-gaps.json")

    e = load("edition.json")
    if e:
        m.source("results/edition.json (scripts/edition_inventory.py)")
        for k, v in e["macros"].items():
            m.add(f"edition-{k}", tex_escape(v) if isinstance(v, str) else num(v))
    else:
        m.missing("results/edition.json")

    ul = load("usage-leads.json")
    if ul:
        m.source("results/usage-leads.json (scripts/usage_leads.py): leads, not evidence")
        m.add("leads-targets", num(ul["targets"]))
        m.add("leads-with", num(ul["with_leads"]))
    else:
        m.missing("results/usage-leads.json")

    du = load("duplicates.json")
    if du:
        m.source("results/duplicates.json (scripts/dedupe.py): a proposal, not applied")
        m.add("dup-clusters", num(du["clusters"]))
        m.add("dup-linked", num(du["linked"]))
        m.add("dup-after", num(du["after"]))
    else:
        m.missing("results/duplicates.json")

    runs = [json.loads(x.read_text(encoding="utf-8")) | {"_file": x.name}
            for x in sorted(ROOT.glob("raw/*-oa-fulltext-manifest.json"))]
    runs = [r for r in runs if r.get("complete")]
    for pass_, pop, prefix, keys in (
            ("locations", "ab", "oaharvest", ("text", "failed", "no PDF URL", "pdf without text")),
            ("locations", "d", "oad", ("text", "failed", "no PDF URL", "pdf without text")),
            ("landing pages", "ab", "oalanding", ("text", "failed", "no citation_pdf_url", "pdf without text"))):
        sel = [r for r in runs if r.get("pass", "locations") == pass_ and r.get("population", "ab") == pop]
        if sel:
            mf = sel[-1]
            m.source(f"raw/{mf['_file']} ({pass_})")
            m.add(f"{prefix}-pool", num(mf["pool"]))
            for k in keys:
                m.add(f"{prefix}-{k.replace(' ', '-').replace('_', '-').lower()}", num(mf["outcomes"].get(k, 0)))

    o = load("oa-pilot.json")
    if o:
        m.source("results/oa-pilot.json (scripts/pilot_oa_fulltext.py)")
        m.add("oapilot-pool", num(o["pool"]))
        m.add("oapilot-sample", num(o["sample"]))
        m.add("oapilot-pdf", num(o["outcomes"].get("pdf", 0)))
        m.add("oapilot-no-url", num(o["outcomes"].get("no PDF URL", 0)))
        m.add("oapilot-failed", num(o["outcomes"].get("error", 0) + o["outcomes"].get("not a PDF", 0)
                                    + o["outcomes"].get("too large", 0)))
        m.add("oapilot-refs-cut", num(o["refs_cut"]))
        m.add("oapilot-naming", num(o["naming"]))
    else:
        m.missing("results/oa-pilot.json")

    gi = load("edition-issues.json")
    if gi:
        m.source("results/edition-issues.json (scripts/harvest_gh_issues.py)")
        m.add("issues-date", date(gi["stamp"]))
        for key in ("issues", "issues_open", "issues_closed", "pulls", "pulls_merged", "authors"):
            m.add("gh-" + key.replace("_", "-"), num(gi[key]))
        m.add("gh-first-year", gi["first"][:4])
        since23 = {y: v for y, v in gi["by_year"].items() if y >= "2023"}
        m.add("gh-issues-since-2023", num(sum(v["issues"] for v in since23.values())))
        m.add("gh-issues-before-2023", num(sum(v["issues"] for y, v in gi["by_year"].items() if y < "2023")))
        for i, (lab, n_) in enumerate(gi["labels"][:5], 1):
            m.add(f"gh-label-{i}-name", tex_escape(lab))
            m.add(f"gh-label-{i}", num(n_))
    else:
        m.missing("results/edition-issues.json")

    k = load("edition-checks.json")
    if k:
        m.source("results/edition-checks.json (scripts/harvest_ci_checks.py)")
        m.add("check-run-date", date(k["run_created"]))
        m.add("check-sha", k["head_sha"])
        for key, v in k["figures"].items():
            m.add(f"check-{key}", num(v))
    else:
        m.missing("results/edition-checks.json")
    for f in sorted(RESULTS.glob("edition-checks-*.json")):  # earlier runs, by commit
        e2 = json.loads(f.read_text(encoding="utf-8"))
        m.source(f"results/{f.name} (scripts/harvest_ci_checks.py --run)")
        sha = e2["head_sha"]
        m.add(f"check-{sha}-run-date", date(e2["run_created"]))
        for key in ("definitions-differing", "definitions-matching"):
            if key in e2["figures"]:
                m.add(f"check-{sha}-{key}", num(e2["figures"][key]))

    mc = load("model-comparison.json")
    if mc:
        # the ladder of models (pilotage review/105): agreement between models, not accuracy
        m.source("results/model-comparison.json (scripts/model_code.py compare)")
        for name, v in mc["models"].items():
            m.add(f"ladder-{name}-works", num(v["works"]))
        for r in mc["pairs"]:
            k = f"ladder-{r['pair']}"
            m.add(f"{k}-works", num(r["works"]))
            for q, v in r["questions"].items():
                qk = q.replace("_", "-")
                if v.get("kappa") is not None:
                    m.add(f"{k}-{qk}-kappa", f"{v['kappa']:.2f}")
                if v.get("kappa_ci"):
                    m.add(f"{k}-{qk}-kappa-ci", f"{v['kappa_ci'][0]:.2f}--{v['kappa_ci'][1]:.2f}")
                if v.get("agreement") is not None and v["n"]:
                    m.add(f"{k}-{qk}-agree-pct", pct(v["agreement"], 1, 0))
                if v.get("jaccard") is not None:
                    m.add(f"{k}-{qk}-jaccard", f"{v['jaccard']:.2f}")
            if r.get("use_kappa") is not None:
                m.add(f"{k}-use-kappa", f"{r['use_kappa']:.2f}")
            if r.get("use_kappa_ci"):
                m.add(f"{k}-use-kappa-ci", f"{r['use_kappa_ci'][0]:.2f}--{r['use_kappa_ci'][1]:.2f}")
            m.add(f"{k}-use-n", num(r["use_missed"]["n"]))
            m.add(f"{k}-use-missed", num(r["use_missed"]["missed"]))
            m.add(f"{k}-use-missed-pct", pct(r["use_missed"]["missed"], r["use_missed"]["n"], 0))
            m.add(f"{k}-within-one-pct", pct(r["within_one"], 1, 0))

    h = load("hypothetical-findings.json")
    if h:
        # HYPOTHETICAL: the model's codes taken as the readers' decisions (Maxime, 2026-11-13);
        # printed only inside the light blue \hypothetical{} boxes of common/draft.tex
        m.source("results/hypothetical-findings.json (scripts/hypothetical_findings.py): HYPOTHETICAL, not results")
        for key, value in h["macros"].items():
            m.add(f"hyp-{key}", value)

    u = load("usage-patterns.json")
    if u and u.get("macros"):
        # what the full texts show, read by script (names, namespaces, simple results)
        m.source("results/usage-patterns.json (scripts/usage_patterns.py)")
        for key, value in u["macros"].items():
            m.add(f"use-{key}", value)

    pc = load("pattern-coding.json")
    if pc and pc.get("macros"):
        # HYPOTHETICAL: the modelling patterns coded from excerpts by Claude agents, unchecked
        m.source("results/pattern-coding.json (scripts/pattern_coding.py): HYPOTHETICAL, agent codes")
        for key, value in pc["macros"].items():
            m.add(f"hyp-pat-{key}", value)
        # agreement of the second, blind coder on its sample (Cohen's kappa per question)
        ag = pc.get("agreement") or {}
        if ag:
            kappas = sorted(v["kappa"] for v in ag.values())
            m.add("hyp-pat-agree-n", num(next(iter(ag.values()))["n"]))
            m.add("hyp-pat-agree-questions", num(len(ag)))
            m.add("hyp-pat-agree-kappa-min", f"{kappas[0]:.2f}")
            m.add("hyp-pat-agree-kappa-max", f"{kappas[-1]:.2f}")
            m.add("hyp-pat-agree-kappa-median", f"{kappas[len(kappas) // 2]:.2f}")
            for q, v in ag.items():
                m.add(f"hyp-pat-agree-{q.replace('_', '-')}-kappa", f"{v['kappa']:.2f}")
        if pc.get("quotes"):
            m.add("hyp-pat-quotes", num(pc["quotes"]))

    ow = load("observatory-watch.json")
    if ow:
        m.source("results/observatory-watch.json (scripts/observatory_watch.py)")
        m.add("watch-new", num(ow["new"]))
        m.add("watch-known", num(ow["known"]))
        m.add("watch-date", date(ow["stamp"]))

    kg = load("kg.json")
    if kg:
        # the knowledge graph of the observatory (scripts/build_kg.py)
        m.source("results/kg.json (scripts/build_kg.py)")
        for key, value in kg["macros"].items():
            m.add(f"kg-{key}", value)

    t = load("text-seeds.json")
    if t:
        m.source("results/text-seeds.json (scripts/text_seeds.py)")
        m.add("textseed-held", num(t["held_texts"]))
        for key, v in t["seeds"].items():
            m.add(f"textseed-{key}-held", num(v["held_citing"]))
            m.add(f"textseed-{key}-refs", num(v["in_references"]))
            m.add(f"textseed-{key}-search", num(v["search_found"]))
            m.add(f"textseed-{key}-new", num(len(v["search_new"])))

    head = ["% Figures of the papers, generated by slr/scripts/article_macros.py: do not edit.",
            "% Use: \\slr{key}. An unknown key prints as ??key?? and warns.",
            "\\providecommand{\\slrdef}[2]{\\expandafter\\def\\csname slr@#1\\endcsname{#2}}",
            "\\providecommand{\\slr}[1]{\\ifcsname slr@#1\\endcsname\\csname slr@#1\\endcsname"
            "\\else\\textbf{??#1??}\\GenericWarning{}{SLR figure #1 undefined}\\fi}"]
    (RESULTS / "macros.tex").write_text("\n".join(head + m.lines) + "\n", encoding="utf-8")
    print(f"results/macros.tex: {len(m.keys)} figures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
