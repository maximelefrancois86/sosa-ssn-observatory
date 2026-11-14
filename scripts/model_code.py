#!/usr/bin/env python3
"""The coding of the works by a language model, as recommendations (pilotage review/105).

    python3 -I scripts/model_code.py prepare --set blind         # or --set all, --items ID…, --limit N, --dry-run, --again
    python3 -I scripts/model_code.py submit STAMP                # sends the batch (API key needed)
    python3 -I scripts/model_code.py fetch STAMP                 # state; results into raw/ once ended
    python3 -I scripts/model_code.py ingest                      # recommendations + results/model-coding.md
    python3 -I scripts/model_code.py prepare --model sonnet --set blind --sample 300   # a stronger model,
                                                                 # on a nested seeded part of a set
    python3 -I scripts/model_code.py compare                     # results/model-comparison.md: the models
                                                                 # against each other on the works they share
    python3 -I scripts/model_code.py budget                      # what each model cost this month

`prepare` builds one request per work: the system prompt (protocol/model-prompt.md, then
protocol/codebook.md, then the SOSA/SSN terms of each version from results/terms.csv),
and the body of the work without its bibliography (screening/bodies.jsonl.gz, written by
scripts/build_items.py). The answer is constrained by a JSON schema built from
protocol/codebook.toml: for each question a justification, verbatim quotations, then the
value. The requests go to screening/model/STAMP/ (full texts: not versioned); the manifest
raw/STAMP-model-manifest.json records the model, the parameters, the hashes of the system
prompt and of each body, and the cost estimated before the run. No network.

`submit` sends the requests to the Message Batches API (protocol/model.toml) and records the
batch in raw/STAMP-model-batch.json. `fetch` downloads the results, unchanged, into
raw/STAMP-model-results.jsonl.gz, once the batch has ended. Credentials: $ANTHROPIC_API_KEY
if set, otherwise the signed-in profile of the `ant` command (`ant auth print-credentials
--access-token`, a short-lived token asked for at each call); never written anywhere.

`ingest` reads every run fetched (the latest run wins for a work), checks each quotation
against the body (whitespace, case and hyphenation aside), and writes:
- screening/recommendations.jsonl: one line per (work, question), source "model", with the
  justification, the quotations and whether each was found; the lines of other sources are
  kept (scripts/recommend_script.py keeps these);
- results/model-coding.md and .json: what the model recommends, by stratum, the share of
  quotations found, its agreement with the script's E0 and E1, the tokens used and the cost.
These are recommendations, not results: a reader decides (protocol § 5). Only the runs of
the primary model ([model] of protocol/model.toml) become recommendations.

The stronger models of [checks] (`prepare --model sonnet|opus`) code a nested part of a set:
`--sample N` keeps the N first works in an order fixed by a seeded hash of each work, so the
part coded by one model contains the smaller part coded by another. `compare` measures the
agreement between the models on the works they share (`results/model-comparison.md`), the
first rungs of the ladder that ends with the readers' blind codes (pilotage review/105).

`submit` refuses a batch that would take the month's cost of its model over the ceiling of
[budget.monthly], or that would spend more than the account's credit left ([budget.credit],
all models together, since the date it was given): the cost of each run of the calendar month is measured from its usage once
fetched, and taken from its estimate before. Standard library only.
"""
import argparse
import collections
import csv
import datetime as dt
import gzip
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import tomllib
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from strata import ROOT  # noqa: E402

API = "https://api.anthropic.com/v1/messages/batches"
NOT_ASKED = "not-asked"
PREFIX = {"http://www.w3.org/ns/sosa/": "sosa:", "http://www.w3.org/ns/ssn/": "ssn:",
          "http://www.w3.org/ns/ssn/systems/": "ssn-system:", "http://purl.oclc.org/NET/ssnx/ssn#": "ssn:"}


def config(check=None):
    """protocol/model.toml, with [model] and [price] of a stronger model of [checks] if named."""
    cfg = tomllib.loads((ROOT / "protocol/model.toml").read_text(encoding="utf-8"))
    cfg["primary"] = cfg["model"]["id"]
    if check:
        cfg["model"], cfg["price"] = cfg["checks"][check]["model"], cfg["checks"][check]["price"]
    return cfg


def usage_cost(u, p):
    """Dollars of one answer from its usage, at the prices p of its run."""
    prompt = u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
    scale = p.get("input_long", p["input"]) / p["input"] if prompt > 100000 else 1  # the long-context rate card, when the price table has one
    return scale * (u.get("input_tokens", 0) * p["input"] + u.get("output_tokens", 0) * p["output"]
                    + u.get("cache_creation_input_tokens", 0) * p["cache_write"]
                    + u.get("cache_read_input_tokens", 0) * p["cache_read"]) / 1e6


def run_cost(stamp):
    """(dollars, measured): the cost of a run from the usage of its results once fetched, else
    the estimate of its manifest."""
    man = json.loads((ROOT / f"raw/{stamp}-model-manifest.json").read_text(encoding="utf-8"))
    res = ROOT / f"raw/{stamp}-model-results.jsonl.gz"
    if not res.exists():
        return man["estimate"]["dollars"], False
    total = 0.0
    with gzip.open(res, "rt", encoding="utf-8") as f:
        for r in map(json.loads, f):
            if r["result"]["type"] == "succeeded":
                u = {k: v for k, v in r["result"]["message"].get("usage", {}).items() if isinstance(v, int)}
                total += usage_cost(u, man["price"])
    return total, True


def month_spent(model_id, month=None):
    """Dollars of the runs of a model sent in a calendar month (YYYY-MM, the current one by default)."""
    month = month or dt.date.today().strftime("%Y-%m")
    total = 0.0
    for b in (ROOT / "raw").glob("*-model-batch.json"):
        stamp = b.name.split("-model-batch")[0]
        rec = json.loads(b.read_text(encoding="utf-8"))
        man = json.loads((ROOT / f"raw/{stamp}-model-manifest.json").read_text(encoding="utf-8"))
        if man["model"]["id"] == model_id and rec["submitted"][:7] == month:
            total += run_cost(stamp)[0]
    return total


def credit_left(cfg):
    """Dollars left of the account's credit ([budget.credit]): the credit given at `as_of`, less
    the runs of every model sent since; None when no credit is set."""
    c = cfg["budget"].get("credit")
    if not c:
        return None
    since = dt.datetime.fromisoformat(c["as_of"])
    spent = 0.0
    for b in (ROOT / "raw").glob("*-model-batch.json"):
        rec = json.loads(b.read_text(encoding="utf-8"))
        if dt.datetime.fromisoformat(rec["submitted"]) >= since:
            spent += run_cost(b.name.split("-model-batch")[0])[0]
    return c["dollars"] - spent


def cmd_budget(args):
    cfg = config()
    for model_id, cap in cfg["budget"]["monthly"].items():
        spent = month_spent(model_id)
        print(f"{model_id}: {spent:.2f} of {cap:.2f} dollars this month, {cap - spent:.2f} left")
    left = credit_left(cfg)
    if left is not None:
        print(f"account credit: {left:.2f} of {cfg['budget']['credit']['dollars']:.2f} dollars left "
              f"(given on {cfg['budget']['credit']['as_of']}, all models)")
    return 0


def codebook():
    return tomllib.loads((ROOT / "protocol/codebook.toml").read_text(encoding="utf-8"))["question"]


def term_lists():
    by = collections.defaultdict(list)
    with open(ROOT / "results/terms.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            ns = r["namespace"]
            name = PREFIX.get(ns, ns) + r["term"][len(ns):]
            # deprecation marked in the 2023 list only: SSN-XG is superseded as a whole, and a
            # term deprecated in 2023 is not an error in a work that uses 2017
            dep = r["deprecated"] and r["version"] == "ssn-2023"
            by[(r["version"], ns)].append(name + (" (deprecated in 2023)" if dep else ""))
    title = {"ssn-xg": "SSN-XG (2011)", "sosa-ssn-2017": "SOSA/SSN 2017", "ssn-2023": "SOSA/SSN 2023 Edition"}
    out = ["# The terms of each version\n",
           "Prefixed names, with the namespace of each list. In SSN-XG the prefix `ssn:` stands for "
           "`http://purl.oclc.org/NET/ssnx/ssn#`; in 2017 and 2023 for `http://www.w3.org/ns/ssn/`. "
           "A name absent from every list is declared by no version. SSN-XG as a whole is superseded by "
           "SOSA/SSN 2017; using it is not an error in itself.\n"]
    for (version, ns), names in sorted(by.items(), key=lambda kv: (list(title).index(kv[0][0]), kv[0][1])):
        out.append(f"## {title[version]}, namespace {ns}\n\n" + ", ".join(sorted(names)) + "\n")
    return "\n".join(out)


def allowed_values(questions):
    """The identifiers of the questions and their values, from codebook.toml: codebook.md
    names some values in prose only (the modules), and the answers must use the identifiers."""
    out = ["# The questions and their values\n",
           "Answer with these identifiers exactly, never with the prose of the codebook. `unknown` is "
           "allowed everywhere; `not-asked` when the condition of a question is false.\n"]
    for q in questions:
        when = q.get("when", {}).get("engagement")
        line = f"- `{q['id']}` ({q['kind']}): {q['label']}" + (f"; asked when engagement is {', '.join(when)}" if when else "")
        out.append(line)
        meanings = q.get("meaning") or next((x.get("meaning", {}) for x in questions if x["id"] == q.get("meaning_from")), {})
        for v in q.get("values", []):
            out.append(f"  - `{v}`" + (f": {meanings[v]}" if v in meanings else ""))
        for k, f in (q.get("fields") or {}).items():
            out.append(f"  - field `{k}`: " + (", ".join(f"`{x}`" for x in f) if isinstance(f, list) else f))
    return "\n".join(out)


def system_prompt(cfg):
    return "\n\n".join([(ROOT / cfg["model"]["prompt"]).read_text(encoding="utf-8").strip(),
                        (ROOT / "protocol/codebook.md").read_text(encoding="utf-8").strip(),
                        allowed_values(codebook()).strip(),
                        term_lists().strip()]) + "\n"


def schema(questions):
    """The answer: one entry per question of the codebook, justification and evidence first.

    One small object repeated, with every value as a list of strings: a schema with one
    object per question, typed values and enumerations is refused (400, "compiled grammar
    too large"). `answer()` gives the values their types and checks them against the
    codebook."""
    return {"type": "object", "additionalProperties": False,
            "required": ["text_is_the_work", "answers", "uncertain"],
            "properties": {
                "text_is_the_work": {"type": "string", "enum": ["yes", "no", "unsure"]},
                "answers": {"type": "array", "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["question", "justification", "evidence", "values"],
                    "properties": {"question": {"type": "string", "enum": [q["id"] for q in questions]},
                                   "justification": {"type": "string"},
                                   "evidence": {"type": "array", "items": {"type": "string"}},
                                   "values": {"type": "array", "items": {"type": "string"}}}}},
                "uncertain": {"type": "array", "items": {"type": "string"}}}}


def answer(raw, questions, problems):
    """The model's answer as {question: {justification, evidence, value}}, values typed by
    the codebook; a value outside the codebook is dropped and counted in `problems`."""
    given = {a["question"]: a for a in raw["answers"]}
    out = {"text_is_the_work": raw["text_is_the_work"], "uncertain": raw["uncertain"]}
    for q in questions:
        a = given.get(q["id"])
        if a is None:
            problems["question missing"] += 1
            a = {"justification": "", "evidence": [], "values": []}
        vals = [v.strip() for v in a["values"] if v.strip()]
        allowed = set(q.get("values", [])) | {"unknown"}
        if q["kind"] == "one":
            if not vals or vals[0] == NOT_ASKED:
                value = NOT_ASKED
            elif vals[0] in allowed:
                value = vals[0]
            else:
                problems[f"{q['id']}: value outside the codebook"] += 1
                value = NOT_ASKED
        elif q["kind"] == "many":
            value = [v for v in vals if v in allowed]
            if len(vals) - len(value) - vals.count(NOT_ASKED):
                problems[f"{q['id']}: value outside the codebook"] += len(vals) - len(value) - vals.count(NOT_ASKED)
        elif q["kind"] == "terms":
            value = [v for v in vals if v != NOT_ASKED]
        elif q["kind"] == "entries":
            value = []
            for v in vals:
                if v == NOT_ASKED:
                    continue
                parts = [x.strip() for x in v.split("|")]
                entry = {}
                for (k, kind), part in zip(q["fields"].items(), parts + [""] * len(q["fields"])):
                    entry[k] = [t.strip() for t in part.split(",") if t.strip()] if kind == "terms" else part
                    if isinstance(kind, list) and part not in kind:
                        problems[f"{q['id']}.{k}: value outside the codebook"] += 1
                value.append(entry)
        else:  # text
            value = "; ".join(v for v in vals if v != NOT_ASKED) or NOT_ASKED
        out[q["id"]] = {"justification": a["justification"], "evidence": a["evidence"], "value": value}
    return out


def custom_id(item):
    return re.sub(r"[^A-Za-z0-9_-]", "-", item)[:64]


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_items():
    return {it["item"]: it for it in map(json.loads, open(ROOT / "screening/items.jsonl", encoding="utf-8"))}


def load_bodies():
    with gzip.open(ROOT / "screening/bodies.jsonl.gz", "rt", encoding="utf-8") as f:
        return {r["item"]: r["body"] for r in map(json.loads, f)}


def abstract_works(items, bodies):
    """The candidates of strata A and B without a full text, with their OpenAlex abstract:
    coded from it (protocol § 4, `engagement_basis` = abstract), as items of their own."""
    from strata import load_corpus, load_seeds, stratum
    role = {x["key"]: x["role"] for x in load_seeds()}
    dois = {it["doi"] for it in items.values() if it.get("doi")}
    extra_items, extra_bodies = {}, {}
    for w in load_corpus():
        item = f"openalex:{w['openalex']}"
        st = stratum(w, role)
        if st not in ("A", "B") or item in bodies or (w.get("doi") or "").lower() in dois or not w.get("abstract"):
            continue
        extra_items[item] = {"item": item, "title": w["title"], "doi": (w.get("doi") or "").lower() or None,
                             "source": "abstract", "stratum": st, "passages": []}
        extra_bodies[item] = w["abstract"]
    return extra_items, extra_bodies


def cut(body, item, limit):
    """The body as sent: whole, or its first part and every passage when it is too long."""
    words = body.split()
    if len(words) <= limit:
        return body, "full text"
    head = " ".join(words[:30000])
    passages = "\n\n".join(f"[passage, section: {p['section'] or 'unknown'}]\n{p['text']}" for p in item["passages"])
    return (head + "\n\n[… the text is cut here; what follows are the passages of the rest that name SOSA/SSN …]\n\n"
            + passages), "first 30,000 words and passages"


def stamp_now():
    return dt.datetime.now().strftime("%Y-%m-%dT%H%M")


def cmd_prepare(args):
    cfg = config(args.model)
    questions = codebook()
    items, bodies = load_items(), load_bodies()
    if args.set == "abstracts":
        extra_items, extra_bodies = abstract_works(items, bodies)
        items.update(extra_items)
        bodies.update(extra_bodies)
    if args.items:
        chosen = args.items
    elif args.set in ("calibration", "blind"):
        blind = tomllib.loads((ROOT / "protocol/budget.toml").read_text(encoding="utf-8"))["budget"]["blind"]
        reasons = {"calibration"} if args.set == "calibration" else set(blind)
        last = {}  # the queue is append-only: the last line of an item gives its reason
        for q in map(json.loads, open(ROOT / "screening/queue.jsonl", encoding="utf-8")):
            last.setdefault(q["item"], {}).update(q)
        chosen = [i for i, q in last.items() if q["reason"] in reasons]
    elif args.set == "abstracts":
        chosen = sorted(extra_items)
    else:
        chosen = [i for i, it in items.items() if it["stratum"] in cfg["input"]["strata"]]
    chosen = [i for i in chosen if i in bodies]
    if args.sample:
        # a nested part: the same order for every model, the N first works of it; the works of
        # the blind sample come first (the readers' codes will be the reference for them), each
        # group in the order of a seeded hash
        blind_reasons = set(tomllib.loads((ROOT / "protocol/budget.toml").read_text(encoding="utf-8"))["budget"]["blind"])
        last = {}
        for q in map(json.loads, open(ROOT / "screening/queue.jsonl", encoding="utf-8")):
            last.setdefault(q["item"], {}).update(q)
        blind = {i for i, q in last.items() if q["reason"] in blind_reasons}
        chosen = sorted(chosen, key=lambda i: (i not in blind, sha(f"{args.seed}:{i}")))[:args.sample]
    system = system_prompt(cfg)
    if not args.again:
        # a work already sent with the same model, prompt and text is not sent again: new full
        # texts and top-ups of the queue are coded by a later run of the same command
        done = set()
        for m in (ROOT / "raw").glob("*-model-manifest.json"):
            man = json.loads(m.read_text(encoding="utf-8"))
            if (ROOT / f"raw/{man['stamp']}-model-batch.json").exists() and man["model"]["id"] == cfg["model"]["id"] \
                    and man["system_sha256"] == sha(system):
                done.update((w["item"], w["body_sha256"]) for w in man["works"])
        chosen = [i for i in chosen if (i, sha(bodies[i])) not in done]
    if not chosen:
        print("nothing to send: every work chosen was already sent with this model, prompt and text")
        return 0
    if args.limit:
        chosen = chosen[:args.limit]
    sch = schema(questions)
    stamp = stamp_now()
    while (ROOT / f"raw/{stamp}-model-manifest.json").exists():
        stamp += "b"
    out = ROOT / f"screening/model/{stamp}"
    if not args.dry_run:
        out.mkdir(parents=True)
    tpw = cfg["input"]["tokens_per_word"]
    rows, words_in, long_in = [], 0, 0
    with (open(os.devnull, "w") if args.dry_run else gzip.open(out / "requests.jsonl.gz", "wt", encoding="utf-8")) as f:
        for i in chosen:
            it = items[i]
            body, basis = cut(bodies[i], it, cfg["input"]["max_body_words"])
            if it["source"] == "abstract":
                basis = "abstract"
            user = (f"Title: {it.get('title') or 'unknown'}\nDOI: {it.get('doi') or 'none'}\n"
                    f"Source of the text: {it['source']}\n\n<text>\n{body}\n</text>")
            params = {"model": cfg["model"]["id"], "max_tokens": cfg["model"]["max_tokens"],
                      "thinking": {"type": "adaptive"},
                      "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                      "messages": [{"role": "user", "content": user}],
                      "output_config": {"effort": cfg["model"]["effort"],
                                        "format": {"type": "json_schema", "schema": sch}}}
            f.write(json.dumps({"custom_id": custom_id(i), "params": params}, ensure_ascii=False) + "\n")
            words_in += len(user.split())
            if (len(user.split()) + len(system.split())) * cfg["input"]["tokens_per_word"] > 100000:
                long_in += len(user.split())
            rows.append({"item": i, "custom_id": custom_id(i), "stratum": it["stratum"], "source": it["source"],
                         "words": len(user.split()), "basis": basis, "body_sha256": sha(bodies[i])})
    p = cfg["price"]
    sys_tokens = round(len(system.split()) * cfg["input"].get("system_tokens_per_word", tpw))
    est_in = round(words_in * tpw)
    est_long = round(long_in * tpw)
    out_per_work = cfg["model"].get("output_tokens_estimate", 6000)  # answer and thinking
    est_out = out_per_work * len(rows)
    cost = ((est_in - est_long) * p["input"] + est_long * p.get("input_long", p["input"])
            + sys_tokens * p["cache_write"] + sys_tokens * max(0, len(rows) - 1) * p["cache_read"]
            + est_out * p["output"]) / 1e6
    left = cfg["budget"]["monthly"].get(cfg["model"]["id"], 0) - month_spent(cfg["model"]["id"])
    manifest = {"stamp": stamp, "script": "model_code.py 1", "set": args.items and "items" or args.set,
                "sample": args.sample and {"n": args.sample, "seed": args.seed},
                "model": cfg["model"], "price": p, "system_sha256": sha(system), "schema_sha256": sha(json.dumps(sch, sort_keys=True)),
                "system_words": len(system.split()), "requests": len(rows),
                "estimate": {"input_tokens": est_in, "system_tokens": sys_tokens, "output_tokens": est_out,
                             "dollars": round(cost, 2), "long_prompt_tokens": est_long, "how": f"{tpw} tokens per word, {out_per_work:,} output tokens per work (thinking included)"},
                "works": rows}
    cut_n = sum(r["basis"] not in ("full text", "abstract") for r in rows)
    print(f"{'(dry run) ' if args.dry_run else ''}{stamp}: {len(rows)} requests ({cut_n} cut), system prompt "
          f"{sys_tokens:,} tokens, input about {est_in:,} tokens; estimated cost {cost:.2f} dollars "
          f"(batch prices of protocol/model.toml); {cfg['model']['id']}: {left:.2f} dollars left this month")
    if args.dry_run:
        return 0
    (ROOT / f"raw/{stamp}-model-manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (ROOT / f"raw/{stamp}-model-system.md").write_text(system, encoding="utf-8")
    (ROOT / f"raw/{stamp}-model-schema.json").write_text(json.dumps(sch, indent=1) + "\n", encoding="utf-8")
    return 0


def auth_headers():
    """An API key if one is set, otherwise the OAuth token of the signed-in `ant` profile."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return {"x-api-key": os.environ["ANTHROPIC_API_KEY"]}
    try:
        token = subprocess.run(["ant", "auth", "print-credentials", "--access-token"], capture_output=True,
                               text=True, timeout=60, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError) as e:
        sys.exit(f"no credentials: set ANTHROPIC_API_KEY or sign in with `ant auth login` ({e.__class__.__name__})")
    return {"authorization": f"Bearer {token}", "anthropic-beta": "oauth-2025-04-20"}


def call(url, data=None, raw=False):
    headers = {**auth_headers(), "anthropic-version": "2023-06-01", "content-type": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                body = r.read()
                return body if raw else json.loads(body)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 529) and attempt < 4:
                time.sleep(15 * 2 ** attempt)
                continue
            sys.exit(f"{e.code} {e.reason}: {e.read()[:500].decode('utf-8', 'replace')}")


def cmd_submit(args):
    path = ROOT / f"screening/model/{args.stamp}/requests.jsonl.gz"
    batch_file = ROOT / f"raw/{args.stamp}-model-batch.json"
    if batch_file.exists():
        sys.exit(f"{batch_file.name} exists: this run was already sent")
    with gzip.open(path, "rt", encoding="utf-8") as f:
        requests = [json.loads(line) for line in f]
    man = json.loads((ROOT / f"raw/{args.stamp}-model-manifest.json").read_text(encoding="utf-8"))
    model_id = man["model"]["id"]
    cap = config()["budget"]["monthly"].get(model_id)
    if cap is None:
        sys.exit(f"no monthly ceiling for {model_id} in [budget.monthly] of protocol/model.toml: not sent")
    spent, estimate = month_spent(model_id), man["estimate"]["dollars"]
    if spent + estimate > cap:
        sys.exit(f"not sent: {model_id} has cost {spent:.2f} dollars this month, and this batch is estimated at "
                 f"{estimate:.2f}, over the monthly ceiling of {cap:.2f} (protocol/model.toml, [budget.monthly])")
    left = credit_left(config())
    if left is not None and estimate > left:
        sys.exit(f"not sent: this batch is estimated at {estimate:.2f} dollars and {left:.2f} are left of the "
                 f"account's credit (protocol/model.toml, [budget.credit])")
    batch = call(API, json.dumps({"requests": requests}).encode("utf-8"))
    batch_file.write_text(json.dumps({"submitted": dt.datetime.now().isoformat(timespec="seconds"), "batch": batch},
                                     indent=1) + "\n", encoding="utf-8")
    print(f"batch {batch['id']}: {batch['processing_status']}, {len(requests)} requests")
    return 0


def cmd_cancel(args):
    rec = json.loads((ROOT / f"raw/{args.stamp}-model-batch.json").read_text(encoding="utf-8"))
    batch = call(f"{API}/{rec['batch']['id']}/cancel", b"{}")
    print(f"batch {batch['id']}: {batch['processing_status']}; `fetch` keeps what was done before the cancel")
    return 0


def cmd_fetch(args):
    rec = json.loads((ROOT / f"raw/{args.stamp}-model-batch.json").read_text(encoding="utf-8"))
    batch = call(f"{API}/{rec['batch']['id']}")
    print(f"batch {batch['id']}: {batch['processing_status']}, {batch['request_counts']}")
    out = ROOT / f"raw/{args.stamp}-model-results.jsonl.gz"
    if batch["processing_status"] != "ended" or out.exists():
        return 0
    data = call(batch["results_url"], raw=True)
    with gzip.open(out, "wb") as f:
        f.write(data)
    (ROOT / f"raw/{args.stamp}-model-batch-ended.json").write_text(json.dumps(batch, indent=1) + "\n", encoding="utf-8")
    print(f"{out.name}: {len(data.splitlines())} results")
    return 0


def norm(s):
    s = re.sub(r"-\s+(?=[a-z])", "", s.lower())
    return re.sub(r"[^a-z0-9]+", "", s)


def visible(q, engagement):
    when = q.get("when")
    return not when or engagement in when.get("engagement", [])


def as_text(q, value):
    """Entries as the lines the application's text field takes; the structure stays in `entries`."""
    if q["kind"] != "entries":
        return value
    keys = [k for k in q["fields"]]
    return ["; ".join(f"{k}: {', '.join(e[k]) if isinstance(e[k], list) else e[k]}" for k in keys) for e in value]


def cmd_ingest(args):
    cfg = config()
    questions = codebook()
    items, bodies = load_items(), load_bodies()
    extra_items, extra_bodies = abstract_works(items, bodies)
    items.update(extra_items)
    bodies.update(extra_bodies)
    # the models whose answers become recommendations, the weakest first ([model] recommend of
    # protocol/model.toml): for each work, the strongest model that coded it from its current
    # text wins, and within one model the latest run
    recommend = cfg["model"].get("recommend", [cfg["primary"]])
    rank = {m: len(recommend) - k for k, m in enumerate(recommend)}

    def model_of(stamp):
        return json.loads((ROOT / f"raw/{stamp}-model-manifest.json").read_text(encoding="utf-8"))["model"]["id"]
    runs = sorted((p.name.split("-model-results")[0] for p in (ROOT / "raw").glob("*-model-results.jsonl.gz")
                   if model_of(p.name.split("-model-results")[0]) in rank),
                  key=lambda st: (rank[model_of(st)], st))
    answers, meta, usage = {}, {}, collections.Counter()
    p = cfg["price"]
    dollars = 0.0
    # the counts are those of the run kept for each work (the latest), not of all runs; the
    # tokens and the cost are those of all runs
    failed_of, item_problems = {}, {}
    for stamp in runs:
        man = json.loads((ROOT / f"raw/{stamp}-model-manifest.json").read_text(encoding="utf-8"))
        by_cid = {w["custom_id"]: w for w in man["works"]}
        with gzip.open(ROOT / f"raw/{stamp}-model-results.jsonl.gz", "rt", encoding="utf-8") as f:
            for r in map(json.loads, f):
                w = by_cid[r["custom_id"]]
                if r["result"]["type"] != "succeeded":
                    failed_of.setdefault(w["item"], r["result"]["type"])
                    continue
                msg = r["result"]["message"]
                u = {k: v for k, v in msg.get("usage", {}).items() if isinstance(v, int)}
                usage.update(u)
                dollars += usage_cost(u, man.get("price", p))
                if msg.get("stop_reason") in ("refusal", "max_tokens"):
                    failed_of.setdefault(w["item"], msg["stop_reason"])
                    continue
                if w["basis"] == "abstract" and meta.get(w["item"], {}).get("basis", "abstract") != "abstract":
                    continue  # an answer from the full text is never replaced by one from the abstract
                if w["basis"] != "abstract" and items.get(w["item"], {}).get("source") == "abstract":
                    continue  # a full text withdrawn since (protocol/wrong-texts.toml): its answer goes too
                text = next((b["text"] for b in msg["content"] if b["type"] == "text"), "")
                item_problems[w["item"]] = collections.Counter()
                try:
                    answers[w["item"]] = answer(json.loads(text), questions, item_problems[w["item"]])
                except (json.JSONDecodeError, KeyError, TypeError):
                    failed_of[w["item"]] = f"unreadable ({msg.get('stop_reason')})"
                    continue
                failed_of.pop(w["item"], None)
                meta[w["item"]] = {"run": stamp, "basis": w["basis"],
                                   "version": f"{man['model']['id']}, prompt {man['system_sha256'][:12]}",
                                   "date": stamp[:10], "changed": sha(bodies.get(w["item"], "")) != w["body_sha256"]}
    failed = collections.Counter(v for i, v in failed_of.items() if i not in answers)
    problems = sum((item_problems[i] for i in answers), collections.Counter())
    path = ROOT / "screening/recommendations.jsonl"
    kept = [json.loads(line) for line in open(path, encoding="utf-8")] if path.exists() else []
    kept = [r for r in kept if r.get("source") != "model"]
    script = {(r["item"], r["question"]): r["value"] for r in kept if r.get("source") == "script"}
    out, quotes = [], collections.Counter()
    eng = collections.defaultdict(collections.Counter)
    not_work = []
    for item, a in sorted(answers.items()):
        m = meta[item]
        body = norm(bodies.get(item, ""))
        e = a["engagement"]["value"]
        eng[items[item]["stratum"] if item in items else "?"][e] += 1
        if a["text_is_the_work"] != "yes":
            not_work.append((item, a["text_is_the_work"]))
        for q in questions:
            ans = a[q["id"]]
            v = ans["value"]
            if v == NOT_ASKED or not visible(q, e):
                continue
            ev = list(ans["evidence"])
            found = [bool(norm(x)) and norm(x) in body for x in ev]
            quotes["found"] += sum(found)
            quotes["all"] += len(found)
            line = {"item": item, "source": "model", "version": m["version"], "date": m["date"], "run": m["run"],
                    "question": q["id"], "value": as_text(q, v), "justification": ans["justification"],
                    "evidence": ev, "evidence_found": found, "basis": m["basis"],
                    "uncertain": q["id"] in a["uncertain"]}
            if q["kind"] == "entries":
                line["entries"] = v
            out.append(line)
    with open(path, "w", encoding="utf-8") as f:
        for r in kept + out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    # agreement with the script's rules (E0: no occurrence; E1: named in background sections only)
    agree = collections.defaultdict(collections.Counter)
    for item, a in answers.items():
        s = script.get((item, "engagement"))
        if s:
            agree[s][a["engagement"]["value"]] += 1
    levels = ["E0", "E1", "E2", "E3", "E4", "E5", "unknown"]
    L = ["# Coding by the language model\n",
         f"Recommendations of {', then '.join(recommend)} (the strongest that coded each work; protocol/model.toml, prompt protocol/model-prompt.md), "
         f"runs {', '.join(runs) or 'none'}; computed by `scripts/model_code.py ingest`. **Recommendations, not "
         "results**: a reader decides (protocol § 5, pilotage review/105).\n",
         f"- Works coded: {len(answers)}; failed requests: {dict(failed) or 0}; texts that are not the work "
         f"(`no` or `unsure`): {len(not_work)}",
         f"- Values outside the codebook, dropped: {dict(problems) or 0}",
         f"- Quotations found verbatim in the body (whitespace, case and hyphenation aside): {quotes['found']} of "
         f"{quotes['all']} ({100 * quotes['found'] / max(1, quotes['all']):.1f} %)",
         f"- Tokens: {usage['input_tokens']:,} input, {usage['cache_read_input_tokens']:,} read from the cache, "
         f"{usage['cache_creation_input_tokens']:,} written to it, {usage['output_tokens']:,} output; "
         f"cost at the prices of protocol/model.toml: {dollars:.2f} dollars\n",
         "## Engagement recommended, by stratum\n",
         "| stratum | " + " | ".join(levels) + " |", "|---|" + "---|" * len(levels)]
    L += [f"| {s} | " + " | ".join(str(eng[s][x]) for x in levels) + " |" for s in sorted(eng)]
    L += ["\n## Against the script's rules\n",
          "Rows: the script's recommendation; columns: the model's. The script's E0 means no occurrence of "
          "SOSA/SSN in the body; E1, named only in background sections.\n",
          "| script | " + " | ".join(levels) + " |", "|---|" + "---|" * len(levels)]
    L += [f"| {s} | " + " | ".join(str(agree[s][x]) for x in levels) + " |" for s in sorted(agree)]
    if not_work:
        L += ["\n## Texts the model does not take for the work\n", "To check (wrong PDF, front matter, proceedings):\n"]
        L += [f"- `{i}` ({v}): {items.get(i, {}).get('title', '')}" for i, v in not_work]
    (ROOT / "results/model-coding.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (ROOT / "results/model-coding.json").write_text(json.dumps(
        {"runs": runs, "works": len(answers), "failed": failed, "problems": problems, "quotes": quotes, "usage": usage,
         "dollars": round(dollars, 2), "engagement": eng, "against_script": agree,
         "not_the_work": not_work}, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"screening/recommendations.jsonl: {len(out)} model recommendations for {len(answers)} works; "
          f"results/model-coding.md")
    return 0


def answers_of(model_id, questions):
    """{item: answer} of a model from the full text, the latest run winning for a work; each
    answer carries the hash of the body it was given (`_body`), so that two models are compared
    on the same text only."""
    out = {}
    for res in sorted((ROOT / "raw").glob("*-model-results.jsonl.gz")):
        stamp = res.name.split("-model-results")[0]
        man = json.loads((ROOT / f"raw/{stamp}-model-manifest.json").read_text(encoding="utf-8"))
        if man["model"]["id"] != model_id:
            continue
        by_cid = {w["custom_id"]: w for w in man["works"]}
        with gzip.open(res, "rt", encoding="utf-8") as f:
            for r in map(json.loads, f):
                w = by_cid[r["custom_id"]]
                if r["result"]["type"] != "succeeded" or w["basis"] == "abstract":
                    continue
                msg = r["result"]["message"]
                if msg.get("stop_reason") in ("refusal", "max_tokens"):
                    continue
                text = next((b["text"] for b in msg["content"] if b["type"] == "text"), "")
                try:
                    out[w["item"]] = answer(json.loads(text), questions, collections.Counter()) | {"_body": w["body_sha256"]}
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue
    return out


def kappa(pairs):
    """Cohen's kappa of a list of (a, b) labels; None when undefined."""
    n = len(pairs)
    if not n:
        return None
    po = sum(a == b for a, b in pairs) / n
    ca, cb = collections.Counter(a for a, _ in pairs), collections.Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in ca) / n / n
    return None if pe == 1 else (po - pe) / (1 - pe)


def kappa_ci(pairs, n_boot=2000, seed=20261113):
    """A 95 % bootstrap interval of Cohen's kappa (percentiles; resampling the works)."""
    import random
    if len(pairs) < 5:
        return None
    rnd = random.Random(seed)
    ks = sorted(k for k in (kappa([rnd.choice(pairs) for _ in pairs]) for _ in range(n_boot)) if k is not None)
    return [ks[int(0.025 * len(ks))], ks[int(0.975 * len(ks)) - 1]] if ks else None


def as_set(q, v):
    if v == NOT_ASKED or v is None:
        return None
    if q["kind"] == "entries":
        field = {"extensions": "builds_on", "errors": "code", "artefacts": "kind"}.get(q["id"])
        out = set()
        for e in v:
            x = e.get(field)
            out.update(x if isinstance(x, list) else [x] if x else [])
        return out
    if q["kind"] in ("many", "terms"):
        return {x.strip().lower() if q["kind"] == "terms" else x for x in v}
    return None


def cmd_compare(args):
    """The models against each other on the works they share, coded from the full text."""
    cfg = config()
    questions = codebook()
    used = set(cfg["model"].get("recommend", []))   # the models whose answers are used
    ladder = [(k, c["model"]["id"]) for k, c in cfg["checks"].items() if not used or c["model"]["id"] in used]
    coded = {name: answers_of(mid, questions) for name, mid in ladder}
    use = {"E3", "E4", "E5"}
    pairs_out = []
    L = ["# The models against each other\n",
         "Computed by `scripts/model_code.py compare` from the runs of `raw/`: each model of "
         "protocol/model.toml on the works it coded from the full text, against each stronger model on "
         "the works they share. Agreement between models, not accuracy: the readers' blind codes are the "
         "reference (pilotage review/105).\n",
         "Models: " + ", ".join(f"{n} ({m}, {len(coded[n])} works)" for n, m in ladder) + ".\n"]
    for i, (na, _) in enumerate(ladder):
        for nb, _ in ladder[i + 1:]:
            a, b = coded[na], coded[nb]
            shared = sorted(w for w in set(a) & set(b) if a[w]["_body"] == b[w]["_body"])
            if not shared:
                continue
            row = {"pair": f"{na}-{nb}", "works": len(shared), "questions": {}}
            for q in questions:
                # a question is compared on the works where both models' engagement asks it
                asked = [w for w in shared if visible(q, a[w]["engagement"]["value"])
                         and visible(q, b[w]["engagement"]["value"])]
                if q["kind"] == "one":
                    pr = [(a[w][q["id"]]["value"], b[w][q["id"]]["value"]) for w in asked
                          if a[w][q["id"]]["value"] != NOT_ASKED and b[w][q["id"]]["value"] != NOT_ASKED]
                    k = kappa(pr)
                    row["questions"][q["id"]] = {"n": len(pr), "agreement": len(pr) and sum(x == y for x, y in pr) / len(pr),
                                                 "kappa": k, "kappa_ci": kappa_ci(pr)}
                elif q["kind"] in ("many", "terms", "entries"):
                    js = []
                    for w in asked:
                        sa, sb = as_set(q, a[w][q["id"]]["value"]), as_set(q, b[w][q["id"]]["value"])
                        if sa is None or sb is None:
                            continue
                        js.append(1.0 if not (sa | sb) else len(sa & sb) / len(sa | sb))
                    row["questions"][q["id"]] = {"n": len(js), "jaccard": sum(js) / len(js) if js else None}
            eng = [(a[w]["engagement"]["value"], b[w]["engagement"]["value"]) for w in shared]
            conf = collections.defaultdict(collections.Counter)
            for x, y in eng:
                conf[y][x] += 1
            strong_use = [(x, y) for x, y in eng if y in use]
            row["use_kappa"] = kappa([(x in use, y in use) for x, y in eng])
            row["use_kappa_ci"] = kappa_ci([(x in use, y in use) for x, y in eng])
            row["use_missed"] = {"n": len(strong_use), "missed": sum(x in ("E0", "E1") for x, _ in strong_use)}
            row["within_one"] = sum(x[:1] == "E" and y[:1] == "E" and abs(int(x[1]) - int(y[1])) <= 1
                                    for x, y in eng) / len(eng)
            row["confusion"] = conf
            pairs_out.append(row)
            L += [f"\n## {na} against {nb} ({len(shared)} works)\n",
                  f"- Engagement: kappa {row['questions']['engagement']['kappa']:.2f}, agreement "
                  f"{100 * row['questions']['engagement']['agreement']:.0f} %, within one level {100 * row['within_one']:.0f} %; "
                  f"use (E3-E5) or not: kappa {row['use_kappa']:.2f}; of the {row['use_missed']['n']} works {nb} codes E3-E5, "
                  f"{na} codes {row['use_missed']['missed']} E0 or E1\n",
                  "| question | works | agreement | kappa [95 % CI] | Jaccard |", "|---|---|---|---|---|"]
            for qid, v in row["questions"].items():
                ag = f"{100 * v['agreement']:.0f} %" if v.get("agreement") is not None and v["n"] else ""
                kp = f"{v['kappa']:.2f}" if v.get("kappa") is not None else ""
                if v.get("kappa_ci"):
                    kp += f" [{v['kappa_ci'][0]:.2f}, {v['kappa_ci'][1]:.2f}]"
                jc = f"{v['jaccard']:.2f}" if v.get("jaccard") is not None else ""
                L.append(f"| {qid} | {v['n']} | {ag} | {kp} | {jc} |")
            levels = ["E0", "E1", "E2", "E3", "E4", "E5", "unknown"]
            L += [f"\nEngagement: rows {nb}, columns {na}.\n", "| | " + " | ".join(levels) + " |",
                  "|---|" + "---|" * len(levels)]
            L += [f"| {y} | " + " | ".join(str(conf[y][x]) for x in levels) + " |" for y in levels if conf[y]]
    (ROOT / "results/model-comparison.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (ROOT / "results/model-comparison.json").write_text(json.dumps(
        {"models": {n: {"id": m, "works": len(coded[n])} for n, m in ladder}, "pairs": pairs_out},
        indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("results/model-comparison.md: " + "; ".join(f"{r['pair']} on {r['works']} works" for r in pairs_out))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--set", choices=["calibration", "blind", "all", "abstracts"], default="blind")
    p.add_argument("--items", nargs="*")
    p.add_argument("--limit", type=int)
    p.add_argument("--dry-run", action="store_true", help="count and estimate, write nothing")
    p.add_argument("--again", action="store_true", help="also the works already sent with this model, prompt and text")
    p.add_argument("--model", choices=["sonnet", "opus"], help="a stronger model of [checks] in protocol/model.toml")
    p.add_argument("--sample", type=int, help="the N first works of the set in a seeded order (nested parts)")
    p.add_argument("--seed", default="model-ladder-2026-11-13")
    for name in ("submit", "fetch", "cancel"):
        sub.add_parser(name).add_argument("stamp")
    sub.add_parser("ingest")
    sub.add_parser("compare")
    sub.add_parser("budget")
    args = ap.parse_args()
    return {"prepare": cmd_prepare, "submit": cmd_submit, "fetch": cmd_fetch, "cancel": cmd_cancel,
            "ingest": cmd_ingest, "compare": cmd_compare, "budget": cmd_budget}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
