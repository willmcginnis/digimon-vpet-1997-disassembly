"""Figures that need no trace data: display mapping, address spaces, super-loop,
link timing, battle sequence, sprite columns.

usage: python3 figs_static.py OUTDIR
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from svgkit import SVG  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "figures"
os.makedirs(OUT, exist_ok=True)


def vram_addr(n):
    """BrickEmuPy VRAM index -> CPU address (two 0x50-nibble windows)."""
    return 0xE00 + n if n < 0x50 else 0xE80 + (n - 0x50)


# Column -> (low nibble index) for each half, from the BrickEmuPy LCD face.
LEFT_TOP = [0x78 + 2 * c + (2 if c >= 8 else 0) for c in range(16)]     # 78..86, 8A..98
LEFT_BOT = [0x28 + 2 * c + (2 if c >= 8 else 0) for c in range(16)]     # 28..36, 3A..48
RIGHT_TOP = [0x76 - 2 * c - (6 if c >= 8 else 0) for c in range(16)]    # 76..68, 60..52
RIGHT_BOT = [0x26 - 2 * c - (6 if c >= 8 else 0) for c in range(16)]    # 26..18, 10..02
ICONS_TOP = [("STATUS", 0x89, 3), ("FEED", 0x9B, 3), ("TRAIN", 0x9D, 3), ("BATTLE", 0x9F, 3)]
ICONS_BOT = [("FLUSH", 0x16, 0), ("LIGHT", 0x14, 0), ("MEDIC", 0x12, 0), ("CALL", 0x00, 0)]


def column_low_nibble(col, top):
    if col < 16:
        return (LEFT_TOP if top else LEFT_BOT)[col]
    return (RIGHT_TOP if top else RIGHT_BOT)[col - 16]


def fig_display_map(theme):
    cell = 22
    ox, oy = 70, 190
    W, H = ox + 32 * cell + 260, oy + 16 * cell + 150
    s = SVG(W, H, theme, "LCD dot matrix to display RAM",
            "Each LCD column is one byte split over two nibbles; four quadrants run in different directions.")
    t = s.t
    s.arrow_marker("ar", t["text2"])
    s.text(ox, 30, "How display RAM becomes pixels", 18, weight="bold")
    s.text(ox, 52, "32 × 16 dots + 8 icons. One column = one byte = two nibbles (odd nibble = upper 4 dots, bit 3 at the top).",
           12, t["text2"])
    quad = {("L", True): t["series"][0], ("R", True): t["series"][1],
            ("L", False): t["series"][2], ("R", False): t["series"][6]}
    for r in range(16):
        top = r < 8
        for c in range(32):
            lo = column_low_nibble(c, top)
            half = "L" if c < 16 else "R"
            bitrow = r % 8
            nib = lo + 1 if bitrow < 4 else lo
            bit = 3 - (bitrow % 4)
            a = vram_addr(nib)
            s.rect(ox + c * cell + 1, oy + r * cell + 1, cell - 2, cell - 2, quad[(half, top)], rx=3,
                   opacity=0.85 if bitrow < 4 else 0.55, title="row %d col %d -> %03X bit %d" % (r, c, a, bit))
    # column labels: address of the low nibble of each column, top half above, bottom half below
    for c in range(32):
        x = ox + c * cell + cell / 2 + 4
        s.text(x, oy - 8, "%03X" % vram_addr(column_low_nibble(c, True)), 9, t["text2"], mono=True, rotate=-90)
        s.text(x, oy + 16 * cell + 34, "%03X" % vram_addr(column_low_nibble(c, False)), 9, t["text2"],
               mono=True, rotate=-90)
    # row labels
    for r in range(16):
        y = oy + r * cell + cell / 2 + 4
        lab = "+1 b%d" % (3 - r % 4) if r % 8 < 4 else "+0 b%d" % (3 - r % 4)
        s.text(ox - 8, y, lab, 9, t["muted"], anchor="end", mono=True)
    # direction arrows
    ay = oy + 16 * cell + 52
    s.line(ox + 4, ay, ox + 16 * cell - 8, ay, t["text2"], 1.5, marker="ar")
    s.text(ox + 8 * cell, ay + 16, "left half: addresses rise →", 11, t["text2"], anchor="middle")
    s.line(ox + 32 * cell - 4, ay, ox + 16 * cell + 8, ay, t["text2"], 1.5, marker="ar")
    s.text(ox + 24 * cell, ay + 16, "← right half: addresses fall", 11, t["text2"], anchor="middle")
    # icons
    iy = oy - 112
    for i, (name, n, b) in enumerate(ICONS_TOP):
        x = ox + i * 8 * cell
        s.rect(x + 2, iy, 8 * cell - 6, 26, t["panel"], rx=4, stroke=t["axis"])
        s.text(x + 10, iy + 17, "%s  %03X.%d" % (name, vram_addr(n), b), 11, mono=True)
    by = oy + 16 * cell + 78
    for i, (name, n, b) in enumerate(ICONS_BOT):
        x = ox + i * 8 * cell
        s.rect(x + 2, by, 8 * cell - 6, 26, t["panel"], rx=4, stroke=t["axis"])
        s.text(x + 10, by + 17, "%s  %03X.%d" % (name, vram_addr(n), b), 11, mono=True)
    # legend / inset
    lx = ox + 32 * cell + 24
    s.text(lx, oy + 4, "Quadrants", 12, weight="bold")
    for i, (lab, key) in enumerate([("top-left  EA8–EC9", ("L", True)), ("top-right EA6–E82", ("R", True)),
                                    ("bottom-left  E28–E49", ("L", False)), ("bottom-right E26–E02", ("R", False))]):
        s.rect(lx, oy + 16 + i * 22, 14, 14, quad[key], rx=3)
        s.text(lx + 22, oy + 27 + i * 22, lab, 11, mono=True)
    s.text(lx, oy + 124, "Top half = bottom half + 0x80", 11, t["text2"])
    s.text(lx, oy + 140, "(two 80-nibble windows,", 11, t["text2"])
    s.text(lx, oy + 156, " E00–E4F and E80–ECF)", 11, t["text2"])
    s.text(lx, oy + 186, "Gaps in the runs hold the icons:", 11, t["text2"])
    s.text(lx, oy + 202, "EB8/EB9, E92–E97, E12–E17, E00", 11, t["text2"], mono=True)
    s.text(lx, oy + 232, "Source: LCD face of BrickEmuPy", 10, t["muted"])
    s.text(lx, oy + 246, "(azya52), built from the device.", 10, t["muted"])
    return s


def fig_address_spaces(theme):
    W, H = 1000, 430
    s = SVG(W, H, theme, "E0C6200 address spaces as used by the Digimon V-Pet",
            "Program ROM of 8192 12-bit words in 2 banks of 16 pages; data memory of 4-bit nibbles.")
    t = s.t
    s.text(24, 32, "Two memories, two word sizes", 18, weight="bold")
    s.text(24, 54, "Program: 12-bit instruction words.  Data: 4-bit nibbles.  Nothing else is byte-addressed.", 12, t["text2"])
    # ROM
    x0, y0 = 24, 84
    s.text(x0, y0, "Program ROM  (8,192 × 12 bit)", 13, weight="bold")
    pw, ph = 26, 15
    for bank in range(2):
        bx = x0
        by = bank * 78
        s.text(bx, y0 + 22 + by, "bank %d  (0x%d000–0x%dFFF)" % (bank, bank, bank), 11, t["text2"], mono=True)
        for page in range(16):
            col = t["series"][0] if bank == 0 else t["series"][6]
            if bank == 0 and page == 0:
                col = t["series"][3]
            if bank == 0 and page == 1:
                col = t["series"][1]
            s.rect(bx + page * pw, y0 + 30 + by, pw - 3, ph * 2, col, rx=3, opacity=0.8,
                   title="bank %d page %X: 256 words" % (bank, page))
            s.text(bx + page * pw + (pw - 3) / 2, y0 + 30 + by + ph * 2 + 14, "%X" % page, 10, t["text2"],
                   anchor="middle", mono=True)
    notes = [
        (t["series"][3], "page 0: CALZ library (one-word calls from anywhere in the bank)"),
        (t["series"][1], "page 1: reset at 0x100, interrupt vectors 0x102–0x10C, main loop at 0x132"),
        (t["series"][0], "bank 0: game logic"),
        (t["series"][6], "bank 1: per-species graphics and animation handlers"),
    ]
    for i, (c, n) in enumerate(notes):
        s.rect(x0, y0 + 180 + i * 20, 12, 12, c, rx=2)
        s.text(x0 + 20, y0 + 190 + i * 20, n, 11)
    s.text(x0, y0 + 278, "Address = bank:page:step (1 + 4 + 8 bits). JP/CALL only reach their own page;", 11, t["text2"])
    s.text(x0, y0 + 294, "PSET p in front of them selects another page (and bank) for that one jump.", 11, t["text2"])
    # Data
    dx = 560
    s.text(dx, y0, "Data memory  (4-bit nibbles)", 13, weight="bold")
    blocks = [
        (0x000, 0x0FF, "RAM page 0", "game state, timers, link buffer, RNG, stack", t["series"][2]),
        (0x100, 0x1FF, "RAM page 1", "scratch / draw buffers (cleared by 0x004C)", t["series"][2]),
        (0x200, 0x2FF, "RAM page 2", "scratch 200–27F; sound note list 280–2FF (measured)", t["series"][2]),
        (0xE00, 0xE4F, "Display RAM 1", "bottom half of the dot matrix + 4 icons", t["series"][4]),
        (0xE80, 0xECF, "Display RAM 2", "top half of the dot matrix + 4 icons", t["series"][4]),
        (0xF00, 0xF7E, "I/O registers", "24 used: timers, interrupts, K0 keys, P2 prong, buzzer, LCD, OSC", t["series"][7]),
    ]
    for i, (a, b, name, note, c) in enumerate(blocks):
        y = y0 + 20 + i * 42
        s.rect(dx, y, 26, 34, c, rx=3, opacity=0.85)
        s.text(dx + 36, y + 14, "%03X–%03X  %s" % (a, b, name), 12, mono=True, weight="bold")
        s.text(dx + 36, y + 29, note, 11, t["text2"])
    s.text(dx, y0 + 290, "Pointers: X and Y are 12-bit (XP/YP page + 8-bit offset).", 11, t["text2"])
    s.text(dx, y0 + 306, "Helpers 0x0087/0x0089/0x008D/0x008F set the page before each access.", 11, t["text2"])
    return s


TASKS = [
    (0x0010, "cpu_clock_fast", "switch CPU to the fast oscillator"),
    (0x01CA, "task_mark_awake", "restart the clock-timer flag"),
    (0x0900, "task_timekeeping", "LCD timeout, clock, sleep schedule"),
    (0x07BF, "task_key_scan", "debounce A/B/C into key_event"),
    (0x0200, "task_key_dispatch", "route the key by mode"),
    (0x0800, "task_life_clock", "hunger, strength, poop, evolution timing"),
    (0x0A5D, "task_animation", "per-frame sprite motion"),
    (0x0B06, "task_link_rx", "listen on the prong"),
    (0x0B5B, "task_link_tx", "send a queued word"),
    (0x0410, "task_mode_render", "the mode state machine"),
    (0x0A00, "task_sound", "sound sequencer"),
    (0x0E7B, "rng_step", "advance the random counters"),
]


def fig_super_loop(theme):
    W, H = 900, 560
    s = SVG(W, H, theme, "The main super-loop at 0x0132",
            "Twelve calls per pass, then HALT until an interrupt.")
    t = s.t
    s.arrow_marker("ar", t["text2"])
    s.text(24, 32, "One pass of the main loop (0x0132–0x016D)", 18, weight="bold")
    s.text(24, 54, "Every pass calls the same twelve routines in the same order, then sleeps until an interrupt.",
           12, t["text2"])
    x, y0, bh, gap = 60, 80, 30, 6
    for i, (a, name, note) in enumerate(TASKS):
        y = y0 + i * (bh + gap)
        c = t["series"][i % 8] if a not in (0x0010, 0x0E7B) else t["neutral"]
        s.rect(x, y, 6, bh, c, rx=2)
        s.rect(x + 8, y, 520, bh, t["panel"], rx=4, stroke=t["axis"])
        s.text(x + 18, y + 20, "%04X" % a, 12, t["text2"], mono=True)
        s.text(x + 70, y + 20, name, 12, mono=True, weight="bold")
        s.text(x + 260, y + 20, note, 12, t["text2"])
        if i < len(TASKS) - 1:
            s.line(x + 290 - 240, y + bh, x + 290 - 240, y + bh + gap, t["axis"], 1)
    yb = y0 + len(TASKS) * (bh + gap) + 6
    s.rect(x + 8, yb, 520, 40, t["neutral2"], rx=4)
    s.text(x + 18, yb + 17, "idle?  (no keys, link quiet, mode allows)", 12)
    s.text(x + 18, yb + 33, "cpu_clock_slow → EI → HALT", 12, mono=True, weight="bold")
    # loop-back arrow
    s.path("M %d %d C %d %d, %d %d, %d %d" % (x + 528, yb + 20, x + 600, yb + 20, x + 600, y0 + 15, x + 532, y0 + 15),
           t["text2"], 1.5, marker="ar")
    s.text(x + 612, (yb + y0) / 2 - 10, "busy: loop", 12, t["text2"])
    s.text(x + 612, (yb + y0) / 2 + 6, "again at once", 12, t["text2"])
    # interrupts
    ix = 640
    s.text(ix, yb - 70, "Interrupts wake the HALT", 12, weight="bold")
    for i, (v, n) in enumerate([(0x102, "clock timer → 0x17D6"), (0x106, "K0 buttons → 0x1EDE"),
                                (0x10C, "prog. timer → 0x1CEB")]):
        s.text(ix, yb - 50 + i * 16, "%04X  %s" % (v, n), 11, t["text2"], mono=True)
    s.path("M %d %d L %d %d" % (ix - 8, yb - 20, x + 532, yb + 20), t["text2"], 1.2, marker="ar", dash="4 3")
    return s


def fig_link_timing(theme):
    # BrickEmuPy CON_DGM model (cycles at 1.06 MHz): idle high; START low 67869;
    # 2 AGC periods high 2135 / low 1003; 16 bits: bit0 high 1067 low 3461, bit1 high 2911 low 1779; END high 7000
    clk = 1.06e6
    segs = [("lo", 67869, "start"), ("hi", 2135, ""), ("lo", 1003, ""), ("hi", 2135, ""), ("lo", 1003, "")]
    word = 0x13EC  # EC13 in DMComm notation is sent LSB first: wire order bits of 0xEC13 from bit 0
    bits = [(0xEC13 >> i) & 1 for i in range(16)]
    for b in bits:
        segs += [("hi", 2911, "1"), ("lo", 1779, "")] if b else [("hi", 1067, "0"), ("lo", 3461, "")]
    segs.append(("hi", 7000, "end"))
    total = sum(c for _, c, _ in segs)
    W, H = 1000, 330
    s = SVG(W, H, theme, "One 16-bit word on the prong",
            "Pulse-width encoding on a single open-drain line, as modelled by BrickEmuPy's CON_DGM.")
    t = s.t
    s.text(24, 32, "One 16-bit word on the link prong (packet EC13)", 18, weight="bold")
    s.text(24, 54, "Single wire, pulled high when idle. Each bit is a high/low pair whose split encodes the value.",
           12, t["text2"])
    x0, x1 = 40, W - 30
    hi_y, lo_y = 120, 170
    # compress the long start pulse visually
    vis = []
    for lvl, c, lab in segs:
        w = 36 if c == 67869 else c
        vis.append((lvl, w, lab, c))
    vtotal = sum(w for _, w, _, _ in vis)
    scale = (x1 - x0) / vtotal
    x = x0
    d = "M %.1f %.1f" % (x0 - 20, hi_y)
    for lvl, w, lab, c in vis:
        y = hi_y if lvl == "hi" else lo_y
        d += " L %.1f %.1f L %.1f %.1f" % (x, y, x + w * scale, y)
        if lab in ("0", "1"):
            s.text(x + w * scale / 2 + 6, hi_y - 10, lab, 11, t["text"], anchor="middle", mono=True, weight="bold")
        x += w * scale
    s.path(d, t["series"][0], 2)
    s.text(x0 - 22, hi_y + 4, "H", 11, t["muted"], anchor="end")
    s.text(x0 - 22, lo_y + 4, "L", 11, t["muted"], anchor="end")
    s.text(x0 + 2, lo_y + 22, "start ≈ 64 ms low", 11, t["text2"])
    s.text(x0 + 2, lo_y + 36, "(drawn compressed)", 10, t["muted"])
    s.text(x0 + 150, lo_y + 22, "← 2 sync periods", 11, t["text2"])
    s.text(x - 4, lo_y + 22, "end", 11, t["text2"], anchor="end")
    rows = [("bit 0", 1067, 3461), ("bit 1", 2911, 1779), ("sync", 2135, 1003)]
    ty = 240
    s.text(40, ty, "Timing", 12, weight="bold")
    for i, (n, h, l) in enumerate(rows):
        s.text(40, ty + 18 + i * 16, "%-6s high %.2f ms  low %.2f ms" % (n, h / clk * 1e3, l / clk * 1e3), 11,
               t["text2"], mono=True)
    s.text(420, ty, "Reading the value", 12, weight="bold")
    s.text(420, ty + 18, "bits go out least-significant first; DMComm writes words in that order,", 11, t["text2"])
    s.text(420, ty + 34, "so EC13 = 0xEC13 read from bit 0 upward. Whole word ≈ %.0f ms." % (total / clk * 1e3), 11,
           t["text2"])
    s.text(420, ty + 58, "Source: BrickEmuPy peripherals/CON_DGM.py (modelled timings, documented).", 10, t["muted"])
    return s


def fig_battle_sequence(theme):
    W, H = 980, 600
    s = SVG(W, H, theme, "A linked battle, packet by packet",
            "The initiator decides the outcome alone and the responder takes the complement.")
    t = s.t
    s.arrow_marker("ar", t["text2"])
    s.text(24, 32, "A linked battle, packet by packet  (measured in emulation)", 18, weight="bold")
    s.text(24, 54, "Two emulated Ver.1 units wired through the prong model. Times from the B press on unit A.",
           12, t["text2"])
    ax, bx = 230, 750
    top, bot = 100, 560
    for x, name, sub, c in [(ax, "Unit A", "initiator (pressed B last)", t["series"][0]),
                            (bx, "Unit B", "responder (waiting in battle stance)", t["series"][1])]:
        s.rect(x - 110, top - 24, 220, 40, c, rx=6, opacity=0.9)
        s.text(x, top - 6, name, 13, t["ink_on_fill"], anchor="middle", weight="bold")
        s.text(x, top + 10, sub, 10, t["ink_on_fill"], anchor="middle")
        s.line(x, top + 16, x, bot, t["axis"], 1.5, dash="5 4")
    msgs = [
        (0.149, "A>B", "EC13", "packet 1: enhancement 1, slot 3 (+ complements)"),
        (0.439, "B>A", "EC13", "packet 1 from B: its own slot and enhancement"),
        (0.729, "A>B", "FD02", "packet 2: version 0, outcome 2 = A loses"),
        (1.020, "B>A", "FE01", "packet 2 from B: outcome 1 = B wins"),
    ]

    def ty(tm):
        return top + 40 + tm * 260

    for tm, d, w, note in msgs:
        y = ty(tm)
        if d == "A>B":
            s.line(ax + 4, y, bx - 6, y, t["text2"], 1.6, marker="ar")
        else:
            s.line(bx - 4, y, ax + 6, y, t["text2"], 1.6, marker="ar")
        s.text((ax + bx) / 2, y - 6, "%s  %s" % (w, note), 11, anchor="middle", mono=False)
        s.text(24, y + 4, "t = %.3f s" % tm, 11, t["muted"], mono=True)
    # decision box on A between packet 1 replies and packet 2
    y = ty(0.55)
    s.rect(ax - 210, y - 22, 200, 50, t["panel"], rx=5, stroke=t["series"][0], sw=1.5)
    s.text(ax - 200, y - 5, "0x0D7A battle_outcome_roll", 10, mono=True, weight="bold")
    s.text(ax - 200, y + 10, "threshold = table(slots) + Δenh", 10, t["text2"])
    s.text(ax - 200, y + 24, "win ⇔ RNG nibble M(A3) ≥ threshold", 10, t["text2"])
    y = ty(0.85)
    s.rect(bx + 10, y - 16, 210, 38, t["panel"], rx=5, stroke=t["series"][1], sw=1.5)
    s.text(bx + 20, y + 1, "0x0EB0 responder outcome", 10, mono=True, weight="bold")
    s.text(bx + 20, y + 16, "outcome = 3 − received outcome", 10, t["text2"])
    y = ty(1.15)
    s.rect(ax - 60, y, bx - ax + 120, 60, t["neutral2"], rx=6)
    s.text((ax + bx) / 2, y + 24, "≈ 20 s of attack animation on both screens", 12, anchor="middle", weight="bold")
    s.text((ax + bx) / 2, y + 42, "pure playback: the result was fixed at t ≈ 0.6 s", 11, t["text2"], anchor="middle")
    yy = ty(1.55)
    s.text(24, yy, "Tampering (measured)", 12, weight="bold")
    s.text(24, yy + 18, "flip A's packet 2 in transit → B records the flipped result unchecked", 11, t["text2"])
    s.text(24, yy + 34, "cut the line after packet 1 → A keeps its result, B gets none", 11, t["text2"])
    s.text(24, yy + 50, "button mashing after t ≈ 1 s → no effect", 11, t["text2"])
    return s


HEART = [0x00, 0x38, 0x44, 0x42, 0x21, 0x42, 0x44, 0x38]  # lbpx operands at 0x056C-0x0573


def fig_sprite_columns(theme):
    cell = 26
    W, H = 900, 380
    s = SVG(W, H, theme, "How a sprite is stored: one LBPX per column",
            "Eight LBPX instructions write eight column bytes; each byte's bits are the column's dots.")
    t = s.t
    s.arrow_marker("ar", t["text2"])
    s.text(24, 32, "Sprites are code: one  lbpx M(X), byte  per column", 18, weight="bold")
    s.text(24, 54, "The empty heart of the hearts meter, drawn by 0x0563 draw_hearts_meter (operands at 0x056C–0x0573).", 12, t["text2"])
    x0, y0 = 40, 90
    for i, b in enumerate(HEART):
        s.text(x0, y0 + 16 + i * 26, "%04X  lbpx M(X), 0x%02X" % (0x056C + i, b), 13, mono=True)
    gx, gy = 420, 80
    for c, b in enumerate(HEART):
        s.text(gx + c * cell + cell / 2, gy - 6, "%02X" % b, 11, t["text2"], anchor="middle", mono=True)
        for r in range(8):
            on = (b >> (7 - r)) & 1
            s.rect(gx + c * cell + 1, gy + r * cell + 1, cell - 2, cell - 2,
                   t["series"][0] if on else t["neutral2"], rx=3,
                   title="column %d bit %d = %d" % (c, 7 - r, on))
    for r in range(8):
        s.text(gx - 8, gy + r * cell + cell / 2 + 4, "b%d" % (7 - r), 10, t["muted"], anchor="end", mono=True)
    s.text(gx, gy + 8 * cell + 24, "lbpx writes the low nibble to M(X), the high nibble to M(X+1), then X += 2:", 11,
           t["text2"])
    s.text(gx, gy + 8 * cell + 40, "exactly one LCD column (see the display map).", 11, t["text2"])
    s.path("M %d %d C %d %d, %d %d, %d %d" % (330, 150, 370, 150, 370, 150, gx - 26, 150), t["text2"], 1.4,
           marker="ar")
    return s


if __name__ == "__main__":
    figs = {"display_map": fig_display_map, "address_spaces": fig_address_spaces,
            "super_loop": fig_super_loop, "link_timing": fig_link_timing,
            "battle_sequence": fig_battle_sequence, "sprite_columns": fig_sprite_columns}
    for name, fn in figs.items():
        for theme in ("light", "dark"):
            fn(theme).save(os.path.join(OUT, "%s-%s.svg" % (name, theme)))
    print("wrote", len(figs) * 2, "files to", OUT)
