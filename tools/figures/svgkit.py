"""Minimal SVG builder with light/dark themes (dataviz reference palette)."""
from xml.sax.saxutils import escape

THEMES = {
    "light": {
        "surface": "#fcfcfb", "text": "#0b0b0b", "text2": "#52514e", "muted": "#898781",
        "grid": "#e1e0d9", "axis": "#c3c2b7", "panel": "#f3f2ef",
        "series": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"],
        "neutral": "#b9b7af", "neutral2": "#dedcd5", "ink_on_fill": "#0b0b0b",
    },
    "dark": {
        "surface": "#1a1a19", "text": "#f0efec", "text2": "#c3c2b7", "muted": "#898781",
        "grid": "#2c2c2a", "axis": "#383835", "panel": "#232322",
        "series": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"],
        "neutral": "#55544f", "neutral2": "#383835", "ink_on_fill": "#0b0b0b",
    },
}
FONT = "ui-sans-serif, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
MONO = "ui-monospace, 'SF Mono', Menlo, Consolas, monospace"


class SVG:
    def __init__(self, w, h, theme, title, desc=""):
        self.w, self.h, self.t = w, h, THEMES[theme]
        self.parts = []
        self.title, self.desc = title, desc

    def rect(self, x, y, w, h, fill, rx=0, stroke=None, sw=1, title=None, opacity=None):
        s = '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%s" fill="%s"' % (x, y, w, h, rx, fill)
        if stroke:
            s += ' stroke="%s" stroke-width="%s"' % (stroke, sw)
        if opacity is not None:
            s += ' fill-opacity="%s"' % opacity
        if title:
            s += "><title>%s</title></rect>" % escape(title)
        else:
            s += "/>"
        self.parts.append(s)

    def line(self, x1, y1, x2, y2, stroke, sw=1, dash=None, marker=None):
        s = '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%s"' % (x1, y1, x2, y2, stroke, sw)
        if dash:
            s += ' stroke-dasharray="%s"' % dash
        if marker:
            s += ' marker-end="url(#%s)"' % marker
        self.parts.append(s + "/>")

    def path(self, d, stroke, sw=1.5, fill="none", marker=None, dash=None):
        s = '<path d="%s" stroke="%s" stroke-width="%s" fill="%s"' % (d, stroke, sw, fill)
        if marker:
            s += ' marker-end="url(#%s)"' % marker
        if dash:
            s += ' stroke-dasharray="%s"' % dash
        self.parts.append(s + "/>")

    def text(self, x, y, s, size=12, fill=None, anchor="start", weight="normal", mono=False, rotate=None):
        fam = MONO if mono else FONT
        tr = ' transform="rotate(%s %.1f %.1f)"' % (rotate, x, y) if rotate else ""
        self.parts.append('<text x="%.1f" y="%.1f" font-family="%s" font-size="%s" fill="%s" '
                          'text-anchor="%s" font-weight="%s"%s>%s</text>'
                          % (x, y, fam, size, fill or self.t["text"], anchor, weight, tr, escape(s)))

    def arrow_marker(self, mid, color):
        self.parts.insert(0, '<defs><marker id="%s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
                             'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" '
                             'fill="%s"/></marker></defs>' % (mid, color))

    def render(self):
        head = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
                'role="img" aria-labelledby="t d"><title id="t">%s</title><desc id="d">%s</desc>'
                '<rect width="100%%" height="100%%" fill="%s"/>'
                % (self.w, self.h, self.w, self.h, escape(self.title), escape(self.desc), self.t["surface"]))
        return head + "".join(self.parts) + "</svg>"

    def save(self, path):
        open(path, "w", encoding="utf-8").write(self.render())
