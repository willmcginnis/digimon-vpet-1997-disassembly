"""Run a linked battle between two emulated pets and log the packets.

argv: stateA.pkl stateB.pkl [slotA] [slotB] [seconds]
Pet A navigates to the BATTLE icon and presses B to start; pet B stays idle.
"""
import pickle
import sys

import harness as h  # noqa: F401
import link as L


def load(path, slot):
    with open(path, "rb") as f:
        p = pickle.load(f)
    if slot is not None:
        p.poke(0xB, slot)
    p.host.tx.clear()
    return p


def goto_icon(lk, pet, name, tries=16):
    for _ in range(tries):
        if name in pet.frame()[1]:
            return True
        lk.press(pet, "A", hold_s=0.15, gap_s=0.35)
    return name in pet.frame()[1]


def bits_rev(w):
    return int("{:016b}".format(w)[::-1], 2)


if __name__ == "__main__":
    sa = int(sys.argv[3], 0) if len(sys.argv) > 3 and sys.argv[3] else None
    sb = int(sys.argv[4], 0) if len(sys.argv) > 4 and sys.argv[4] else None
    secs = float(sys.argv[5]) if len(sys.argv) > 5 else 25
    a, b = load(sys.argv[1], sa), load(sys.argv[2], sb)
    lk = L.Link(a, b)
    ok = goto_icon(lk, a, "BATTLE")
    print("on BATTLE icon:", ok)
    lk.press(a, "B", hold_s=0.15, gap_s=0.5)
    shots = []
    for i in range(int(secs * 2)):
        lk.run_seconds(0.5)
        shots.append((a.ascii(), b.ascii()))
    for t, d, w in lk.log:
        print("%.2fs %s dmcomm=%04X" % (t, d, bits_rev(w)))
    uniq = []
    for s in shots:
        if s not in uniq:
            uniq.append(s)
    print("distinct (A,B) screen pairs:", len(uniq))
    print("final A:\n" + a.ascii().replace(".", " "))
    print("final B:\n" + b.ascii().replace(".", " "))


def feed(lk, pet, meat=4, protein=4):
    """Feed via the FEED menu. Returns nothing; pet may refuse when full."""
    for kind, n in (("meat", meat), ("protein", protein)):
        for _ in range(n):
            goto_icon(lk, pet, "FEED")
            lk.press(pet, "B", hold_s=0.15, gap_s=0.6)
            if kind == "protein":
                lk.press(pet, "A", hold_s=0.15, gap_s=0.4)
            lk.press(pet, "B", hold_s=0.15, gap_s=0.4)
            lk.run_seconds(6)
            lk.press(pet, "C", hold_s=0.15, gap_s=0.4)
            lk.run_seconds(1)


def flush(lk, pet):
    goto_icon(lk, pet, "FLUSH")
    lk.press(pet, "B", hold_s=0.15, gap_s=0.4)
    lk.run_seconds(5)
