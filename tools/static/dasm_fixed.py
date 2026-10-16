"""BrickEmuPy's E0C6200 disassembler with three fixes found by the round-trip test.

1. Opcodes 0xA70-0xA7F are CP YL,i (the core executes _cp_yl_i as a compare),
   but the disassembler prints them as "adc YL, i", aliasing 0xA30-0xA3F.
2. Opcodes 0xF70-0xF7F are DEC M(n) but print as "inc M(n)" (neither ROM uses them).
3. RLC r is encoded 1010 1111 r1 r0 r1 r0 (register field repeated). The text
   is unchanged; the assembler emits the canonical repeated-field form.
"""
from cores.E0C6200dasm import E0C6200dasm


def _cp_yl_i(self, pc, opcode):
    return "cp YL, " + self._nibbase % (opcode & 0x00F)


def _dec_mn(self, pc, opcode):
    return "dec M(" + self._nibbase % (opcode & 0x00F) + ")"


E0C6200dasm._cp_yl_i = _cp_yl_i
E0C6200dasm._dec_mn = _dec_mn


class FixedDasm(E0C6200dasm):
    def __init__(self):
        super().__init__()
        tbl = list(self._instruction_tbl)
        for op in range(0xA70, 0xA80):
            tbl[op] = _cp_yl_i
        for op in range(0xF70, 0xF80):
            tbl[op] = _dec_mn
        self._instruction_tbl = tuple(tbl)


def canonical(op):
    """Pick the canonical encoding when several opcodes print identically."""
    if op & 0xFF0 == 0xAF0:  # rlc r: r1 r0 r1 r0
        r = op & 0x3
        return 0xAF0 | (r << 2) | r
    if op & 0xFF0 in (0xEE0, 0xEF0) and op & 0xF in (0x0, 0x5, 0xA, 0xF):  # inc X / inc Y
        return op & 0xFF0
    return op
