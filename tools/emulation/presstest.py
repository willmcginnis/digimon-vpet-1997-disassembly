"""Look for hidden press counters: press a button N times and see whether any RAM
nibble keeps a memory of how many presses happened.

Method: from one saved state, run a control (no presses) and a treatment (press
the button every `period` seconds). At each press slot k we snapshot RAM in both
runs at the same emulated time. For every nibble we ask: as a function of k,
does the treatment-minus-control difference show long-period structure (a
counter) or only short-period structure (menu cycling) or none?

argv: state.pkl button N [period_s]
"""
import pickle
import sys

import harness as h  # noqa: F401  (needed for unpickling)

state, button, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
period = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
RAM_RANGE = range(0x000, 0x280)


def load():
    with open(state, "rb") as f:
        return pickle.load(f)


def snap(p):
    return tuple(p.cpu.get_mem(a) for a in RAM_RANGE)


ctrl, treat = load(), load()
ctrl_snaps, treat_snaps = [], []
buttons = list(button)  # e.g. "A" or "AC" for a combo
for k in range(n):
    treat.hold(*buttons)
    treat.run_seconds(0.08)
    treat.release(*buttons)
    treat.run_seconds(period - 0.08)
    ctrl.run_seconds(period)
    ctrl_snaps.append(snap(ctrl))
    treat_snaps.append(snap(treat))


def min_period(seq, skip=8):
    """Smallest p such that seq[i] == seq[i+p] for all i >= skip, else None."""
    s = seq[skip:]
    for p in range(1, len(s) // 2 + 1):
        if all(s[i] == s[i + p] for i in range(len(s) - p)):
            return p
    return None


report = []
for idx, addr in enumerate(RAM_RANGE):
    t = [s[idx] for s in treat_snaps]
    c = [s[idx] for s in ctrl_snaps]
    if t == c:
        continue
    pt = min_period(t)
    report.append((addr, pt, len(set(t)), "".join("%X" % v for v in t[:48])))

print("button=%s presses=%d nibbles_differing_from_control=%d" % (button, n, len(report)))
for addr, pt, nvals, head in report:
    flag = "  <-- long/no period" if (pt is None or pt >= 9) else ""
    print("%03X period=%s distinct=%d seq=%s%s" % (addr, pt, nvals, head, flag))
print("screen after treatment:")
print(treat.ascii())
