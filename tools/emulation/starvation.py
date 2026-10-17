"""How long an unanswered call (an empty heart) takes to kill, measured in emulated time.

usage (PYTHONPATH=$BRICK, from tools/emulation):
    python3 starvation.py STATE.pkl START_HOURS OUT.json

From a saved unit, the clock is set to 8:00 AM and the bedtime M(66) to 10 PM so that the
Digimon stays awake throughout. The call state is started the way 09DB starts it (call
bit M(06).0 and alert bit .3 set, the empty-heart mask M(65) = 4, the call timer
M(40-43) cleared), with the hour counter M(42) preset to START_HOURS so a long wait can
be bracketed in two shorter runs. No button is pressed. Every emulated minute the call
timer, care mistakes M(31) and the mode are logged until the mode becomes B (dying) or
14 emulated hours pass.
"""
import json
import pickle
import sys

import harness  # noqa: F401

pet = pickle.load(open(sys.argv[1], "rb"))
start = int(sys.argv[2])
g, poke = pet.cpu.get_mem, pet.poke
for a, v in zip(range(0x1A, 0x20), [0, 0, 0, 0, 8, 0]):   # 8:00:00 AM
    poke(a, v)
poke(0x66, 10)
poke(0x67, 8)
poke(0x65, 4)
poke(0x06, (g(0x06) | 0x9) & 0xB)
for a, v in zip(range(0x40, 0x44), [0, 0, start, 0]):
    poke(a, v)
log = []
for minute in range(14 * 60):
    pet.run_seconds(60)
    row = {"minute": minute + 1, "mode": g(0x09), "M06": g(0x06),
           "call_min": g(0x41) * 10 + g(0x40), "call_hours": g(0x42), "M43": g(0x43),
           "care_mistakes": g(0x31)}
    log.append(row)
    if row["mode"] in (0xB, 0xC):
        break
json.dump({"start_hours": start, "log": log}, open(sys.argv[3], "w"))
last = log[-1]
print("start", start, "-> ended after", last["minute"], "min, mode %X" % last["mode"], last)
