"""Measure the battle threshold table by executing battle_outcome_roll on the emulated CPU.

usage (PYTHONPATH=$BRICK):
    python3 threshold.py ROM OUT.json [ENTRY] [--patch ADDR=OP ...]

ENTRY is the routine's address (0D7A in Ver. 1, 0D7E in Ver. 2). For every pair of
own slot M(0B) and opponent slot M(7F) from 3 to E, with both enhancements M(7B) and
M(7E) at 0, the CPU is started at ENTRY with interrupts off and stepped until it
reaches the compare `ld X, 0xA3` (ENTRY + 0x65); register A then holds the threshold.
The initiator wins iff M(A3) >= threshold, so its chance is (16 - threshold) / 16.

--patch rewrites ROM words before running (a what-if, never a claim about the device):
    --patch 0D84=DDB  turns `cp A, 0xB` into `cp B, 0xB` at 0D84.
A second table with the opponent's enhancement swept from -4 to +4 is written for the
child-against-child pairing 3,3 under the key "enh".
"""
import json
import os
import sys
import tempfile

import harness as h

args = [a for a in sys.argv[1:] if not a.startswith("--")]
patches = {}
if "--patch" in sys.argv:
    for a in sys.argv[sys.argv.index("--patch") + 1:]:
        addr, op = a.split("=")
        patches[int(addr, 16)] = int(op, 16)
rom, out = args[0], args[1]
entry = int(args[2], 16) if len(args) > 2 and "=" not in args[2] else 0x0D7A
stop = entry + 0x65

if patches:
    data = bytearray(open(rom, "rb").read())
    for a, op in patches.items():
        data[2 * a], data[2 * a + 1] = op >> 8, op & 0xFF
    fd, rom = tempfile.mkstemp(suffix=".bin")
    os.write(fd, bytes(data))
    os.close(fd)

pet = h.Pet(rom, link=False)
cpu = pet.cpu


def threshold(own, opp, own_enh=0, opp_enh=0):
    cpu.set_mem(0x0B, own)
    cpu.set_mem(0x7F, opp)
    cpu.set_mem(0x7B, own_enh)
    cpu.set_mem(0x7E, opp_enh)
    cpu._IF = 0
    cpu._HALT = 0
    cpu._PC = cpu._NPC = entry
    for _ in range(200):
        if cpu.pc() == stop:
            return cpu._A
        cpu.clock()
    raise RuntimeError("did not reach %04X from %d,%d" % (stop, own, opp))


table = {"%X,%X" % (a, b): threshold(a, b) for a in range(3, 15) for b in range(3, 15)}
# enhancement: own 4, opponent 0..8 gives an opponent-minus-own difference of -4..+4
table["enh"] = {str(d): threshold(3, 3, 4, 4 + d) for d in range(-4, 5)}
json.dump(table, open(out, "w"), indent=0, sort_keys=True)
print(out, "entry %04X" % entry, "patches", {"%04X" % a: "%03X" % o for a, o in patches.items()})
