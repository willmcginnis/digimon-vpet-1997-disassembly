"""Count main-loop passes (calls of rng_step at 0E7B) and the carry flag on entry.

usage (PYTHONPATH=$BRICK): python3 rng_rate.py STATE.pkl [SECONDS]
The decimal half of the dice adds 73 plus the incoming carry (the routine never clears
it), so both the pass rate and the entry carry decide how the dice move.
"""
import collections
import pickle
import sys

import harness  # noqa: F401

pet = pickle.load(open(sys.argv[1], "rb"))
secs = float(sys.argv[2]) if len(sys.argv) > 2 else 42
cpu = pet.cpu
calls, carry = 0, collections.Counter()
end = pet.cycles + int(secs * harness.CLOCK)
while pet.cycles < end:
    if (cpu.pc() & 0x1FFF) == 0x0E7B and not cpu._HALT:
        calls += 1
        carry[cpu._CF] += 1
    c = cpu.clock()
    pet.ic.emit_clock(c)
    pet.cycles += c
print("%s: %d calls in %g s (%.2f per second); entry carry %s" % (
    sys.argv[1], calls, secs, calls / secs, dict(carry)))
