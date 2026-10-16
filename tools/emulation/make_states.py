"""Rebuild every saved emulator state the scenarios use, from power-on.

usage (from tools/emulation, with PYTHONPATH=$BRICK and ROM set):
    python3 make_states.py
Writes into the current directory:
    st_v1_egg_reset.pkl   fresh egg after reset
    st_v1_baby.pkl        clock set, hatched, 400 s old
    st_v1_childA.pkl      a child (slot 3), cleaned and fed: battle partner A
    st_v1_childB.pkl      the same child, partner B
    injured_pair.pkl      (A, B) after battling until one is injured
    dead_pre.pkl          the injured unit one minute before its death sequence
    dead_settled.pkl      the grave, 20 minutes after death
Each step is the procedure the article's experiments used.
"""
import os
import pickle

import harness as h
import link as L
import battle as BT

ROM = os.environ.get("ROM", "roms/digimon_v1.bin")


def save(obj, name):
    with open(name, "wb") as f:
        pickle.dump(obj, f)
    print("wrote", name)


# 1. egg after reset
p = h.Pet(ROM)
p.reset()
p.run_seconds(1)
save(p, "st_v1_egg_reset.pkl")

# 2. set the clock, hatch, let the baby live 400 s
p.press("B", hold_s=0.15, gap_s=1)
for _ in range(9):
    p.press("A", hold_s=0.1, gap_s=0.3)
p.press("C", hold_s=0.15, gap_s=1)
p.run_seconds(400)
save(p, "st_v1_baby.pkl")

# 3. wait for baby II (slot 2), then bring the next evolution forward to reach a child
g = p.cpu.get_mem
for hour in range(24):
    if g(0xB) >= 2:
        break
    p.run_seconds(3600)
assert g(0xB) == 2, "expected baby II, got slot %X" % g(0xB)
m = g(0x48) + 10 * g(0x49)
hr = g(0x4A) + 16 * g(0x4B)
m2 = m + 2
hr2 = hr + m2 // 60
m2 %= 60
for addr, v in zip(range(0x4C, 0x50), [m2 % 10, m2 // 10, hr2 & 15, hr2 >> 4]):
    p.poke(addr, v)
p.run_seconds(180)
assert g(0xB) >= 3, "evolution did not fire (slot %X)" % g(0xB)
child = p

# 4. two cleaned, fed copies for linked battles
a = pickle.loads(pickle.dumps(child))
b = pickle.loads(pickle.dumps(child))
lk = L.Link(a, b)
for pet in (a, b):
    BT.flush(lk, pet)
    BT.feed(lk, pet, 4, 2)
save(a, "st_v1_childA.pkl")
save(b, "st_v1_childB.pkl")

# 5. battle until one unit is injured
for i in range(30):
    BT.goto_icon(lk, a, "BATTLE")
    BT.goto_icon(lk, b, "BATTLE")
    lk.press(a, "B", hold_s=0.15, gap_s=0.3)
    lk.press(b, "B", hold_s=0.15, gap_s=0.3)
    lk.press(a, "B", hold_s=0.15, gap_s=0.3)
    lk.run_seconds(26)
    if a.cpu.get_mem(5) & 1 or b.cpu.get_mem(5) & 1:
        break
save((a, b), "injured_pair.pkl")

# 6. leave the injured one untreated until the death sequence begins
pet = b if b.cpu.get_mem(5) & 1 else a
prev = pickle.dumps(pet)
for minute in range(24 * 60):
    pet.run_seconds(60)
    if pet.cpu.get_mem(0x9) in (0xB, 0xC):
        break
    prev = pickle.dumps(pet)
open("dead_pre.pkl", "wb").write(prev)
print("wrote dead_pre.pkl (death began after %d minutes)" % (minute + 1))
pet.run_seconds(1200)
save(pet, "dead_settled.pkl")
