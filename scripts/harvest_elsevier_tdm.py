#!/usr/bin/env python3
"""Full texts of the Elsevier candidates through the Elsevier text-mining API.

    python3 -I scripts/harvest_elsevier_tdm.py            # every Elsevier DOI still without a text
    python3 -I scripts/harvest_elsevier_tdm.py --limit 3  # a trial

The text-mining channel that Elsevier licenses to subscribers (dev.elsevier.com), instead of
downloads from ScienceDirect, which its terms forbid to robots. The pool: the DOIs 10.1016/
of results/closed-access.csv (closed access, no S2ORC text) and of results/oa-unretrieved.csv
(open access, the downloads refused by ScienceDirect). For each one, the entitlement API says
whether the school's subscription covers it (by the IP address, so the run must come from the
school's network or VPN); if so, the article is fetched as plain text.

The key is read from $ELSEVIER_API_KEY or from the line `Elsevier_API_Key: …` of
~/.secrets/keys.md (or `ELSEVIER_AI_KEY: …`), sent in the X-ELS-APIKey header and never written anywhere. An
institutional token, if the library gives one, is read the same way (`Elsevier_Insttoken`).

Writes raw/<stamp>-oa-fulltext-manifest.json (`pass`: `elsevier tdm`, same form as the other
passes, so that scripts/build_items.py reads the texts) and the texts in
fulltext/oa-pdf/<stamp>/ (not versioned). Standard library only.
"""
import argparse
import csv
import datetime as dt
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from strata import ROOT  # noqa: E402

API = "https://api.elsevier.com/content/article"


def secret(env, *names):
    if os.environ.get(env):
        return os.environ[env]
    keys = pathlib.Path.home() / ".secrets" / "keys.md"
    if keys.exists():
        for line in keys.read_text(encoding="utf-8").splitlines():
            k, _, value = line.partition(":")
            if k.strip().strip("-* `") in names and value.strip():
                return value.strip().strip("`")
    return None


def call(url, headers, tries=4):
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=90) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt + 1 < tries:
                time.sleep(10 * 2 ** attempt)
                continue
            return e.code, b""
        except OSError as e:
            if attempt + 1 == tries:
                return None, repr(e)[:200].encode()
            time.sleep(5)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--pause", type=float, default=1.0)
    args = ap.parse_args(argv)
    key = secret("ELSEVIER_API_KEY", "Elsevier_API_Key", "ELSEVIER_AI_KEY")
    if not key:
        sys.exit("no Elsevier API key: create one at https://dev.elsevier.com (signed in with the school "
                 "account) and add the line `Elsevier_API_Key: …` to ~/.secrets/keys.md")
    headers = {"X-ELS-APIKey": key, "User-Agent": "sosa-ssn-slr-harvest"}
    token = secret("ELSEVIER_INSTTOKEN", "Elsevier_Insttoken")
    if token:
        headers["X-ELS-Insttoken"] = token

    pool = {}
    for name, origin in (("closed-access.csv", "closed"), ("oa-unretrieved.csv", "oa refused")):
        with open(ROOT / "results" / name, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["doi"].lower().startswith("10.1016/"):
                    pool.setdefault(row["openalex"], {"openalex": row["openalex"], "doi": row["doi"],
                                                      "stratum": row["stratum"], "origin": origin})
    pool = sorted(pool.values(), key=lambda w: w["openalex"])
    if args.limit:
        pool = pool[:args.limit]
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M")
    out = ROOT / f"fulltext/oa-pdf/{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    rows, outcomes = [], {}
    for n, w in enumerate(pool, 1):
        doi = urllib.parse.quote(w["doi"], safe="/")
        entry = {**w, "oa_status": "closed" if w["origin"] == "closed" else "open", "tried": []}
        status, body = call(f"{API}/entitlement/doi/{doi}?httpAccept=application/json", headers)
        try:
            ent = json.loads(body)["entitlement-response"]["document-entitlement"]
            entitled = ent.get("entitled") in (True, "true")
        except (ValueError, KeyError, TypeError):
            entitled = None
        entry["tried"].append({"url": f"{API}/entitlement/doi/{w['doi']}", "status": status, "entitled": entitled})
        outcome = "not entitled" if entitled is False else "entitlement unknown"
        if entitled:
            status, body = call(f"{API}/doi/{doi}?httpAccept=text/plain", headers)
            text = body.decode("utf-8", errors="replace") if status == 200 else ""
            entry["tried"].append({"url": f"{API}/doi/{w['doi']}?httpAccept=text/plain", "status": status,
                                   "bytes": len(body or b"")})
            # an entitled answer carries the body; a few hundred words means only the abstract came back
            if len(text.split()) > 1500:
                (out / f"{w['openalex']}.txt").write_text(text, encoding="utf-8")
                outcome = "text"
            else:
                outcome = "abstract only" if status == 200 else "failed"
        entry["outcome"] = outcome
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
        rows.append(entry)
        time.sleep(args.pause)
        if n % 10 == 0:
            print(f"{n}/{len(pool)} {outcomes}", file=sys.stderr, flush=True)
    manifest = {"stamp": stamp, "pass": "elsevier tdm", "pool": len(pool), "done": len(rows),
                "complete": not args.limit, "insttoken_used": bool(token), "works": rows, "outcomes": outcomes}
    (ROOT / f"raw/{stamp}-oa-fulltext-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{stamp}: {outcomes}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
