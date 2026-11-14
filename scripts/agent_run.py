#!/usr/bin/env python3
"""A model run coded by isolated Claude Code subagents instead of the Batches API.

    python3 -I scripts/agent_run.py export STAMP          # screening/model/STAMP/agents/<id>/
    python3 -I scripts/agent_run.py check STAMP <id>      # is agents/<id>/answer.json valid?
    python3 -I scripts/agent_run.py collect STAMP --agent-model sonnet
                                  # raw/STAMP-model-results.jsonl.gz and -agents.json

Maxime, 2026-11-14: the works taken in after the runs of the Batches API are coded by
Sonnet "here, with isolated subagents, not through the API". `model_code.py prepare --model
sonnet` writes the requests and the manifest as for any run; `export` writes, for each
request, the system prompt (`system.md`), the user message with the body of the work
(`work.md`) and the JSON schema of the answer (`schema.json`); one subagent per work, with no
other context, reads them and writes `answer.json`, which `check` validates against the
schema. `collect` writes the answers in the format of the results of the Batches API
(`succeeded`, the answer as the text block, no usage), so that `model_code.py` reads them like
any run, and records how they were made in raw/STAMP-model-agents.json (the subagent model,
the date, the works answered and missing). No network. Standard library only.
"""
import argparse
import datetime as dt
import gzip
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def validate(v, s, path="$"):
    """Errors of value v against the subset of JSON Schema that the requests use."""
    errs = []
    t = s.get("type")
    types = {"object": dict, "array": list, "string": str, "boolean": bool, "integer": int, "number": (int, float)}
    if t and not isinstance(v, types.get(t, object)):
        return [f"{path}: expected {t}"]
    if "enum" in s and v not in s["enum"]:
        errs.append(f"{path}: {v!r} not in {s['enum'][:8]}")
    if t == "object":
        for k in s.get("required", []):
            if k not in v:
                errs.append(f"{path}: missing {k}")
        props = s.get("properties", {})
        if s.get("additionalProperties") is False:
            errs += [f"{path}: unexpected {k}" for k in v if k not in props]
        for k, sub in props.items():
            if k in v:
                errs += validate(v[k], sub, f"{path}.{k}")
    if t == "array":
        for i, x in enumerate(v):
            errs += validate(x, s.get("items", {}), f"{path}[{i}]")
        if "minItems" in s and len(v) < s["minItems"]:
            errs.append(f"{path}: fewer than {s['minItems']} items")
    for alt in ("anyOf", "oneOf"):
        if alt in s and all(validate(v, sub, path) for sub in s[alt]):
            errs.append(f"{path}: matches none of {alt}")
    return errs


def export(args):
    d = ROOT / f"screening/model/{args.stamp}"
    n = 0
    with gzip.open(d / "requests.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            p = r["params"]
            w = d / "agents" / r["custom_id"]
            w.mkdir(parents=True, exist_ok=True)
            (w / "system.md").write_text("\n\n".join(b["text"] for b in p["system"]), encoding="utf-8")
            c = p["messages"][0]["content"]
            (w / "work.md").write_text(c if isinstance(c, str) else "\n".join(b.get("text", "") for b in c), encoding="utf-8")
            (w / "schema.json").write_text(json.dumps(p["output_config"]["format"]["schema"], indent=1), encoding="utf-8")
            n += 1
    print(f"{n} works exported to {d / 'agents'}")


def check(args):
    w = ROOT / f"screening/model/{args.stamp}/agents/{args.id}"
    try:
        ans = json.loads((w / "answer.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"invalid: {e}")
        return 1
    errs = validate(ans, json.loads((w / "schema.json").read_text(encoding="utf-8")))
    print("valid" if not errs else "invalid:\n" + "\n".join(errs[:30]))
    return 1 if errs else 0


def collect(args):
    d = ROOT / f"screening/model/{args.stamp}"
    man = json.loads((ROOT / f"raw/{args.stamp}-model-manifest.json").read_text(encoding="utf-8"))
    out, done, missing = [], [], []
    for w in man["works"]:
        a = d / "agents" / w["custom_id"] / "answer.json"
        schema = json.loads((d / "agents" / w["custom_id"] / "schema.json").read_text(encoding="utf-8"))
        try:
            ans = json.loads(a.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            missing.append(w["custom_id"])
            continue
        if validate(ans, schema):
            missing.append(w["custom_id"])
            continue
        text = json.dumps(ans, ensure_ascii=False)
        out.append({"custom_id": w["custom_id"], "result": {"type": "succeeded", "message": {
            "model": man["model"]["id"], "id": "agent-" + hashlib.sha1(text.encode()).hexdigest()[:16],
            "type": "message", "role": "assistant", "content": [{"type": "text", "text": text}],
            "stop_reason": "end_turn", "usage": {}}}})
        done.append(w["custom_id"])
    with gzip.open(ROOT / f"raw/{args.stamp}-model-results.jsonl.gz", "wt", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    (ROOT / f"raw/{args.stamp}-model-agents.json").write_text(json.dumps({
        "stamp": args.stamp, "how": "isolated Claude Code subagents, one per work, each given only system.md, "
        "work.md and schema.json of its request (Maxime, 2026-11-14: Sonnet here, not through the API)",
        "agent_model": args.agent_model, "manifest_model": man["model"]["id"],
        "collected": dt.datetime.now().isoformat(timespec="minutes"), "answered": done, "missing": missing},
        indent=1) + "\n", encoding="utf-8")
    print(f"raw/{args.stamp}-model-results.jsonl.gz: {len(done)} answers; missing or invalid: {missing or 'none'}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("export", "check", "collect"):
        p = sub.add_parser(name)
        p.add_argument("stamp")
        if name == "check":
            p.add_argument("id")
        if name == "collect":
            p.add_argument("--agent-model", default="sonnet")
    args = ap.parse_args(argv)
    return {"export": export, "check": check, "collect": collect}[args.cmd](args) or 0


if __name__ == "__main__":
    sys.exit(main())
