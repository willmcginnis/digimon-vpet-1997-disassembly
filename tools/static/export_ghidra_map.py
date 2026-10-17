"""Turn the walker's map and the name tables into the TSV that ghidra/ApplyMap.java reads.

usage: python3 export_ghidra_map.py STATIC_JSON NAMES_PY OUT_TSV

Lines (tab-separated):
    code  ADDR              every word the walker reached (all of it is code)
    jpba  ADDR T1,T2,...    a JPBA site and its resolved targets
    func  ADDR NAME CMT     every subroutine; named ones carry [confidence] and a note
    label ADDR NAME CMT     named labels inside functions
    ram   ADDR NAME CMT     named RAM nibbles and I/O registers
"""
import importlib.util
import json
import sys

static = json.load(open(sys.argv[1]))
spec = importlib.util.spec_from_file_location("names", sys.argv[2])
names = importlib.util.module_from_spec(spec)
spec.loader.exec_module(names)

out = []
for a, roles in sorted(static["roles"].items(), key=lambda kv: int(kv[0], 16)):
    if roles:  # code, jump-table entries, and trace-seeded words alike
        out.append(("code", a))
for site, j in sorted(static["jpba"].items()):
    if j["targets"]:
        out.append(("jpba", site, ",".join(j["targets"])))
for e, f in sorted(static["functions"].items(), key=lambda kv: int(kv[0], 16)):
    ea = int(e, 16)
    if ea in names.FUNCS:
        nm, conf, note = names.FUNCS[ea]
        out.append(("func", e, nm, ("[%s] %s" % (conf, note)).strip()))
    else:
        nm = f.get("vector_name") or "sub_%s" % e
        out.append(("func", e, nm, "%d callers" % len(f["callers"])))
funcs = {int(e, 16) for e in static["functions"]}
for ea, (nm, conf, note) in sorted(names.FUNCS.items()):
    if ea not in funcs:  # named entry points reached by jumps (main loop, mode handlers)
        out.append(("label", "%04X" % ea, nm, ("[%s] %s" % (conf, note)).strip()))
for ea, (nm, conf, note) in sorted(names.LABELS.items()):
    out.append(("label", "%04X" % ea, nm, ("[%s] %s" % (conf, note)).strip()))
for ea, (nm, conf, note) in sorted(names.RAM.items()):
    out.append(("ram", "%03X" % ea, nm, ("[%s] %s" % (conf, note)).strip()))
for ea, nm in sorted(names.IO.items()):
    out.append(("ram", "%03X" % ea, nm, "[documented] I/O register"))

with open(sys.argv[3], "w") as o:
    for row in out:
        o.write("\t".join(row) + "\n")
kinds = {}
for row in out:
    kinds[row[0]] = kinds.get(row[0], 0) + 1
print(sys.argv[3], kinds)
