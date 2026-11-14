#!/usr/bin/env python3
"""When each term of the 2023 Edition first appeared in the `sosa:` namespace of its RDF files.

    python3 -I scripts/namespace_history.py [--repo ../../sdw-sosa-ssn] [--rev gh-pages]
                                            # results/namespace-history.{md,json}

For every term that results/terms.csv gives in the `sosa:` namespace of the 2023 Edition,
the first commit of the revision's first-parent history whose RDF files
(`ssn/rdf/**/*.ttl`, `ssn/integrated/*.ttl`) contain `sosa:<term>` followed by a
non-name character (`git log -G`): the date from which a work could have read the name in
the editor's draft. The terms of the Extensions to SSN, which were in `sosa:` from 2018
(protocol/namespace-history.toml), and the 2017 terms keep their own dates. The clone is
read, never modified. Standard library and `git` only.
"""
import argparse
import csv
import json
import pathlib
import subprocess
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOSA = "http://www.w3.org/ns/sosa/"
IMPORT = "4bd6ca5a"   # "Original SSN work from swd repo", 2023-08-10: files imported from w3c/sdw


def first_commit(repo, rev, term):
    out = subprocess.run(["git", "-C", str(repo), "log", rev, "--first-parent", "--reverse", "--format=%h %cs",
                          "-G", rf"sosa:{term}([^A-Za-z0-9_]|$)", "--", "ssn/rdf", "ssn/integrated"],
                         capture_output=True, text=True, check=True).stdout.split("\n")
    return out[0].split() if out and out[0] else None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default=str(ROOT.parent.parent / "sdw-sosa-ssn"))
    ap.add_argument("--rev", default="gh-pages")
    ap.add_argument("--sdw", default=str(ROOT.parent.parent / "sdw"),
                    help="clone of w3c/sdw, for the terms the 2023 repository imported from it")
    args = ap.parse_args(argv)
    repo = pathlib.Path(args.repo)
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", args.rev], capture_output=True,
                          text=True, check=True).stdout.strip()
    hist = tomllib.loads((ROOT / "protocol/namespace-history.toml").read_text(encoding="utf-8"))
    with open(ROOT / "results/terms.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    sosa17 = {r["term"][len(SOSA):] for r in rows if r["version"] == "sosa-ssn-2017" and r["namespace"] == SOSA}
    sosa23 = sorted({r["term"][len(SOSA):] for r in rows if r["version"] == "ssn-2023" and r["namespace"] == SOSA})
    ext = set(hist["introduced_by_ssn_ext"]["terms"])
    out = {"repo_rev": f"{args.rev} {head}", "terms": {}}
    L = ["# When the terms of the 2023 Edition entered `sosa:`", "",
         f"Written by `scripts/namespace_history.py` from `{args.rev}` at `{head}` of w3c/sdw-sosa-ssn. "
         f"Decision that every term goes into `sosa:`: {hist['decision']['all_terms_in_sosa']} (PR #97).", "",
         "| Term | In sosa: since | Source |", "|---|---|---|"]
    for t in sosa23:
        if t in sosa17:
            continue
        if t in ext:
            date, src = hist["introduced_by_ssn_ext"]["date"], "Extensions to SSN, FPWD"
        elif t in hist.get("moved_to_sosa", {}):
            date, src = hist["moved_to_sosa"][t], "protocol/namespace-history.toml"
        else:
            fc = first_commit(repo, args.rev, t)
            date, src = (fc[1], f"commit {fc[0]}") if fc else (None, "not found in the RDF files")
            if fc and fc[0] == IMPORT:  # imported from w3c/sdw: its own history is older
                old = subprocess.run(["git", "-C", args.sdw, "log", "--all", "--reverse", "--format=%h %cs",
                                      "-G", rf"sosa:{t}([^A-Za-z0-9_]|$)", "--", "ssn"],
                                     capture_output=True, text=True).stdout.split("\n")
                if old and old[0]:
                    date, src = old[0].split()[1], f"w3c/sdw commit {old[0].split()[0]} (a draft before the 2023 repository)"
        out["terms"][t] = {"date": date, "source": src}
        L.append(f"| `sosa:{t}` | {date or '—'} | {src} |")
    (ROOT / "results/namespace-history.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (ROOT / "results/namespace-history.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(f"results/namespace-history.md: {len(out['terms'])} terms new in 2023, from {args.rev} {head}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
