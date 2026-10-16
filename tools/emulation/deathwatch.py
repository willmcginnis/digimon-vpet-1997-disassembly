"""Leave the injured pet untreated and watch for the game's own death sequence.

Saves dead_pre.pkl (last minute before the end-of-life mode) and dead.pkl
(first minute in it), plus a log of the counters each emulated minute.
"""
import pickle
import sys

import harness as h  # noqa: F401

a, b = pickle.load(open("injured_pair.pkl", "rb"))
p = b
g = p.cpu.get_mem
prev = pickle.dumps(p)
max_minutes = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
for minute in range(max_minutes):
    p.run_seconds(60)
    m9, ma, slot = g(0x9), g(0xA), g(0xB)
    if minute % 30 == 0 or m9 in (0xB, 0xC) or slot == 0xF:
        print("min %d M9=%X MA=%X slot=%X M5=%X 36-39=%s 75=%X 76=%X icons=%s" % (
            minute, m9, ma, slot, g(5), "".join("%X" % g(x) for x in range(0x36, 0x3A)),
            g(0x75), g(0x76), p.frame()[1]), flush=True)
    if m9 in (0xB, 0xC) or slot == 0xF:
        open("dead_pre.pkl", "wb").write(prev)
        pickle.dump(p, open("dead.pkl", "wb"))
        print(p.ascii(), flush=True)
        break
    prev = pickle.dumps(p)
