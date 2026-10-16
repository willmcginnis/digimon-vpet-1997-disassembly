"""Battle odds heatmap from the threshold table measured by executing 0x0D7A.

usage: python3 figs_battle.py threshold_v1.json OUTDIR
threshold_v1.json maps "OWN,OPP" (hex slots) -> threshold T; P(initiator wins) = (16 - T) / 16.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from svgkit import SVG  # noqa: E402

NAMES = {3: "Agumon", 4: "Betamon", 5: "Greymon", 6: "Tyranomon", 7: "Devimon", 8: "Meramon",
         9: "Airdramon", 10: "Seadramon", 11: "Numemon", 12: "MetalGreymon", 13: "Mamemon", 14: "Monzaemon"}
RAMP = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6",
        "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]


def hex2rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def lum(h):
    r, g, b = [c / 255 for c in hex2rgb(h)]
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4  # noqa: E731
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ramp(p, theme):
    steps = RAMP if theme == "light" else RAMP[::-1]
    i = min(len(steps) - 1, max(0, round(p * (len(steps) - 1))))
    return steps[i]


def fig(T, theme):
    cell = 46
    ox, oy = 150, 150
    n = 12
    W, H = ox + n * cell + 300, oy + n * cell + 110
    s = SVG(W, H, theme, "Initiator's chance to win a linked battle (Ver.1)",
            "P(win) = (16 - threshold) / 16, threshold computed by executing 0x0D7A, equal enhancement.")
    t = s.t
    s.text(24, 32, "Who wins a linked battle: the initiator's odds", 18, weight="bold")
    s.text(24, 54, "Chance the initiating unit wins, equal enhancement. Each cell = 16 − threshold, out of 16.", 12,
           t["text2"])
    s.text(24, 72, "Computed by running the outcome routine (0x0D7A) on the emulated CPU for every pairing; "
                   "identical in Ver.2.", 12, t["text2"])
    slots = list(range(3, 15))
    for j, q in enumerate(slots):
        s.text(ox + j * cell + cell / 2 + 4, oy - 8, NAMES[q], 11, t["text2"], rotate=-55)
    for i, o in enumerate(slots):
        s.text(ox - 10, oy + i * cell + cell / 2 + 4, NAMES[o], 11, t["text2"], anchor="end")
        for j, q in enumerate(slots):
            thr = T["%X,%X" % (o, q)]
            p = (16 - thr) / 16
            fill = ramp(p, theme)
            ink = "#0b0b0b" if lum(fill) > 0.25 else "#f5f5f3"
            s.rect(ox + j * cell + 1, oy + i * cell + 1, cell - 2, cell - 2, fill, rx=3,
                   title="%s initiates vs %s: threshold %X, wins %d/16" % (NAMES[o], NAMES[q], thr, 16 - thr))
            s.text(ox + j * cell + cell / 2, oy + i * cell + cell / 2 + 4, "%d" % (16 - thr), 12, ink,
                   anchor="middle", weight="bold" if o == q else "normal")
    s.text(ox - 10, oy - 24, "initiator ↓   opponent →", 11, t["muted"], anchor="end")
    # stage brackets
    for lab, a, b in [("child", 0, 1), ("adult", 2, 8), ("perfect", 9, 11)]:
        y = oy + n * cell + 18
        s.line(ox + a * cell + 4, y, ox + (b + 1) * cell - 4, y, t["axis"], 2)
        s.text(ox + (a + b + 1) * cell / 2, y + 16, lab, 11, t["text2"], anchor="middle")
    # legend
    lx, ly = ox + n * cell + 30, oy
    s.text(lx, ly, "wins out of 16", 12, weight="bold")
    for k in range(0, 17, 2):
        p = k / 16
        s.rect(lx, ly + 12 + (16 - k) * 9, 22, 18, ramp(p, theme), rx=2)
        s.text(lx + 30, ly + 26 + (16 - k) * 9, "%d" % k, 10, t["text2"])
    s.text(lx, ly + 200, "Each enhancement point the", 11, t["text2"])
    s.text(lx, ly + 216, "opponent has over you adds 1", 11, t["text2"])
    s.text(lx, ly + 232, "to the threshold (−1/16).", 11, t["text2"])
    s.text(lx, ly + 262, "Rows are not complements of", 11, t["text2"])
    s.text(lx, ly + 278, "columns: the responder just", 11, t["text2"])
    s.text(lx, ly + 294, "takes 3 − the initiator's result,", 11, t["text2"])
    s.text(lx, ly + 310, "so who presses B last matters.", 11, t["text2"])
    s.text(lx, ly + 340, "Names: slots 3–14 per humulos /", 10, t["muted"])
    s.text(lx, ly + 354, "NHOKO (slot letters A–L).", 10, t["muted"])
    return s


if __name__ == "__main__":
    T = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    for theme in ("light", "dark"):
        fig(T, theme).save(os.path.join(out, "battle_odds-%s.svg" % theme))
    print("ok")
