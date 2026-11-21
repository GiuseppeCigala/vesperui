"""Owner-drawn canvas with simple shape primitives."""

from .common import *  # noqa: F401,F403

# ============================================================================
# CANVAS
# ============================================================================
class Canvas(Widget):
    def __init__(self, bg=(255, 255, 255)):
        super().__init__(); self.bg = bg; self.items = []
    def measure(self, app): return (int(300 * app.scale), int(200 * app.scale))
    def clear(self): self.items.clear()
    def line(self, x1, y1, x2, y2, color=(0, 0, 0), width=1):
        self.items.append(('line', x1, y1, x2, y2, color, width))
    def rect(self, x, y, w, h, color=(0, 0, 0), width=1, fill=None):
        self.items.append(('rect', x, y, w, h, color, width, fill))
    def ellipse(self, x, y, w, h, color=(0, 0, 0), width=1, fill=None):
        self.items.append(('ellipse', x, y, w, h, color, width, fill))
    def circle(self, cx, cy, r, color=(0, 0, 0), width=1, fill=None):
        self.ellipse(cx - r, cy - r, 2 * r, 2 * r, color, width, fill)
    def text(self, x, y, text, size=14, color=(0, 0, 0), bold=False):
        self.items.append(('text', x, y, text, size, color, bold))
    def draw(self, hdc, app):
        rc = wintypes.RECT(self.x, self.y, self.x + self.w, self.y + self.h)
        user32.FillRect(hdc, ctypes.byref(rc), app.get_brush(self.bg))
        for it in self.items: self._draw_item(hdc, app, it)
    def _draw_item(self, hdc, app, it):
        kind = it[0]; ox, oy = self.x, self.y
        if kind == 'line':
            _, x1, y1, x2, y2, c, w = it
            pen = app.get_pen(c, max(1, int(w))); old = gdi32.SelectObject(hdc, pen)
            gdi32.MoveToEx(hdc, int(ox + x1), int(oy + y1), None)
            gdi32.LineTo(hdc, int(ox + x2), int(oy + y2))
            gdi32.SelectObject(hdc, old)
        elif kind in ('rect', 'ellipse'):
            _, x, y, w, h, c, lw, fill = it
            draw_fn = gdi32.Rectangle if kind == 'rect' else gdi32.Ellipse
            if fill is not None:
                br = app.get_brush(fill); pn = app.get_pen(fill, 1)
                ob = gdi32.SelectObject(hdc, br); op = gdi32.SelectObject(hdc, pn)
                draw_fn(hdc, int(ox + x), int(oy + y), int(ox + x + w), int(oy + y + h))
                gdi32.SelectObject(hdc, ob); gdi32.SelectObject(hdc, op)
            if lw > 0:
                pen = app.get_pen(c, max(1, int(lw)))
                ob = gdi32.SelectObject(hdc, pen)
                obn = gdi32.SelectObject(hdc, gdi32.GetStockObject(NULL_BRUSH))
                draw_fn(hdc, int(ox + x), int(oy + y), int(ox + x + w), int(oy + y + h))
                gdi32.SelectObject(hdc, ob); gdi32.SelectObject(hdc, obn)
        elif kind == 'text':
            _, x, y, text, size, c, bold = it
            rc = wintypes.RECT(int(ox + x), int(oy + y),
                               int(ox + x) + self.w, int(oy + y) + int(size * 3 * app.scale))
            gdi32.SetBkMode(hdc, TRANSPARENT); gdi32.SetTextColor(hdc, COLORREF(*c))
            of = gdi32.SelectObject(hdc, app.get_font(size, bold))
            user32.DrawTextW(hdc, text, -1, ctypes.byref(rc), DT_LEFT | DT_SINGLELINE)
            gdi32.SelectObject(hdc, of)

