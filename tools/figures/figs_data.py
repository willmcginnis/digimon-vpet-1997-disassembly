"""Figures built from measured traces: ROM atlas, RAM map, mode machine.

usage: python3 figs_data.py STATIC_JSON CLASSES_JSON TRACE_DIR LAYOUT_JSON OUTDIR
  STATIC_JSON   walker output (static.json)
  CLASSES_JSON  static fallback classes (classify.py output)
  TRACE_DIR     directory of coverage.py outputs (pcs, mem, attr, transitions, frames)
  LAYOUT_JSON   {"NIB,BIT": ["px", col, row] | ["icon", name]} display layout
"""
import glob
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from svgkit import SVG  # noqa: E402

TASK2CAT = {"spine": "spine", "factory_test": "spine", "input": "input", "irq_k0": "input",
            "screens": "screens", "life": "life", "irq_timer": "life", "link": "link_battle",
            "animation": "animation", "sound": "sound", "irq_prog_timer": "sound", "rng": "library"}
CATS = ["spine", "input", "screens", "life", "link_battle", "animation", "sound", "graphics"]
LABEL = {"spine": "reset, main loop, factory test", "input": "keys", "screens": "mode machine / screens",
         "life": "time, care, evolution, death", "link_battle": "link and battle",
         "animation": "animation", "sound": "sound", "graphics": "bitmap runs (LBPX/RETD)",
         "library": "page-0 library and RNG", "shared": "shared by several tasks",
         "static": "reached, not executed in the scenarios", "filler": "nop7 filler",
         "unreached": "not reached"}


def load_traces(d):
    pcs, attr, mem, trans, frames = set(), defaultdict(set), defaultdict(lambda: [set(), set()]), Counter(), {}
    for f in sorted(glob.glob(os.path.join(d, "*.json"))):
        try:
            j = json.load(open(f))
        except Exception:
            continue
        if not isinstance(j, dict) or "attr" not in j:
            continue
        pcs |= set(j["pcs"])
        for p, v in j["attr"].items():
            attr[int(p, 16)] |= set(v)
        for a, v in j["mem"].items():
            m = mem[int(a, 16)]
            m[0] |= set(v["r"])
            m[1] |= set(v["w"])
        for t in j["transitions"]:
            trans[tuple(t[:5])] += t[5]
        for k, v in j["frames"].items():
            frames.setdefault(k, v)
    return pcs, attr, mem, trans, frames


def word_classes(static, classes, attr):
    T = static["text"]
    reached = set(static["reached"])
    out = {}

    def is_gfx(p):
        t = T.get("%04X" % p, "")
        return t.startswith("lbpx M(X)") or t.startswith("retd")

    for p in range(static["words"]):
        if p not in reached:
            out[p] = "filler" if T["%04X" % p] == "nop7" else "unreached"
            continue
        run = sum(1 for q in range(p - 3, p + 4) if 0 <= q < static["words"] and is_gfx(q))
        if is_gfx(p) and run >= 4:
            out[p] = "graphics"
            continue
        if p < 0x100:
            out[p] = "library"
            continue
        if p in attr:
            cats = {TASK2CAT.get(a, "shared") for a in attr[p]}
            out[p] = cats.pop() if len(cats) == 1 else "shared"
            continue
        sc = classes["words"].get("%04X" % p)
        out[p] = sc if sc in CATS or sc == "library" else "static"
    return out


def colour(t, cat):
    if cat in CATS:
        return t["series"][CATS.index(cat)]
    return {"library": t["text2"], "shared": t["muted"], "static": t["neutral"],
            "filler": t["grid"], "unreached": t["neutral2"]}[cat]


def fig_atlas(wc, theme, executed):
    cw, ch = 3.2, 11
    ox, oy = 90, 100
    W, H = int(ox + 256 * cw + 40), oy + 32 * (ch + 1) + 210
    s = SVG(W, H, theme, "Atlas of the Ver.1 ROM",
            "Every instruction word coloured by the task that executed it (measured), or by shape for bitmap runs.")
    t = s.t
    s.text(24, 32, "An atlas of the ROM: who runs each word", 18, weight="bold")
    s.text(24, 54, "Each row is one 256-word page; each sliver one instruction. Colour = the main-loop task or "
                   "interrupt that was running when the word executed (measured).", 12, t["text2"])
    s.text(24, 70, "Bitmap runs are coloured by shape. Words never executed in the scenarios fall back to a "
                   "static assignment, or grey.", 12, t["text2"])
    for row in range(32):
        bank, page = divmod(row, 16)
        y = oy + row * (ch + 1) + (8 if bank else 0)
        s.text(ox - 8, y + ch - 2, "%X:%X" % (bank, page), 9, t["muted"], anchor="end", mono=True)
        base = bank * 0x1000 + page * 0x100
        # merge runs of equal class for compact SVG
        x = 0
        while x < 256:
            c = wc[base + x]
            e = x
            while e < 256 and wc[base + e] == c:
                e += 1
            s.rect(ox + x * cw, y, (e - x) * cw, ch, colour(t, c), title="%04X-%04X %s" % (base + x, base + e - 1, LABEL[c]))
            x = e
    for k in range(0, 257, 32):
        s.text(ox + k * cw, oy - 6, "%02X" % (k % 256) if k < 256 else "", 9, t["muted"], anchor="middle", mono=True)
    s.text(ox - 60, oy + 8 * (ch + 1), "bank 0", 11, t["text2"], rotate=-90)
    s.text(ox - 60, oy + 24 * (ch + 1) + 8, "bank 1", 11, t["text2"], rotate=-90)
    counts = Counter(wc.values())
    ly = oy + 32 * (ch + 1) + 30
    order = CATS + ["library", "shared", "static", "filler", "unreached"]
    for i, c in enumerate(order):
        col, rowi = i % 3, i // 3
        x = 24 + col * 300
        y = ly + rowi * 22
        s.rect(x, y - 10, 14, 14, colour(t, c), rx=2)
        s.text(x + 22, y + 1, "%s  (%d)" % (LABEL[c], counts.get(c, 0)), 11)
    s.text(24, ly + 5 * 22 + 12, "%d of 8,192 words executed across the scenarios." % len(executed), 11, t["text2"])
    return s, counts


RAM_NAMES = {
    0x00: "tick", 0x01: "anim", 0x02: "key", 0x03: "kst", 0x05: "stat", 0x06: "ui", 0x09: "MODE",
    0x0A: "sub", 0x0B: "SLOT", 0x0C: "ovl", 0x0D: "snd", 0x10: "tx", 0x11: "tx", 0x12: "tx~", 0x13: "tx~",
    0x15: "menu", 0x17: "sseq", 0x1A: "sec", 0x1B: "sec", 0x1C: "min", 0x1D: "min", 0x1E: "hr", 0x1F: "pm",
    0x36: "inj", 0x37: "inj", 0x38: "injh", 0x46: "s.s", 0x47: "s.s", 0x48: "s.m", 0x49: "s.m", 0x4A: "s.h",
    0x4B: "s.h", 0x4C: "evo", 0x4D: "evo", 0x4E: "evo", 0x4F: "evo", 0x54: "sched", 0x66: "bed",
    0x67: "wake", 0x75: "b.inj", 0x76: "lifef", 0x78: "bst", 0x79: "RES", 0x7B: "enh", 0x7C: "rx",
    0x7D: "rx", 0x7E: "o.enh", 0x7F: "o.slt", 0x8C: "nrg", 0x8D: "nrg", 0xA0: "RNG", 0xA1: "RNG",
    0xA2: "RNG", 0xA3: "RNG", 0xA4: "kdb", 0xA5: "kdb", 0xA6: "kdb",
}


def fig_ram(mem, attr, theme):
    cell = 30
    ox, oy = 60, 110
    small = 9
    W, H = ox + 16 * cell + 60 + 2 * (16 * small + 30) + 60, oy + 16 * cell + 150
    s = SVG(W, H, theme, "RAM map of the Ver.1 firmware",
            "Each nibble coloured by the task that writes it (measured); page 0 labelled.")
    t = s.t
    s.text(24, 32, "RAM: who writes each nibble", 18, weight="bold")
    s.text(24, 54, "Colour = the main-loop task or interrupt whose code wrote the nibble (measured from access "
                   "traces). Pale = read but never written; blank = untouched.", 12, t["text2"])
    s.text(24, 70, "Page 0 holds the game state; the stack grows down from 0FF.", 12, t["text2"])

    def cat_of(addr):
        m = mem.get(addr)
        if not m:
            return None, False
        writers = m[1]
        if not writers:
            return "read_only", False
        cats = set()
        for pc in writers:
            for a in attr.get(pc, ()):
                cats.add(TASK2CAT.get(a, "shared"))
        if not cats:
            return "shared", True
        return (cats.pop() if len(cats) == 1 else "shared"), True

    def draw_page(page, x0, y0, c):
        for i in range(256):
            a = page * 0x100 + i
            r, col = divmod(i, 16)
            cat, written = cat_of(a)
            x, y = x0 + col * c, y0 + r * c
            if cat is None:
                fill, op = t["surface"], None
                s.rect(x + 1, y + 1, c - 2, c - 2, fill, rx=2, stroke=t["grid"])
                continue
            fill = t["neutral2"] if cat == "read_only" else colour(t, cat)
            name = RAM_NAMES.get(a) if page == 0 else None
            tip = "%03X %s %s" % (a, name or "", "(read only)" if cat == "read_only" else "written by " + cat)
            s.rect(x + 1, y + 1, c - 2, c - 2, fill, rx=2, title=tip,
                   opacity=0.9 if cat != "read_only" else None)
            if name and c >= 24:
                s.text(x + c / 2, y + c / 2 + 3, name, 8, "#0b0b0b", anchor="middle",
                       weight="bold" if name.isupper() else "normal")

    s.text(ox, oy - 26, "page 0  (000–0FF)", 12, weight="bold")
    for i in range(16):
        s.text(ox + i * cell + cell / 2, oy - 8, "%X" % i, 9, t["muted"], anchor="middle", mono=True)
        s.text(ox - 8, oy + i * cell + cell / 2 + 3, "%X0" % i, 9, t["muted"], anchor="end", mono=True)
    draw_page(0, ox, oy, cell)
    for k, page in enumerate((1, 2)):
        x0 = ox + 16 * cell + 60 + k * (16 * small + 30)
        s.text(x0, oy - 26, "page %d" % page, 12, weight="bold")
        draw_page(page, x0, oy, small)
    # stack bracket
    s.rect(ox, oy + 14 * cell, 16 * cell, 2 * cell, "none", stroke=t["text2"], sw=1.5)
    s.text(ox + 16 * cell + 8, oy + 15 * cell + 4, "stack", 11, t["text2"])
    lx, ly = ox + 16 * cell + 60, oy + 16 * small + 40
    present = Counter()
    for a in range(0x300):
        cat, _ = cat_of(a)
        if cat:
            present[cat] += 1
    for i, c in enumerate([c for c in CATS + ["library", "shared"] if present.get(c)] + ["read_only"]):
        y = ly + i * 20
        s.rect(lx, y - 10, 12, 12, t["neutral2"] if c == "read_only" else colour(t, c), rx=2)
        s.text(lx + 20, y, "%s (%d)" % ("read, never written" if c == "read_only" else LABEL[c], present[c]), 11)
    return s


def thumb(s, vram, layout, x0, y0, px, t, on, off):
    grid = [[0] * 32 for _ in range(16)]
    for key, info in layout.items():
        nib, bit = map(int, key.split(","))
        if info[0] == "px" and nib < len(vram) and (vram[nib] >> bit) & 1:
            grid[info[2]][info[1]] = 1
    s.rect(x0 - 3, y0 - 3, 32 * px + 6, 16 * px + 6, off, rx=4)
    for r in range(16):
        c = 0
        while c < 32:
            if grid[r][c]:
                e = c
                while e < 32 and grid[r][e]:
                    e += 1
                s.rect(x0 + c * px, y0 + r * px, (e - c) * px, px - 0.4, on)
                c = e
            else:
                c += 1


MODE_NAMES = {0: "home", 1: "clock", 2: "STATUS", 3: "FEED", 4: "TRAIN", 5: "BATTLE", 6: "FLUSH",
              7: "LIGHT", 8: "MEDIC", 9: "evolving", 0xA: "mode A", 0xB: "dying", 0xC: "grave"}
MODE_POS = {0: (520, 300), 1: (170, 300), 2: (100, 560), 3: (240, 560), 4: (380, 560), 5: (520, 560),
            6: (660, 560), 7: (800, 560), 8: (940, 560), 9: (870, 300), 0xA: (870, 130), 0xB: (520, 130),
            0xC: (170, 130)}
# What causes each mode write, from the scenario that produced it (measured).
EDGE_LABELS = {0x0252: "A", 0x0268: "A", 0x0303: "C", 0x025A: "B", 0x02C5: "B", 0x0537: "set done",
               0x05AB: "stage timer", 0x0586: "done", 0x05BE: "done", 0x07DC: "6 h injured",
               0x07E9: "", 0x0CF3: "A+C", 0x0866: "idle"}
BW, BH, PX = 112, 86, 3


def _border(x, y, dx, dy):
    """Point where a ray from the centre of a node box leaves the box."""
    hw, hh = BW / 2 + 4, BH / 2 + 4
    kx = hw / abs(dx) if dx else 1e9
    ky = hh / abs(dy) if dy else 1e9
    k = min(kx, ky)
    return x + dx * k, y + dy * k


def fig_modes(trans, frames, layout, theme, mode_names=None):
    names = dict(MODE_NAMES)
    if mode_names:
        names.update(mode_names)
    W, H = 1060, 700
    s = SVG(W, H, theme, "The mode machine (measured transitions)",
            "Each node is a value of the mode nibble M(09) with its own screen; arrows are transitions seen in emulation.")
    t = s.t
    s.arrow_marker("ar", t["text2"])
    s.text(24, 32, "The mode machine, as measured", 18, weight="bold")
    s.text(24, 54, "Nodes: values of the mode nibble M(09), each drawn with its own screen. Arrows: every mode "
                   "change seen in the scenarios.", 12, t["text2"])
    s.text(24, 70, "Arrow labels say what caused it; hover an arrow for the instruction that wrote the new mode.",
           12, t["text2"])
    edges = defaultdict(lambda: [0, set()])
    for (o9, oa, n9, na, pc), cnt in trans.items():
        if o9 != n9:
            e = edges[(o9, n9)]
            e[0] += cnt
            e[1].add(pc)
    present = {a for a, _ in edges} | {b for _, b in edges} | {int(k[0], 16) for k in frames}
    for (a, b), (cnt, pcs) in sorted(edges.items()):
        if a not in MODE_POS or b not in MODE_POS:
            continue
        (x1, y1), (x2, y2) = MODE_POS[a], MODE_POS[b]
        dx, dy = x2 - x1, y2 - y1
        L = max(1.0, (dx * dx + dy * dy) ** 0.5)
        # two-way pairs: each direction is pushed to its own right-hand side
        off = 15 if (b, a) in edges else 0
        nx, ny = -dy / L * off, dx / L * off
        sx, sy = _border(x1 + nx, y1 + ny, dx, dy)
        ex, ey = _border(x2 + nx, y2 + ny, -dx, -dy)
        tip = "%X -> %X: %s (%d times)" % (a, b, ", ".join("%04X" % p for p in sorted(pcs)), cnt)
        s.parts.append('<g><title>%s</title>' % tip)
        s.line(sx, sy, ex, ey, t["text2"], 1.4, marker="ar")
        lab = "/".join(sorted({EDGE_LABELS.get(p, "%04X" % p) for p in pcs} - {""}))
        if lab:
            lx, ly = sx + (ex - sx) * 0.5 + (nx * 1.2), sy + (ey - sy) * 0.5 + (ny * 1.2)
            s.rect(lx - 4 * len(lab) - 4, ly - 10, 8 * len(lab) + 8, 14, t["surface"], rx=3)
            s.text(lx, ly + 1, lab, 10, t["text2"], anchor="middle")
        s.parts.append("</g>")
    for m, (x, y) in MODE_POS.items():
        if m not in present:
            continue
        key = next((k for k in sorted(frames) if int(k[0], 16) == m and k[1] != "0"), None) or \
            next((k for k in sorted(frames) if int(k[0], 16) == m), None)
        accent = t["series"][2] if 2 <= m <= 8 else (t["series"][7] if m in (0xB, 0xC) else t["series"][0])
        s.rect(x - BW / 2, y - BH / 2, BW, BH, t["panel"], rx=6, stroke=accent, sw=1.6)
        s.text(x - BW / 2 + 8, y - BH / 2 + 15, "%X  %s" % (m, names[m]), 11, weight="bold")
        if key:
            thumb(s, frames[key], layout, x - 32 * PX / 2, y - BH / 2 + 24, PX, t, t["text"], t["neutral2"])
    s.text(24, H - 50, "Modes 2–8 are the seven menu icons in order: the icon cursor is the mode itself, and A "
                       "steps it (0x0268). After MEDIC, A wraps back to home.", 11, t["text2"])
    s.text(24, H - 34, "idle = a menu left untouched returns home when the counter M(2D), reset by every key, "
                       "reaches 60 (0x0866).", 11, t["text2"])
    s.text(24, H - 18, "Submodes M(0A) are each screen's pages and animation steps and are not drawn.", 11,
           t["text2"])
    return s, edges


if __name__ == "__main__":
    static = json.load(open(sys.argv[1]))
    classes = json.load(open(sys.argv[2]))
    pcs, attr, mem, trans, frames = load_traces(sys.argv[3])
    layout = json.load(open(sys.argv[4]))
    out = sys.argv[5]
    os.makedirs(out, exist_ok=True)
    wc = word_classes(static, classes, attr)
    names = json.load(open(sys.argv[6])) if len(sys.argv) > 6 else None
    for theme in ("light", "dark"):
        a, counts = fig_atlas(wc, theme, pcs)
        a.save(os.path.join(out, "rom_atlas-%s.svg" % theme))
        fig_ram(mem, attr, theme).save(os.path.join(out, "ram_map-%s.svg" % theme))
        m, edges = fig_modes(trans, frames, layout, theme,
                             {int(k, 16): v for k, v in names.items()} if names else None)
        m.save(os.path.join(out, "mode_machine-%s.svg" % theme))
    json.dump({"counts": counts, "executed": len(pcs),
               "edges": [[a, b, c, sorted(p)] for (a, b), (c, p) in sorted(edges.items())],
               "word_classes": {"%04X" % p: c for p, c in wc.items()}},
              open(os.path.join(out, "..", "..", "data", "figures_data_v1.json"), "w"))
    print("executed", len(pcs), dict(counts))
    print("mode edges:", sorted((("%X" % a, "%X" % b, c) for (a, b), (c, _) in edges.items())))
