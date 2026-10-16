"""Hatch a Digimon, then neglect it, logging the screen hourly until it looks dead.

argv: rom_path out_dir max_hours
Writes out_dir/hNNN.txt (ascii frame + RAM dump) every emulated hour, and
out_dir/state.pkl (pickled Pet) at the end so later runs can resume.
"""
import os
import pickle
import sys

import harness as h

rom, out, max_hours = sys.argv[1], sys.argv[2], int(sys.argv[3])
os.makedirs(out, exist_ok=True)
p = h.Pet(rom)
p.reset()
p.run_seconds(1)
p.press("B", hold_s=0.15, gap_s=1)
for _ in range(9):
    p.press("A", hold_s=0.1, gap_s=0.3)
p.press("C", hold_s=0.15, gap_s=1)

for hour in range(max_hours):
    for _ in range(60):
        p.run_seconds(60)
    ram = "".join("%X" % p.cpu.get_mem(a) for a in range(0x280))
    with open(os.path.join(out, "h%03d.txt" % hour), "w") as f:
        f.write(p.ascii() + "\n" + ram + "\n")
    print(hour, p.frame()[1], flush=True)
    try:
        with open(os.path.join(out, "state.pkl"), "wb") as f:
            pickle.dump(p, f)
    except Exception as e:  # pickling is best-effort
        print("pickle failed:", e, flush=True)
