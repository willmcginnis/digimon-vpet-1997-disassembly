"""Static control-flow recovery for E0C6200-family ROMs (Digimon V-Pet 1997).

Semantics follow BrickEmuPy's core (cores/E0C6200.py), which runs the game:
  * PSET p sets the (bank, page) used by the very next jump/call only.
  * JP/JP cc/CALL/JPBA without PSET stay in the current bank and page.
  * CALZ goes to page 0 of the current bank (or the PSET bank).
  * RET/RETS/RETD restore page+step but keep the CURRENT bank.
  * RETS returns to the call site + 2 (skips one instruction).
  * JPBA jumps to step B<<4 | A; B is resolved from a preceding "ld B, i".

Usage:  python3 walker.py ROM.bin OUTDIR [BRICKEMUPY_DIR]
Writes OUTDIR/static.json with words, functions, call graph, RAM xrefs.
"""
import json
import os
import sys
from collections import defaultdict, deque

BRICK = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("BRICK", "")
if BRICK:
    sys.path.insert(0, BRICK)
from dasm_fixed import FixedDasm as E0C6200dasm  # noqa: E402

ROM_WORDS = 0x2000
RESET = 0x100
VECTORS = {0x100: "reset_vector", 0x102: "irq_vec_02", 0x104: "irq_vec_04",
           0x106: "irq_vec_06", 0x108: "irq_vec_08", 0x10A: "irq_vec_0A",
           0x10C: "irq_vec_0C"}


def load(path):
    data = open(path, "rb").read()
    return [((data[2 * i] << 8) | data[2 * i + 1]) & 0xFFF for i in range(len(data) // 2)]


def kind(op):
    hi = op >> 8
    if hi == 0x0:
        return "jp"
    if hi == 0x1:
        return "retd"
    if hi in (0x2, 0x3, 0x6, 0x7):
        return "jcc"
    if hi == 0x4:
        return "call"
    if hi == 0x5:
        return "calz"
    if op & 0xFE0 == 0xE40:
        return "pset"
    if op == 0xFE8:
        return "jpba"
    if op == 0xFDF:
        return "ret"
    if op == 0xFDE:
        return "rets"
    if op in (0xFF8, 0xFF9):
        return "halt"
    return "op"


def nxt(pc):
    return (pc & 0x1000) | ((pc + 1) & 0xFFF)


def target(pc, op, pset):
    """Destination of a jp/jcc/call at pc given an optional preceding PSET."""
    if pset is not None:
        base = (pset << 8) & 0x1F00
    else:
        base = pc & 0x1F00
    return base | (op & 0xFF)


def calz_target(pc, pset):
    bank = ((pset << 8) & 0x1000) if pset is not None else (pc & 0x1000)
    return bank


class Walker:
    def __init__(self, words):
        self.w = words
        self.dasm = E0C6200dasm()
        self.reached = {}            # pc -> set of roles
        self.edges = defaultdict(set)  # pc -> successors (intra-procedural)
        self.calls = defaultdict(set)  # call site -> callee
        self.call_sites = defaultdict(set)  # callee -> call sites
        self.jpba = {}               # pc -> dict(info)
        self.entries = set(VECTORS)
        self.rets_callees = set()

    def text(self, pc):
        op = self.w[pc]
        prev = self.w[pc - 1] if pc else 0
        p = pc
        if prev & 0xFE0 == 0xE40:
            p = (prev << 8) & 0x1F00 | (pc & 0xFF)
        try:
            return self.dasm._instruction_tbl[op](self.dasm, p, op)
        except Exception:
            return "dw 0x%03X" % op

    def resolve_b(self, pc):
        """Walk back through straight-line code for 'ld B, i' (0xE1i).
        Returns (list_of_B_values or None, where). Understands the
        'ld B,i ... rlc B' doubling idiom used to index 32-entry tables."""
        cur = pc
        doublings = 0
        self._a_even = False
        for _ in range(12):
            cur = (cur & 0x1000) | ((cur - 1) & 0xFFF)
            op = self.w[cur]
            k = kind(op)
            if op & 0xFF0 == 0xE10:
                vals = {op & 0xF}
                for _ in range(doublings):
                    vals = {((v << 1) | c) & 0xF for v in vals for c in (0, 1)}
                return sorted(vals), cur
            t = self.text(cur)
            mnem, _, rest = t.partition(" ")
            dest = rest.split(",")[0].strip()
            if mnem == "rlc" and dest == "B":
                doublings += 1
                continue
            if mnem == "rlc" and dest == "A" and self.text((cur & 0x1000) | ((cur - 1) & 0xFFF)) == "rcf":
                self._a_even = True
                continue
            if dest == "B" and mnem not in ("cp", "fan", "push"):
                return None, cur
            if k in ("jp", "ret", "rets", "retd", "jpba"):
                return None, cur
        return None, cur

    def run(self, extra_entries=()):
        self.skip_sites = defaultdict(set)
        work = deque()
        for e in list(self.entries):
            work.append((e, None, "entry"))
        for e in extra_entries:
            prev = self.w[(e & 0x1000) | ((e - 1) & 0xFFF)]
            ctx = (prev & 0x1F) if kind(prev) == "pset" else None
            work.append((e, ctx, "measured"))
        seen_state = set()
        self._seen_state = seen_state
        self._work = work
        while True:
            self._drain()
            added = 0
            for callee, body in self.functions().items():
                if not any(kind(self.w[p]) == "rets" for p in body):
                    continue
                for site in self.skip_sites.get(callee, ()):
                    ret_to = nxt(nxt(site))
                    if (ret_to, None) not in seen_state:
                        work.append((ret_to, None, "code"))
                        self.edges[site].add(ret_to)
                        added += 1
            if not added:
                break
        return self

    def _drain(self):
        work, seen_state = self._work, self._seen_state
        while work:
            pc, pset, role = work.popleft()
            if (pc, pset) in seen_state:
                continue
            seen_state.add((pc, pset))
            while True:
                if pc >= len(self.w):
                    break
                op = self.w[pc]
                k = kind(op)
                self.reached.setdefault(pc, set()).add(role if role != "entry" else "code")
                role = "code"
                if k == "pset":
                    n = nxt(pc)
                    self.edges[pc].add(n)
                    work.append((n, op & 0x1F, "code"))
                    break
                if k == "jp":
                    t = target(pc, op, pset)
                    self.edges[pc].add(t)
                    work.append((t, None, "code"))
                    break
                if k == "jcc":
                    t = target(pc, op, pset)
                    n = nxt(pc)
                    self.edges[pc].update((t, n))
                    work.append((t, None, "code"))
                    pset = None
                    pc = n
                    continue
                if k in ("call", "calz"):
                    t = target(pc, op, pset) if k == "call" else (calz_target(pc, pset) | (op & 0xFF))
                    self.calls[pc].add(t)
                    self.call_sites[t].add(pc)
                    if t not in self.entries:
                        self.entries.add(t)
                        work.append((t, None, "code"))
                    n = nxt(pc)
                    self.edges[pc].add(n)
                    # RETS would return past the next instruction; resolved after
                    # the pass, only for callees that can actually execute RETS.
                    self.skip_sites[t].add(pc)
                    pset = None
                    pc = n
                    continue
                if k == "jpba":
                    b, where = self.resolve_b(pc)
                    if pset is not None:
                        base = (pset << 8) & 0x1F00
                    else:
                        base = pc & 0x1F00
                    info = {"base": base, "b": b, "b_from": where, "targets": []}
                    if b is not None:
                        for bv in b:
                            for a in range(0, 16, 2 if self._a_even else 1):
                                t = base | (bv << 4) | a
                                info["targets"].append(t)
                                self.edges[pc].add(t)
                                work.append((t, None, "jpba_entry"))
                    self.jpba[pc] = info
                    break
                if k in ("ret", "rets", "retd"):
                    break
                n = nxt(pc)
                self.edges[pc].add(n)
                pset = None
                pc = n

    def functions(self):
        """Assign reachable words to functions (entry = call target or vector)."""
        funcs = {}
        for e in sorted(self.entries):
            body = set()
            stack = [e]
            while stack:
                p = stack.pop()
                if p in body or p not in self.reached:
                    continue
                body.add(p)
                for s in self.edges.get(p, ()):
                    stack.append(s)
            funcs[e] = body
        return funcs


def ram_refs(words, reached):
    """Direct RAM nibble references: ld A/B,M(i); ld M(i),A/B (0xFA_, 0xFB_, 0xF8_, 0xF9_),
    and the X/Y loads that set up M(X)/M(Y) pointers (ld X,xx 0xBxx; ld Y,yy 0x8yy)."""
    refs = defaultdict(lambda: {"r": set(), "w": set(), "ptr": set()})
    for pc in reached:
        op = words[pc]
        if op & 0xFF0 == 0xFA0:
            refs[op & 0xF]["r"].add(pc)
        elif op & 0xFF0 == 0xFB0:
            refs[op & 0xF]["r"].add(pc)
        elif op & 0xFF0 == 0xF80:
            refs[op & 0xF]["w"].add(pc)
        elif op & 0xFF0 == 0xF90:
            refs[op & 0xF]["w"].add(pc)
        elif op & 0xF00 == 0xB00:
            refs[op & 0xFF]["ptr"].add(pc)
        elif op & 0xF00 == 0x800:
            refs[op & 0xFF]["ptr"].add(pc)
    return refs


def main():
    rom, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    words = load(rom)
    seeds = []
    seed_file = os.environ.get("SEED_PCS")  # JSON list of executed PCs (measured)
    if seed_file and os.path.exists(seed_file):
        seeds = json.load(open(seed_file))
    W = Walker(words)
    W.run()
    # Second pass: only measured PCs the static pass missed, entered with the
    # PSET context of the preceding word (a seed right after PSET must not
    # be treated as a same-page jump/call).
    missed = [p for p in seeds if p not in W.reached]
    W.run(extra_entries=missed)
    funcs = W.functions()
    owner = defaultdict(list)
    for e, body in funcs.items():
        for p in body:
            owner[p].append(e)
    res = {
        "rom": os.path.basename(rom),
        "words": len(words),
        "reached": sorted(W.reached),
        "roles": {"%04X" % p: sorted(r) for p, r in W.reached.items()},
        "functions": {"%04X" % e: {
            "body": sorted(b),
            "size": len(b),
            "callers": sorted("%04X" % s for s in W.call_sites.get(e, ())),
            "callees": sorted({"%04X" % t for p in b for t in W.calls.get(p, ())}),
            "is_vector": e in VECTORS,
            "vector_name": VECTORS.get(e),
        } for e, b in funcs.items()},
        "jpba": {"%04X" % p: {"base": "%04X" % i["base"],
                              "b": i["b"], "targets": ["%04X" % t for t in i["targets"]]}
                 for p, i in W.jpba.items()},
        "text": {"%04X" % p: W.text(p) for p in range(len(words))},
        "shared_words": sum(1 for p, o in owner.items() if len(o) > 1),
    }
    json.dump(res, open(os.path.join(out, "static.json"), "w"))
    unresolved = [p for p, i in W.jpba.items() if i["b"] is None]
    print("reached words: %d / %d" % (len(W.reached), len(words)))
    print("functions (call targets + vectors): %d" % len(funcs))
    print("jpba sites: %d (unresolved B: %d -> %s)" % (len(W.jpba), len(unresolved),
          " ".join("%04X" % p for p in unresolved)))
    print("words shared by >1 function: %d" % res["shared_words"])


if __name__ == "__main__":
    main()
