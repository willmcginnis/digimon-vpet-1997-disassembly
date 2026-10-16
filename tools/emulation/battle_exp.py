"""Battle experiments on two linked emulated V1 pets.

1. normal       - plain battle; who wins and when it was decided
2. flip         - man-in-the-middle flips the initiator's outcome packet
3. cut_after_p1 - prongs separated right after packet 1 exchange (decision made, not sent)
4. cut_before   - prongs separated before the initiator's first packet arrives
5. sweep        - many battles started at different moments; win rate vs RNG nibble
"""
import pickle
import sys

import harness as h
import link as L
import battle as BT
import battletrace as T


def rev(w):
    return int("{:016b}".format(w)[::-1], 2)


def outcome_of(p):
    # 0x79 holds this device's own result: 1 = win, 2 = lose (see 0xDE4 / 0xEB7)
    return {1: "WIN", 2: "LOSE"}.get(p.cpu.get_mem(0x79), "none(%X)" % p.cpu.get_mem(0x79))


def run(tamper=None, pre_wait=0.0, secs=25):
    a, b, lk = T.setup(pre_wait=pre_wait)
    a.poke(0x79, 0)
    b.poke(0x79, 0)
    lk.tamper = tamper
    rng_at = {}
    cpu = a.cpu
    orig = cpu.get_mem

    def gm(addr, _o=orig):
        if addr == 0xA3 and cpu.pc() == 0xDE0:
            rng_at["A3"] = _o(addr)
        return _o(addr)

    cpu.get_mem = gm
    lk.press(a, "B", hold_s=0.15, gap_s=0.3)
    lk.run_seconds(secs)
    cpu.get_mem = orig
    pk = " ".join("%s:%04X" % (d, rev(w)) for _t, d, w in lk.log)
    return a, b, pk, rng_at.get("A3")


def flip(tag, word, idx):
    # initiator's 2nd packet carries its outcome; swap 1<->2 (and the inverted copy)
    if tag == "A>B" and idx == 3:
        v = rev(word)
        out = v & 0xF
        new_out = {1: 2, 2: 1}.get(out, out)
        v = (v & 0xF0F0) | (((~new_out) & 0xF) << 8) | new_out
        return rev(v)
    return word


def cut_after_p1(tag, word, idx):
    return word if idx <= 2 else None


def cut_before(tag, word, idx):
    return None


mode = sys.argv[1] if __name__ == "__main__" else ""
if mode in ("normal", "flip", "cut_after_p1", "cut_before"):
    tam = {"normal": None, "flip": flip, "cut_after_p1": cut_after_p1, "cut_before": cut_before}[mode]
    a, b, pk, r = run(tam)
    print("mode=%s packets: %s" % (mode, pk or "(none)"))
    print("initiator RNG nibble 0xA3 at decision:", "-" if r is None else "%X" % r)
    print("A (initiator): %s   B (responder): %s" % (outcome_of(a), outcome_of(b)))
    a.png("final_%s_A.png" % mode)
    b.png("final_%s_B.png" % mode)
elif mode == "sweep":
    n = int(sys.argv[2])
    rows = []
    for i in range(n):
        a, b, pk, r = run(None, pre_wait=0.37 * i, secs=2)
        rows.append((r, outcome_of(a), outcome_of(b)))
        print("start+%.2fs A3=%s A:%s B:%s" % (0.37 * i, "-" if r is None else "%X" % r, rows[-1][1], rows[-1][2]), flush=True)
    pickle.dump(rows, open("sweep_rows.pkl", "wb"))

if mode == "sweep_enh":
    want = int(sys.argv[3], 16)

    def spoof_enh(tag, word, idx):
        if tag == "B>A" and idx == 2:
            v = rev(word)
            slot = v & 0xF
            v = (((~want) & 0xF) << 12) | (((~slot) & 0xF) << 8) | (want << 4) | slot
            return rev(v)
        return word

    n = int(sys.argv[2])
    for i in range(n):
        a, b, pk, r = run(spoof_enh, pre_wait=0.37 * i, secs=2)
        print("A3=%s A:%s" % ("-" if r is None else "%X" % r, outcome_of(a)), flush=True)
