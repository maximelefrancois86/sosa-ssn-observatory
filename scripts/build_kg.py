#!/usr/bin/env python3
"""The knowledge graph of the SOSA/SSN Usage Observatory and the data of its web application.

    python3 -I scripts/build_kg.py                 # explorer/data/works.json, figures.json,
                                                   # method.json, meta.json, kg.ttl.gz
    python3 -I scripts/build_kg.py --public DIR    # the same without the quotations of the works

Every candidate work (strata A to D) with its bibliographic record (an extract of OpenAlex,
completed by Semantic Scholar), the seeds it cites, and what the observatory knows of its
relation to SOSA/SSN: the full text held or not, the codes of the language model that coded
it (engagement, version, modules, terms, extensions, results, errors, domain, companions,
artefacts, gaps, with their quotations), the modelling patterns coded from excerpts
(scripts/pattern_coding.py), and the names and simple results read by script
(scripts/usage_patterns.py). Each code says who made it (`prov:wasAttributedTo`).

Vocabularies of the graph:
- SPAR: FaBiO (types of works), CiTO (citations; `cito:Citation` with a characterisation
  derived from the engagement code), PRISM (DOI), FRBR (`frbr:partOf` a venue);
- MOD 3.2 (https://w3id.org/mod#): the versions of SOSA/SSN and the artefacts the works
  publish are `mod:SemanticArtefact`; an artefact that reuses SOSA/SSN `mod:reliesOn` it;
- DCTERMS, DCAT (the dataset itself, with its licence), FOAF, PROV-O, the Web Annotation
  vocabulary (`oa:TextQuoteSelector` for the quotations), and a small vocabulary of the
  observatory (`slr:`) for its codes, with labels;
- SOSA/SSN terms keep their own IRIs, `rdfs:isDefinedBy` the version that declares them.
Works, terms, codes and the `slr:` vocabulary have an `rdfs:label`, for browsing (Sparklis).

The application (explorer/index.html) reads works.json, figures.json and method.json, and
queries kg.ttl.gz with SPARQL in the browser. figures.json gives, for the figures that count
works, the filter that selects those works (or the works themselves), so that the application
recomputes each figure and lists its works; the key figures carry a label and a group.
method.json holds the glossary of the codes (from protocol/codebook.toml,
protocol/patterns-codebook.md, scripts/usage_patterns.py and protocol/namespace-history.toml)
and the facts the methodology page states. Standard library only.
"""
import ast
import collections
import csv
import gzip
import hashlib
import json
import pathlib
import re
import sys
import tomllib
import datetime as _dt

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from strata import ROOT, load_corpus, load_seeds, stratum  # noqa: E402

OUT = ROOT / "explorer/data"
BASE = "https://ci.mines-stetienne.fr/sosa-ssn-observatory/kg/"
SLR = BASE + "vocab#"
PREFIXES = {
    "slr": SLR, "kg": BASE, "fabio": "http://purl.org/spar/fabio/", "cito": "http://purl.org/spar/cito/",
    "prism": "http://prismstandard.org/namespaces/basic/2.0/", "frbr": "http://purl.org/vocab/frbr/core#",
    "mod": "https://w3id.org/mod#", "dcterms": "http://purl.org/dc/terms/", "foaf": "http://xmlns.com/foaf/0.1/",
    "prov": "http://www.w3.org/ns/prov#", "oa": "http://www.w3.org/ns/oa#", "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "xsd": "http://www.w3.org/2001/XMLSchema#", "owl": "http://www.w3.org/2002/07/owl#",
    "sosa": "http://www.w3.org/ns/sosa/", "ssn": "http://www.w3.org/ns/ssn/", "ssn-system": "http://www.w3.org/ns/ssn/systems/",
    "ssnx": "http://purl.oclc.org/NET/ssnx/ssn#", "dcat": "http://www.w3.org/ns/dcat#", "schema": "https://schema.org/",
}
FABIO = {"article": "JournalArticle", "conference-paper": "ConferencePaper", "book-chapter": "BookChapter",
         "dissertation": "Thesis", "preprint": "Preprint", "review": "ReviewArticle", "book": "Book",
         "data-paper": "DataPaper", "report": "Report", "editorial": "Editorial", "software-paper": "Article"}
CITO = {"E0": "cites", "E1": "citesForInformation", "E2": "discusses", "E3": "usesMethodIn",
        "E4": "extends", "E5": "extends"}
VERSIONS = {
    "ssn-xg": ("Semantic Sensor Network ontology of the W3C SSN-XG (2011)", "http://purl.oclc.org/NET/ssnx/ssn"),
    "sosa-ssn-2017": ("SOSA/SSN, W3C Recommendation and OGC standard (2017)", "http://www.w3.org/ns/ssn/"),
    "ssn-ext": ("Extensions to the Semantic Sensor Network Ontology (W3C draft, 2018-2020)", "http://www.w3.org/ns/ssn/ext/"),
    "ssn-2023": ("Semantic Sensor Network Ontology, 2023 Edition (W3C drafts, 2025-)", "http://www.w3.org/ns/sosa/"),
}
ARTEFACT_TYPE = {"ontology": "mod:SemanticArtefact", "alignment": "mod:SemanticArtefact",
                 "design-pattern": "mod:SemanticArtefact", "shacl-shapes": "mod:SemanticArtefact",
                 "dataset": "dcat:Dataset", "software": "schema:SoftwareSourceCode"}
TITLE = "SOSA/SSN Usage Observatory"
LICENSE = "https://creativecommons.org/licenses/by/4.0/"
LICENSE_NAME = "CC BY 4.0"
MODELS = {"claude-sonnet-5-5": "Claude Sonnet 5.5", "claude-opus-5-5": "Claude Opus 5.5",
          "claude-opus-5-5-agent": "Claude Opus 5.5 agents (modelling patterns)"}
TERM_PREFIX = [("sosa", "http://www.w3.org/ns/sosa/"), ("ssn-system", "http://www.w3.org/ns/ssn/systems/"),
               ("ssn", "http://www.w3.org/ns/ssn/"), ("ssnx", "http://purl.oclc.org/NET/ssnx/ssn#")]
STRATA = {"A": "cites a publication on SOSA/SSN of 2017 or later (a core seed)",
          "B": "cites only the earlier SSN publications (lineage seeds), published in 2018 or later",
          "C": "cites only the earlier SSN publications (lineage seeds), published before 2018",
          "D": "cites no seed: found by the SOSA/SSN names and namespaces in its full text"}

# The modelling patterns, in plain words (protocol/patterns-codebook.md, version 1):
# question -> (label, what it asks, {value: definition}). Order of the codebook.
PATTERNS = {
    "property_individuals": ("Property individuals", "What the objects of sosa:observedProperty, sosa:actsOnProperty and hasProperty stand for (one value).", {
        "generic": "One individual per kind of property, shared by all the features of interest (ex:Temperature observed on many rooms).",
        "specific": "One individual per feature of interest: the temperature of room 1 is not that of room 2 (<office/1/temperature>).",
        "both": "Both: feature-specific properties linked to a generic kind of property.",
        "class": "The property is an OWL class and nothing else: a subclass of sosa:ObservableProperty, and observations point to the class.",
        "not-shown": "The excerpts show no property individual or class."}),
    "property_source": ("Property source", "Where the properties come from (several values).", {
        "own-classes": "The work defines subclasses of sosa:ObservableProperty, sosa:ActuatableProperty or ssn:Property.",
        "own-individuals": "The work names its own property individuals, with no catalogue.",
        "catalogue": "The properties come from an external vocabulary: QUDT quantity kinds, SWEET, ENVO, OM, I-ADOPT, SAREF, CF standard names, Wikidata…",
        "not-shown": "The excerpts do not show where the properties come from."}),
    "punning": ("Punning", "Whether the same IRI is used both as a class and as an individual, which the specification says one should not do (one value).", {
        "yes": "The same IRI is a class (a subclass of a SOSA/SSN class, or the object of rdf:type) and an individual (the object of observedProperty, madeBySensor…).",
        "no": "Classes and individuals are shown, and they are distinct.",
        "not-shown": "The excerpts do not show both classes and individuals."}),
    "system_individuals": ("System individuals", "What the instances of sosa:Sensor, sosa:Actuator, sosa:Sampler, ssn:System and sosa:Platform stand for (one value).", {
        "individual-devices": "Each individual is one physical or software device (a serial number, :DHT22_kitchen).",
        "generic-individuals": "An individual stands for a model or kind of device, shared by the observations of many devices (:DHT22 as the sensor of every reading).",
        "types-and-instances": "Device models or kinds are classes (subclasses of sosa:Sensor or ssn:System) and the devices are their instances, as the 2023 Edition recommends.",
        "not-shown": "The excerpts show no system individual."}),
    "result_form": ("Result form", "How the value of an observation is written (several values).", {
        "simple-literal": "A literal with sosa:hasSimpleResult.",
        "qudt": "A QUDT quantity value (qudt:QuantityValue, qudt:numericValue).",
        "om": "An OM measure (om:Measure, om:Point).",
        "schema-org": "A schema.org quantitative value (schema:QuantitativeValue).",
        "own-result-node": "A result node (sosa:Result or a class of the work) with the work's own value property.",
        "own-value-property": "The value hangs on the observation by a property of the work other than hasSimpleResult (:hasValue).",
        "structured": "An array, a matrix, a JSON or CSV literal, an RDF list or a Data Cube.",
        "by-reference": "A file, an image or a stream given by its IRI.",
        "nested": "An observation or a collection as the result.",
        "not-shown": "The excerpts show no result."}),
    "unit_placement": ("Unit placement", "Where the unit of a value is written (several values).", {
        "in-literal": "In the literal: a cdt:ucum or other custom datatype, or a string with the unit (\"22 °C\").",
        "on-result-node": "On the result node (qudt:unit, qudt:hasUnit, om:hasUnit, schema:unitCode).",
        "on-observation": "On the observation, by a unit property.",
        "on-property": "On the observed property or its class.",
        "on-sensor-or-collection": "On the sensor or on a collection of observations.",
        "none": "Values are shown without any unit.",
        "not-shown": "The excerpts show no value."}),
    "time": ("Time", "How the time of an observation is written (several values).", {
        "resultTime-literal": "sosa:resultTime with an xsd:dateTime literal.",
        "phenomenonTime-owl-time": "sosa:phenomenonTime pointing to an OWL-Time instant or interval.",
        "phenomenonTime-literal": "sosa:phenomenonTime with a literal.",
        "own-time-property": "A timestamp property of the work or of another vocabulary.",
        "forecast": "An observation whose phenomenon time is after its result time: the forecast pattern of the specification.",
        "none": "The observations shown have no time.",
        "not-shown": "The excerpts show no observation time."}),
    "hosting": ("Hosting", "How systems are hosted and deployed (several values).", {
        "platform": "Platforms host systems (sosa:hosts, sosa:isHostedBy).",
        "deployment": "Deployments (ssn:Deployment, ssn:deployedSystem, ssn:deployedOnPlatform).",
        "subsystem": "Systems have subsystems (ssn:hasSubSystem).",
        "none": "Systems are described but never hosted.",
        "not-shown": "The excerpts show no system."}),
    "location": ("Location", "What the location is attached to, and how it is encoded (several values).", {
        "on-system": "Attached to the sensor or the actuator.",
        "on-platform": "Attached to the platform.",
        "on-feature": "Attached to the feature of interest.",
        "on-observation": "Attached to the observation.",
        "geosparql": "Encoded with GeoSPARQL (geo:hasGeometry, a WKT literal).",
        "wgs84": "Encoded with W3C Basic Geo (geo:lat, geo:long).",
        "schema-org": "Encoded with schema.org.",
        "own-property": "Encoded with a property of the work.",
        "not-shown": "The excerpts show no location."}),
    "grouping": ("Grouping", "How observations are grouped (several values).", {
        "one-by-one": "Each reading is one observation.",
        "collection-ssn-ext": "An ObservationCollection of the Extensions to SSN, written ssn-ext:.",
        "collection-sosa": "A sosa:ObservationCollection.",
        "own-collection": "A class or property of the work, a named graph or a Data Cube slice.",
        "series-literal": "A whole series as one literal or one file.",
        "stream": "An RDF stream of observations.",
        "not-shown": "The excerpts show no group of observations."}),
    "feature_typing": ("Feature typing", "How features of interest are typed (one value).", {
        "explicit": "Individuals typed sosa:FeatureOfInterest.",
        "subclass": "Domain classes declared subclasses of sosa:FeatureOfInterest.",
        "domain-only": "Features typed only by domain classes, linked by hasFeatureOfInterest.",
        "both": "Both: individuals typed sosa:FeatureOfInterest and domain subclasses of it.",
        "not-shown": "The excerpts show no feature of interest."}),
}


def name_classes(decided):
    """The classes of prefixed names of scripts/usage_patterns.py (its docstring and classify()),
    in plain words; `decided` is the date of the decision that every term goes into sosa:
    (protocol/namespace-history.toml)."""
    d = decided
    return {
        "ok-2017": "A name of SOSA/SSN 2017, in its namespace.",
        "ok-xg": "A name of the SSN-XG ontology (2011), in its namespace.",
        "ok-xg (no namespace shown)": "An SSN-XG name written ssn:, in a work that shows no namespace IRI.",
        "new-2023": "A term that only the 2023 Edition declares, written sosa: after it entered that namespace.",
        "new-2023 (year it entered sosa:)": "A term that only the 2023 Edition declares, in a work of the year it entered sosa:.",
        "new-2023 (before it existed in sosa:)": "A term that only the 2023 Edition declares, written sosa: before it existed: a term that did not exist yet (S2).",
        "ns-ssn-term-as-sosa (before the decision)": f"An ssn: term of 2017 written sosa: (sosa:System) by a work published before {d}, when the Working Group decided that every term goes into sosa:: a wrong namespace (S1), not an anticipation of the 2023 Edition.",
        "ns-ssn-term-as-sosa (year of the decision)": f"An ssn: term of 2017 written sosa: by a work published in the year of the decision of {d} (every term goes into sosa:).",
        "ns-ssn-term-as-sosa (after the decision)": f"An ssn: term of 2017 written sosa: by a work published after the decision of {d}: the 2023 name of the term.",
        "ns-system-term-as-sosa (never in sosa:)": "A term of the SSN System module written sosa:, a namespace it never entered.",
        "ns-sosa-term-as-ssn": "A SOSA term written ssn: (ssn:Observation for sosa:Observation) by a work that declares the 2017 namespaces (S1).",
        "ns-system-term-as-ssn": "A term of the SSN System module (ssn-system:) written ssn: (S1).",
        "ns-sosa-term-as-system": "A sosa: term written with the prefix of the SSN System module (S1).",
        "ns-xg-term-as-sosa": "An SSN-XG term written sosa: (sosa:SensingDevice): a wrong namespace or a term that does not exist (S1 or S2).",
        "ns-ssn-ext-prefix": "A term of the Extensions to SSN written ssn-ext:, whereas the Extensions put their terms in sosa: (S1).",
        "case": "A declared name with another case (sosa:observedproperty): a misspelling (S3).",
        "plural": "A declared name written in the plural (sosa:Observations).",
        "misspelt": "A name one or two letters away from a declared name (S3).",
        "undeclared": "A name that no version declares (sosa:hasUnit): S2.",
        "individual minted in the namespace": "An IRI of the work's own minted below a SOSA/SSN namespace (http://www.w3.org/ns/sosa/sensor/1).",
        "namespace written with # for /": "The namespace written with a hash (http://www.w3.org/ns/sosa#), whereas the 2017 namespaces end with a slash.",
    }


def simple_form(k):
    """The form of a value of sosa:hasSimpleResult (scripts/usage_patterns.py, simple_values()),
    in plain words."""
    fixed = {
        "query variable": "A SPARQL variable: the text shows a query, with no datatype.",
        "bare number": "A number without quotes or datatype (in Turtle, an xsd:integer, xsd:decimal or xsd:double).",
        "bare boolean": "true or false without quotes (in Turtle, an xsd:boolean).",
        "plain string": "A quoted string with no datatype.",
        "plain string, unit inside": "A quoted string with no datatype and the unit inside it (\"22 °C\").",
        "cdt:ucum": "A literal of the UCUM custom datatype, value and unit together (\"22 Cel\"^^cdt:ucum).",
        "cdt: other": "A literal of another custom datatype of the cdt: vocabulary (cdt:temperature…).",
    }
    if k in fixed:
        return fixed[k]
    base, notes = k, []
    for suffix, note in ((" (IRI cut)", "its datatype IRI cut by the text extraction"),
                         (" (as @datatype)", "written with @datatype in JSON-LD, which is not a JSON-LD keyword"),
                         (", unit inside", "the unit written inside the value")):
        if base.endswith(suffix):
            base, notes = base[:-len(suffix)], notes + [note]
    head = fixed.get(base, f"A literal of datatype {base}.").rstrip(".")
    return head + (", " + "; ".join(notes) if notes else "") + "."


def lit(v, dtype=None, lang=None):
    s = str(v).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")
    return f'"{s}"' + (f"^^{dtype}" if dtype else f"@{lang}" if lang else "")


def iri(u):
    return "<" + re.sub(r"[\s<>\"{}|^`\\]", lambda m: "%%%02X" % ord(m.group()), u) + ">"


def h(*parts):
    return hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:12]


def listval(v):
    if isinstance(v, list):
        return v
    if isinstance(v, str) and v.startswith("["):
        try:
            return ast.literal_eval(v)
        except (ValueError, SyntaxError):
            return []
    return [v] if v not in (None, "", "not-asked") else []


def entry_codes(record, key):
    """The `key` of each entry of an `entries` answer (errors: code; artefacts: kind and url).
    The entries are dicts; older records wrote them as "code: S1; term: …" strings."""
    out = []
    for e in listval((record or {}).get("entries") or (record or {}).get("value")):
        if isinstance(e, dict):
            out.append(e)
        elif isinstance(e, str):
            out.append({k.strip(): v.strip() for k, _, v in (p.partition(":") for p in e.split(";")) if v})
    return [e for e in out if e.get(key)]


def flagged_works():
    """OpenAlex ids of the candidates flagged by scripts/venue_risk.py (results/venue-risk.json
    gives only the counts): the same rules, on the same corpus."""
    import venue_risk as vr
    cfg = tomllib.loads((ROOT / "protocol/venue-risk.toml").read_text(encoding="utf-8"))
    publishers = vr.read_list(cfg["list"]["harvest"], "publishers")
    journals = vr.read_list(cfg["list"]["harvest"], "journals")
    alias = {vr.norm(k): v for k, v in cfg.get("publisher_alias", {}).items()}
    prefixes = cfg.get("doi_prefix", {})
    out = set()
    for w in load_corpus():
        p = vr.norm(w["publisher"])
        listed = p in publishers or p in alias or (not p and (w["doi"] or "").split("/")[0] in prefixes)
        if listed or (w["venue"] and not w["publisher"] and vr.norm(w["venue"]) in journals):
            out.add(w["openalex"])
    return out


def work_iri(item):
    kind, _, ident = item.partition(":")
    return f"https://openalex.org/{ident}" if kind == "openalex" else f"https://api.semanticscholar.org/CorpusID:{ident}"


class Graph:
    def __init__(self):
        self.lines = []
        self.seen = set()

    @staticmethod
    def term(t):
        # `kg:artefact/ssn-xg` is not a Turtle prefixed name ('/' is not allowed in a local
        # name): the nodes of the graph whose names have a '/' are written as full IRIs
        if t.startswith("kg:") and "/" in t:
            return iri(BASE + t[3:])
        return t

    def add(self, s, p, o):
        line = f"{self.term(s)} {p} {self.term(o)} ."
        if line not in self.seen:
            self.seen.add(line)
            self.lines.append(line)

    def label(self, s, text):
        if text:
            self.add(s, "rdfs:label", lit(text))

    def write(self, path):
        head = "".join(f"@prefix {k}: <{v}> .\n" for k, v in PREFIXES.items())
        with gzip.open(path, "wt", encoding="utf-8") as f:
            f.write(head + "\n" + "\n".join(self.lines) + "\n")


def macros():
    """[(key, value, source)] of results/macros.tex, in order."""
    out, src = [], ""
    for line in open(ROOT / "results/macros.tex", encoding="utf-8"):
        if line.startswith("% --- "):
            src = line[6:].strip()
        m = re.match(r"\\slrdef\{([^}]+)\}\{(.*)\}\s*$", line)
        if m:
            out.append((m.group(1), m.group(2), src))
    return out


def figures(rows, up, patterns):
    """explorer/data/figures.json: every figure of the papers, and for those that count works,
    either the works themselves (a set the producing script exports) or a filter on works.json
    that the explorer evaluates, so that it recomputes the figure and lists its works."""
    by_text = {r["text_item"]: r["id"] for r in rows if r.get("text_item")}
    full = {"all": [{"field": "stratum", "in": ["A", "B", "D"]}, {"field": "basis", "eq": "full text"},
                    {"field": "not_the_work", "eq": False}, {"field": "engagement", "ne": None}]}
    users = {"all": full["all"] + [{"field": "engagement", "in": ["E3", "E4", "E5"]}]}
    spec = {"hyp-users": users, "hyp-eng-ab-n": {"all": full["all"] + [{"field": "stratum", "in": ["A", "B"]}]}}
    for st in "ABD":
        spec[f"hyp-eng-{st}-full-n"] = {"all": full["all"] + [{"field": "stratum", "eq": st}]}
        for lv in ["E0", "E1", "E2", "E3", "E4", "E5"]:
            spec[f"hyp-eng-{st}-full-{lv}"] = {"all": full["all"] + [{"field": "stratum", "eq": st},
                                                                      {"field": "engagement", "eq": lv}]}
    for lv in ["E0", "E1", "E2", "E3", "E4", "E5"]:
        spec[f"hyp-eng-ab-{lv}"] = {"all": full["all"] + [{"field": "stratum", "in": ["A", "B"]},
                                                           {"field": "engagement", "eq": lv}]}
    for v in ["ssn-xg", "sosa-ssn-2017", "ssn-2023", "mixed", "unknown"]:
        spec[f"hyp-ver-{v}"] = {"all": users["all"] + [{"field": "version_used", "eq": v}]}
    for mod in ["sosa-observation", "sosa-actuation", "sosa-sampling", "ssn", "ssn-system", "alignments",
                "2023-execution", "2023-collections", "2023-sample-relations", "2023-oms", "2023-systems"]:
        spec[f"hyp-mod-{mod}"] = {"all": users["all"] + [{"field": "modules", "has": mod}]}
    # the populations of scripts/hypothetical_findings.py: coded (strata A, B, D, the text is
    # the work), from the full text or the abstract, the users (E3-E5)
    coded = [{"field": "stratum", "in": ["A", "B", "D"]}, {"field": "not_the_work", "eq": False},
             {"field": "engagement", "ne": None}]
    spec["hyp-coded"] = {"all": coded}
    spec["hyp-full"] = full
    spec["hyp-abstract"] = {"all": coded + [{"field": "basis", "eq": "abstract"}]}
    for name in ("opus", "sonnet"):
        spec[f"hyp-from-{name}"] = {"all": coded + [{"field": "coded_by", "eq": f"claude-{name}-5-5"}]}
    for st in "ABD":
        ab = coded + [{"field": "stratum", "eq": st}, {"field": "basis", "eq": "abstract"}]
        spec[f"hyp-eng-{st}-abs-n"] = {"all": ab}
        spec[f"hyp-eng-{st}-full-unknown"] = {"all": full["all"] + [{"field": "stratum", "eq": st},
                                                                     {"field": "engagement", "eq": "unknown"}]}
        for lv in ["E0", "E1", "E2", "E3", "E4", "E5", "unknown"]:
            spec[f"hyp-eng-{st}-abs-{lv}"] = {"all": ab + [{"field": "engagement", "eq": lv}]}
    spec["hyp-e45"] = {"all": full["all"] + [{"field": "engagement", "in": ["E4", "E5"]}]}
    for x in ["simple-literal", "quantity-value", "custom-result-class", "structured", "by-reference",
              "time-series", "coverage", "nested", "none"]:
        spec[f"hyp-rp-{x}"] = {"all": users["all"] + [{"field": "result_pattern", "has": x}]}
    for x in ["unit", "uncertainty", "quality", "time", "none"]:
        spec[f"hyp-vp-{x}"] = {"all": users["all"] + [{"field": "value_properties", "has": x}]}
    spec["hyp-err-works"] = {"all": users["all"] + [{"field": "errors", "ne": []}]}
    for code in ["S1", "S2", "S3", "M1", "M2", "M3", "M4", "G1", "G2", "G3"]:
        spec[f"hyp-err-{code}"] = {"all": users["all"] + [{"field": "errors", "has": code}]}
    spec["flagged"] = {"all": [{"field": "flagged_venue", "eq": True}]}
    printed = {k: v for k, v, _ in macros()}
    dom_pop = full["all"] + [{"field": "engagement", "in": ["E2", "E3", "E4", "E5"]}]
    for k in range(1, 13):
        d = printed.get(f"hyp-dom-{k}-name")
        if d and "\\" not in d:   # a name the macro did not escape: the same string as the code
            spec[f"hyp-dom-{k}"] = {"all": dom_pop + [{"field": "domain", "eq": d}]}
            spec[f"hyp-dom-{k}-use"] = {"all": users["all"] + [{"field": "domain", "eq": d}]}
    prefix = {"sosa": "http://www.w3.org/ns/sosa/", "ssn": "http://www.w3.org/ns/ssn/",
              "ssn-system": "http://www.w3.org/ns/ssn/systems/", "ssnx": "http://purl.oclc.org/NET/ssnx/ssn#"}
    for k in range(1, 16):
        m = re.fullmatch(r"\\texttt\{([a-z-]+):([A-Za-z_]\w*)\}", printed.get(f"hyp-term-{k}-name", ""))
        if m and m.group(1) in prefix:
            spec[f"hyp-term-{k}"] = {"all": users["all"] + [{"field": "term_iris", "has": prefix[m.group(1)] + m.group(2)}]}
    sets = {f"use-{k.replace('_', '-')}": v for k, v in (up.get("sets") or {}).items()}
    named = {"use-simple-xsd": "simple_xsd", "use-simple-cdt": "simple_cdt", "use-simple-ucum": "simple_ucum",
             "use-simple-untyped": "simple_untyped", "use-simple-shown": "simple_shown",
             "use-name-error-works": "name_error", "use-writers": "writers"}
    for key, name in named.items():
        if name in (up.get("sets") or {}):
            sets[key] = up["sets"][name]
    for k, v in up["names"]["by_class"].items():
        sets[f"use-names-{slug(k)}"] = [x["item"] for x in v["list"]]
    for k, v in up["simple"]["by_form"].items():
        sets[f"use-form-{slug(k)}"] = [x["item"] for x in v["list"]]
    pc = json.loads((ROOT / "results/pattern-coding.json").read_text(encoding="utf-8")) \
        if (ROOT / "results/pattern-coding.json").exists() else {"questions": {}}
    for q, v in pc["questions"].items():
        shown = set()
        for val, items in v["works"].items():
            sets[f"hyp-pat-{q.replace('_', '-')}-{slug(val)}"] = items
            if val != "not-shown":
                shown |= set(items)
        sets[f"hyp-pat-{q.replace('_', '-')}-shown"] = sorted(shown)
    sets["hyp-pat-coded"] = sorted(patterns)
    # the populations of the observatory itself, on works.json
    spec["obs-works"] = {"all": []}
    for st in "ABCD":
        spec[f"obs-stratum-{st}"] = {"all": [{"field": "stratum", "eq": st}]}
    spec["obs-fulltext"] = {"all": [{"field": "fulltext", "eq": True}]}
    for key in {k for r in rows for k in r["text_seeds"]}:
        spec[f"textseed-{key}-held"] = {"all": [{"field": "text_seeds", "has": key}]}
    out, seen = [], set()
    for key, value, src in macros():
        f = {"key": key, "value": value, "source": src}
        if key in spec:
            f["filter"] = spec[key]
        elif key in sets:
            f["works"] = sorted({by_text.get(i, i) for i in sets[key]})
        out.append(f)
        seen.add(key)
    for key, flt in spec.items():   # filters without a macro: the count is computed here
        if key not in seen:
            out.append({"key": key, "value": f"{sum(matches(r, flt) for r in rows):,}", "source": "derived", "filter": flt})
            seen.add(key)
    for key, items in sets.items():   # sets without a macro: still browsable
        if key not in seen:
            out.append({"key": key, "value": f"{len(set(items)):,}", "source": "derived",
                        "works": sorted({by_text.get(i, i) for i in items})})
    by_key = {f["key"]: f for f in out}
    for n, k in enumerate(key_figures(printed, pc)):
        f = by_key.get(k["key"])
        if f and ("filter" in f or "works" in f):
            f.update(k, main=True, order=n)
    (OUT / "figures.json").write_text(json.dumps({"figures": out}, ensure_ascii=False, separators=(",", ":")) + "\n",
                                      encoding="utf-8")


def slug(v):
    return re.sub(r"[^a-z0-9]+", "-", v.lower()).strip("-")


def matches(row, flt):
    """The filter language of figures.json, as the application evaluates it."""
    def cond(c):
        v = row.get(c["field"])
        if "eq" in c:
            return v == c["eq"]
        if "ne" in c:
            return v != c["ne"]
        if "in" in c:
            return v in c["in"]
        if "has" in c:
            return isinstance(v, list) and c["has"] in v
        return False
    return all(cond(c) for c in flt["all"])


def key_figures(printed, pc):
    """The key figures of the observatory, in order: {key, label, group, sub?, of?, code?}.
    `of` names the figure the share is computed on; `code` = [glossary group, value]."""
    cb = {q["id"]: q for q in tomllib.loads((ROOT / "protocol/codebook.toml").read_text(encoding="utf-8"))["question"]}
    mean = lambda q, v: cb[q].get("meaning", {}).get(v, v)   # noqa: E731
    K = []

    def add(group, key, label, of=None, code=None, sub=None):
        k = {"key": key, "label": label, "group": group}
        for name, x in (("of", of), ("code", code), ("sub", sub)):
            if x:
                k[name] = x
        K.append(k)
    g = "Corpus and strata"
    add(g, "obs-works", "Candidate works, strata A to D")
    for st in "ABCD":
        add(g, f"obs-stratum-{st}", f"Stratum {st}: {STRATA[st]}", "obs-works", ["strata", st])
    add(g, "obs-fulltext", "Works whose full text is held", "obs-works")
    add(g, "textseed-cox-2020-ssn-ext-held", "Full texts that name the Extensions to SSN (W3C draft)", "obs-fulltext",
        ["seeds", "cox-2020-ssn-ext"])
    add(g, "textseed-w3c-ssn-2023-held", "Full texts that name the 2023 Edition drafts", "obs-fulltext",
        ["seeds", "w3c-ssn-2023"])
    add(g, "hyp-coded", "Works coded by the language model (strata A, B and D)")
    add(g, "hyp-full", "Coded from the full text", "hyp-coded", ["coding", "full text"])
    add(g, "hyp-abstract", "Coded from the abstract only", "hyp-coded", ["coding", "abstract"])
    add(g, "hyp-from-sonnet", "Codes of Claude Sonnet 5.5", "hyp-coded", ["coding", "claude-sonnet-5-5"])
    add(g, "hyp-from-opus", "Codes of Claude Opus 5.5", "hyp-coded", ["coding", "claude-opus-5-5"])
    g = "Engagement"
    add(g, "hyp-eng-ab-n", "Works of strata A and B coded from the full text")
    for lv in ["E0", "E1", "E2", "E3", "E4", "E5"]:
        m = mean("engagement", lv)
        add(g, f"hyp-eng-ab-{lv}", m[0].upper() + m[1:], "hyp-eng-ab-n", ["engagement", lv])
    add(g, "hyp-eng-D-full-n", "Works of stratum D coded from the full text")
    for lv in ["E3", "E4"]:
        add(g, f"hyp-eng-D-full-{lv}", f"Stratum D: {mean('engagement', lv).split(':')[0]}", "hyp-eng-D-full-n",
            ["engagement", lv])
    add(g, "hyp-users", "Works that use SOSA/SSN: E3 to E5, coded from the full text, strata A, B and D", "hyp-full")
    add(g, "hyp-e45", "Works with an ontology that reuses or extends SOSA/SSN (E4 or E5)", "hyp-full")
    g = "Versions used"
    labels = {"sosa-ssn-2017": "SOSA/SSN 2017", "ssn-xg": "The SSN-XG ontology (2011)", "ssn-2023": "The 2023 Edition",
              "mixed": "Terms of several versions", "unknown": "Version not shown by the text"}
    for v, label in labels.items():
        add(g, f"hyp-ver-{v}", label, "hyp-users", ["version", v])
    g = "Modules and terms"
    for mod in cb["modules"]["values"]:
        m = mean("modules", mod)
        m = m if mod.startswith("2023") else m.split(":")[0]
        add(g, f"hyp-mod-{mod}", m[0].upper() + m[1:], "hyp-users", ["modules", mod], "Modules")
    for k in range(1, 16):
        m = re.fullmatch(r"\\texttt\{([^}]*)\}", printed.get(f"hyp-term-{k}-name", ""))
        if m:
            add(g, f"hyp-term-{k}", f"Use {m.group(1)}", "hyp-users", None, "The most used terms")
    g = "Results and datatypes"
    for x in cb["result_pattern"]["values"]:
        if x != "unknown":
            add(g, f"hyp-rp-{x}", mean("result_pattern", x)[0].upper() + mean("result_pattern", x)[1:], "hyp-users",
                ["result_pattern", x], "How results are represented")
    for x in cb["value_properties"]["values"]:
        add(g, f"hyp-vp-{x}", mean("value_properties", x)[0].upper() + mean("value_properties", x)[1:], "hyp-users",
            ["value_properties", x], "Properties attached to values")
    sub = "Values of sosa:hasSimpleResult written in the full texts"
    add(g, "use-simple-shown", "Full texts that show a value of sosa:hasSimpleResult", None, None, sub)
    add(g, "use-simple-xsd", "… typed with an XSD datatype", "use-simple-shown", None, sub)
    add(g, "use-simple-cdt", "… typed with a custom datatype (cdt:)", "use-simple-shown", None, sub)
    add(g, "use-simple-ucum", "… typed cdt:ucum", "use-simple-shown", ["simple_forms", "cdt:ucum"], sub)
    add(g, "use-simple-untyped", "… with no datatype (a plain string or a bare number)", "use-simple-shown", None, sub)
    g = "Modelling patterns"
    add(g, "hyp-pat-coded", "Works coded for their modelling patterns, from excerpts")
    for q, (label, _, values) in PATTERNS.items():
        if q not in pc.get("questions", {}):
            continue
        qk = q.replace("_", "-")
        add(g, f"hyp-pat-{qk}-shown", "Works whose excerpts show it", "hyp-pat-coded", None, label)
        for v in values:
            if v != "not-shown" and v in pc["questions"][q]["works"]:
                add(g, f"hyp-pat-{qk}-{slug(v)}", values[v], f"hyp-pat-{qk}-shown", [f"pattern-{q}", v], label)
    g = "Names and errors"
    sub = "Prefixed names written in the full texts (found by script)"
    add(g, "use-writers", "Full texts that write prefixed names of SOSA/SSN", None, None, sub)
    add(g, "use-name-error-works", "… with at least one wrong name", "use-writers", None, sub)
    hist = tomllib.loads((ROOT / "protocol/namespace-history.toml").read_text(encoding="utf-8"))
    decided = hist.get("decision", {}).get("all_terms_in_sosa", "")
    short_names = {
        "ok-2017": "A 2017 name, in its namespace", "ok-xg": "An SSN-XG name, in its namespace",
        "ok-xg (no namespace shown)": "An SSN-XG name written ssn:, no namespace shown",
        "new-2023": "A 2023 term written sosa:", "new-2023 (year it entered sosa:)": "A 2023 term, in the year it entered sosa:",
        "new-2023 (before it existed in sosa:)": "A 2023 term written sosa: before it existed",
        "ns-ssn-term-as-sosa (before the decision)": f"An ssn: term written sosa:, before the decision of {decided}",
        "ns-ssn-term-as-sosa (year of the decision)": "An ssn: term written sosa:, in the year of the decision",
        "ns-ssn-term-as-sosa (after the decision)": "An ssn: term written sosa:, after the decision",
        "ns-system-term-as-sosa (never in sosa:)": "An SSN System term written sosa:",
        "ns-sosa-term-as-ssn": "A SOSA term written ssn:", "ns-system-term-as-ssn": "An SSN System term written ssn:",
        "ns-sosa-term-as-system": "A SOSA term written with the SSN System prefix",
        "ns-xg-term-as-sosa": "An SSN-XG term written sosa:", "ns-ssn-ext-prefix": "A term of the Extensions written ssn-ext:",
        "case": "A declared name with another case", "plural": "A declared name in the plural", "misspelt": "A misspelt name",
        "undeclared": "A name that no version declares",
        "individual minted in the namespace": "An individual minted in a SOSA/SSN namespace",
        "namespace written with # for /": "The namespace written with # for /"}
    for k, d in name_classes(decided).items():
        add(g, f"use-names-{slug(k)}", short_names.get(k, d), "use-writers", ["names", k], sub)
    sub = "Errors coded by the language model"
    add(g, "hyp-err-works", "Works that use SOSA/SSN with at least one error", "hyp-users", None, sub)
    for code in cb["errors"]["fields"]["code"]:
        add(g, f"hyp-err-{code}", mean("errors", code)[0].upper() + mean("errors", code)[1:], "hyp-users", ["errors", code], sub)
    return K


def short(text, n=80):
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


def short_term(u):
    for p, ns in TERM_PREFIX:
        if u.startswith(ns):
            return f"{p}:{u[len(ns):]}"
    return u


# labels of the classes and properties of other vocabularies, for browsing (Sparklis lists the
# declared classes and properties first); the others get their local name in words
TERM_LABELS = {
    "fabio:JournalArticle": "journal article", "fabio:ConferencePaper": "conference paper", "fabio:BookChapter": "book chapter",
    "fabio:Thesis": "thesis", "fabio:Preprint": "preprint", "fabio:ReviewArticle": "review article", "fabio:Book": "book",
    "fabio:DataPaper": "data paper", "fabio:Report": "report", "fabio:Editorial": "editorial", "fabio:Article": "article",
    "fabio:Expression": "work", "cito:Citation": "citation of SOSA/SSN", "mod:SemanticArtefact": "semantic artefact",
    "oa:TextQuoteSelector": "quotation", "dcat:Dataset": "dataset", "prov:SoftwareAgent": "coder (software agent)",
    "schema:SoftwareSourceCode": "software", "prov:Entity": "other artefact", "foaf:Person": "person",
    "foaf:Organization": "publisher", "owl:Class": "class", "rdf:Property": "property",
    "dcterms:title": "title", "dcterms:creator": "author", "fabio:hasPublicationYear": "publication year",
    "prism:doi": "DOI", "owl:sameAs": "same as", "frbr:partOf": "venue", "dcterms:publisher": "publisher",
    "foaf:name": "name", "cito:cites": "cites", "cito:hasCitingEntity": "citing work", "cito:hasCitedEntity": "cited version",
    "cito:hasCitationCharacterization": "citation characterisation", "prov:wasAttributedTo": "coder",
    "rdfs:isDefinedBy": "declaring version", "owl:deprecated": "deprecated", "mod:specializes": "version of",
    "mod:URI": "namespace", "mod:reliesOn": "relies on", "oa:exact": "quoted text", "dcterms:license": "licence",
    "dcterms:modified": "modified", "dcterms:description": "description", "rdfs:comment": "comment",
}


def declare_terms(g):
    """Declares, with a label, every class and property the graph uses and does not declare."""
    classes, props = set(), set()
    for line in g.lines:
        s_, p_, o_ = line[:-2].split(" ", 2)
        if p_ == "a":
            classes.add(o_)
        elif p_ not in ("rdfs:label",):
            props.add(p_)
    have = {line.split(" ", 1)[0] for line in g.lines if " a owl:Class ." in line or " a rdf:Property ." in line}
    words = lambda t: re.sub(r"(?<=[a-z])(?=[A-Z])", " ", t.split(":", 1)[-1]).lower()   # noqa: E731
    for c in sorted(classes - have - {"owl:Class", "rdf:Property"}):
        g.add(c, "a", "owl:Class")
        g.label(c, TERM_LABELS.get(c, words(c)))
    for q in sorted(props - have):
        g.add(q, "a", "rdf:Property")
        g.label(q, TERM_LABELS.get(q, words(q)))


def vocabulary(g, questions):
    """The small vocabulary of the observatory (slr:), with labels and comments, and the agents."""
    classes = {"Coding": ("coding", "An answer of the language model to one question of the codebook, about one work."),
               "PatternCoding": ("pattern coding", "An answer of an agent to one question of the codebook of modelling patterns, about one work.")}
    props = {
        "about": ("about", "The work a coding is about."), "question": ("question", "The question a coding answers."),
        "value": ("value", "A value of the answer."), "basis": ("coded from", "What the coder read: the full text or the abstract."),
        "evidence": ("evidence", "A passage of the work quoted as evidence."),
        "stratum": ("stratum", "The stratum of the work, A to D."), "seedRole": ("seed role", "Why a seed is a seed: core, lineage or variant."),
        "seedKey": ("seed key", "The key of a seed."), "fullTextHeld": ("full text held", "Whether the full text of the work is held."),
        "usesTerm": ("uses term", "A SOSA/SSN term the work uses, as coded by the language model."),
        "nameClass": ("name class", "The class of a prefixed name of SOSA/SSN the full text writes (found by script)."),
        "simpleResultForm": ("simple-result form", "The form of a value of sosa:hasSimpleResult the full text writes (found by script)."),
        "publishes": ("publishes", "An artefact the work publishes."), "artefactKind": ("artefact kind", "The kind of an artefact."),
        "engagement": ("engagement", "The engagement of a citation of SOSA/SSN, E0 to E5."),
    }
    for k, (label, comment) in classes.items():
        g.add(f"slr:{k}", "a", "owl:Class")
        g.label(f"slr:{k}", label)
        g.add(f"slr:{k}", "rdfs:comment", lit(comment, lang="en"))
    for k, (label, comment) in props.items():
        g.add(f"slr:{k}", "a", "rdf:Property")
        g.label(f"slr:{k}", label)
        g.add(f"slr:{k}", "rdfs:comment", lit(comment, lang="en"))
    for q in questions:
        g.label(f"slr:q-{q['id']}", q["id"].replace("_", " "))
        g.add(f"slr:q-{q['id']}", "rdfs:comment", lit(q["label"], lang="en"))
        if q["id"] == "engagement":
            for v, m in q["meaning"].items():
                g.label(f"slr:{v}", f"{v} {m.split(':')[0]}")
                g.add(f"slr:{v}", "rdfs:comment", lit(m, lang="en"))
    for q, (label, comment, _) in PATTERNS.items():
        g.label(f"slr:p-{q}", label.lower())
        g.add(f"slr:p-{q}", "rdfs:comment", lit(comment, lang="en"))
    g.label("slr:p-other", "other idioms")
    for k, name in MODELS.items():
        g.add(f"kg:agent/{k}", "a", "prov:SoftwareAgent")
        g.label(f"kg:agent/{k}", name)


def method(rows, seeds, text_seeds, questions):
    """explorer/data/method.json: the glossary of every code the application shows, with its
    definition (from the codebooks and the scripts), and the facts the methodology page states."""
    cb = {q["id"]: q for q in questions}
    hist = tomllib.loads((ROOT / "protocol/namespace-history.toml").read_text(encoding="utf-8"))
    decided = hist.get("decision", {}).get("all_terms_in_sosa", "")
    seen = collections.defaultdict(set)
    for r in rows:
        for k in ("names", "simple_results", "domain", "result_pattern", "value_properties", "errors", "modules"):
            v = r.get(k)
            seen[k] |= set(v if isinstance(v, list) else [v] if v else [])
        for q, v in (r.get("patterns") or {}).items():
            seen["pattern-" + q] |= set(v)

    def from_codebook(q, title, intro, extra=()):
        meaning = cb[q].get("meaning", {})
        values = list(cb[q].get("values") or cb[q].get("fields", {}).get("code") or []) + list(extra)
        return {"id": {"version_used": "version"}.get(q, q), "title": title, "intro": intro, "source": "protocol/codebook.toml",
                "entries": [{"code": v, "def": meaning.get(v, v)} for v in values]}
    G = []
    G.append({"id": "strata", "title": "Strata", "source": "scripts/strata.py",
              "intro": "Every candidate work is in one stratum, from the seeds it cites and its year.",
              "entries": [{"code": k, "def": f"The work {v}."} for k, v in STRATA.items()]})
    G.append({"id": "seeds", "title": "Seeds", "source": "protocol/seeds.toml",
              "intro": "The publications on SOSA/SSN whose citing works are collected (core: the publications that describe "
                       "SOSA/SSN; lineage: the earlier SSN and its patterns; variant: another record of a core publication), "
                       "and the text seeds, which no citation index holds and which are found by their names in the full texts.",
              "entries": [{"code": s["key"], "def": f"{s['title']} ({s['year']}; {s['role']})"} for s in seeds]
              + [{"code": s["key"], "def": f"{s['title']} ({s['year']}; text seed, found by {', '.join(s['strings'][:2])}…)"}
                 for s in text_seeds]})
    G.append({"id": "coding", "title": "Coders and sources of the codes", "source": "explorer/data/works.json",
              "intro": "Who made the codes, and from what.",
              "entries": [{"code": "claude-sonnet-5-5", "def": "Claude Sonnet 5.5, a language model: it coded every work."},
                          {"code": "claude-opus-5-5", "def": "Claude Opus 5.5, a language model: it coded a subset of the works; "
                                                            "where it did, its answers are the ones used."},
                          {"code": "claude-opus-5-5-agent", "def": "Claude Opus 5.5 agents: they coded the modelling patterns, from excerpts of the full texts."},
                          {"code": "full text", "def": "Coded from the full text of the work, without its bibliography."},
                          {"code": "abstract", "def": "Coded from the abstract only: no full text could be obtained."}]})
    G.append(from_codebook("engagement", "Engagement", "How deeply a work engages with SOSA/SSN: one value, the deepest that applies."))
    G[-1]["entries"].append({"code": "unknown", "def": "The text does not settle it."})
    G.append(from_codebook("version_used", "Version used", "The version of SOSA/SSN a work uses, as namespace IRIs and term names show it "
                                                        "(asked for E3 to E5)."))
    G.append(from_codebook("modules", "Modules", "The modules of SOSA/SSN a work uses (several values, asked for E3 to E5)."))
    G.append(from_codebook("result_pattern", "Result patterns", "How a work represents the results of observations (several values)."))
    G.append(from_codebook("value_properties", "Value properties", "The properties a work attaches to values (several values)."))
    G[-1]["entries"].append({"code": "unknown", "def": "The text does not show it."})
    G.append(from_codebook("errors", "Error codes", "Errors in the use of SOSA/SSN, coded by the language model: syntactic (S), "
                                                   "semantic (M) and structural (G)."))
    G.append({"id": "domain", "title": "Domains", "source": "protocol/codebook.toml",
              "intro": "The application domain, from a closed, coarse list fixed before coding (asked for E2 to E5).",
              "entries": [{"code": v, "def": f"Application domain: {v}."} for v in cb["domain"]["values"]]})
    nc = name_classes(decided)
    G.append({"id": "names", "title": "Name classes (found by script)", "source": "scripts/usage_patterns.py",
              "intro": "Each prefixed name of SOSA/SSN a full text writes (sosa:System, ssn:Observation…) is classified by a "
                       "script against the terms of SSN-XG, of the 2017 Recommendation and of the 2023 Edition, knowing the "
                       f"namespaces the work declares and the dates at which terms entered sosa: (the Working Group decided "
                       f"on {decided} that every term goes into sosa:; protocol/namespace-history.toml). S1 to S3 are the "
                       "matching error codes.",
              "entries": [{"code": k, "def": d} for k, d in nc.items()]})
    forms = sorted(seen["simple_results"])
    G.append({"id": "simple_forms", "title": "Simple-result forms (found by script)", "source": "scripts/usage_patterns.py",
              "intro": "The form of each value that follows sosa:hasSimpleResult in a full text (Turtle, N-Triples, JSON-LD, "
                       "RDF/XML, a rule or a figure caption). A work counts once per form it shows.",
              "entries": [{"code": k, "def": simple_form(k)} for k in forms]})
    for q, (label, comment, values) in PATTERNS.items():
        G.append({"id": f"pattern-{q}", "title": f"Modelling pattern: {label}", "source": "protocol/patterns-codebook.md",
                  "intro": comment, "entries": [{"code": v, "def": d} for v, d in values.items()]})
    missing = []
    for grp in G:
        key = {"names": "names", "simple_forms": "simple_results", "domain": "domain", "result_pattern": "result_pattern",
               "value_properties": "value_properties", "errors": "errors", "modules": "modules"}.get(grp["id"], grp["id"])
        have = {e["code"] for e in grp["entries"]}
        missing += [f"{grp['id']}: {v}" for v in sorted(seen.get(key, set()) - have)]
    if missing:
        print("method.json: codes without a definition:", "; ".join(missing), file=sys.stderr)
    pc = json.loads((ROOT / "results/pattern-coding.json").read_text(encoding="utf-8")) \
        if (ROOT / "results/pattern-coding.json").exists() else {}
    ag = pc.get("agreement") or {}
    kappas = [v["kappa"] for v in ag.values() if v.get("kappa") is not None]
    facts = {"decision_all_terms_in_sosa": decided,
             "patterns": {"coded": pc.get("works_coded"), "quotes": pc.get("quotes"), "quotes_found": pc.get("quotes_found"),
                          "second_coder_works": max((v["n"] for v in ag.values()), default=None),
                          "kappa_min": round(min(kappas), 2) if kappas else None,
                          "kappa_max": round(max(kappas), 2) if kappas else None,
                          "questions": len(ag)}}
    (OUT / "method.json").write_text(json.dumps({"generated_by": "slr/scripts/build_kg.py", "glossary": G, "facts": facts},
                                                ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main(argv=None):
    """Writes explorer/data; with --public DIR, a copy for publication in DIR without the
    quotations of the works (Maxime, 2026-11-14: the public explorer has no quotations)."""
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--public", help="output folder of the public version (no quotations)")
    args = ap.parse_args(argv)
    global OUT
    quotes = not args.public
    if args.public:
        OUT = pathlib.Path(args.public).resolve()
    import hypothetical_findings as hf
    import model_code as mc
    seeds = load_seeds()
    role = {s["key"]: s["role"] for s in seeds}
    seed_iri = {s["key"]: f"https://openalex.org/{s['openalex']}" for s in seeds}
    text_seeds = tomllib.loads((ROOT / "protocol/seeds.toml").read_text(encoding="utf-8")).get("text_seed", [])
    corpus = {w["openalex"]: w for w in load_corpus()}
    with gzip.open(ROOT / "corpus/stratum-d-candidates.jsonl.gz", "rt", encoding="utf-8") as f:
        dcands = {w["openalex"]: w for w in map(json.loads, f)}
    its = hf.items()
    cites = {}
    for line in open(ROOT / "screening/citations.jsonl", encoding="utf-8"):
        c = json.loads(line)
        cites[c["item"]] = c
    answers, not_work, source = hf.ladder_answers()
    # quotations of the strongest model (the ladder keeps values only)
    questions = mc.codebook()
    cfg = mc.config()
    evidence = collections.defaultdict(dict)
    for line in open(ROOT / "screening/recommendations.jsonl", encoding="utf-8"):
        r = json.loads(line)
        if r.get("source") == "model":
            evidence[r["item"]][r["question"]] = {"evidence": listval(r.get("evidence")), "justification": r.get("justification", "")}
    for name in ("sonnet", "opus"):
        mid = cfg["checks"][name]["model"]["id"]
        for item, a in mc.answers_of(mid, questions).items():
            if source.get(item) == mid:
                for q in questions:
                    if q["id"] in a:
                        evidence[item][q["id"]] = {"evidence": a[q["id"]].get("evidence", []),
                                                   "justification": a[q["id"]].get("justification", "")}
    up = json.loads((ROOT / "results/usage-patterns.json").read_text(encoding="utf-8"))
    names_by_work = collections.defaultdict(list)
    for k, v in up["names"]["by_class"].items():
        for x in v["list"]:
            names_by_work[x["item"]].append(k)
    simple_by_work = collections.defaultdict(list)
    for k, v in up["simple"]["by_form"].items():
        for x in v["list"]:
            simple_by_work[x["item"]].append(k)
    pc_path = ROOT / "results/pattern-coding.json"
    patterns = {}
    if pc_path.exists():
        pc = json.loads(pc_path.read_text(encoding="utf-8"))
        stamp = pc["stamp"]
        for p in sorted(ROOT.glob(f"raw/{stamp}-patterns-coded-*.jsonl")):
            for line in open(p, encoding="utf-8"):
                if line.strip():
                    r = json.loads(line)
                    patterns[r["item"]] = r
    ts = json.loads((ROOT / "results/text-seeds.json").read_text(encoding="utf-8"))
    text_cites = collections.defaultdict(list)
    for key, v in ts["seeds"].items():
        for item in v["works"]:
            text_cites[item].append(key)
    flagged = flagged_works()
    with open(ROOT / "results/terms.csv", encoding="utf-8", newline="") as f:
        declared = {r["term"] for r in csv.DictReader(f)}

    # the population: every candidate of A-C, stratum D, and every item with a full text
    works = {}
    for oid, w in list(corpus.items()) + [(k, v) for k, v in dcands.items() if k not in corpus]:
        works[f"openalex:{oid}"] = {"meta": w, "stratum": stratum(w, role) if oid in corpus else "D"}
    by_doi = {(r["meta"].get("doi") or "").lower(): k for k, r in works.items() if r["meta"].get("doi")}
    alias = {}   # the item of a full text -> the work it is (an S2ORC text of an OpenAlex work)
    for item, it in its.items():
        if item in works:
            continue
        k = by_doi.get((it.get("doi") or "").lower()) if it.get("doi") else None
        if k:
            alias[k] = item
        else:
            works[item] = {"meta": {}, "stratum": it.get("stratum")}
    g = Graph()
    rows = []
    today = _dt.date.today().isoformat()
    vocabulary(g, questions)
    g.add("kg:dataset", "a", "dcat:Dataset")
    g.add("kg:dataset", "dcterms:title", lit(f"{TITLE}: knowledge graph", lang="en"))
    g.label("kg:dataset", f"{TITLE}: knowledge graph")
    g.add("kg:dataset", "dcterms:description", lit(
        "The works that cite SOSA/SSN or write its names, with what a language model, agents and scripts "
        "found of their use of SOSA/SSN" + ("" if quotes else "; without the quotations of the works") + ".", lang="en"))
    g.add("kg:dataset", "dcterms:license", iri(LICENSE))
    g.add("kg:dataset", "dcterms:modified", lit(today, "xsd:date"))
    g.add("kg:artefact/sosa-ssn", "a", "mod:SemanticArtefact")
    g.add("kg:artefact/sosa-ssn", "dcterms:title", lit("The Semantic Sensor Network ontology and SOSA, all versions", lang="en"))
    g.label("kg:artefact/sosa-ssn", "SOSA/SSN, all versions")
    for vkey in VERSIONS:
        g.add(f"kg:artefact/{vkey}", "mod:specializes", "kg:artefact/sosa-ssn")
    for vkey, (title, ns) in VERSIONS.items():
        a = f"kg:artefact/{vkey}"
        g.add(a, "a", "mod:SemanticArtefact")
        g.add(a, "dcterms:title", lit(title, lang="en"))
        g.label(a, title)
        g.add(a, "mod:URI", lit(ns, "xsd:anyURI"))
    for s in seeds:
        g.add(iri(seed_iri[s["key"]]), "a", "fabio:Expression")
        g.add(iri(seed_iri[s["key"]]), "dcterms:title", lit(s["title"]))
        g.label(iri(seed_iri[s["key"]]), s["title"])
        g.add(iri(seed_iri[s["key"]]), "slr:seedRole", lit(s["role"]))
        g.add(iri(seed_iri[s["key"]]), "slr:seedKey", lit(s["key"]))
    for s in text_seeds:
        g.add(iri(s["url"]), "a", "fabio:Expression")
        g.add(iri(s["url"]), "dcterms:title", lit(s["title"]))
        g.label(iri(s["url"]), s["title"])
        g.add(iri(s["url"]), "slr:seedKey", lit(s["key"]))
    with open(ROOT / "results/terms.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            g.add(iri(r["term"]), "rdfs:isDefinedBy", f"kg:artefact/{r['version']}")
            g.label(iri(r["term"]), short_term(r["term"]))
            if r["deprecated"]:
                g.add(iri(r["term"]), "owl:deprecated", lit("true", "xsd:boolean"))

    for item, rec in sorted(works.items()):
        w, c = rec["meta"], cites.get(item, {})
        code_item = alias.get(item, item)    # the item that holds the full text and the codes
        it = its.get(code_item, {})
        s = iri(work_iri(item))
        title = w.get("title") or c.get("title") or it.get("title") or ""
        year = w.get("year") or c.get("year")
        typ = w.get("type") or c.get("type") or ""
        authors = listval(w.get("authors")) or c.get("authors") or []
        doi = (w.get("doi") or c.get("doi") or it.get("doi") or "").lower() or None
        seeds_cited = listval(w.get("seeds"))
        a = answers.get(code_item, {})

        def val(q):
            r = a.get(q)
            return r.get("value") if r else None
        eng = val("engagement")
        terms = listval(val("terms"))
        term_iris = sorted({u for u in (hf.term_iri(t, val("version_used"), declared) for t in terms) if u})
        row = {"id": item, "title": title, "year": int(year) if str(year or "").isdigit() else None,
               "type": typ, "authors": authors[:12], "venue": w.get("venue") or c.get("venue"),
               "publisher": w.get("publisher") or c.get("publisher"), "doi": doi, "stratum": rec["stratum"],
               "seeds": seeds_cited, "text_seeds": text_cites.get(code_item, []),
               "countries": listval(w.get("countries")), "flagged_venue": item[9:] in flagged,
               "fulltext": code_item in its and its[code_item].get("source") in ("s2orc", "oa-pdf"), "text_item": code_item if code_item in its else None,
               "not_the_work": code_item in not_work, "coded_by": source.get(code_item) if a else None,
               "basis": (a.get("engagement") or {}).get("basis") if a else None,
               "engagement": eng, "engagement_uncertain": bool((a.get("engagement") or {}).get("uncertain")) and
               str((a.get("engagement") or {}).get("uncertain")) not in ("False", "false"),
               "version_used": val("version_used"), "modules": listval(val("modules")),
               "terms": terms, "term_iris": term_iris, "result_pattern": listval(val("result_pattern")),
               "value_properties": listval(val("value_properties")), "domain": val("domain"),
               "subdomain": val("subdomain"), "companions": val("companions"), "gaps": val("gaps"),
               "errors": sorted({e["code"] for e in entry_codes(a.get("errors"), "code")}),
               "names": sorted(set(names_by_work.get(code_item, []))), "simple_results": sorted(set(simple_by_work.get(code_item, []))),
               "patterns": {q: v.get("values", []) for q, v in (patterns.get(code_item, {}).get("answers") or {}).items()
                            if q != "other"}}
        rows.append(row)
        g.add(s, "a", "fabio:" + FABIO.get(typ, "Expression"))
        if title:
            g.add(s, "dcterms:title", lit(title))
        g.label(s, title or item)
        if row["year"]:
            g.add(s, "fabio:hasPublicationYear", lit(row["year"], "xsd:gYear"))
        if doi:
            g.add(s, "prism:doi", lit(doi))
            g.add(s, "owl:sameAs", iri("https://doi.org/" + doi))
        for n, au in enumerate(authors[:30]):
            g.add(s, "dcterms:creator", f"kg:person/{h(au)}")
            g.add(f"kg:person/{h(au)}", "a", "foaf:Person")
            g.add(f"kg:person/{h(au)}", "foaf:name", lit(au))
            g.label(f"kg:person/{h(au)}", au)
        if row["venue"]:
            v = f"kg:venue/{h(row['venue'])}"
            g.add(s, "frbr:partOf", v)
            g.add(v, "dcterms:title", lit(row["venue"]))
            g.label(v, row["venue"])
        if row["publisher"]:
            g.add(s, "dcterms:publisher", f"kg:publisher/{h(row['publisher'])}")
            g.add(f"kg:publisher/{h(row['publisher'])}", "a", "foaf:Organization")
            g.add(f"kg:publisher/{h(row['publisher'])}", "foaf:name", lit(row["publisher"]))
            g.label(f"kg:publisher/{h(row['publisher'])}", row["publisher"])
        g.add(s, "slr:stratum", lit(rec["stratum"] or "?"))
        for sk in seeds_cited:
            if sk in seed_iri:
                g.add(s, "cito:cites", iri(seed_iri[sk]))
        for sk in row["text_seeds"]:
            url = next(t["url"] for t in text_seeds if t["key"] == sk)
            g.add(s, "cito:cites", iri(url))
        g.add(s, "slr:fullTextHeld", lit(str(row["fulltext"]).lower(), "xsd:boolean"))
        if not a:
            continue
        model = f"kg:agent/{source.get(code_item) or 'model'}"
        # the relation to SOSA/SSN, as a CiTO citation act, coded by the model
        if eng in CITO:
            ca = f"kg:citation/{h(item, 'sosa-ssn')}"
            g.add(ca, "a", "cito:Citation")
            g.add(ca, "cito:hasCitingEntity", s)
            # the version used when the codes give one; otherwise the ontology as a whole, of
            # which the versions are mod:specializes (E0 to E2 have no version used)
            target = f"kg:artefact/{row['version_used']}" if row["version_used"] in VERSIONS else "kg:artefact/sosa-ssn"
            g.add(ca, "cito:hasCitedEntity", target)
            g.add(ca, "cito:hasCitationCharacterization", "cito:" + CITO[eng])
            g.add(ca, "slr:engagement", f"slr:{eng}")
            g.add(ca, "prov:wasAttributedTo", model)
            g.label(ca, f"{eng} citation of SOSA/SSN by {short(title or item)}")
        for q, r in a.items():
            if q in ("text_is_the_work",):
                continue
            node = f"kg:coding/{h(item, q)}"
            g.add(node, "a", "slr:Coding")
            g.add(node, "slr:about", s)
            g.add(node, "slr:question", f"slr:q-{q}")
            vals = [v for v in (listval(r.get("value")) if q not in ("subdomain", "companions", "gaps") else [r.get("value")])
                    if v not in (None, "")]
            for v in vals:
                g.add(node, "slr:value", lit(v))
            g.label(node, f"{q.replace('_', ' ')}: {short(', '.join(map(str, vals)) or 'none', 60)} ({short(title or item, 50)})")
            g.add(node, "prov:wasAttributedTo", model)
            g.add(node, "slr:basis", lit(r.get("basis") or "full text"))
            for qt in evidence.get(code_item, {}).get(q, {}).get("evidence", [])[:3]:
                sel = f"kg:quote/{h(item, q, qt)}"
                if not quotes:
                    continue
                g.add(node, "slr:evidence", sel)
                g.add(sel, "a", "oa:TextQuoteSelector")
                g.add(sel, "oa:exact", lit(qt))
        for t in term_iris:   # the IRI the term resolves to (hypothetical_findings.term_iri)
            g.add(s, "slr:usesTerm", iri(t))
            g.label(iri(t), short_term(t))
        for k in row["names"]:
            g.add(s, "slr:nameClass", lit(k))
        for k in row["simple_results"]:
            g.add(s, "slr:simpleResultForm", lit(k))
        for e in entry_codes(a.get("artefacts"), "url"):
            kind, url = (e.get("kind") or "").strip(), e["url"].strip()
            if not url.startswith("http"):
                continue
            art = iri(url)
            g.add(s, "slr:publishes", art)
            g.add(art, "a", ARTEFACT_TYPE.get(kind, "prov:Entity"))
            g.add(art, "slr:artefactKind", lit(kind))
            if kind in ("ontology", "alignment", "shacl-shapes", "design-pattern") and eng in ("E4", "E5"):
                g.add(art, "mod:reliesOn", target)
        for q, v in (patterns.get(code_item, {}).get("answers") or {}).items():
            node = f"kg:pattern/{h(item, q)}"
            g.add(node, "a", "slr:PatternCoding")
            g.add(node, "slr:about", s)
            g.add(node, "slr:question", f"slr:p-{q}")
            for x in v.get("values", []):
                g.add(node, "slr:value", lit(x))
            g.label(node, f"{PATTERNS.get(q, (q,))[0]}: {short(', '.join(v.get('values', [])) or 'none', 60)} ({short(title or item, 50)})")
            g.add(node, "prov:wasAttributedTo", "kg:agent/claude-opus-5-5-agent")
            for qt in v.get("quotes", [])[:2]:
                sel = f"kg:quote/{h(item, q, qt)}"
                if not quotes:
                    continue
                g.add(node, "slr:evidence", sel)
                g.add(sel, "a", "oa:TextQuoteSelector")
                g.add(sel, "oa:exact", lit(qt))
    declare_terms(g)
    OUT.mkdir(parents=True, exist_ok=True)
    g.write(OUT / "kg.ttl.gz")
    (OUT / "meta.json").write_text(json.dumps({
        "title": TITLE, "generated": _dt.datetime.now().isoformat(timespec="minutes"), "date": today,
        "quotations": quotes, "works": len(rows), "triples": len(g.lines),
        "license": LICENSE, "license_name": LICENSE_NAME, "base": BASE, "dataset": BASE + "dataset",
        "prefixes": PREFIXES}, indent=1) + "\n", encoding="utf-8")
    figures(rows, up, patterns)
    method(rows, seeds, text_seeds, questions)
    (OUT / "works.json").write_text(json.dumps({"generated_by": "slr/scripts/build_kg.py", "works": rows},
                                               ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    # results/kg.json: the size of the graph, for the papers (article_macros.py, kg-*); each
    # mode (full, public) updates its own keys
    kp = ROOT / "results/kg.json"
    k = json.loads(kp.read_text(encoding="utf-8")) if kp.exists() else {"macros": {}}
    figs = json.loads((OUT / "figures.json").read_text(encoding="utf-8"))["figures"]
    figs = figs.values() if isinstance(figs, dict) else figs
    key = sum(1 for f in figs if isinstance(f, dict) and f.get("group"))
    tag = "" if quotes else "public-"
    k["macros"].update({f"{tag}triples": f"{len(g.lines):,}", "works": f"{len(rows):,}",
                        "key-figures": f"{key:,}"})
    k["generated_by"] = "slr/scripts/build_kg.py"
    k["date"] = _dt.date.today().isoformat()
    kp.write_text(json.dumps(k, indent=1) + "\n", encoding="utf-8")
    print(f"{OUT}: {len(rows)} works, {len(g.lines)} triples")
    return 0


if __name__ == "__main__":
    sys.exit(main())
