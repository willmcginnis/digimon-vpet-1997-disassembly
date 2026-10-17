"""Align the Ver. 1 and Ver. 2 instruction streams (data/v1v2_align.json).

usage: python3 align_versions.py STATIC_V1_JSON STATIC_V2_JSON OUT.json

Each word's disassembly text is compared with jump and call targets reduced to their
8-bit step, so code that moved but is otherwise identical still matches. The matching
runs come from difflib.SequenceMatcher with autojunk disabled (with autojunk on, frequent
instructions are discarded as junk and a few short runs are lost).
Writes {"blocks": [[v1_start, v2_start, length], ...]} and prints the shares per bank.
"""
import difflib
import json
import re
import sys


def norm(text):
    m = re.match(r"(jp|call|callz)( (?:c|nc|z|nz),)? ([0-9A-F]{4})$", text)
    return "%s%s %s" % (m.group(1), m.group(2) or "", m.group(3)[2:]) if m else text


def stream(path):
    st = json.load(open(path))
    return [norm(st["text"]["%04X" % p]) for p in range(st["words"])]


a, b = stream(sys.argv[1]), stream(sys.argv[2])
sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
blocks = [[m.a, m.b, m.size] for m in sm.get_matching_blocks() if m.size]
json.dump({"blocks": blocks}, open(sys.argv[3], "w"))
for bank in (0, 1):
    lo, hi = bank * 4096, (bank + 1) * 4096
    n = sum(max(0, min(i + k, hi) - max(i, lo)) for i, _, k in blocks)
    print("bank %d: %d / 4096 words of Ver. 1 in aligned runs (%.0f%%)" % (bank, n, 100 * n / 4096))
total = sum(k for _, _, k in blocks)
print("whole ROM: %d words in %d runs, the longest %d" % (total, len(blocks), max(k for _, _, k in blocks)))
