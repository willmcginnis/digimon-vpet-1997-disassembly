"""Does the device remember HOW MANY times a button was pressed?

From one saved state, do several runs that press a button N times (various N,
various press rates), then let every run idle until the same absolute emulated
time so menus time out. Snapshot all RAM at that common end time and report the
nibbles that differ between runs. A hidden press counter would show up as a
nibble that tracks N; the known event-stepped RNG at 0xA0-0xA3 is listed apart.

argv: state.pkl buttons counts(comma) periods(comma) [settle_s] [sequence]
  buttons: e.g. "A" or "AB" (pressed together)
  sequence mode: if argv[6] == "seq", counts are per-button for a sequence like
  A then B then C, e.g. buttons=ABC counts=200,200,25
"""
import pickle
import sys

import harness as h  # noqa: F401

state = sys.argv[1]
buttons = sys.argv[2]
counts = [int(x) for x in sys.argv[3].split(",")]
periods = [float(x) for x in sys.argv[4].split(",")]
settle = float(sys.argv[5]) if len(sys.argv) > 5 else 400.0
seq_mode = len(sys.argv) > 6 and sys.argv[6] == "seq"
RNG = set(range(0xA0, 0xA4))


def load():
    with open(state, "rb") as f:
        return pickle.load(f)


def do_presses(p, period):
    if seq_mode:
        for b, n in zip(buttons, counts):
            for _ in range(n):
                p.press(b, hold_s=0.08, gap_s=period - 0.08)
    else:
        raise RuntimeError


runs = {}
if seq_mode:
    variants = []
    for per in periods:
        variants.append(("seq%s@%.2f" % (sys.argv[3], per), per, None))
    # neighbours: one fewer / one more press of the last button
    for delta in (-1, 1):
        c2 = counts[:-1] + [counts[-1] + delta]
        variants.append(("seq%s@%.2f" % (",".join(map(str, c2)), periods[0]), periods[0], c2))
    variants.append(("none", periods[0], [0] * len(counts)))
    longest = sum(max(counts[-1] + 1, c) for c in counts) * max(periods)
    end_t = longest + settle
    for name, per, c2 in variants:
        p = load()
        t0 = p.cycles
        cs = c2 if c2 is not None else counts
        for b, n in zip(buttons, cs):
            for _ in range(n):
                p.press(b, hold_s=0.08, gap_s=per - 0.08)
        p.run_cycles(int(end_t * h.CLOCK) - (p.cycles - t0))
        runs[name] = (tuple(p.cpu.get_mem(a) for a in range(0x280)), p.ascii())
else:
    longest = max(counts) * max(periods)
    end_t = longest + settle
    for n in counts:
        for per in periods:
            p = load()
            t0 = p.cycles
            for _ in range(n):
                p.hold(*buttons)
                p.run_seconds(0.08)
                p.release(*buttons)
                p.run_seconds(per - 0.08)
            p.run_cycles(int(end_t * h.CLOCK) - (p.cycles - t0))
            runs["N=%d@%.2f" % (n, per)] = (tuple(p.cpu.get_mem(a) for a in range(0x280)), p.ascii())

names = list(runs)
diff = [a for a in range(0x280) if len({runs[n][0][a] for n in names}) > 1]
print("runs:", ", ".join(names))
print("end time %.0fs after state; nibbles that differ between runs (RNG 0xA0-A3 excluded):" % end_t)
for a in diff:
    if a in RNG:
        continue
    print("  %03X  " % a + "  ".join("%s=%X" % (n, runs[n][0][a]) for n in names))
print("RNG nibbles differ:", [hex(a) for a in diff if a in RNG])
screens = {runs[n][1] for n in names}
print("distinct final screens:", len(screens))
