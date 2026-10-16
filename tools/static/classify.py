"""Assign every ROM word to a subsystem.

A subsystem is defined by its roots (main-loop tasks and interrupt handlers).
A function belongs to the subsystem(s) whose roots reach it through the call
graph; jump-reached code is already inside each function body. Words owned by
functions reached from more than one subsystem are "shared". Graphics data is
recognised by shape: runs of LBPX/RETD that write column bitmaps.

usage: python3 classify.py static.json executed.json OUT.json
"""
import json
import sys
from collections import defaultdict

SUBSYSTEMS = [
    # name, roots
    ("spine", [0x0100, 0x010E, 0x0132, 0x016E, 0x09F4]),
    ("input", [0x07BF, 0x0200, 0x0106]),
    ("screens", [0x0410]),
    ("life", [0x0900, 0x0800, 0x0102]),
    ("link_battle", [0x0B06, 0x0B5B]),
    ("animation", [0x0A5D]),
    ("sound", [0x0A00, 0x010C]),
]
LIBRARY_PAGE0 = range(0x0000, 0x0100)


def main():
    st = json.load(open(sys.argv[1]))
    executed = set(json.load(open(sys.argv[2])))
    T = st["text"]
    F = {int(k, 16): v for k, v in st["functions"].items()}
    callees = {e: [int(c, 16) for c in f["callees"]] for e, f in F.items()}

    reach = defaultdict(set)  # function -> subsystems
    for name, roots in SUBSYSTEMS:
        stack = [r for r in roots if r in F]
        seen = set()
        while stack:
            f = stack.pop()
            if f in seen:
                continue
            seen.add(f)
            reach[f].add(name)
            stack.extend(callees.get(f, ()))

    word_funcs = defaultdict(set)
    for e, f in F.items():
        for p in f["body"]:
            word_funcs[p].add(e)

    def is_gfx(p):
        t = T["%04X" % p]
        return t.startswith("lbpx M(X)") or t.startswith("retd")

    words = {}
    for p in range(st["words"]):
        t = T["%04X" % p]
        if p not in set(st["reached"]):
            words[p] = "filler" if t == "nop7" else "unreached"
            continue
        if p in LIBRARY_PAGE0:
            cat = "library"
        else:
            subs = set()
            for f in word_funcs.get(p, ()):
                subs |= reach.get(f, set())
            if not subs:
                cat = "unattributed"
            elif len(subs) == 1:
                cat = next(iter(subs))
            else:
                cat = "shared"
        # graphics data overrides: inside a run of >= 4 bitmap-writing words
        run = sum(1 for q in range(p - 3, p + 4) if 0 <= q < st["words"] and is_gfx(q))
        if is_gfx(p) and run >= 4:
            cat = "graphics"
        words[p] = cat

    funcs = {}
    for e in F:
        subs = sorted(reach.get(e, ()))
        funcs["%04X" % e] = {
            "subsystems": subs,
            "executed": e in executed,
        }
    counts = defaultdict(int)
    for c in words.values():
        counts[c] += 1
    json.dump({"words": {"%04X" % p: c for p, c in words.items()}, "functions": funcs,
               "counts": counts}, open(sys.argv[3], "w"))
    for c, n in sorted(counts.items(), key=lambda x: -x[1]):
        print("%-13s %5d" % (c, n))
    # bank summary
    for bank in (0, 1):
        bc = defaultdict(int)
        for p in range(bank * 0x1000, bank * 0x1000 + 0x1000):
            bc[words[p]] += 1
        print("bank %d:" % bank, dict(sorted(bc.items(), key=lambda x: -x[1])))


if __name__ == "__main__":
    main()
