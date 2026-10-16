"""Dynamic coverage: record every PC the emulated CPU executes across scenarios.

usage: python3 coverage.py SCENARIO OUT.json [ROM]
Patches E0C6200.clock at class level so pickled pets are covered too.
"""
import os
import json
import pickle
import sys

import harness as h
from cores.E0C6200 import E0C6200

PCS = set()
_orig = E0C6200.clock


# --- task attribution: which main-loop task / interrupt is running each PC ---
TASKS = {0x01CA: "spine", 0x0900: "life", 0x07BF: "input", 0x0200: "input",
         0x0800: "life", 0x0A5D: "animation", 0x0B06: "link", 0x0B5B: "link",
         0x0410: "screens", 0x0A00: "sound", 0x0E7B: "rng", 0x016E: "factory_test"}
# The core vectors into page 1 of the CURRENT bank, so bank 1 has its own table.
VECS = {0x102: "irq_timer", 0x104: "irq_04", 0x106: "irq_k0", 0x108: "irq_08",
        0x10A: "irq_0A", 0x10C: "irq_prog_timer",
        0x1102: "irq_timer", 0x1104: "irq_04", 0x1106: "irq_k0", 0x1108: "irq_08",
        0x110A: "irq_0A", 0x110C: "irq_prog_timer"}
ATTR = {}
_ctx = {"cur": "spine", "stack": []}


def _attribute(self):
    pc = self._PC & 0x1FFF
    c = _ctx
    if pc in VECS:
        c["stack"].append((c["cur"], self._SP))
        c["cur"] = VECS[pc]
    else:
        # the stack starts at SP=0 and grows down through 0xFF, so compare
        # modulo 256: the handler has returned once SP climbs back >= 3 above entry
        while c["stack"] and 3 <= ((self._SP - c["stack"][-1][1]) & 0xFF) < 0x80:
            c["cur"] = c["stack"].pop()[0]
    if not c["stack"]:
        if pc in TASKS:
            c["cur"] = TASKS[pc]
        elif 0x0132 <= pc <= 0x016D or pc == 0x0100 or 0x010E <= pc <= 0x0131:
            c["cur"] = "spine"
    ATTR.setdefault(pc, set()).add(c["cur"])


def _clock(self):
    if not self._RESET and not self._HALT:
        PCS.add(self._PC & 0x1FFF)
        _attribute(self)
    _tick[0] += 1
    if _tick[0] % 40000 == 0 and not self._RESET:
        k = (self._RAM[0x09], self._RAM[0x0A])
        if k not in FRAMES:
            FRAMES[k] = list(self.get_VRAM())
    return _orig(self)


E0C6200.clock = _clock

MEM = {}
_og, _os = E0C6200.get_mem, E0C6200.set_mem


def _gm(self, addr):
    MEM.setdefault(addr, [set(), set()])[0].add(self._PC & 0x1FFF)
    return _og(self, addr)


TRANS = {}   # (old_mode, old_sub, new_mode, new_sub, pc) -> count
FRAMES = {}  # (mode, sub) -> VRAM snapshot (list)
_tick = [0]


def _sm(self, addr, value):
    MEM.setdefault(addr, [set(), set()])[1].add(self._PC & 0x1FFF)
    if addr in (0x09, 0x0A):
        old9, oldA = _og(self, 0x09), _og(self, 0x0A)
        r = _os(self, addr, value)
        new9, newA = _og(self, 0x09), _og(self, 0x0A)
        if (old9, oldA) != (new9, newA):
            k = (old9, oldA, new9, newA, self._PC & 0x1FFF)
            TRANS[k] = TRANS.get(k, 0) + 1
        return r
    return _os(self, addr, value)


E0C6200.get_mem, E0C6200.set_mem = _gm, _sm

scenario, out = sys.argv[1], sys.argv[2]
ROM = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("ROM", "roms/digimon_v1.bin")


def _reset_ctx():
    _ctx["cur"] = "spine"
    _ctx["stack"] = []


def fresh():
    _reset_ctx()
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
    # Real-time clock: M(1A-1B) seconds BCD, M(1C-1D) minutes BCD, M(1E) hour 1-12,
    # M(1F) bit0 = PM. Set 7:58 PM so the bedtime code runs, later 6:58 AM for waking.
    for addr, v in zip(range(0x1A, 0x20), [0, 0, 8, 5, 7, 1]):
        p.poke(addr, v)
    p.run_seconds(2 * 3600)
    menu_tour(p)
    goto(p, "LIGHT")
    p.press("B", hold_s=0.12, gap_s=0.6)
    p.press("B", hold_s=0.12, gap_s=0.6)
    p.run_seconds(3600)
    for addr, v in zip(range(0x1A, 0x20), [0, 0, 8, 5, 6, 0]):
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
           "mem": {"%03X" % a: {"r": sorted(v[0]), "w": sorted(v[1])} for a, v in MEM.items()},
           "transitions": [[*k, c] for k, c in TRANS.items()],
           "attr": {"%04X" % p: sorted(v) for p, v in ATTR.items()},
           "frames": {"%X%X" % k: v for k, v in FRAMES.items()}},
          open(out, "w"))
print(scenario, "executed PCs:", len(PCS))
