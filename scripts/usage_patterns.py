#!/usr/bin/env python3
"""How the works write SOSA/SSN: names, namespaces and simple results, read by script.

    python3 -I scripts/usage_patterns.py      # results/usage-patterns.{md,json},
                                              # results/figures/simple-result-datatypes.csv

Reads the bodies of the full texts (screening/bodies.jsonl.gz, bibliography cut), the terms
of each version (results/terms.csv), the dates at which terms entered the `sosa:` namespace
(protocol/namespace-history.toml), and, for the population and the engagement, the codes of
the strongest model that coded each work (scripts/hypothetical_findings.py). Three
analyses, each a rule applied to the text, with the works it finds listed so that a
reader can check them:

1. **Prefixed names** (`sosa:System`, `ssn:Observation`…). Each name a work writes is
   classified against the terms of SSN-XG, the 2017 Recommendation and the 2023 Edition,
   knowing which namespaces the work declares (namespace IRIs and `@prefix`, `PREFIX` or
   `xmlns` bindings found in the text, spaces squeezed):
   - `ok-2017`, `ok-xg`, `ok-2023`: a name of that version, in its namespace;
   - `ns-ssn-term-as-sosa`: a 2017 `ssn:` term written `sosa:` (sosa:System). It is the
     2023 name of the term only from the date the Working Group decided that every term
     goes into `sosa:` (namespace-history.toml); a work published before writes a wrong
     namespace (error S1), it does not anticipate the 2023 Edition;
   - `ns-sosa-term-as-ssn`: a SOSA term written `ssn:` by a work that declares the 2017
     namespaces and not SSN-XG's (ssn:Observation for sosa:Observation: S1);
   - `ns-xg-term-as-sosa`: an SSN-XG term written `sosa:` (sosa:SensingDevice: S1 or S2);
   - `new-2023`: a term that only the 2023 Edition declares, used before or after the date
     it entered `sosa:` (before: S2, a term that did not exist yet);
   - `case`: a declared name with another case or a plural (sosa:observedproperty: S3);
   - `undeclared`: no version declares it (S2), e.g. `sosa:hasUnit`.
   Prose is not read: `SOSA: A lightweight ontology` is skipped (a space after the colon is
   accepted only before a declared name).
2. **Simple results**: each `hasSimpleResult` followed by a value in the text (Turtle,
   N-Triples, JSON-LD, RDF/XML, a rule or a figure caption) gives that value's form: a
   datatype (`xsd:double`, `cdt:ucum`, another custom datatype…), a plain string (with a
   unit inside it or not), a bare number or boolean (Turtle: xsd:integer, decimal,
   double, boolean), or a SPARQL variable (a query, no datatype shown). A work counts
   once per form it shows. Datatypes written anywhere in the work (`cdt:ucum` with another
   property, `qudt:numericValue "1"^^xsd:double`) are counted apart.
3. **Quantity values**: the structured results the text writes with QUDT, OM or schema.org
   terms, and the works that bind a unit some other way.

These are counts of what the text **shows**, from PDF text with broken lines: a work that
uses cdt:ucum without printing it is not counted, and a listing garbled by the extraction
may be missed. They are not decisions of the readers. Standard library only.
"""
import collections
import csv
import gzip
import json
import pathlib
import re
import sys
import tomllib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from strata import ROOT  # noqa: E402

RESULTS = ROOT / "results"
NS = {
    "sosa": "http://www.w3.org/ns/sosa/",
    "ssn": "http://www.w3.org/ns/ssn/",
    "ssn-system": "http://www.w3.org/ns/ssn/systems/",
    "ssn-ext": "http://www.w3.org/ns/ssn/ext/",
    "xg": "http://purl.oclc.org/NET/ssnx/ssn#",
}
SYSTEM_PREFIXES = {"ssn-system", "ssn-systems", "ssnsystem", "ssnsys", "ssn-sys", "sys"}
PREFIXES = {"sosa", "ssn", "ssnx", "ssn-xg", "ssn-ext", "ssnext"} | SYSTEM_PREFIXES
NAME = re.compile(r"(?<![\w/#.-])(sosa|ssn-systems?|ssnsystem|ssnsys|ssn-sys|ssn-ext|ssnext|ssn-xg|ssnx|ssn)"
                  r"(\s?):([A-Za-z_][A-Za-z0-9_]*(?:[-/][A-Za-z0-9_]+)*)")
HASH = re.compile(r"w3\.org/ns/(sosa|ssn)#([A-Za-z_]\w*)")
MINTED = re.compile(r"w3\.org/ns/(sosa|ssn)/([A-Za-z_][\w.-]*/[\w./%-]+)")  # an IRI below a term
BIND = [re.compile(r"@prefix([A-Za-z][\w-]*):<([^>]+)>", re.I),
        re.compile(r"PREFIX([A-Za-z][\w-]*):<([^>]+)>"),
        re.compile(r"xmlns:([A-Za-z][\w-]*)=\"([^\"]+)\""),
        re.compile(r"\"([A-Za-z][\w-]*)\":\"(https?://[^\"]+)\"")]
DT_MARK = r"(?:\^\^|ˆˆ|∧∧|\^ˆ|ˆ\^)"   # matched in the squeezed text: no spaces left
XSD = sorted(["string", "boolean", "decimal", "integer", "int", "long", "short", "byte", "float", "double",
              "dateTimeStamp", "dateTime", "date", "time", "duration", "dayTimeDuration", "yearMonthDuration",
              "gYearMonth", "gYear", "gMonthDay", "gDay", "gMonth", "anyURI", "hexBinary", "base64Binary",
              "nonNegativeInteger", "positiveInteger", "nonPositiveInteger", "negativeInteger",
              "unsignedInt", "unsignedLong", "unsignedShort", "unsignedByte", "normalizedString", "token",
              "language"], key=len, reverse=True)
DATATYPE = re.compile(DT_MARK + r"(<[^>]{3,120}>|[A-Za-z][\w-]*:[A-Za-z]*)")
SIMPLE = re.compile(r"hasSimpleResult")
UNIT_IN_STRING = re.compile(r"^-?[\d.,]+[A-Za-z°%µ/]+")


def squeeze(t):
    return re.sub(r"\s+", "", t)


def squeezed(text):
    """The text without whitespace, and for each of its characters the index in the text."""
    idx = [i for i, ch in enumerate(text) if not ch.isspace()]
    return "".join(text[i] for i in idx), idx


def norm_datatype(tok):
    """A datatype token of the squeezed text, as a prefixed name; a local name glued to what
    follows it (squeezing) is cut at the longest XSD name it starts with."""
    t = tok.strip("<>")
    low = t.lower()
    if "xmlschema#" in low:
        p, local = "xsd", t.split("#", 1)[1]
    elif "custom_datatypes#" in low or "lindt" in low:
        return "cdt:" + (t.split("#", 1)[1] if "#" in t else "?")
    elif low.startswith("http"):
        return "<" + t + ">"
    elif ":" in t:
        p, _, local = t.partition(":")
        p = p.lower()
    else:
        return t
    if p == "xsd":
        for x in XSD:
            if local.lower().startswith(x.lower()):
                return "xsd:" + x
        return "xsd:" + (local or "?") + " (not an XSD name)"
    if p == "cdt":
        m = re.match(r"(ucum|length|temperature|area|volume|mass|speed|time|frequency|power|energy|"
                     r"electricCurrent|luminousIntensity|amountOfSubstance|dimensionless)", local, re.I)
        return "cdt:" + (m.group(1) if m else (local or "?"))
    return f"{p}:{local}" if local else f"{p}:?"


def family(dt):
    if dt == "cdt:ucum":
        return "cdt:ucum"
    if dt.startswith("cdt:"):
        return "cdt: other"
    if dt.startswith("xsd:") or dt.startswith("rdf:"):
        return dt
    if dt.startswith("geo:") or "wktliteral" in dt.lower():
        return "geo:wktLiteral"
    return "other datatype"


def simple_values(body):
    """The forms of the values that follow `hasSimpleResult` in the text, with their quotations.
    Read in the squeezed text, so that a listing whose letters the PDF extraction spaced out
    (`h a s S i m p l e R e s u l t`) is read too."""
    sq, idx = squeezed(body)
    out = []
    for m in SIMPLE.finditer(sq):
        t = sq[m.end():m.end() + 160]
        before = sq[max(0, m.start() - 6):m.start()]
        if re.search(r"[\"“'‘](sosa:|ssn:|[\w/.#:]*)$", before) and t[:1] in "\"”'’":
            t = t[1:]                       # the closing quote of a quoted name
            if before.endswith(("/", "#")) and t[:1] in ",}]":
                continue                    # the end of a full IRI in JSON: a context or a type
            if not t.startswith(":"):
                continue                    # a name quoted in prose or in code: no value
            t = t[1:]                       # a JSON(-LD) key: its value follows
        t = re.sub(r"^>", "", t)            # N-Triples IRI end, RDF/XML element
        start, end = idx[max(0, m.start() - 30)], idx[min(len(idx) - 1, m.end() + 60)]
        quote = " ".join(body[start:end + 1].split())
        dt = None
        x = re.match(r"rdf:datatype=[\"“]([^\"”]+)[\"”]", t)
        if x:
            dt = norm_datatype(x.group(1))
        if not dt:  # JSON-LD value object; `@datatype` is not a JSON-LD keyword, but is written
            x = re.match(r"\{[^}]{0,120}?\"@(type|datatype)\":\"([^\"]+)\"", t)
            if x:
                dt = norm_datatype(x.group(2)) + (" (as @datatype)" if x.group(1) == "datatype" else "")
        if not dt:  # RDFa: property="sosa:hasSimpleResult" datatype="cdt:ucum" content="…"
            x = re.match(r"[\"”][^<>]{0,40}?datatype=[\"“]([^\"”]+)[\"”]", t)
            if x:
                dt = norm_datatype(x.group(1))
        lit = re.match(r"[\"“”'‘’]([^\"“”'‘’]{0,60})[\"“”'‘’](" + DT_MARK + r")?", t) \
            or re.match(r"[\"“”]([-\d.,]+)()(?=" + DT_MARK + r")", t)  # a closing quote lost by the extraction
        if lit and not lit.group(2) and t[lit.end(1):lit.end(1) + 2] in ("^^", "ˆˆ", "∧∧"):
            lit = re.match(r"[\"“”]([-\d.,]+)(" + DT_MARK + r")", t)
        if not dt and lit and lit.group(2):
            d = DATATYPE.match(t[lit.end(1) + 1:])
            if d:
                dt = norm_datatype(d.group(1))
        if not dt and lit and lit.group(2):  # a full datatype IRI without angle brackets (code)
            d = re.match(DT_MARK + r"(https?://[^\"'<>),;]+)", t[lit.end(1) + 1:])
            if d:
                dt = norm_datatype(d.group(1))
        if not dt:
            d = re.match(r"[\"“'‘][^\"”'’]{0,60}[\"”'’]\+?\"?" + DT_MARK + r"(https?://[^\"'<>),;]+)", t)
            if d:
                dt = norm_datatype(d.group(1))
        if lit and not dt and re.match(r"https?://", lit.group(1)):
            continue                        # a JSON-LD context: the IRI of the term, not a value
        if dt:
            out.append(("typed", dt, quote))
        elif lit:
            out.append(("plain string, unit inside" if UNIT_IN_STRING.match(lit.group(1)) else "plain string",
                        None, quote))
        elif re.match(r"[?$][A-Za-z_]", t):
            out.append(("query variable", None, quote))
        elif re.match(r"-?\d[\d.]*(e-?\d+)?[;.,}\]<]", t, re.I) and not re.match(r"\d{1,2}[\],)]", t):
            out.append(("bare number", None, quote))
        elif re.match(r"\(-?\d[\d.]*\)", t) or re.match(r"\(\w+,-?\d[\d.]*\)", t):
            out.append(("bare number", None, quote))     # a rule or a fact: hasSimpleResult(130)
        elif re.match(r"(true|false)[;.,}\]<]", t):
            out.append(("bare boolean", None, quote))
    return out


RANGE = [re.compile(r"subPropertyOf(?:sosa:)?hasSimpleResult"), re.compile(r"hasSimpleResult(?:some|only|exactly1|max1|min1)\(?([A-Za-z][\w-]*:[A-Za-z]+)"),
         re.compile(r"hasSimpleResult(?:[^.]{0,60}?)(?:rdfs:)?range(?:Includes)?([A-Za-z][\w-]*:[A-Za-z]+)")]


def declared_ranges(body):
    """Datatypes a work declares for simple results: the range of a subproperty of
    hasSimpleResult, or an OWL restriction on it (`hasSimpleResult some xsd:double`)."""
    sq, idx = squeezed(body)
    out = []
    for m in RANGE[0].finditer(sq):
        win = sq[max(0, m.start() - 160):m.end() + 160]
        for r in re.finditer(r"range(?:Includes)?([A-Za-z][\w-]*:[A-Za-z]+)", win):
            out.append((norm_datatype(r.group(1)), " ".join(body[idx[max(0, m.start() - 120)]:idx[min(len(idx) - 1, m.end() + 60)]].split())))
    for rx in RANGE[1:]:
        for m in rx.finditer(sq):
            out.append((norm_datatype(m.group(1)), " ".join(body[idx[max(0, m.start() - 40)]:idx[min(len(idx) - 1, m.end() + 20)]].split())))
    return out


def cdt_kinds(body):
    """How a text writes the custom datatypes of LINDT (`cdt:`, w3id.org/lindt/custom_datatypes):
    as the datatype of a literal, as a declared range, in a prefix declaration, or in prose
    only. `cmo-simple-cdt:` and the like (another prefix ending in cdt) are not counted."""
    kinds = set()
    for m in re.finditer(r"(?<![A-Za-z0-9_-])cdt\s?:|custom_datatypes|/lindt", body, re.I):
        pre = squeeze(body[max(0, m.start() - 60):m.start()])[-14:]
        if re.search(r"(\^\^|ˆˆ|∧∧)$", pre) or re.search(r"\"@?datatype\":\"$|datatype=\"$", pre):
            kinds.add("datatype of a literal")
        elif re.search(r"range(Includes)?$", pre):
            kinds.add("declared range")
        elif re.search(r"(@prefix|PREFIX)$|\"$", pre) or squeeze(body[m.end():m.end() + 5])[:1] == "<":
            kinds.add("prefix declaration")
        else:
            kinds.add("prose")
    return kinds


def term_sets():
    by_version = collections.defaultdict(set)   # version -> {(ns, local)}
    deprecated = set()
    with open(RESULTS / "terms.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            ns, local = r["namespace"], r["term"][len(r["namespace"]):]
            by_version[r["version"]].add((ns, local))
            if r["deprecated"]:
                deprecated.add((r["version"], ns, local))
    return by_version, deprecated


def publication_dates():
    """OpenAlex id and DOI -> publication date, from the raw OpenAlex harvests (citations,
    full-text searches) and the Semantic Scholar metadata."""
    by_id, by_doi = {}, {}
    for path in sorted(ROOT.glob("raw/*-openalex-*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                for w in rec.get("results", [rec]) if isinstance(rec, dict) else []:
                    if not isinstance(w, dict) or not w.get("publication_date") or not w.get("id"):
                        continue
                    by_id[w["id"].rsplit("/", 1)[-1]] = w["publication_date"]
                    if w.get("doi"):
                        by_doi[w["doi"].replace("https://doi.org/", "").lower()] = w["publication_date"]
    for path in sorted(ROOT.glob("raw/*-s2-*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                w = rec.get("citingPaper", rec) if isinstance(rec, dict) else {}
                d = w.get("publicationDate") if isinstance(w, dict) else None
                doi = ((w.get("externalIds") or {}).get("DOI") or "").lower() if isinstance(w, dict) else ""
                if d and doi:
                    by_doi.setdefault(doi, d)
    return by_id, by_doi


def history():
    p = ROOT / "protocol/namespace-history.toml"
    hist = tomllib.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    q = RESULTS / "namespace-history.json"
    hist["new_terms"] = {t: v["date"] for t, v in json.loads(q.read_text(encoding="utf-8"))["terms"].items()} \
        if q.exists() else {}
    return hist


def when(date, since):
    """'before', 'after', or 'same year' (the work has a year only, the year of `since`)."""
    if not date or not since:
        return "after"
    if len(date) == 4:
        return "before" if date < since[:4] else "after" if date > since[:4] else "same year"
    return "before" if date < since else "after"


def bindings(sq):
    out = {}
    for rx in BIND:
        for p, iri in rx.findall(sq):
            out[p.lower()] = iri.rstrip("#/").lower()
    return out


def declares(sq, bind):
    low = sq.lower()
    seen = set()
    for key, iri in NS.items():
        bare = iri.split("://", 1)[1].rstrip("#/").lower()
        if key == "ssn":  # w3.org/ns/ssn/ but not its sub-namespaces only
            if re.search(r"w3\.org/ns/ssn(?:[/#\"'>]|$)(?!systems|ext)", low):
                seen.add(key)
        elif bare in low:
            seen.add(key)
    for p, iri in bind.items():
        for key, ns in NS.items():
            if iri == ns.split("://", 1)[1].rstrip("#/").lower() or iri == ns.rstrip("#/").lower():
                seen.add(key)
    return seen


def distance(a, b, cap=3):
    """Levenshtein distance, stopped at `cap`."""
    if abs(len(a) - len(b)) >= cap:
        return cap
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
        if min(prev) >= cap:
            return cap
    return min(prev[-1], cap)


def classify(prefix, local, space, ctx, terms, date, hist):
    """The class of one prefixed name in a work (see the docstring)."""
    if "-" in local and "/" not in local:  # a word cut at a line end by the PDF: Fea-tureOfInterest
        joined = local.replace("-", "")
        k = classify(prefix, joined, space, ctx, terms, date, hist)
        if k not in ("undeclared", "individual minted in the namespace", "misspelt"):
            return k
    S17, X, S23 = terms["sosa-ssn-2017"], terms["ssn-xg"], terms["ssn-2023"]
    sosa17 = {l for n, l in S17 if n == NS["sosa"]}
    ssn17 = {l for n, l in S17 if n == NS["ssn"]}
    sys17 = {l for n, l in S17 if n == NS["ssn-system"]}
    xg = {l for n, l in X}
    sosa23 = {l for n, l in S23 if n == NS["sosa"]}
    known = sosa17 | ssn17 | sys17 | xg | sosa23
    if space and local not in known:
        return None
    lower = {k.lower(): k for k in known}
    bound = ctx["bind"].get(prefix)
    if bound:  # a declared prefix wins over the usual one
        for key, ns in NS.items():
            if bound == ns.split("://", 1)[1].rstrip("#/").lower() or bound == ns.rstrip("#/").lower():
                prefix = {"xg": "ssnx", "ssn-system": "ssn-system"}.get(key, key)
    moved = hist.get("moved_to_sosa", {})
    decided = hist.get("decision", {}).get("all_terms_in_sosa")
    if prefix == "sosa":
        if local in sosa17:
            return "ok-2017"
        if local in ssn17 or local in sys17:
            since = moved.get(local) or (decided if local in ssn17 else hist.get("new_terms", {}).get(local))
            w = when(date, since)
            if not since:
                return "ns-system-term-as-sosa (never in sosa:)"
            return {"before": "ns-ssn-term-as-sosa (before the decision)",
                    "same year": "ns-ssn-term-as-sosa (year of the decision)"}.get(w, "ns-ssn-term-as-sosa (after the decision)")
        if local in sosa23:
            since = hist.get("new_terms", {}).get(local) or decided
            w = when(date, since)
            return {"before": "new-2023 (before it existed in sosa:)",
                    "same year": "new-2023 (year it entered sosa:)"}.get(w, "new-2023")
        if local in xg:
            return "ns-xg-term-as-sosa"
    elif prefix in ("ssn",):
        xg_ctx = "xg" in ctx["declares"] and not ({"sosa", "ssn"} & ctx["declares"])
        if local in ssn17:
            return "ok-2017"
        if local in xg and (xg_ctx or "ssn" not in ctx["declares"]):
            return "ok-xg" if xg_ctx else "ok-xg (no namespace shown)"
        if local in sosa17 or local in sosa23:
            return "ns-sosa-term-as-ssn"
        if local in sys17:
            return "ns-system-term-as-ssn"
    elif prefix in ("ssnx", "ssn-xg"):
        if local in xg:
            return "ok-xg"
    elif prefix in SYSTEM_PREFIXES:
        if local in sys17:
            return "ok-2017"
        if local in sosa23:
            return "ns-sosa-term-as-system"
    elif prefix in ("ssn-ext", "ssnext"):
        # the Extensions put their terms in sosa:; ssn-ext:X is a wrong namespace, unless
        # the work binds the prefix to sosa: (handled above)
        return "ns-ssn-ext-prefix" if local in sosa23 else "undeclared"
    if re.search(r"/|\d", local) or "_" in local.strip("_"):
        return "individual minted in the namespace"
    if local.lower() in lower:
        return "case"
    if local.endswith("s") and local[:-1].lower() in lower:
        return "plural"
    if len(local) >= 6 and min(distance(local.lower(), k) for k in lower) <= 2:
        return "misspelt"
    return "undeclared"


def main():
    import hypothetical_findings as hf
    answers, not_work, source = hf.ladder_answers()
    its = hf.items()
    by_id, by_doi = hf.work_meta()
    terms, deprecated = term_sets()
    hist = history()

    def meta(item):
        it = its.get(item, {})
        if item.startswith("openalex:") and item[9:] in by_id:
            return by_id[item[9:]]
        return by_doi.get((it.get("doi") or "").lower(), {})

    bodies = {}
    with gzip.open(ROOT / "screening/bodies.jsonl.gz", "rt", encoding="utf-8") as f:
        for d in map(json.loads, f):
            bodies[d["item"]] = d["body"]
    from strata import load_seeds
    seed_ids = {x["openalex"] for x in load_seeds()}
    seed_dois = {x["doi"].lower() for x in load_seeds() if x.get("doi")}
    seeds = {i for i in bodies if i[9:] in seed_ids or (its.get(i, {}).get("doi") or "").lower() in seed_dois}
    pop = [i for i in bodies if i not in not_work and i not in seeds
           and its.get(i, {}).get("stratum") in ("A", "B", "D")]
    eng = {i: answers.get(i, {}).get("engagement", {}).get("value") for i in pop}

    names = {}         # item -> Counter((prefix, local, class))
    simple = {}        # item -> list of (form, datatype, quote)
    ranges = {}        # item -> list of (datatype, quote): declared ranges of simple results
    cdts = {}          # item -> how the text writes the custom datatypes cdt:
    anywhere = {}      # item -> Counter(datatype family) anywhere in the body
    qv = {}            # item -> set of quantity-value vocabularies written
    declared, dates = {}, {}
    pub_id, pub_doi = publication_dates()
    for i in pop:
        b = bodies[i]
        sq = squeeze(b)
        bind = bindings(sq)
        ctx = {"bind": bind, "declares": declares(sq, bind)}
        declared[i] = sorted(ctx["declares"])
        m = meta(i)
        doi = (m.get("doi") or its.get(i, {}).get("doi") or "").lower()
        date = pub_id.get(m.get("openalex") or "") or pub_doi.get(doi) or (str(m["year"]) if m.get("year") else None)
        dates[i] = date
        c = collections.Counter()
        for x in NAME.finditer(b):
            prefix, space, local = x.group(1).lower(), x.group(2), x.group(3)
            k = classify(prefix, local, bool(space), ctx, terms, date, hist)
            if k:
                c[(prefix, local, k)] += 1
        for x in HASH.finditer(sq):   # the 2017 namespaces end with a slash, not a hash
            c[(x.group(1), x.group(2), "namespace written with # for /")] += 1
        for x in MINTED.finditer(sq):
            c[(x.group(1), x.group(2)[:40], "individual minted in the namespace")] += 1
        names[i] = c
        simple[i] = simple_values(b)
        ranges[i] = declared_ranges(b)
        cdts[i] = cdt_kinds(b)
        anywhere[i] = collections.Counter(family(norm_datatype(d.group(1))) for d in DATATYPE.finditer(sq))
        q = set()
        if re.search(r"qudt\s?:\s?(QuantityValue|numericValue|unit\b|hasUnit|value\b)|qudt\.org/(schema|vocab)", b):
            q.add("QUDT")
        if re.search(r"\bom\s?:\s?(Measure|hasNumericalValue|hasUnit|hasValue|Point)\b|ontology-of-units-of-measure", b):
            q.add("OM")
        if re.search(r"schema\s?:\s?(QuantitativeValue|unitCode|unitText)", b):
            q.add("schema.org")
        if re.search(r"\bucum\b", b, re.I):
            q.add("UCUM named")
        qv[i] = q

    def year(i):
        y = meta(i).get("year")
        return int(y) if y else None

    def label(i):
        m = meta(i)
        return {"item": i, "title": (m.get("title") or its.get(i, {}).get("title") or "")[:140],
                "year": year(i), "stratum": its.get(i, {}).get("stratum"), "engagement": eng.get(i),
                "doi": m.get("doi") or its.get(i, {}).get("doi"), "date": dates.get(i)}

    out = {"population": len(pop), "decision": hist.get("decision", {}), "names": {}, "simple": {}, "quantity": {}}
    L = ["# How the works write SOSA/SSN: names, namespaces, simple results", "",
         "Written by `scripts/usage_patterns.py` from the bodies of the full texts (bibliography cut). "
         "Counts of what the text **shows**: not decisions of the readers.", "",
         f"Population: {len(pop)} full texts of strata A, B and D, less the texts a model took for another work "
         f"and the {len(seeds & set(bodies))} seeds held (the papers on SOSA/SSN itself, whose examples are the specification's)."]

    # 1. names
    by_class = collections.defaultdict(set)
    occ_class = collections.Counter()
    terms_class = collections.defaultdict(collections.Counter)
    for i, c in names.items():
        for (p, l, k), n in c.items():
            by_class[k].add(i)
            occ_class[k] += n
            terms_class[k][f"{p}:{l}"] += 1
    writers = [i for i in pop if names[i]]
    out["names"]["works_writing_names"] = len(writers)
    out["names"]["by_class"] = {k: {"works": len(v), "occurrences": occ_class[k],
                                     "terms": dict(terms_class[k].most_common()),
                                     "list": [label(i) for i in sorted(v)]} for k, v in sorted(by_class.items())}
    err_classes = [k for k in by_class if not k.startswith("ok") and k not in (
        "new-2023", "plural", "ns-ssn-term-as-sosa (after the decision)", "new-2023 (year it entered sosa:)",
        "ns-ssn-term-as-sosa (year of the decision)")]
    err_works = set().union(*(by_class[k] for k in err_classes)) if err_classes else set()
    out["names"]["works_with_a_name_error"] = len(err_works)
    L += ["", "## 1. Prefixed names and their namespaces", "",
          f"{len(writers)} of the {len(pop)} full texts write at least one prefixed name of SOSA/SSN. "
          f"{len(err_works)} of them ({100 * len(err_works) / max(1, len(writers)):.0f} %) write at least one "
          "name in a wrong namespace, with a wrong case, or that no version declares.", "",
          "Decision that every term goes into `sosa:`: " + json.dumps(hist.get("decision", {}), ensure_ascii=False), "",
          "| Class | Works | Occurrences | Most frequent names (works) |", "|---|---|---|---|"]
    for k, v in sorted(by_class.items(), key=lambda kv: -len(kv[1])):
        top = ", ".join(f"`{t}` ({n})" for t, n in terms_class[k].most_common(8))
        L.append(f"| {k} | {len(v)} | {occ_class[k]} | {top} |")
    for k in sorted(by_class, key=lambda k: -len(by_class[k])):
        if k.startswith("ok"):
            continue
        L += ["", f"### {k}", ""]
        for i in sorted(by_class[k], key=lambda i: (year(i) or 0, i)):
            lb = label(i)
            ts = ", ".join(f"`{p}:{l}`" for (p, l, kk) in names[i] if kk == k)
            L.append(f"- `{i}` ({lb['date'] or lb['year']}, {lb['stratum']}, {lb['engagement']}; declares "
                     f"{', '.join(declared[i]) or 'no namespace'}): {ts} — {lb['title']}")

    # 2. simple results; the works an agent checked replace the rules' reading
    checked = tomllib.loads((ROOT / "protocol/simple-results-checked.toml").read_text(encoding="utf-8")).get("work", [])
    corrected = {}
    for w in checked:
        if w["item"] in simple:
            simple[w["item"]] = [("checked", f, w["why"]) for f in w["forms"]]
            corrected[w["item"]] = w["why"]
    forms = collections.defaultdict(set)
    quotes = collections.defaultdict(list)
    for i, vals in simple.items():
        for form, dt, q in vals:
            if form == "checked":   # dt is the checked form, q the reason
                key = family(dt) if re.match(r"(xsd|cdt|rdf|geo):", dt) and "," not in dt and "(" not in dt else dt
                forms[key].add(i)
                if len(quotes[key]) < 400:
                    quotes[key].append((i, "checked", q))
                continue
            key = family(dt) if form == "typed" else form
            forms[key].add(i)
            if len(quotes[key]) < 400:
                quotes[key].append((i, dt, q))
    mention = [i for i in pop if SIMPLE.search(bodies[i])]
    shown = set().union(*(forms[k] for k in forms if k != "query variable")) if forms else set()
    typed = set().union(*(v for k, v in forms.items() if k.startswith(("xsd:", "cdt", "geo:", "rdf:", "other datatype")))) \
        if forms else set()
    out["simple"]["corrected_by_agent"] = corrected
    out["simple"] = {"works_naming_hasSimpleResult": len(mention), "works_showing_a_value": len(shown),
                     "works_showing_a_datatype": len(typed),
                     "by_form": {k: {"works": len(v), "list": [label(i) for i in sorted(v)]} for k, v in forms.items()},
                     "quotes": {k: [{"item": i, "datatype": d, "quote": q} for i, d, q in v] for k, v in quotes.items()}}
    rng = collections.defaultdict(set)
    rquotes = []
    for i, rs in ranges.items():
        for d, q in rs:
            rng[family(d)].add(i)
            rquotes.append((i, d, q))
    out["simple"]["declared_ranges"] = {k: {"works": len(v), "list": [label(i) for i in sorted(v)]} for k, v in rng.items()}
    out["simple"]["declared_range_quotes"] = [{"item": i, "datatype": d, "quote": q} for i, d, q in rquotes]
    either = collections.defaultdict(set)
    for k, v in list(forms.items()) + list(rng.items()):
        if k.startswith(("xsd:", "cdt", "geo:", "rdf:", "other datatype")):
            either[k] |= v
    out["simple"]["datatype_values_or_ranges"] = {k: {"works": len(v), "list": [label(i) for i in sorted(v)]}
                                                  for k, v in either.items()}
    anyw = collections.defaultdict(set)
    for i, c in anywhere.items():
        for k in c:
            anyw[k].add(i)
    out["simple"]["datatypes_anywhere"] = {k: {"works": len(v), "list": sorted(v)} for k, v in anyw.items()}
    L += ["", "## 2. Simple results (`sosa:hasSimpleResult`)", "",
          f"{len(mention)} full texts name `hasSimpleResult`; {len(shown)} of them show the value of at least one "
          f"simple result (a literal after the property), {len(typed)} with a datatype.", "",
          "| Form of the value | Works | Works (ids) |", "|---|---|---|"]
    for k, v in sorted(forms.items(), key=lambda kv: -len(kv[1])):
        L.append(f"| {k} | {len(v)} | {', '.join(f'`{i}`' for i in sorted(v))} |")
    L += ["", "Datatypes declared for simple results (range of a subproperty of `hasSimpleResult`, or an OWL "
          "restriction on it), works per datatype:", "", "| Datatype | Works | Works (ids) |", "|---|---|---|"]
    for k, v in sorted(rng.items(), key=lambda kv: -len(kv[1])):
        L.append(f"| {k} | {len(v)} | {', '.join(f'`{i}`' for i in sorted(v))} |")
    L += [""] + [f"- `{i}` {d}: “{q}”" for i, d, q in rquotes]
    L += ["", "Datatypes of simple results, shown on a value or declared as a range, works per datatype "
          f"({len(set().union(*either.values())) if either else 0} works):", "", "| Datatype | Works | Works (ids) |", "|---|---|---|"]
    for k, v in sorted(either.items(), key=lambda kv: -len(kv[1])):
        L.append(f"| {k} | {len(v)} | {', '.join(f'`{i}`' for i in sorted(v))} |")
    L += ["", "Datatypes written anywhere in the body (any property), works per family:", "",
          "| Datatype | Works |", "|---|---|"]
    for k, v in sorted(anyw.items(), key=lambda kv: -len(kv[1])):
        L.append(f"| {k} | {len(v)} |")
    L += ["", "### Quotations, by form", ""]
    for k in sorted(quotes, key=lambda k: -len(forms[k])):
        L += ["", f"**{k}**", ""]
        L += [f"- `{i}`{(' ' + d) if d else ''}: “{q}”" for i, d, q in quotes[k]]

    # 2b. custom datatypes anywhere in the text
    cdt_any = {i for i, k in cdts.items() if k}
    cdt_data = {i for i, k in cdts.items() if k & {"datatype of a literal", "declared range"}}
    cdt_lit = {i for i, k in cdts.items() if "datatype of a literal" in k}
    cdt_rng = {i for i, k in cdts.items() if "declared range" in k} - cdt_lit
    cdt_pref = {i for i, k in cdts.items() if "prefix declaration" in k} - cdt_data
    cdt_prose = cdt_any - cdt_data - cdt_pref
    out["cdt"] = {"any": sorted(cdt_any), "literal": sorted(cdt_lit), "range_only": sorted(cdt_rng),
                  "prefix_only": sorted(cdt_pref), "prose_only": sorted(cdt_prose),
                  "kinds": {i: sorted(k) for i, k in cdts.items() if k}}
    L += ["", "### Custom datatypes (`cdt:`) anywhere in the text", "",
          f"{len(cdt_any)} full texts write `cdt:` or the LINDT namespace: {len(cdt_lit)} as the datatype of a literal, "
          f"{len(cdt_rng)} more only as a declared range, {len(cdt_pref)} only in a prefix declaration and prose, "
          f"{len(cdt_prose)} in prose only.", ""]
    L += [f"- `{i}` ({label(i)['year']}): {', '.join(sorted(k))} — {label(i)['title']}" for i, k in sorted(cdts.items()) if k]

    # 3. quantity values
    qvw = collections.defaultdict(set)
    for i, s in qv.items():
        for k in s:
            qvw[k].add(i)
    out["quantity"] = {k: {"works": len(v), "list": sorted(v)} for k, v in qvw.items()}
    L += ["", "## 3. Quantity values and units", "", "| Written in the text | Works |", "|---|---|"]
    for k, v in sorted(qvw.items(), key=lambda kv: -len(kv[1])):
        L.append(f"| {k} | {len(v)} |")

    # macros of the papers (scripts/article_macros.py adds the prefix `use-`)
    from article_macros import num, pct, tex_escape
    M = {}

    def slug(k):
        return re.sub(r"[^a-z0-9]+", "-", k.lower()).strip("-")
    M["pop"] = num(len(pop))
    M["writers"] = num(len(writers))
    M["writers-pct"] = pct(len(writers), len(pop), 0)
    M["name-error-works"] = num(len(err_works))
    M["name-error-pct"] = pct(len(err_works), len(writers), 0)
    for k, v in by_class.items():
        M[f"names-{slug(k)}"] = num(len(v))
        M[f"names-{slug(k)}-pct"] = pct(len(v), len(writers), 0)
        M[f"names-{slug(k)}-top"] = ", ".join(f"\\term{{{tex_escape(t)}}} ({n})" for t, n in terms_class[k].most_common(5))
    before = by_class.get("ns-ssn-term-as-sosa (before the decision)", set())
    M["ns-before-list"] = ", ".join(f"\\term{{{tex_escape(t)}}} ({n})" for t, n in
                                    terms_class["ns-ssn-term-as-sosa (before the decision)"].most_common())
    ys = [year(i) for i in before if year(i)]
    M["ns-before-years"] = f"{min(ys)}--{max(ys)}" if ys else ""
    dec = hist.get("decision", {}).get("all_terms_in_sosa", "")
    if dec:
        import datetime as _dt
        M["ns-decision-date"] = _dt.date.fromisoformat(dec).strftime("%-d %B %Y")
    sosa_ext = by_class.get("new-2023", set())
    M["ext-terms-works"] = num(len(sosa_ext))
    M["simple-naming"] = num(len(mention))
    M["simple-shown"] = num(len(shown))
    M["simple-shown-pct"] = pct(len(shown), len(mention), 0)
    M["simple-typed"] = num(len(typed))
    M["simple-query-only"] = num(len(forms.get("query variable", set()) - shown))
    xsd = set().union(*(v for k, v in forms.items() if k.startswith("xsd:"))) if forms else set()
    cdt = set().union(*(v for k, v in forms.items() if k.startswith("cdt"))) if forms else set()
    ucum = set().union(*(v for k, v in forms.items() if k.startswith("cdt:ucum"))) if forms else set()
    untyped = set().union(*(forms.get(k, set()) for k in ("bare number", "bare boolean", "plain string",
                                                           "plain string, unit inside")))
    M["simple-xsd"] = num(len(xsd))
    M["simple-cdt"] = num(len(cdt))
    M["simple-ucum"] = num(len(ucum))
    M["simple-untyped"] = num(len(untyped))
    M["simple-unit-in-string"] = num(len(forms.get("plain string, unit inside", set()) | forms.get("rdfs:Literal, unit inside", set())))
    M["simple-xsd-list"] = ", ".join(f"\\term{{{k}}} ({len(v)})" for k, v in sorted(forms.items(), key=lambda kv: -len(kv[1]))
                                     if k.startswith("xsd:"))
    rng_all = set().union(*rng.values()) if rng else set()
    M["simple-ranges"] = num(len(rng_all))
    M["simple-any-datatype"] = num(len(set().union(*either.values())) if either else 0)
    for k in ("QUDT", "OM", "schema.org", "UCUM named"):
        M[f"qv-{slug(k)}"] = num(len(qvw.get(k, set())))
    def studies(items):
        ids = [i[9:] if i.startswith("openalex:") else i for i in sorted(items, key=lambda i: (dates.get(i) or "", i))]
        return "\\study{" + ",".join(ids) + "}" if ids else ""
    M["ns-before-studies"] = studies(before)
    M["simple-ucum-studies"] = studies(ucum)
    M["simple-cdt-studies"] = studies(cdt)
    M["simple-xsd-studies"] = studies(xsd)
    M["simple-unit-in-string-studies"] = studies(forms.get("plain string, unit inside", set()) | forms.get("rdfs:Literal, unit inside", set()))
    M["ext-prefix-studies"] = studies(by_class.get("ns-ssn-ext-prefix", set()))
    M["hash-ns-studies"] = studies(by_class.get("namespace written with # for /", set()))
    M["ns-after-studies"] = studies(by_class.get("ns-ssn-term-as-sosa (after the decision)", set()))
    hasprop = {i for i in before if any(l == "hasProperty" and k.startswith("ns-ssn-term-as-sosa") for (p_, l, k) in names[i])}
    M["ns-before-hasproperty"] = num(len(hasprop))
    M["ns-before-hasproperty-studies"] = studies(hasprop)
    M["cdt-any"] = num(len(cdt_any))
    M["cdt-literal"] = num(len(cdt_lit))
    M["cdt-range-only"] = num(len(cdt_rng))
    M["cdt-in-data"] = num(len(cdt_data))
    M["cdt-prefix-only"] = num(len(cdt_pref))
    M["cdt-prose-only"] = num(len(cdt_prose))
    M["cdt-in-data-studies"] = studies(cdt_data)
    M["cdt-mention-studies"] = studies(cdt_pref | cdt_prose)
    out["macros"] = M
    out["sets"] = {"simple_xsd": sorted(xsd), "simple_cdt": sorted(cdt), "simple_ucum": sorted(ucum),
                   "simple_untyped": sorted(untyped), "simple_shown": sorted(shown), "name_error": sorted(err_works),
                   "ns_before": sorted(before), "writers": sorted(writers)}
    (RESULTS / "figures").mkdir(exist_ok=True)
    with open(RESULTS / "figures/simple-result-datatypes.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["form", "works"])
        for k, v in sorted(forms.items(), key=lambda kv: -len(kv[1])):
            w.writerow([k, len(v)])
    (RESULTS / "usage-patterns.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (RESULTS / "usage-patterns.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"results/usage-patterns.md: {len(writers)} works write names, {len(err_works)} with a name error; "
          f"{len(mention)} name hasSimpleResult, {len(shown)} show a value, {len(typed)} a datatype")
    return 0


if __name__ == "__main__":
    sys.exit(main())
