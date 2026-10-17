"""Carry the Ver. 1 name tables over to Ver. 2 through the instruction-stream alignment.

usage: python3 port_names.py names_v1.py v1v2_align.json STATIC_V1_JSON STATIC_V2_JSON OUT_names_v2.py

A Ver. 1 function or label is ported when its address lies inside an aligned run of
identical instructions (jump targets compared by step); the
aligned address keeps its name even where it is a jump target rather than a subroutine
(export_ghidra_map.py then writes it as a label). A function outside
the aligned runs is still ported when its first eight instructions (jump targets reduced
to their step) match exactly one Ver. 2 subroutine entry. The confidence
becomes "ported" with the Ver. 1 address in the note: these names are inferred by
alignment, not measured on Ver. 2. RAM and I/O tables are copied unchanged, since
both versions use the same variables wherever the code is shared.
"""
import importlib.util
import json
import pprint
import re
import sys

spec = importlib.util.spec_from_file_location("names", sys.argv[1])
n1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(n1)
blocks = json.load(open(sys.argv[2]))["blocks"]
st1 = json.load(open(sys.argv[3]))
st2 = json.load(open(sys.argv[4]))
funcs2 = {int(k, 16) for k in st2["functions"]}


def norm(text):
    m = re.match(r"(jp|call|callz)( (?:c|nc|z|nz),)? ([0-9A-F]{4})$", text)
    return "%s%s %s" % (m.group(1), m.group(2) or "", m.group(3)[2:]) if m else text


def signature(st, a, n=8):
    return tuple(norm(st["text"].get("%04X" % (a + k), "")) for k in range(n))


sig2 = {}
for b in funcs2:
    sig2.setdefault(signature(st2, b), []).append(b)


def to_v2(a):
    for i, j, n in blocks:
        if i <= a < i + n:
            return j + (a - i)
    return None


def port(table, need_func):
    out, missed = {}, []
    for a, (nm, conf, note) in sorted(table.items()):
        b = to_v2(a)
        how = "aligned"
        if need_func and b is None:
            cand = sig2.get(signature(st1, a), [])
            b, how = (cand[0], "signature") if len(cand) == 1 else (None, "")
        if b is None:
            missed.append((a, nm))
            continue
        out[b] = (nm, "ported", "Ver. 1 %04X (%s; %s). %s" % (a, conf, how, note))
    return out, missed


F, fm = port(n1.FUNCS, True)
L, lm = port(n1.LABELS, False)
with open(sys.argv[5], "w") as o:
    o.write('"""Ver. 2 names carried over from names_v1.py by tools/static/port_names.py.\n\n')
    o.write("Generated; do not edit. Confidence \"ported\" means inferred by alignment.\n")
    o.write("Not ported (outside the aligned runs, and no unique signature match):\n")
    for a, nm in fm + lm:
        o.write("    %04X %s\n" % (a, nm))
    o.write('"""\n\n')
    for name, tab in (("FUNCS", F), ("LABELS", L), ("RAM", n1.RAM), ("IO", n1.IO)):
        o.write("%s = %s\n\n" % (name, pprint.pformat(tab, width=110)))
print("ported %d/%d functions, %d/%d labels" % (len(F), len(n1.FUNCS), len(L), len(n1.LABELS)))
print("not ported:", ", ".join("%04X %s" % m for m in fm + lm))
