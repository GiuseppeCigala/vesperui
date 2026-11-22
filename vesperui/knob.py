"""Owner-drawn rotary knob with an accent ring and a value plate."""
import math

from .common import *  # noqa: F401,F403
from .style import style_of

START_ANGLE = 135.0   # bottom-left end of the ring, in screen degrees
SWEEP = 270.0         # gap left at the bottom


class Knob(Widget):
    """Rotary knob with a dark bezel, an accent ring and a white pointer.

    Drag around the dial to set the value (or focus the widget and use the
    arrow keys). A rounded plate below the knob shows the current value as a
    percentage; pass ``formatter`` to customise the text.
    """

    def __init__(self, value=0.0, on_change=None, show_value=True,
                 formatter=None, accent=None):
        super().__init__()
        self.value = max(0.0, min(1.0, float(value)))
        self.on_change = on_change
        self.show_value = show_value
        self.formatter = formatter
        self.accent = accent
        self.focusable = True
        self._app = None
        self._dragging = False

    # ----------------------------------------------------------- sizing/state
    def measure(self, app):
        return (int(120 * app.scale), int(150 * app.scale))

    def _scale(self):
        return getattr(self._app, 'scale', 1.0)

    def _geometry(self):
        s = self._scale()
        margin = max(2, int(4 * s))
        dial_h = min(self.w, max(10, self.h - int(30 * s)))
        outer_r = max(16, min(self.w // 2, dial_h // 2) - margin)
        cx = self.x + self.w // 2
        cy = self.y + margin + outer_r
        return cx, cy, outer_r

    def _point(self, cx, cy, radius, fraction):
        angle = math.radians(START_ANGLE + SWEEP * fraction)
        return (cx + radius * math.cos(angle),
                cy + radius * math.sin(angle))

    def _value_from_pos(self, x, y):
        cx, cy, _radius = self._geometry()
        angle = math.degrees(math.atan2(y - cy, x - cx)) % 360.0
        rel = (angle - START_ANGLE) % 360.0
        if rel <= SWEEP:
            return rel / SWEEP
        # Inside the bottom gap: snap to the nearest end of the ring.
        return 0.0 if rel > 180.0 + SWEEP / 2.0 else 1.0

    def set_value(self, value, notify=True):
        value = max(0.0, min(1.0, float(value)))
        changed = value != self.value
        self.value = value
        if changed and notify and self.on_change:
            self.on_change(value)
        self._invalidate()
        return changed

    def value_text(self):
        if self.formatter:
            return self.formatter(self.value)
        return '%.1f %%' % (self.value * 100.0)

    def _invalidate(self):
        if self._app:
            self._app.invalidate_rect(self.x, self.y, self.w, self.h)

    # ------------------------------------------------------------ interaction
    def on_mouse_down(self, x, y):
        self._dragging = True
        self.set_value(self._value_from_pos(x, y))

    def on_mouse_move(self, x, y):
        if self._dragging:
            self.set_value(self._value_from_pos(x, y))

    def on_mouse_up(self, x, y):
        self._dragging = False
        self._invalidate()

    def on_key(self, vk, ch):
        if vk in (VK_LEFT, VK_DOWN):
            self.set_value(self.value - 0.05)
        elif vk in (VK_RIGHT, VK_UP):
            self.set_value(self.value + 0.05)

    def on_wheel(self, delta):
        return False

    # -------------------------------------------------------------- drawing
    @staticmethod
    def _fill_circle(hdc, app, cx, cy, r, color):
        if r <= 0:
            return
        brush = app.get_brush(color)
        old_brush = gdi32.SelectObject(hdc, brush)
        old_pen = gdi32.SelectObject(hdc, gdi32.GetStockObject(NULL_PEN))
        gdi32.Ellipse(hdc, cx - r, cy - r, cx + r, cy + r)
        gdi32.SelectObject(hdc, old_brush)
        gdi32.SelectObject(hdc, old_pen)

    @staticmethod
    def _fill_circle_gradient(hdc, app, cx, cy, r, top, bottom):
        if r <= 0:
            return
        rgn = gdi32.CreateEllipticRgn(cx - r, cy - r, cx + r + 1, cy + r + 1)
        saved = gdi32.SaveDC(hdc)
        gdi32.ExtSelectClipRgn(hdc, rgn, RGN_AND)
        fill_gradient_v(hdc, cx - r, cy - r, 2 * r, 2 * r, top, bottom)
        gdi32.RestoreDC(hdc, saved)
        gdi32.DeleteObject(rgn)

    def _polyline(self, hdc, app, points, color, width, cap=False):
        pen = app.get_pen(color, max(1, int(round(width))))
        old = gdi32.SelectObject(hdc, pen)
        gdi32.MoveToEx(hdc, int(round(points[0][0])),
                       int(round(points[0][1])), None)
        for px, py in points[1:]:
            gdi32.LineTo(hdc, int(round(px)), int(round(py)))
        gdi32.SelectObject(hdc, old)
        if cap:
            size = max(1, int(round(width)))
            for px, py in (points[0], points[-1]):
                self._fill_circle(hdc, app, int(round(px)), int(round(py)),
                                  size // 2, color)

    def _ring(self, hdc, app, cx, cy, radius, color, width):
        steps = max(24, int(SWEEP / 2))
        points = [self._point(cx, cy, radius, i / steps)
                  for i in range(steps + 1)]
        self._polyline(hdc, app, points, color, width, cap=True)

    def _draw_value(self, hdc, app, cx, cy, outer_r, s, st):
        width = int(76 * s)
        height = int(22 * s)
        px = cx - width // 2
        py = cy + outer_r + int(8 * s)
        radius = max(3, int(4 * s))
        fill_round_rect(hdc, app, px, py, width, height, radius,
                        mix(st['window'], st['base'], 0.5))
        stroke_round_rect(hdc, app, px, py, width, height, radius,
                          st['border'], max(1, int(s)))
        rc = wintypes.RECT(px, py, px + width, py + height)
        gdi32.SetBkMode(hdc, TRANSPARENT)
        gdi32.SetTextColor(hdc, COLORREF(*st['windowText']))
        of = gdi32.SelectObject(hdc, app.get_font(11, True))
        user32.DrawTextW(hdc, self.value_text(), -1, ctypes.byref(rc),
                         DT_CENTER | DT_VCENTER | DT_SINGLELINE)
        gdi32.SelectObject(hdc, of)

    def draw(self, hdc, app):
        self._app = app
        s = app.scale
        st = style_of(app)
        accent = self.accent if self.accent is not None else st['highlight']
        cx, cy, outer_r = self._geometry()

        bezel_w = max(4, int(7 * s))
        ring_w = max(3, int(4 * s))
        bezel_r = outer_r - bezel_w // 2
        ring_r = outer_r - bezel_w - int(3 * s) - ring_w // 2
        inner_r = max(8, ring_r - ring_w // 2 - int(3 * s))

        if self.focused or self.hovered or self._dragging:
            self._ring(hdc, app, cx, cy, outer_r + int(2 * s),
                       mix(st['window'], accent, 0.55), max(2, int(2 * s)))

        bezel = mix(st['window'], st['border'], 0.60)
        self._ring(hdc, app, cx, cy, bezel_r, bezel, bezel_w)

        self._ring(hdc, app, cx, cy, ring_r,
                   mix(st['window'], accent, 0.30),
                   ring_w + max(2, int(2 * s)))
        self._ring(hdc, app, cx, cy, ring_r, accent, ring_w)

        top = mix(st['base'], accent, 0.12)
        bottom = mix(st['window'], accent, 0.05)
        self._fill_circle_gradient(hdc, app, cx, cy, inner_r, top, bottom)

        p0 = self._point(cx, cy, inner_r * 0.45, self.value)
        p1 = self._point(cx, cy, inner_r * 0.92, self.value)
        self._polyline(hdc, app, [p0, p1], (240, 244, 244),
                       max(4, int(7 * s)), cap=True)

        if self.show_value:
            self._draw_value(hdc, app, cx, cy, outer_r, s, st)
