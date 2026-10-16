"""Tiny E0C6200 assembler built by inverting BrickEmuPy's disassembler.

Every 12-bit opcode is disassembled once with a fixed pc; flow instructions
(jp/jp cc/call/callz/retd) carry their operand in the low byte, so they are
re-encoded from the printed target. Everything else maps text -> opcode 1:1.

usage: python3 asm.py LISTING.asm OUT.bin [BRICK]
Listing lines look like:   "0D7A:  ld A, M(0xB)    ; comment"
Labels ("name:"), blank lines and lines starting with ';' are ignored.
"""
import re
import sys

BRICK = sys.argv[3] if len(sys.argv) > 3 else ""
if BRICK:
    sys.path.insert(0, BRICK)
from dasm_fixed import FixedDasm as E0C6200dasm, canonical  # noqa: E402

FLOW = {"jp": 0x0, "retd": 0x1, "call": 0x4, "callz": 0x5}
JCC = {"c": 0x2, "nc": 0x3, "z": 0x6, "nz": 0x7}


def norm(t):
    return re.sub(r"\s+", " ", t.strip())


def build_table():
    d = E0C6200dasm()
    table = {}
    for op in range(0x1000):
        if op >> 8 in (0x0, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7):
            continue
        t = norm(d._instruction_tbl[op](d, 0, op))
        # first encoding wins, except that a canonical form displaces a
        # non-canonical alias (rlc r); remaining aliases fail the round trip
        if t not in table or (canonical(op) == op and canonical(table[t]) != table[t]):
            table[t] = op
    return table


def encode(text, table):
    t = norm(text)
    m = re.fullmatch(r"(jp|call|callz) ([0-9A-Fa-f]{4})", t)
    if m:
        return (FLOW[m.group(1)] << 8) | (int(m.group(2), 16) & 0xFF)
    m = re.fullmatch(r"jp (c|nc|z|nz), ([0-9A-Fa-f]{4})", t)
    if m:
        return (JCC[m.group(1)] << 8) | (int(m.group(2), 16) & 0xFF)
    m = re.fullmatch(r"retd 0x([0-9A-Fa-f]{2})", t)
    if m:
        return 0x100 | int(m.group(1), 16)
    m = re.fullmatch(r"dw 0x([0-9A-Fa-f]{3})", t)
    if m:
        return int(m.group(1), 16)
    return table[t]


def main():
    src, out = sys.argv[1], sys.argv[2]
    table = build_table()
    words = {}
    for ln, line in enumerate(open(src, encoding="utf-8"), 1):
        body = line.split(";", 1)[0].rstrip()
        m = re.match(r"\s*([0-9A-Fa-f]{4}):\s+(\S.*)$", body)
        if not m:
            continue
        addr = int(m.group(1), 16)
        try:
            words[addr] = encode(m.group(2), table)
        except KeyError:
            raise SystemExit("line %d: cannot encode %r" % (ln, m.group(2)))
    n = max(words) + 1
    missing = [a for a in range(n) if a not in words]
    if missing:
        raise SystemExit("missing addresses, first: %04X" % missing[0])
    # each 12-bit word sits in a 16-bit big-endian slot; the top nibble is zero
    # in every word of both dumps (checked), so nothing else needs carrying.
    open(out, "wb").write(b"".join(bytes([(words[a] >> 8) & 0xF, words[a] & 0xFF]) for a in range(n)))
    print("assembled %d words" % n)


if __name__ == "__main__":
    main()
