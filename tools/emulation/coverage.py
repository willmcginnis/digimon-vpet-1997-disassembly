"""Dynamic coverage: record every PC the emulated CPU executes across scenarios.

usage: python3 coverage.py SCENARIO OUT.json [ROM]
Patches E0C6200.clock at class level so pickled pets are covered too.
"""
import json
import os
import pickle
import sys

import harness as h
from cores.E0C6200 import E0C6200

PCS = set()
_orig = E0C6200.clock


def _clock(self):
    if not self._RESET and not self._HALT:
        PCS.add(self._PC & 0x1FFF)
    return _orig(self)


E0C6200.clock = _clock

MEM = {}
_og, _os = E0C6200.get_mem, E0C6200.set_mem


def _gm(self, addr):
    MEM.setdefault(addr, [set(), set()])[0].add(self._PC & 0x1FFF)
    return _og(self, addr)


def _sm(self, addr, value):
    MEM.setdefault(addr, [set(), set()])[1].add(self._PC & 0x1FFF)
    return _os(self, addr, value)


E0C6200.get_mem, E0C6200.set_mem = _gm, _sm

scenario, out = sys.argv[1], sys.argv[2]
ROM = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("ROM", "roms/digimon_v1.bin")


def fresh():
    p = h.Pet(ROM)
    p.reset()
    p.run_seconds(1)
    return p


def hatch(p):
    p.press("B", hold_s=0.15, gap_s=1)
    for _ in range(9):
        p.press("A", hold_s=0.1, gap_s=0.3)
    p.press("C", hold_s=0.15, gap_s=1)
    p.run_seconds(400)


def goto(p, icon, tries=16):
    for _ in range(tries):
        if icon in p.frame()[1]:
            return True
        p.press("A", hold_s=0.12, gap_s=0.35)
    return False


def menu_tour(p):
    # every icon: select, browse with A, back out with C
    for icon in ["STATUS", "FEED", "TRAIN", "BATTLE", "FLUSH", "LIGHT", "MEDIC"]:
        goto(p, icon)
        p.press("B", hold_s=0.12, gap_s=0.6)
        for _ in range(6):
            p.press("A", hold_s=0.1, gap_s=0.4)
            p.press("B", hold_s=0.1, gap_s=0.4)
        p.run_seconds(8)
        for _ in range(4):
            p.press("C", hold_s=0.1, gap_s=0.4)
        p.run_seconds(2)


if scenario == "boot":
    p = h.Pet(ROM)
    p.run_seconds(120)
    p.reset()
    p.run_seconds(5)
    for b in "ABCABC":
        p.press(b, hold_s=0.12, gap_s=0.5)
    p.run_seconds(30)
elif scenario == "baby_life":
    p = fresh()
    hatch(p)
    menu_tour(p)
    p.run_seconds(3600)  # an hour of neglect: calls, poop, hunger
    menu_tour(p)
elif scenario == "child_life":
    p = pickle.load(open("st_v1_childA.pkl", "rb"))
    menu_tour(p)
    # train repeatedly (TRAIN then B, then mash A/B)
    for _ in range(4):
        goto(p, "TRAIN")
        p.press("B", hold_s=0.12, gap_s=0.6)
        for b in "ABABABAB":
            p.press(b, hold_s=0.08, gap_s=0.25)
        p.run_seconds(10)
    p.run_seconds(3 * 3600)  # hours of neglect: sickness, calls, poop
    menu_tour(p)
elif scenario == "night":
    p = pickle.load(open("st_v1_childA.pkl", "rb"))
    # 0x48-0x4B hold the clock as minute-units, minute-tens, hour (2 nibbles).
    # Jump to 19:58 so the bedtime/lights code runs, then to 06:58 for waking.
    for addr, v in zip(range(0x48, 0x4C), [8, 5, 0x3, 0x1]):
        p.poke(addr, v)
    p.run_seconds(2 * 3600)
    menu_tour(p)
    goto(p, "LIGHT")
    p.press("B", hold_s=0.12, gap_s=0.6)
    p.press("B", hold_s=0.12, gap_s=0.6)
    p.run_seconds(3600)
    for addr, v in zip(range(0x48, 0x4C), [8, 5, 0x6, 0x0]):
        p.poke(addr, v)
    p.run_seconds(3600)
    menu_tour(p)
elif scenario == "battle":
    import link as L
    import battle as BT
    for role in range(2):
        a = BT.load("st_v1_childA.pkl", None)
        b = BT.load("st_v1_childB.pkl", None)
        lk = L.Link(a, b)
        BT.goto_icon(lk, a, "BATTLE")
        BT.goto_icon(lk, b, "BATTLE")
        lk.press(a, "B", hold_s=0.15, gap_s=0.3)
        lk.press(b, "B", hold_s=0.15, gap_s=0.3)
        lk.press(a if role == 0 else b, "B", hold_s=0.15, gap_s=0.3)
        lk.run_seconds(30)
    # unlinked battle attempt (no partner) and cut link
    a = BT.load("st_v1_childA.pkl", None)
    lk = L.Link(a, BT.load("st_v1_childB.pkl", None))
    lk.tamper = lambda tag, w, i: None
    BT.goto_icon(lk, a, "BATTLE")
    lk.press(a, "B", hold_s=0.15, gap_s=0.3)
    lk.press(a, "B", hold_s=0.15, gap_s=0.3)
    lk.run_seconds(20)
elif scenario == "death":
    p = pickle.load(open("dead_pre.pkl", "rb"))
    p.run_seconds(120)
    for b in "ABC":
        p.press(b, hold_s=0.1, gap_s=0.4)
    p.press("A", "C", hold_s=0.2, gap_s=1.0)
    p.run_seconds(30)
elif scenario == "testmode":
    import link as L
    a = h.Pet(ROM)
    b = h.Pet(ROM)
    for p in (a, b):
        p.hold("A")
        p.cpu.port_handler("RES", 0, 0)
        p.run_seconds(0.05)
        p.cpu.port_handler("RES", 0, -1)
        p.run_seconds(1)
        p.release("A")
        p.run_seconds(1)
        for k in "BC":
            p.press(k, hold_s=0.15, gap_s=0.8)
            p.run_seconds(1.5)
    lk = L.Link(a, b)
    lk.press(a, "A", hold_s=0.15, gap_s=0.5)
    lk.run_seconds(3)
    for k in "ABCABC":
        lk.press(a, k, hold_s=0.15, gap_s=0.8)
        lk.run_seconds(2)
    for combo in ["B", "C", "AB", "AC", "BC", "ABC"]:
        p = h.Pet(ROM)
        p.hold(*combo)
        p.cpu.port_handler("RES", 0, 0)
        p.run_seconds(0.05)
        p.cpu.port_handler("RES", 0, -1)
        p.run_seconds(3)
        p.release(*combo)
        for k in "ABCABC":
            p.press(k, hold_s=0.15, gap_s=0.8)
        p.run_seconds(5)
elif scenario == "evolve":
    # walk the slot nibble through every value and let each form live a bit
    base = pickle.load(open("st_v1_childA.pkl", "rb"))
    for slot in range(0, 16):
        p = pickle.loads(pickle.dumps(base))
        p.poke(0xB, slot)
        p.run_seconds(120)
        menu_tour(p)
        g = p.cpu.get_mem
        m = g(0x48) + 10 * g(0x49)
        hr = g(0x4A) + 16 * g(0x4B)
        m2 = m + 2
        hr2 = hr + m2 // 60
        m2 %= 60
        for a, v in zip(range(0x4C, 0x50), [m2 % 10, m2 // 10, hr2 & 15, hr2 >> 4]):
            p.poke(a, v)
        p.run_seconds(600)
else:
    raise SystemExit("unknown scenario")

json.dump({"pcs": sorted(PCS),
           "mem": {"%03X" % a: {"r": sorted(v[0]), "w": sorted(v[1])} for a, v in MEM.items()}},
          open(out, "w"))
print(scenario, "executed PCs:", len(PCS))
