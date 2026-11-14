#!/usr/bin/env python3
"""Stream the S2ORC full texts of Semantic Scholar and keep what concerns SOSA/SSN.

    python3 -I scripts/scan_s2orc.py --shards 0          # one shard (pilot)
    python3 -I scripts/scan_s2orc.py --shards all --skip-done   # resume: skip shards already scanned
    python3 -I scripts/scan_s2orc.py --shards all --skip-done --part 0/4   # one of four parallel runs

S2ORC (dataset `s2orc_v2` of the Semantic Scholar Datasets API) holds the body text and
the bibliography, parsed apart, of millions of open-access papers. Each shard is read as a
stream and never stored whole. A record is kept when

- it is a candidate of the citation harvests: its corpus identifier is one of Semantic
  Scholar's citing papers of the seeds, or its DOI one of the OpenAlex candidates', so
  that its full text is at hand for the detection; or
- its **body** (not its bibliography) contains a string of `results/search-strings.csv`
  of kind namespace or prefixed, exactly, so that it may enter stratum D.

Writes, for one run stamped T:

    fulltext/s2orc-<release>/T-shard-<i>.jsonl.gz   the kept records, as served (full texts:
                                                     this directory is not versioned)
    raw/T-s2orc-scan-manifest.json                  release, shards, bytes and records read,
                                                     records kept and why, hits per string

The shard URLs are signed and short-lived (in practice about three hours, whatever their
announced expiry): they are fetched at run time, fetched again after a failed attempt, and
not written anywhere. The API key is read as in scripts/harvest_s2.py. Standard library only.
"""
import argparse
import collections
import csv
import datetime as dt
import gzip
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request
import zlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from harvest_s2 import api_key  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATASETS = "https://api.semanticscholar.org/datasets/v1"
ATTEMPTS = 4
PREFILTER = ("sosa:", "ssn:", "ssn-system:", "w3.org/ns/sosa", "w3.org/ns/ssn", "ssnx/ssn")


def get_json(url, key, tries=6):
    req = urllib.request.Request(url, headers={"x-api-key": key, "User-Agent": "sosa-ssn-slr-harvest"})
    for attempt in range(tries):
        time.sleep(2)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except OSError:  # 429 and network errors: back off, then give up
            if attempt == tries - 1:
                raise
            time.sleep(2 * 2 ** attempt)


def candidates():
    """Corpus identifiers of the papers that the last Semantic Scholar harvest says cite a
    seed, and the DOIs of those papers and of the OpenAlex candidates (lower case)."""
    manifests = sorted(ROOT.glob("raw/*-s2-manifest.json"))
    stamp = json.loads(manifests[-1].read_text(encoding="utf-8"))["stamp"]
    ids, dois = set(), set()
    for path in ROOT.glob(f"raw/{stamp}-s2-cites-*.jsonl.gz"):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                p = json.loads(line).get("citingPaper") or {}
                ext = p.get("externalIds") or {}
                if ext.get("CorpusId"):
                    ids.add(int(ext["CorpusId"]))
                if ext.get("DOI"):
                    dois.add(ext["DOI"].lower())
    with gzip.open(ROOT / "corpus/openalex-candidates.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in f:
            doi = json.loads(line)["doi"]
            if doi:
                dois.add(doi.lower())
    return stamp, ids, dois


def matcher():
    with open(ROOT / "results/search-strings.csv", encoding="utf-8", newline="") as f:
        strings = [r["string"] for r in csv.DictReader(f) if r["kind"] in ("namespace", "prefixed")]
    # a prefixed name must not run on into a longer name (sosa:Sensor in sosa:SensorOutput)
    pattern = "|".join(re.escape(s) + (r"(?![A-Za-z0-9_])" if ":" in s else "") for s in
                       sorted(strings, key=len, reverse=True))
    return re.compile(pattern)


def text_of(part):
    if isinstance(part, dict):
        return part.get("text") or ""
    return part or ""


RX_ID = re.compile(rb'"corpusid"\s*:\s*(\d+)')
RX_DOI = re.compile(rb'"DOI"\s*:\s*"([^"]+)"')


def is_candidate(head, ids, dois):
    m = RX_ID.search(head)
    if m and int(m.group(1)) in ids:
        return True
    m = RX_DOI.search(head)
    return bool(m and m.group(1).decode("utf-8", "replace").lower() in dois)


class Counting:
    """A file-like wrapper that counts the compressed bytes read from the response."""

    def __init__(self, f):
        self.f, self.n = f, 0

    def read(self, size=-1):
        data = self.f.read(size)
        self.n += len(data)
        return data


def scan_shard(url, ids, dois, rx, sink):
    stats = collections.Counter()
    hits = collections.Counter()
    with urllib.request.urlopen(urllib.request.Request(url), timeout=300) as resp:
        expected = int(resp.headers.get("Content-Length") or 0)
        counted = Counting(resp)
        with gzip.GzipFile(fileobj=counted) as gz:
            for raw in gz:
                stats["records"] += 1
                stats["uncompressed bytes"] += len(raw)
                is_cand = is_candidate(raw[:1000], ids, dois)
                if any(p.encode() in raw for p in PREFILTER):
                    rec = json.loads(raw)
                    found = collections.Counter(rx.findall(text_of(rec.get("body"))))
                elif is_cand:
                    rec, found = json.loads(raw), {}
                else:
                    continue
                if not (is_cand or found):
                    continue
                stats["kept"] += 1
                stats["kept as candidates"] += is_cand
                stats["kept by strings in the body"] += bool(found)
                stats["kept by strings, not candidates"] += bool(found) and not is_cand
                for s in found:
                    hits[s] += 1
                rec["_scan"] = {"candidate": is_cand, "found": dict(found)}
                sink.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if expected and counted.n != expected:
            raise OSError(f"shard read incompletely: {counted.n} of {expected} bytes")
        stats["compressed bytes"] = counted.n
    return stats, hits


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--shards", default="0", help='"all", or indices such as 0,1,5-9')
    ap.add_argument("--release", default="latest")
    ap.add_argument("--part", default="0/1",
                    help="K/N: scan only the shards whose index is K modulo N (parallel runs)")
    ap.add_argument("--skip-done", action="store_true",
                    help="skip the shards of this release that an earlier run already scanned")
    args = ap.parse_args(argv)
    key = api_key()
    release = get_json(f"{DATASETS}/release/{args.release}", key)["release_id"]
    files = get_json(f"{DATASETS}/release/{release}/dataset/s2orc_v2", key)["files"]
    if args.shards == "all":
        chosen = list(range(len(files)))
    else:
        chosen = []
        for part in args.shards.split(","):
            a, _, b = part.partition("-")
            chosen += list(range(int(a), int(b or a) + 1))
    if args.skip_done:
        done = set()
        for m in ROOT.glob("raw/*-s2orc-scan-manifest.json"):
            prev = json.loads(m.read_text(encoding="utf-8"))
            if prev.get("release") == release:
                done.update(s["file"] for s in prev.get("shards", []))
        names = [urllib.parse.urlparse(u).path.rsplit("/", 1)[-1] for u in files]
        chosen = [i for i in chosen if i < len(files) and names[i] not in done]
    k, n = (int(x) for x in args.part.split("/"))
    chosen = [i for i in chosen if i % n == k]
    s2_stamp, ids, dois = candidates()
    rx = matcher()
    stamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M") + (f"-p{k}of{n}" if n > 1 else "")
    out = ROOT / f"fulltext/s2orc-{release}"
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"stamp": stamp, "source": "Semantic Scholar S2ORC (s2orc_v2)", "release": release,
                "shards_in_release": len(files), "candidates_from_s2_harvest": s2_stamp,
                "candidate_corpus_ids": len(ids), "candidate_dois": len(dois), "shards": []}
    total, all_hits = collections.Counter(), collections.Counter()
    for i in chosen:
        if i >= len(files):
            break
        name = urllib.parse.urlparse(files[i]).path.rsplit("/", 1)[-1]
        started = time.time()
        for attempt in range(1, ATTEMPTS + 1):
            try:  # a network failure restarts the shard from its beginning
                with gzip.open(out / f"{stamp}-shard-{i:03d}.jsonl.gz", "wt", encoding="utf-8") as sink:
                    stats, hits = scan_shard(files[i], ids, dois, rx, sink)
                break
            except (OSError, EOFError, zlib.error) as e:
                print(f"shard {i:>3}: attempt {attempt} failed: {e!r}", file=sys.stderr)
                if attempt == ATTEMPTS:
                    manifest.setdefault("failed", []).append({"index": i, "file": name, "error": repr(e)})
                    (ROOT / f"raw/{stamp}-s2orc-scan-manifest.json").write_text(
                        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                    stats = None
                    break
                time.sleep(60 * attempt)
                # the signed links stop working after about three hours (HTTP 400), well
                # before their announced expiry: ask for fresh ones before the next attempt
                fresh = get_json(f"{DATASETS}/release/{release}/dataset/s2orc_v2", key)["files"]
                by_name = {urllib.parse.urlparse(u).path.rsplit("/", 1)[-1]: u for u in fresh}
                if name in by_name:
                    files[i] = by_name[name]
        if stats is None:
            continue
        entry = {"index": i, "file": name, **stats, "seconds": round(time.time() - started),
                 "attempts": attempt}
        manifest["shards"].append(entry)
        total.update(stats)
        all_hits.update(hits)
        print(f"shard {i:>3}: {stats['records']:>7} records, {stats['uncompressed bytes'] / 1e9:5.2f} GB, kept "
              f"{stats['kept']} ({stats['kept as candidates']} candidates, "
              f"{stats['kept by strings, not candidates']} by strings only), {entry['seconds']} s",
              file=sys.stderr)
        manifest["total"] = dict(total)
        manifest["hits_per_string"] = dict(all_hits.most_common())
        (ROOT / f"raw/{stamp}-s2orc-scan-manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(stamp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
