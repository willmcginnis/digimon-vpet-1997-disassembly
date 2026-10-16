"""Ver.1 / Ver.2 alignment ribbon.

usage: python3 figs_versions.py v1v2_align.json OUTDIR
v1v2_align.json: {"blocks": [[v1_start, v2_start, length], ...]} from a difflib alignment of
the two instruction streams with jump targets reduced to their 8-bit step.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from svgkit import SVG  # noqa: E402


def fig(blocks, theme):
    W, H = 1000, 350
    s = SVG(W, H, theme, "Where Ver.1 and Ver.2 share code",
            "Bands connect runs of identical instructions in the two ROMs.")
    t = s.t
    s.text(24, 32, "Where Ver. 1 and Ver. 2 share code", 18, weight="bold")
    s.text(24, 54, "Each band joins a run of identical instructions (≥ 8 words) in the two ROMs; "
                   "jump targets compared by step only.", 12, t["text2"])
    x0, x1 = 70, W - 30
    ya, yb = 110, 250
    sc = (x1 - x0) / 8192
    for y, lab in ((ya, "Ver. 1"), (yb, "Ver. 2")):
        s.rect(x0, y - 14 if y == ya else y, x1 - x0, 14, t["neutral2"], rx=2)
        s.text(x0 - 10, y - 3 if y == ya else y + 11, lab, 12, anchor="end", weight="bold")
    for k in range(0, 8193, 1024):
        x = x0 + k * sc
        s.line(x, ya - 18, x, ya - 14, t["axis"], 1)
        s.text(x, ya - 22, "%04X" % k if k < 8192 else "", 9, t["muted"], anchor="middle", mono=True)
    s.line(x0 + 4096 * sc, ya - 30, x0 + 4096 * sc, yb + 30, t["axis"], 1, dash="3 3")
    s.text(x0 + 2048 * sc, yb + 36, "bank 0: 82% of Ver. 1 shared", 11, t["text2"], anchor="middle")
    s.text(x0 + 6144 * sc, yb + 36, "bank 1: 35% shared", 11, t["text2"], anchor="middle")
    for i, j, n in blocks:
        if n < 8:
            continue
        c = t["series"][0] if i < 0x1000 else t["series"][6]
        d = "M %.1f %d L %.1f %d L %.1f %d L %.1f %d Z" % (
            x0 + i * sc, ya, x0 + (i + n) * sc, ya, x0 + (j + n) * sc, yb, x0 + j * sc, yb)
        s.parts.append('<path d="%s" fill="%s" fill-opacity="0.45" stroke="none"><title>V1 %04X-%04X = V2 %04X-%04X (%d words)</title></path>'
                       % (d, c, i, i + n - 1, j, j + n - 1, n))
        s.rect(x0 + i * sc, ya - 14, max(0.8, n * sc), 14, c, opacity=0.9)
        s.rect(x0 + j * sc, yb, max(0.8, n * sc), 14, c, opacity=0.9)
    s.text(24, 330, "The logic (bank 0) is largely the same program, shifted by small edits; bank 1, the species "
                    "graphics and animation, was largely rewritten for the new roster.", 11, t["text2"])
    return s


if __name__ == "__main__":
    blocks = json.load(open(sys.argv[1]))["blocks"]
    os.makedirs(sys.argv[2], exist_ok=True)
    for theme in ("light", "dark"):
        fig(blocks, theme).save(os.path.join(sys.argv[2], "versions-%s.svg" % theme))
    print("ok")
