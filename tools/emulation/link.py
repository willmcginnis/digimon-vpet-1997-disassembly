"""Wire two emulated pets together through BrickEmuPy's CON_DGM prong model.

Each pet's CON_DGM turns the bits its CPU drives on P2 into bytes (host.tx);
we hand those bytes to the other pet's CON_DGM, which replays them as a
waveform on that pet's P2 input. Both pets advance in lockstep slices.
Every 16-bit word is logged with the emulated time and its direction.
"""
import harness as h


class Link:
    def __init__(self, a, b, slice_cycles=500):
        self.a, self.b = a, b
        self.slice = slice_cycles
        self.log = []  # (t_seconds, "A>B"/"B>A", word)
        self._pend = {id(a): bytearray(), id(b): bytearray()}
        self.tamper = None  # optional fn(tag, wire_word, index) -> wire_word or None

    def _pump(self, src, dst, tag):
        if src.host.tx:
            data = bytes(src.host.tx)
            src.host.tx.clear()
            buf = self._pend[id(src)]
            buf.extend(data)
            while len(buf) >= 2:
                word = (buf[0] << 8) | buf[1]
                del buf[:2]
                self.log.append((src.cycles / h.CLOCK, tag, word))
                if self.tamper is not None:
                    word = self.tamper(tag, word, len(self.log))
                    if word is None:  # dropped: the prongs came apart
                        continue
                dst.link.serial_rx_handler(bytes([word >> 8, word & 0xFF]))

    def run_seconds(self, s):
        end = self.a.cycles + int(s * h.CLOCK)
        while self.a.cycles < end:
            self.a.run_cycles(self.slice)
            self.b.run_cycles(self.a.cycles - self.b.cycles)
            self._pump(self.a, self.b, "A>B")
            self._pump(self.b, self.a, "B>A")

    def press(self, pet, *buttons, hold_s=0.1, gap_s=0.4):
        pet.hold(*buttons)
        self.run_seconds(hold_s)
        pet.release(*buttons)
        self.run_seconds(gap_s)


def decode(word):
    """Split a 16-bit word into nibbles n3 n2 n1 n0 (n3 = high)."""
    return [(word >> s) & 0xF for s in (12, 8, 4, 0)]
