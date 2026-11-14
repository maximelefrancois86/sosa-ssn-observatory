"""The candidate corpus and its strata, shared by the scripts of this directory.

The scripts run with `python3 -I`, which leaves this directory out of `sys.path`; they
import this module after adding their own directory explicitly.
"""
import gzip
import json
import pathlib
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent

STRATA = {
    "A": "A: cites a 2017+ seed",
    "B": "B: lineage seeds only, 2018+",
    "C": "C: lineage seeds only, before 2018",
}


def load_corpus():
    with gzip.open(ROOT / "corpus/openalex-candidates.jsonl.gz", "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def load_seeds():
    return tomllib.loads((ROOT / "protocol/seeds.toml").read_text(encoding="utf-8"))["seed"]


def seed_group(work, role):
    """'lineage only', 'lineage and 2017+' or '2017+ only', from the roles of the seeds cited."""
    roles = {role[s] for s in work["seeds"]}
    if roles <= {"lineage"}:
        return "lineage only"
    if "lineage" in roles:
        return "lineage and 2017+"
    return "2017+ only"


def stratum(work, role):
    """'A', 'B' or 'C' (pilotage review/101): A cites a 2017+ seed; B and C cite only the
    lineage, published from 2018 on (B) or before (C)."""
    if seed_group(work, role) != "lineage only":
        return "A"
    return "B" if (work["year"] or 0) >= 2018 else "C"


def wrong_texts():
    """(stamp, openalex) of the texts taken in for a work they are not
    (protocol/wrong-texts.toml): build_items.py skips them, and the work goes back to the
    download pages."""
    path = ROOT / "protocol/wrong-texts.toml"
    if not path.exists():
        return set()
    return {(t["run"], t["openalex"]) for t in tomllib.loads(path.read_text(encoding="utf-8")).get("text", [])}
