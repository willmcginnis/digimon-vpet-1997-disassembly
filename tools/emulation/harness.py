"""Headless driver for BrickEmuPy's E0C6200 core running Digimon V-Pet ROMs.

Usage (as a module):
    from harness import Pet
    p = Pet("/path/to/digimon.bin")
    p.run_seconds(5)
    print(p.ascii())
"""
import os
import re
import sys

BRICK = os.environ.get("BRICK", os.path.join(os.path.dirname(__file__), "..", "..", "BrickEmuPy"))
SVG = os.path.join(BRICK, "assets", "DigimonV1J.svg")
sys.path.insert(0, BRICK)

from cores.E0C6200 import E0C6200  # noqa: E402
from interconnect import Interconnect  # noqa: E402
from peripherals.CON_DGM import CON_DGM  # noqa: E402

CLOCK = 1_060_000
BUTTON_MASK = {"A": 4, "B": 2, "C": 1}  # K0 bits, active low


def _load_layout():
    """Map (nibble, bit) -> ('px', x, y) or ('icon', name) from the SVG."""
    text = open(SVG, encoding="utf-8").read()
    pixels = {}
    # dot-matrix pixels live in <g id="col_N"> groups as rect-like paths
    for col_match in re.finditer(r'<g id="col_(\d+)">(.*?)</g>', text, re.S):
        col = int(col_match.group(1))
        for pm in re.finditer(r'<path id="(\d+)_(\d)" d="M([\d.]+) ([\d.]+)', col_match.group(2)):
            nib, bit, _x, y = int(pm.group(1)), int(pm.group(2)), float(pm.group(3)), float(pm.group(4))
            pixels[(nib, bit)] = (col, y)
    ys = sorted({y for (_c, y) in pixels.values()})
    yrank = {y: i for i, y in enumerate(ys)}
    layout = {k: ("px", c, yrank[y]) for k, (c, y) in pixels.items()}
    # icons are <g id="N_B"> groups outside the columns; locate by first path coordinate
    icons = []
    for gm in re.finditer(r'<g id="(\d+)_(\d)">\s*<path[^>]*?d="M([\d.]+) ([\d.]+)', text):
        key = (int(gm.group(1)), int(gm.group(2)))
        if key not in layout:
            icons.append((float(gm.group(4)), float(gm.group(3)), key))
    for pm in re.finditer(r'<path id="(\d+)_(\d)"[^>]*?\sd="M([\d.]+) ([\d.]+)', text):
        key = (int(pm.group(1)), int(pm.group(2)))
        if key not in layout and all(key != i[2] for i in icons):
            icons.append((float(pm.group(4)), float(pm.group(3)), key))
    icons.sort()
    if icons:
        mid = (icons[0][0] + icons[-1][0]) / 2
        top = sorted([i for i in icons if i[0] < mid], key=lambda t: t[1])
        bot = sorted([i for i in icons if i[0] >= mid], key=lambda t: t[1])
        names_top = ["STATUS", "FEED", "TRAIN", "BATTLE"]
        names_bot = ["FLUSH", "LIGHT", "MEDIC", "CALL"]
        for name, ic in zip(names_top, top):
            layout[ic[2]] = ("icon", name)
        for name, ic in zip(names_bot, bot):
            layout[ic[2]] = ("icon", name)
    return layout


LAYOUT = _load_layout()
NCOLS = 1 + max(v[1] for v in LAYOUT.values() if v[0] == "px")
NROWS = 1 + max(v[2] for v in LAYOUT.values() if v[0] == "px")


class _Host:
    def __init__(self):
        self.tx = bytearray()

    def audio_handler(self, channel, data):
        pass

    def serial_tx_handler(self, data):
        self.tx.extend(data)


class Pet:
    def __init__(self, rom_path, link=True):
        self.host = _Host()
        self.ic = Interconnect(self.host)
        mask = {"rom_path": rom_path, "port_pullup": {"K0": 15, "K1": 15}, "p3_dedicated": 0}
        self.cpu = E0C6200(mask, CLOCK, self.ic)
        self.link = CON_DGM({"port": "P2", "mask": 1}, self.ic) if link else None
        self.cycles = 0

    # ---- time ----
    def run_cycles(self, n):
        target = self.cycles + n
        clock = self.cpu.clock
        emit = self.ic.emit_clock
        while self.cycles < target:
            c = clock()
            emit(c)
            self.cycles += c

    def run_seconds(self, s):
        self.run_cycles(int(s * CLOCK))

    def run_until_pc(self, pcs, max_seconds=5):
        """Step until PC is in pcs; returns True if hit."""
        pcs = set(pcs)
        target = self.cycles + int(max_seconds * CLOCK)
        while self.cycles < target:
            if self.cpu.pc() in pcs:
                return True
            c = self.cpu.clock()
            self.ic.emit_clock(c)
            self.cycles += c
        return False

    # ---- inputs ----
    def hold(self, *buttons):
        for b in buttons:
            self.cpu.port_handler("K0", BUTTON_MASK[b], 0)

    def release(self, *buttons):
        for b in buttons:
            self.cpu.port_handler("K0", BUTTON_MASK[b], -1)

    def press(self, *buttons, hold_s=0.08, gap_s=0.12):
        self.hold(*buttons)
        self.run_seconds(hold_s)
        self.release(*buttons)
        self.run_seconds(gap_s)

    def reset(self, *held, hold_s=0.3):
        """Press Reset, optionally while holding buttons (like a paperclip reset)."""
        self.hold(*held)
        self.cpu.port_handler("RES", 0, 0)
        self.run_seconds(0.05)
        self.cpu.port_handler("RES", 0, -1)
        self.run_seconds(hold_s)
        self.release(*held)

    # ---- memory ----
    def ram(self, start=0, n=0x280):
        return [self.cpu.get_mem(a) for a in range(start, start + n)]

    def poke(self, addr, value):
        self.cpu.set_mem(addr, value)

    # ---- display ----
    def frame(self):
        vram = self.cpu.get_VRAM()
        grid = [[0] * NCOLS for _ in range(NROWS)]
        icons = []
        for (nib, bit), info in LAYOUT.items():
            if nib < len(vram) and (vram[nib] >> bit) & 1:
                if info[0] == "px":
                    grid[info[2]][info[1]] = 1
                else:
                    icons.append(info[1])
        return grid, sorted(icons)

    def ascii(self):
        grid, icons = self.frame()
        rows = ["".join("#" if v else "." for v in row) for row in grid]
        return "\n".join(rows) + "\nicons: " + (",".join(icons) or "-")

    def png(self, path, scale=8):
        from PIL import Image, ImageDraw

        grid, icons = self.frame()
        img = Image.new("RGB", (NCOLS * scale, NROWS * scale + 16), (200, 210, 180))
        d = ImageDraw.Draw(img)
        for y, row in enumerate(grid):
            for x, v in enumerate(row):
                if v:
                    d.rectangle([x * scale, y * scale, x * scale + scale - 2, y * scale + scale - 2], fill=(30, 30, 30))
        d.text((2, NROWS * scale + 2), " ".join(icons), fill=(0, 0, 0))
        img.save(path)
