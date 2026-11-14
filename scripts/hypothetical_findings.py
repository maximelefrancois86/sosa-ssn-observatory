#!/usr/bin/env python3
"""HYPOTHETICAL answers to RQ2-RQ9: the models' codes taken as if they were the readers'.

    python3 -I scripts/hypothetical_findings.py   # results/hypothetical-findings.json and .md,
                                                  # results/figures/hyp-*.csv

Maxime, 2026-11-13: to see what the findings would say if the readers agreed perfectly with
the model (record review/105). Nothing here is a result of the review: the codes are the
model's recommendations (screening/recommendations.jsonl, `source` = model), not decisions,
and no reader has checked them. The papers print these figures only inside the light blue
`\\hypothetical{}` boxes of common/draft.tex, under keys that start with `hyp-`.

For each work, the codes of the strongest model that coded it from its current text: Claude
Opus 5.5, then Claude Sonnet 5.5, then the primary model (Maxime, 2026-11-13; the ladder of
pilotage review/105). The population: the works of strata A, B and D that a model coded,
less those whose text that model took for another work or a whole volume
(`text_is_the_work` = no).
RQ2 counts every such work, by basis (full text or abstract); RQ3 to RQ9 count the works
coded from their full text only (protocol section 4: the works coded from an abstract are
reported apart). Standard library only.
"""
import collections
import csv
import gzip
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from article_macros import num, pct, tex_escape  # noqa: E402
from strata import ROOT, load_corpus, load_seeds  # noqa: E402

RESULTS = ROOT / "results"
LEVELS = ["E0", "E1", "E2", "E3", "E4", "E5"]
USE = {"E3", "E4", "E5"}
PREFIX = {"sosa": "http://www.w3.org/ns/sosa/", "ssn": "http://www.w3.org/ns/ssn/",
          "ssn-system": "http://www.w3.org/ns/ssn/systems/", "ssn-systems": "http://www.w3.org/ns/ssn/systems/",
          "ssnsystem": "http://www.w3.org/ns/ssn/systems/", "sys": "http://www.w3.org/ns/ssn/systems/"}
XG = "http://purl.oclc.org/NET/ssnx/ssn#"
# companion vocabularies: one name, the patterns that recognise it in the model's free text
COMPANIONS = [
    ("OWL-Time", r"owl[- ]?time|\btime ontology|\btime:|w3ctime|\bowl time"),
    ("QUDT", r"\bqudt"),
    ("OM", r"\bom\b(?! ?2)|ontology of units of measure|\bom-2|\bom 2|\bom2\b"),
    ("GeoSPARQL", r"geosparql"),
    ("WGS84", r"wgs ?84|geo:lat|basic geo"),
    ("PROV-O", r"\bprov\b|prov-o|provenance ontology"),
    ("SAREF", r"\bsaref"),
    ("DUL", r"\bdul\b|dolce"),
    ("IoT-Lite", r"iot[- ]?lite"),
    ("BOT", r"\bbot\b|building topology"),
    ("Brick", r"\bbrick\b"),
    ("WoT TD", r"thing description|\bwot\b|\btd\b"),
    ("schema.org", r"schema\.org"),
    ("SKOS", r"\bskos\b"),
    ("Dublin Core", r"dublin core|\bdcterms|\bdc:|\bdct\b"),
    ("FOAF", r"\bfoaf\b"),
    ("SensorML / O&M", r"sensorml|observations? (and|&) measurements|\bo&m\b|\bom-lite"),
    ("SOSA/SSN alignments", r"\bssnx\b|ssn-xg"),
    ("SEAS", r"\bseas\b"),
    ("ifcOWL", r"ifcowl|\bifc\b"),
    ("SWEET", r"\bsweet\b"),
    ("FIESTA-IoT", r"fiesta"),
    ("oneM2M", r"onem2m"),
    ("SHACL", r"\bshacl\b"),
]
# themes of the gaps, recognised by keywords in the model's free text (a stand-in for the
# thematic synthesis of protocol section 7, which a reader does)
THEMES = [
    ("domain concepts missing", r"domain[- ]specific|lacks? domain|domain concepts|domain knowledge|not cover"),
    ("time and dynamics", r"\btime\b|temporal|dynamic|state|event"),
    ("space and location", r"spatial|location|geo|position"),
    ("units, quantities and values", r"\bunits?\b|quantit|measurement value|numeric"),
    ("uncertainty and quality", r"uncertain|quality|accuracy|precision|confidence|trust"),
    ("provenance", r"provenance|lineage"),
    ("actuation and control", r"actuat|control|command"),
    ("streams and real time", r"stream|real[- ]time|latency"),
    ("scalability and performance", r"scal|performance|large[- ]scale|volume|efficien|overhead|reasoning cost"),
    ("complexity and usability", r"complex|heavy|usabil|learning curve|verbose|difficult"),
    ("tooling and validation", r"tool|validat|shacl|editor|automat"),
    ("interoperability and alignment", r"interoperab|align|mapping|heterogen|integrat"),
    ("privacy and security", r"privacy|secur"),
]


def model_answers():
    """{item: {question: record}} of the model's recommendations."""
    out = collections.defaultdict(dict)
    with open(ROOT / "screening/recommendations.jsonl", encoding="utf-8") as f:
        for r in map(json.loads, f):
            if r.get("source") == "model":
                out[r["item"]][r["question"]] = r
    return out


def ladder_answers():
    """{item: {question: record}}: for each work, the answers of the strongest model that coded
    it from its current text (Opus 5.5, then Sonnet 5.5, which also coded the works that have
    an abstract only; the recommendations of model_code.py ingest); and the works whose text that
    model took for another work or a whole volume. Maxime, 2026-11-13: the hypothetical
    findings take the strongest model for each work."""
    import model_code as mc
    answers = model_answers()
    coding = json.loads((RESULTS / "model-coding.json").read_text(encoding="utf-8"))
    not_work = {i for i, v in coding["not_the_work"] if v == "no"}
    cfg = mc.config()
    questions = mc.codebook()
    bodies = mc.load_bodies()
    source = {i: next(iter(a.values()))["version"].split(",")[0] for i, a in answers.items() if a}
    for name in ("sonnet", "opus"):  # the stronger last: it wins
        mid = cfg["checks"][name]["model"]["id"]
        for item, a in mc.answers_of(mid, questions).items():
            if item not in bodies or a["_body"] != mc.sha(bodies[item]):
                continue  # coded from a text since replaced
            e = a["engagement"]["value"]
            rec = {}
            for q in questions:
                v = a[q["id"]]["value"]
                if v == mc.NOT_ASKED or not mc.visible(q, e):
                    continue
                rec[q["id"]] = {"item": item, "source": "model", "version": mid, "question": q["id"],
                                "value": mc.as_text(q, v), "basis": "full text",
                                "uncertain": q["id"] in a["uncertain"],
                                **({"entries": v} if q["kind"] == "entries" else {})}
            answers[item] = rec
            source[item] = mid
            (not_work.add if a["text_is_the_work"] == "no" else not_work.discard)(item)
    return answers, not_work, source


def items():
    out = {}
    with open(ROOT / "screening/items.jsonl", encoding="utf-8") as f:
        for d in map(json.loads, f):
            out[d["item"]] = d
    return out


def work_meta():
    """(by openalex id, by doi) of the candidates, for the year and the seeds cited."""
    by_id, by_doi = {}, {}
    for w in load_corpus():
        by_id[w["openalex"]] = w
        if w.get("doi"):
            by_doi[w["doi"].lower()] = w
    p = ROOT / "corpus/stratum-d-candidates.jsonl.gz"
    if p.exists():
        with gzip.open(p, "rt", encoding="utf-8") as f:
            for w in map(json.loads, f):
                by_id.setdefault(w["openalex"], w)
                if w.get("doi"):
                    by_doi.setdefault(w["doi"].lower(), w)
    return by_id, by_doi


def term_iri(t, version, declared=frozenset()):
    """The IRI of a prefixed name: `ssn:` is the SSN-XG namespace for a work that uses SSN-XG,
    or for a name that only SSN-XG declares (ssn:Observation, ssn:SensingDevice…)."""
    m = re.match(r"\s*([A-Za-z-]+):([A-Za-z_][\w-]*)\s*$", t or "")
    if not m:
        return None
    p, local = m.group(1).lower(), m.group(2)
    if p in ("ssnx", "ssn-xg"):
        return XG + local
    if p == "ssn" and (version == "ssn-xg" or (PREFIX["ssn"] + local not in declared and XG + local in declared)):
        return XG + local
    return PREFIX[p] + local if p in PREFIX else None


def main():
    answers, not_work, source = ladder_answers()
    its = items()
    by_id, by_doi = work_meta()
    role = {s["key"]: s["role"] for s in load_seeds()}

    def meta(item):
        it = its.get(item, {})
        if item.startswith("openalex:") and item[9:] in by_id:
            return by_id[item[9:]]
        return by_doi.get((it.get("doi") or "").lower(), {})

    def stratum(item):
        if item in its:
            return its[item]["stratum"]
        w = by_id.get(item[9:], {}) if item.startswith("openalex:") else {}
        from strata import stratum as st
        return st(w, role) if w else "?"

    M = {}
    pop = [i for i, a in answers.items() if "engagement" in a and i not in not_work and stratum(i) in "ABD"]
    basis = {i: answers[i]["engagement"].get("basis", "full text") for i in pop}
    full = [i for i in pop if basis[i] != "abstract"]
    eng = {i: answers[i]["engagement"]["value"] for i in pop}
    M["coded"] = num(len(pop))
    by_model = collections.Counter(source[i] for i in pop)
    for name, mid in (("opus", "claude-opus-5-5"), ("sonnet", "claude-sonnet-5-5")):
        M[f"from-{name}"] = num(by_model.get(mid, 0))
    M["excluded-not-work"] = num(len(not_work))
    M["full"] = num(len(full))
    M["abstract"] = num(len(pop) - len(full))

    # RQ2: engagement by stratum and basis
    table = {}
    for st in "ABD":
        for b, label in (("full", "full"), ("abstract", "abs")):
            group = [i for i in pop if stratum(i) == st and (basis[i] == "abstract") == (b == "abstract")]
            c = collections.Counter(eng[i] for i in group)
            table[f"{st}-{label}"] = {**{lv: c.get(lv, 0) for lv in LEVELS + ["unknown"]}, "n": len(group)}
            for lv in LEVELS + ["unknown"]:
                M[f"eng-{st}-{label}-{lv}"] = num(c.get(lv, 0))
            M[f"eng-{st}-{label}-n"] = num(len(group))
    ab_full = [i for i in full if stratum(i) in "AB"]
    c = collections.Counter(eng[i] for i in ab_full)
    for lv in LEVELS:
        M[f"eng-ab-{lv}"] = num(c.get(lv, 0))
        M[f"eng-ab-{lv}-pct"] = pct(c.get(lv, 0), len(ab_full), 0)
    M["eng-ab-n"] = num(len(ab_full))
    use_ab = sum(c.get(lv, 0) for lv in USE)
    M["eng-ab-use"] = num(use_ab)
    M["eng-ab-use-pct"] = pct(use_ab, len(ab_full), 0)
    M["eng-ab-citations-per-use"] = f"{len(ab_full) / use_ab:.1f}" if use_ab else "--"
    low = c.get("E0", 0) + c.get("E1", 0)
    M["eng-ab-low"] = num(low)
    M["eng-ab-low-pct"] = pct(low, len(ab_full), 0)
    for st in "AB":
        g = [i for i in full if stratum(i) == st]
        u = sum(eng[i] in USE for i in g)
        M[f"eng-{st}-use-pct"] = pct(u, len(g), 0)
        M[f"eng-{st}-low-pct"] = pct(sum(eng[i] in ("E0", "E1") for i in g), len(g), 0)
    g = [i for i in full if stratum(i) == "D"]
    M["eng-D-use-pct"] = pct(sum(eng[i] in USE for i in g), len(g), 0)
    # by year, A and B from full text
    years = collections.defaultdict(collections.Counter)
    for i in ab_full:
        y = meta(i).get("year")
        if y:
            years[int(y)][eng[i]] += 1
    (RESULTS / "figures").mkdir(exist_ok=True)
    with open(RESULTS / "figures/hyp-engagement-by-year.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year"] + LEVELS)
        for y in sorted(years):
            if 2010 <= y <= 2025:
                w.writerow([y] + [years[y].get(lv, 0) for lv in LEVELS])
    early = [i for i in ab_full if (meta(i).get("year") or 0) and int(meta(i)["year"]) <= 2019]
    late = [i for i in ab_full if (meta(i).get("year") or 0) and int(meta(i)["year"]) >= 2022]
    M["use-pct-to-2019"] = pct(sum(eng[i] in USE for i in early), len(early), 0)
    M["use-pct-from-2022"] = pct(sum(eng[i] in USE for i in late), len(late), 0)
    # secondary studies
    sec = [i for i in full if answers[i].get("study_type", {}).get("value") == "secondary"]
    M["secondary"] = num(len(sec))
    cs = collections.Counter(eng[i] for i in sec)
    M["secondary-e2"] = num(cs.get("E2", 0))
    M["secondary-e2-pct"] = pct(cs.get("E2", 0), len(sec), 0)
    M["secondary-low-pct"] = pct(cs.get("E0", 0) + cs.get("E1", 0), len(sec), 0)
    unsure = sum(bool(answers[i]["engagement"].get("uncertain")) for i in full)
    M["eng-unsure"] = num(unsure)
    M["eng-unsure-pct"] = pct(unsure, len(full), 0)

    # the works that use SOSA/SSN, from the full text
    users = [i for i in full if eng[i] in USE]
    M["users"] = num(len(users))
    ver = {i: answers[i].get("version_used", {}).get("value", "unknown") for i in users}

    # RQ3: version cited x version used
    def cited(i):
        seeds = meta(i).get("seeds") or []
        roles = {role.get(s) for s in seeds}
        if not seeds:
            return "none"
        if roles <= {"lineage"}:
            return "lineage"
        return "both" if "lineage" in roles else "2017"
    versions = ["ssn-xg", "sosa-ssn-2017", "ssn-2023", "mixed", "unknown"]
    for cg in ("lineage", "both", "2017", "none"):
        g = [i for i in users if cited(i) == cg]
        cv = collections.Counter(ver[i] for i in g)
        for v in versions:
            M[f"ver-{cg}-{v}"] = num(cv.get(v, 0))
        M[f"ver-{cg}-n"] = num(len(g))
    cv = collections.Counter(ver[i] for i in users)
    for v in versions:
        M[f"ver-{v}"] = num(cv.get(v, 0))
        M[f"ver-{v}-pct"] = pct(cv.get(v, 0), len(users), 0)
    b2017 = [i for i in users if stratum(i) == "B" and ver[i] in ("sosa-ssn-2017", "ssn-2023", "mixed")]
    M["b-users"] = num(sum(stratum(i) == "B" for i in users))
    M["b-uses-2017"] = num(len(b2017))
    xg_late = [i for i in users if ver[i] == "ssn-xg" and int(meta(i).get("year") or 0) >= 2019]
    M["xg-from-2019"] = num(len(xg_late))

    # RQ4: modules and terms
    mods = collections.Counter()
    for i in users:
        for mval in answers[i].get("modules", {}).get("value") or []:
            mods[mval] += 1
    for mval in ["sosa-observation", "sosa-actuation", "sosa-sampling", "ssn", "ssn-system", "2023-execution",
                 "2023-collections", "2023-sample-relations", "2023-oms", "2023-systems", "alignments"]:
        M[f"mod-{mval}"] = num(mods.get(mval, 0))
        M[f"mod-{mval}-pct"] = pct(mods.get(mval, 0), len(users), 0)
    terms_csv = list(csv.DictReader(open(RESULTS / "terms.csv", encoding="utf-8")))
    declared = collections.defaultdict(set)
    for r in terms_csv:
        declared[r["version"]].add(r["term"])
    all_declared = set().union(*declared.values())
    new2023 = declared["ssn-2023"] - declared["sosa-ssn-2017"]
    used = collections.Counter()
    written = collections.Counter()
    undeclared = collections.Counter()
    for i in users:
        seen = set()
        for t in answers[i].get("terms", {}).get("value") or []:
            iri = term_iri(t, ver[i], all_declared)
            if not iri:
                continue
            if iri in all_declared:
                seen.add(iri)
            else:
                undeclared[t.strip()] += 1
        for iri in seen:
            used[iri] += 1
        written.update({(t.split(":")[0].lower()) for t in answers[i].get("terms", {}).get("value") or [] if ":" in t})
    with_terms = sum(bool(answers[i].get("terms", {}).get("value")) for i in users)
    M["users-with-terms"] = num(with_terms)
    M["users-with-terms-pct"] = pct(with_terms, len(users), 0)

    def short(iri):
        for p, ns in (("sosa", PREFIX["sosa"]), ("ssn-system", PREFIX["ssn-system"]), ("ssn", PREFIX["ssn"]), ("ssnx", XG)):
            if iri.startswith(ns):
                return f"{p}:{iri[len(ns):]}"
        return iri
    v17 = declared["sosa-ssn-2017"]
    used17 = [t for t in v17 if used.get(t)]
    M["terms-2017"] = num(len(v17))
    M["terms-2017-used"] = num(len(used17))
    M["terms-2017-used-pct"] = pct(len(used17), len(v17), 0)
    never = sorted(short(t) for t in v17 if not used.get(t))
    M["terms-2017-never"] = num(len(never))
    M["terms-2017-never-list"] = ", ".join(f"\\texttt{{{tex_escape(t)}}}" for t in never)
    top = [(t, n) for t, n in used.most_common() if t in v17 or t in declared["ssn-2023"]][:15]
    for k, (t, n) in enumerate(top, 1):
        M[f"term-{k}-name"] = f"\\texttt{{{tex_escape(short(t))}}}"
        M[f"term-{k}"] = num(n)
        M[f"term-{k}-pct"] = pct(n, len(users), 0)
    used_new = [(t, n) for t, n in used.most_common() if t in new2023]
    # a 2023 name is a use of the 2023 Edition only from the date it entered sosa:
    # (protocol/namespace-history.toml, results/namespace-history.json); before, the
    # sosa: name of a 2017 ssn: term is a namespace error, not an anticipation (Maxime,
    # 2026-11-14), and the terms of the Extensions to SSN were in sosa: from 2018
    import usage_patterns as upm
    hist = upm.history()
    pub_id, pub_doi = upm.publication_dates()
    ssn17 = {t[len(PREFIX["ssn"]):] for t in declared["sosa-ssn-2017"] if t.startswith(PREFIX["ssn"])}

    def entered(local):
        if local in ssn17:
            return hist["decision"]["all_terms_in_sosa"]
        return hist.get("new_terms", {}).get(local)

    def pubdate(i):
        m_ = meta(i)
        doi_ = (m_.get("doi") or its.get(i, {}).get("doi") or "").lower()
        return pub_id.get(m_.get("openalex") or "") or pub_doi.get(doi_) or (str(m_["year"]) if m_.get("year") else None)
    split = {"error": collections.Counter(), "extension": collections.Counter(), "edition": collections.Counter()}
    split_works = collections.defaultdict(set)
    for i in users:
        for t in {term_iri(x, ver[i], all_declared) for x in answers[i].get("terms", {}).get("value") or []}:
            if t not in new2023 or not t.startswith(PREFIX["sosa"]):
                continue
            local = t[len(PREFIX["sosa"]):]
            since, d = entered(local), pubdate(i)
            if local in hist["introduced_by_ssn_ext"]["terms"] and (not d or upm.when(d, "2023-09-21") == "before"):
                split["extension"][t] += 1
                split_works["extension"].add(i)
            elif since and d and upm.when(d, since) == "before":
                split["error"][t] += 1
                split_works["error"].add(i)
            else:
                split["edition"][t] += 1
                split_works["edition"].add(i)
    for k, c in split.items():
        M[f"terms-2023-{k}-works"] = num(len(split_works[k]))
        M[f"terms-2023-{k}-list"] = ", ".join(f"\\texttt{{{tex_escape(short(t))}}} ({n})" for t, n in c.most_common(10)) or "none"
    M["terms-2023-new"] = num(len(new2023))
    M["terms-2023-new-used"] = num(len(used_new))
    M["terms-2023-new-list"] = ", ".join(f"\\texttt{{{tex_escape(short(t))}}} ({n})" for t, n in used_new[:12]) or "none"
    xg_used = [t for t in declared["ssn-xg"] if used.get(t)]
    M["terms-xg"] = num(len(declared["ssn-xg"]))
    M["terms-xg-used"] = num(len(xg_used))
    M["terms-undeclared"] = num(len(undeclared))
    M["terms-undeclared-works"] = num(sum(undeclared.values()))
    M["terms-undeclared-top"] = ", ".join(f"\\texttt{{{tex_escape(t)}}}" for t, _ in undeclared.most_common(8))

    # RQ5a: extension points
    ext_users = [i for i in users if eng[i] in ("E4", "E5")]
    M["e45"] = num(len(ext_users))
    base = collections.Counter()
    how = collections.Counter()
    with_ext = 0
    for i in ext_users:
        entries = answers[i].get("extensions", {}).get("entries") or []
        if entries:
            with_ext += 1
        seen = set()
        for e in entries:
            how[e.get("how")] += 1
            for b in e.get("builds_on") or []:
                iri = term_iri(b, ver.get(i), all_declared)
                if iri:
                    seen.add(short(iri).replace("ssnx:", "ssn:"))
        base.update(seen)
    M["e45-with-ext"] = num(with_ext)
    M["e45-with-ext-pct"] = pct(with_ext, len(ext_users), 0)
    for k, (t, n) in enumerate(base.most_common(10), 1):
        M[f"ext-{k}-name"] = f"\\texttt{{{tex_escape(t)}}}"
        M[f"ext-{k}"] = num(n)
    tot = sum(how.values())
    for h in ("subClassOf", "subPropertyOf", "instanceOf", "equivalentTo", "alignment"):
        M[f"how-{h}"] = num(how.get(h, 0))
        M[f"how-{h}-pct"] = pct(how.get(h, 0), tot, 0)
    M["ext-entries"] = num(tot)

    # RQ5b: results and values
    rp = collections.Counter()
    vp = collections.Counter()
    known_rp = known_vp = 0
    for i in users:
        r = [x for x in answers[i].get("result_pattern", {}).get("value") or [] if x != "unknown"]
        if r:
            known_rp += 1
            rp.update(set(r))
        v = [x for x in answers[i].get("value_properties", {}).get("value") or []]
        if v:
            known_vp += 1
            vp.update(set(v))
    M["rp-known"] = num(known_rp)
    for x in ["simple-literal", "quantity-value", "custom-result-class", "structured", "by-reference",
              "time-series", "coverage", "nested", "none"]:
        M[f"rp-{x}"] = num(rp.get(x, 0))
        M[f"rp-{x}-pct"] = pct(rp.get(x, 0), known_rp, 0)
    M["vp-known"] = num(known_vp)
    for x in ["unit", "uncertainty", "quality", "time", "none"]:
        M[f"vp-{x}"] = num(vp.get(x, 0))
        M[f"vp-{x}-pct"] = pct(vp.get(x, 0), known_vp, 0)

    # RQ6: errors
    codes = collections.Counter()
    with_err = 0
    err_by_ver = collections.defaultdict(lambda: [0, 0])
    for i in users:
        entries = answers[i].get("errors", {}).get("entries") or []
        cs_ = {e.get("code") for e in entries if e.get("code")}
        codes.update(cs_)
        with_err += bool(cs_)
        err_by_ver[ver[i]][0] += bool(cs_)
        err_by_ver[ver[i]][1] += 1
    M["err-works"] = num(with_err)
    M["err-works-pct"] = pct(with_err, len(users), 0)
    for code in ["S1", "S2", "S3", "M1", "M2", "M3", "M4", "G1", "G2", "G3"]:
        M[f"err-{code}"] = num(codes.get(code, 0))
    for v in versions:
        e, n = err_by_ver.get(v, (0, 0))
        M[f"err-{v}-pct"] = pct(e, n, 0)

    # RQ7: domains and companions
    dom_pop = [i for i in full if eng[i] in ("E2", "E3", "E4", "E5")]
    doms = collections.Counter(answers[i].get("domain", {}).get("value") for i in dom_pop
                               if answers[i].get("domain", {}).get("value"))
    M["dom-n"] = num(sum(doms.values()))
    for k, (d, n) in enumerate(doms.most_common(12), 1):
        M[f"dom-{k}-name"] = tex_escape(d)
        M[f"dom-{k}"] = num(n)
        M[f"dom-{k}-pct"] = pct(n, sum(doms.values()), 0)
    dom_use = collections.Counter(answers[i].get("domain", {}).get("value") for i in users)
    for k, (d, n) in enumerate(doms.most_common(12), 1):
        M[f"dom-{k}-use"] = num(dom_use.get(d, 0))
    comp = collections.Counter()
    with_comp = 0
    for i in users:
        text = (answers[i].get("companions", {}).get("value") or "").lower()
        found = {name for name, pat in COMPANIONS if re.search(pat, text)}
        with_comp += bool(found)
        comp.update(found)
    M["comp-works"] = num(with_comp)
    M["comp-works-pct"] = pct(with_comp, len(users), 0)
    for k, (name, n) in enumerate(comp.most_common(12), 1):
        M[f"comp-{k}-name"] = tex_escape(name)
        M[f"comp-{k}"] = num(n)
        M[f"comp-{k}-pct"] = pct(n, len(users), 0)

    # RQ8: artefacts
    kinds = collections.Counter()
    hosts = collections.Counter()
    with_art = 0
    for i in users:
        entries = answers[i].get("artefacts", {}).get("entries") or []
        with_art += bool(entries)
        kinds.update({e.get("kind") for e in entries if e.get("kind")})
        for e in entries:
            m = re.match(r"\s*(?:https?://)?([^/\s]+)", e.get("url") or "")
            if m:
                h = m.group(1).lower()
                hosts["github.com" if "github" in h else "w3id.org" if "w3id" in h else "zenodo.org" if "zenodo" in h else "other"] += 1
    M["art-works"] = num(with_art)
    M["art-works-pct"] = pct(with_art, len(users), 0)
    for kd in ["ontology", "dataset", "alignment", "shacl-shapes", "jsonld-context", "json-schema", "sparql-queries",
               "mapping", "design-pattern", "software"]:
        M[f"art-{kd}"] = num(kinds.get(kd, 0))
    totals = sum(hosts.values())
    for h in ("github.com", "w3id.org", "zenodo.org", "other"):
        M[f"host-{h.split('.')[0]}"] = num(hosts.get(h, 0))
        M[f"host-{h.split('.')[0]}-pct"] = pct(hosts.get(h, 0), totals, 0)
    M["art-urls"] = num(totals)

    # RQ9: gaps, by keyword themes
    gap_pop = [i for i in full if eng[i] in ("E2", "E3", "E4", "E5")]
    gaps = {i: (answers[i].get("gaps", {}).get("value") or "").strip() for i in gap_pop}
    gaps = {i: g for i, g in gaps.items() if g and not re.match(r"^(none|no gaps?|not reported|n/?a)\b", g, re.I)}
    M["gap-works"] = num(len(gaps))
    M["gap-works-pct"] = pct(len(gaps), len(gap_pop), 0)
    about = {i for i, g in gaps.items() if re.search(r"sosa|ssn|semantic sensor", g, re.I)}
    M["gap-about-sosa"] = num(len(about))
    th = collections.Counter()
    for i in about:
        th.update({name for name, pat in THEMES if re.search(pat, gaps[i], re.I)})
    for k, (name, n) in enumerate(th.most_common(10), 1):
        M[f"theme-{k}-name"] = name
        M[f"theme-{k}"] = num(n)
    examples = sorted(about, key=lambda i: -len(gaps[i]))

    out = {"note": "HYPOTHETICAL: the model's codes taken as the readers' decisions; no reader checked them",
           "model": sorted({a["engagement"].get("version", "") for a in answers.values() if "engagement" in a}),
           "works_by_model": dict(collections.Counter(source[i] for i in pop)),
           "macros": M, "engagement": table,
           "companions": comp.most_common(), "extension_bases": base.most_common(30),
           "terms_used": [(short(t), n) for t, n in used.most_common()],
           "terms_undeclared": undeclared.most_common(40), "domains": doms.most_common(),
           "gap_themes": th.most_common(),
           "gaps_about_sosa": [{"item": i, "title": its.get(i, {}).get("title") or meta(i).get("title"), "gap": gaps[i]}
                               for i in examples]}
    (RESULTS / "hypothetical-findings.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                                                        encoding="utf-8")
    lines = ["# Hypothetical findings (model codes taken as readers' decisions)", "",
             "**Not results.** Computed by `scripts/hypothetical_findings.py` from the model's",
             "recommendations (record review/105) as if every reader agreed with the model. No reader has",
             "checked them. Model: " + ", ".join(out["model"]) + ".", "",
             "| key | value |", "|---|---|"]
    lines += [f"| `hyp-{k}` | {v} |" for k, v in M.items()]
    lines += ["", "## Gaps that name SOSA/SSN (model's summaries)", ""]
    lines += [f"- `{g['item']}` {g['title']}: {g['gap']}" for g in out["gaps_about_sosa"]]
    (RESULTS / "hypothetical-findings.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"results/hypothetical-findings.json: {len(M)} figures; {len(pop)} works, {len(full)} from the full text, "
          f"{len(users)} use SOSA/SSN (E3-E5)")


if __name__ == "__main__":
    main()
