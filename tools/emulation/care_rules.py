"""Measure the care and evolution rules by executing the firmware's own routines.

usage (PYTHONPATH=$BRICK, from tools/emulation):
    python3 care_rules.py STATE.pkl OUT.json

STATE.pkl is any saved unit (make_states.py writes st_v1_childA.pkl); it supplies a
realistic RAM image. Each experiment pokes the inputs, starts the CPU at a routine's
entry with interrupts off and a fake return frame on the stack, and steps until the
routine returns to the sentinel address 0x132. Nothing is paraphrased from the code:
the numbers in OUT.json are what the routines computed.

Experiments
  evolution   0D10 for slots 2, 3, 4 over care mistakes M(31), overfeed M(32), sleep
              disturbances M(33), training M(34-35): the slot it picks.
  species     0C17 (the per-evolution setup) for every slot and several dice values:
              bedtime M(66), wake hour M(67), base weight M(68-69) (BCD grams), the
              table's flag nibble M(77), and the next-evolution stage time M(4C-4F) as
              minutes and hours for the extreme dice values.
  perfect     0D10 for an adult (slot 5) and a child (slot 3) over battles M(99),
              win score M(98) and the dice nibble M(A3): evolves or not, and whether the
              "qualified" bit M(76).0 is set.
  injuries    set_injured (0510) with the injury count M(36-37) at 18 and 19.
  old_age     the care-mistake tick (08C8) with M(76).1 set and M(75) at 3 and 4.
  injury_roll the post-battle injury roll (01EC) per slot and protein-overdose count
              M(62): how many of the 16 dice values M(A3) leave the unit injured.
  evolution_resets  which counters 0C17 clears when a Digimon evolves.
"""
import json
import pickle
import sys

import harness  # noqa: F401  (puts BrickEmuPy on the path)

SENTINEL = 0x132


def load(path):
    with open(path, "rb") as f:
        return pickle.load(f)


class Runner:
    def __init__(self, pet):
        self.base = pickle.dumps(pet)

    def run(self, entry, pokes, max_steps=200000):
        pet = pickle.loads(self.base)
        cpu = pet.cpu
        for a, v in pokes.items():
            cpu.set_mem(a, v & 0xF)
        # return frame: PCSL, PCSH, PCP of 0x132
        cpu.set_mem(0xF0, SENTINEL & 0xF)
        cpu.set_mem(0xF1, SENTINEL >> 4 & 0xF)
        cpu.set_mem(0xF2, SENTINEL >> 8 & 0xF)
        cpu._SP = 0xF0
        cpu._IF = 0
        cpu._HALT = 0
        cpu._PC = cpu._NPC = entry
        for _ in range(max_steps):
            if (cpu.pc() & 0xFFF) == SENTINEL:
                return cpu
            cpu.clock()
        raise RuntimeError("no return from %04X" % entry)


def mem(cpu, *addrs):
    return [cpu.get_mem(a) for a in addrs]


def training_pokes(t):
    return {0x34: t & 0xF, 0x35: t >> 4}


def main():
    pet = load(sys.argv[1])
    R = Runner(pet)
    out = {}

    # --- evolution choice -------------------------------------------------
    ev = {}
    for slot in (2, 3, 4):
        for cm in range(0, 7):
            for t in (0, 4, 5, 7, 8, 15, 16, 31, 32, 47, 48, 63):
                for of in range(0, 7):
                    for sd in (0, 4, 5, 6, 7, 8, 9, 12):
                        p = {0x0B: slot, 0x31: cm, 0x32: of, 0x33: sd, 0x76: 0, 0x99: 0}
                        p.update(training_pokes(t))
                        cpu = R.run(0x0D10, p)
                        ev["%X,%d,%d,%d,%d" % (slot, cm, t, of, sd)] = cpu.get_mem(0x0B)
    out["evolution"] = ev

    # --- per-species setup --------------------------------------------------
    sp = {}
    for slot in range(0, 15):
        rows = []
        # the stage timer and its target start from zero at hatching (0823 clears 30-9F)
        # every dice nibble the setup can read is set explicitly (A1 decides Botamon's branch)
        for a0, a1, a2, clock_min_tens in ((0, 0, 0, 0), (9, 4, 4, 5), (0, 5, 5, 0), (9, 9, 15, 5)):
            cpu = R.run(0x0C17, {0x0B: slot, 0xA0: a0, 0xA1: a1, 0xA2: a2, 0xA3: 0,
                                 0x1D: clock_min_tens, 0x4C: 0, 0x4D: 0, 0x4E: 0, 0x4F: 0})
            m4c, m4d, m4e, m4f = mem(cpu, 0x4C, 0x4D, 0x4E, 0x4F)
            rows.append({"dice_A0": a0, "dice_A1": a1, "dice_A2": a2, "clock_min_tens": clock_min_tens,
                         "next_evo_minutes": m4d * 10 + m4c, "next_evo_hours": m4f * 16 + m4e,
                         "raw_4C_4F": [m4c, m4d, m4e, m4f]})
        cpu = R.run(0x0C17, {0x0B: slot})
        sp["%X" % slot] = {"bedtime_M66": cpu.get_mem(0x66), "wake_M67": cpu.get_mem(0x67),
                           "M68": cpu.get_mem(0x68), "M69": cpu.get_mem(0x69),
                           "M77": cpu.get_mem(0x77), "timer": rows}
    out["species"] = sp

    # --- perfect evolution roll --------------------------------------------
    pf = {}
    for slot in (3, 5):
        for battles in (0xE, 0xF):
            for ws in range(16):
                for a3 in range(16):
                    cpu = R.run(0x0D10, {0x0B: slot, 0x99: battles, 0x98: ws, 0xA3: a3, 0x76: 0,
                                         0x31: 0, 0x34: 0, 0x35: 3})
                    pf["%X,%X,%d,%d" % (slot, battles, ws, a3)] = {
                        "slot_after": cpu.get_mem(0x0B), "M76": cpu.get_mem(0x76)}
    out["perfect"] = pf

    # --- injury count -----------------------------------------------------------
    inj = {}
    for count in (18, 19):
        cpu = R.run(0x0510, {0x05: 0, 0x36: count % 10, 0x37: count // 10, 0x09: 0, 0x0B: 3})
        inj[str(count)] = {"mode_after": cpu.get_mem(0x09), "count_after":
                           cpu.get_mem(0x37) * 10 + cpu.get_mem(0x36), "M05": cpu.get_mem(0x05)}
    out["injuries"] = inj

    # --- old age -----------------------------------------------------------------
    oa = {}
    for m75 in (3, 4):
        for m76 in (0, 2):
            cpu = R.run(0x08C8, {0x75: m75, 0x76: m76, 0x09: 0, 0x05: 0, 0x06: 0, 0x0B: 5})
            oa["M75=%d,M76=%d" % (m75, m76)] = {"mode_after": cpu.get_mem(0x09),
                                               "M75_after": cpu.get_mem(0x75), "M76_after": cpu.get_mem(0x76)}
    out["old_age"] = oa

    # --- injury roll after a battle ------------------------------------------
    ir = {}
    for slot in range(3, 15):
        for od in range(16):
            n = 0
            for a3 in range(16):
                cpu = R.run(0x01EC, {0x0B: slot, 0x62: od, 0xA3: a3, 0x05: 0, 0x36: 0, 0x37: 0,
                                     0x09: 0})
                n += cpu.get_mem(0x05) & 1
            ir["%X,%d" % (slot, od)] = n
    out["injury_roll"] = ir

    # --- what the per-evolution setup resets ----------------------------------
    keep = {0x31: 3, 0x32: 4, 0x33: 5, 0x34: 6, 0x35: 1, 0x36: 7, 0x37: 1, 0x62: 9,
            0x75: 2, 0x76: 1, 0x98: 11, 0x99: 15}
    cpu = R.run(0x0C17, {**keep, 0x0B: 5})
    out["evolution_resets"] = {"%02X" % a: [v, cpu.get_mem(a)] for a, v in keep.items()}

    json.dump(out, open(sys.argv[2], "w"), indent=1, sort_keys=True)
    print("wrote", sys.argv[2], {k: len(v) for k, v in out.items()})


if __name__ == "__main__":
    main()
