#!/usr/bin/env python3
"""Print the works of one batch of the pattern coding, for a coder (scripts/pattern_coding.py).

    python3 -I scripts/pattern_show.py STAMP K            # the list: index, item, engagement, size
    python3 -I scripts/pattern_show.py STAMP K 3          # work 3 of batch K: title and excerpts
    python3 -I scripts/pattern_show.py STAMP K --check    # which works of the batch are coded yet,
                                                          # and whether each coded line parses
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main(argv):
    stamp, k = argv[0], argv[1]
    works = [json.loads(l) for l in open(ROOT / f"screening/patterns/{stamp}/batch-{k}.jsonl", encoding="utf-8")]
    if len(argv) == 2:
        for n, w in enumerate(works, 1):
            print(f"{n:>3} {w['item']:<24} {w['engagement'] or '-':<4} {len(w['excerpts']):>6}  {(w['title'] or '')[:70]}")
        return 0
    if argv[2] == "--check":
        out = ROOT / f"raw/{stamp}-patterns-coded-{k}.jsonl"
        done = {}
        if out.exists():
            for n, line in enumerate(open(out, encoding="utf-8"), 1):
                if line.strip():
                    try:
                        r = json.loads(line)
                        done[r["item"]] = sorted(r["answers"])
                    except Exception as e:  # noqa: BLE001
                        print(f"line {n} does not parse: {e}")
        missing = [w["item"] for w in works if w["item"] not in done]
        print(f"{len(done)} coded, {len(missing)} missing: {' '.join(missing)}")
        return 0
    w = works[int(argv[2]) - 1]
    print(f"ITEM {w['item']}  engagement {w['engagement']}\nTITLE {w['title']}\n\n{w['excerpts']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
