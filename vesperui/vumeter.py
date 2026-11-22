"""Owner-drawn analog VU meter with a needle and colored zones."""
import math

from .common import *  # noqa: F401,F403
from .style import style_of

START_ANGLE = 195.0   # degrees, left end of the scale (screen coordinates)
SWEEP = 150.0         # total arc width in degrees
SPLIT = 0.62          # fraction where the cyan zone turns magenta (0 dB)

DEFAULT_SCALE = (
    ('20', 0.00), ('10', 0.10), ('7', 0.20), ('5', 0.30), ('3', 0.40),
    ('2', 0.48), ('1', 0.56), ('0', 0.62), ('1', 0.72), ('2', 0.86),
    ('3', 1.00),
)


class VUMeter(Widget):
    """Analog audio level meter: cyan zone up to 0 dB, magenta in the red.

    Drag the needle with the mouse or focus the widget and use the arrow
    keys. The value is always a fraction between 0.0 and 1.0.
    """

    def __init__(self, value=0.0, on_change=None, label='VU', channel='L',
                 scale=None):
        super().__init__()
        self.value = max(0.0, min(1.0, float(value)))
        self.on_change = on_change
        self.label = label
        self.channel = channel
        self.scale = tuple(scale or DEFAULT_SCALE)
        self.focusable = True
        self._app = None
        self._dragging = False

    def measure(self, app):
        return (int(260 * app.scale), int(180 * app.scale))

    # ------------------------------------------------------------- geometry
    def _geometry(self):
        cx = self.x + self.w // 2
        cy = self.y + int(self.h * 0.86)
        radius = max(12, int(min(self.w * 0.40, self.h * 0.60)))
        return cx, cy, radius

    def _point(self, cx, cy, radius, fraction):
        angle = math.radians(START_ANGLE + SWEEP * fraction)
        return (cx + radius * math.cos(angle), cy + radius * math.sin(angle))

    def _angle_at(self, x, y):
        cx, cy, _radius = self._geometry()
        return math.degrees(math.atan2(y - cy, x - cx)) % 360.0

    def _value_from_pos(self, x, y):
        rel = (self._angle_at(x, y) - START_ANGLE) % 360.0
        if rel <= SWEEP:
            return rel / SWEEP
        # Outside the arc: snap to whichever end of the scale is closer.
        return 0.0 if rel > 180.0 + SWEEP / 2.0 else 1.0

    # ----------------------------------------------------------------- state
    def _invalidate(self):
        if self._app:
            self._app.invalidate_rect(self.x, self.y, self.w, self.h)

    def set_value(self, value, notify=True):
        value = max(0.0, min(1.0, float(value)))
        changed = value != self.value
        self.value = value
        if changed and notify and self.on_change:
            self.on_change(value)
        self._invalidate()
        return changed

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
        return False  # let the surrounding ScrollView handle the wheel

    # -------------------------------------------------------------- drawing
    def _polyline(self, hdc, app, points, color, width):
        pen = app.get_pen(color, max(1, int(width)))
        old = gdi32.SelectObject(hdc, pen)
        x0, y0 = points[0]
        gdi32.MoveToEx(hdc, int(round(x0)), int(round(y0)), None)
        for px, py in points[1:]:
            gdi32.LineTo(hdc, int(round(px)), int(round(py)))
        gdi32.SelectObject(hdc, old)

    def _arc(self, hdc, app, cx, cy, r, f0, f1, color, width, st):
        """Draw an arc segment with a soft glow and rounded end caps."""
        steps = max(12, int((f1 - f0) * SWEEP / 2))
        points = [self._point(cx, cy, r, f0 + (f1 - f0) * i / steps)
                  for i in range(steps + 1)]
        glow = mix(st['window'], color, 0.40)
        self._polyline(hdc, app, points, glow, width + 5 * app.scale)
        for px, py in (points[0], points[-1]):
            size = int(width + 5 * app.scale)
            fill_round_rect(hdc, app, int(px) - size // 2, int(py) - size // 2,
                            size, size, size // 2, glow)
        self._polyline(hdc, app, points, color, width)
        for px, py in (points[0], points[-1]):
            size = int(width)
            fill_round_rect(hdc, app, int(px) - size // 2, int(py) - size // 2,
                            size, size, size // 2, color)

    def _tick(self, hdc, app, cx, cy, r, fraction, major, color, s):
        inner = r - 2 * s
        outer = r + (10 if major else 5) * s
        p0 = self._point(cx, cy, inner, fraction)
        p1 = self._point(cx, cy, outer, fraction)
        pen = app.get_pen(color, max(1, int((2 if major else 1) * s)))
        old = gdi32.SelectObject(hdc, pen)
        gdi32.MoveToEx(hdc, int(p0[0]), int(p0[1]), None)
        gdi32.LineTo(hdc, int(p1[0]), int(p1[1]))
        gdi32.SelectObject(hdc, old)

    def draw(self, hdc, app):
        self._app = app
        s = app.scale
        st = style_of(app)
        x, y, w, h = self.x, self.y, self.w, self.h
        cx, cy, r = self._geometry()
        cyan = st['highlight']
        magenta = st['highlight2']
        radius = max(6, int(10 * s))

        if self.focused or self._dragging:
            stroke_round_rect(hdc, app, x - 1, y - 1, w + 2, h + 2,
                              radius + 1, st['glow'], max(2, int(2 * s)))
        fill_round_gradient_v(hdc, app, x, y, w, h, radius,
                              st['panel'], st['window'])
        stroke_round_rect(hdc, app, x, y, w, h, radius, st['border'],
                          max(1, int(s)))

        arc_width = 6 * s
        self._arc(hdc, app, cx, cy, r, 0.0, SPLIT, cyan, arc_width, st)
        self._arc(hdc, app, cx, cy, r, SPLIT, 1.0, magenta, arc_width, st)

        for i in range(len(self.scale)):
            fraction = self.scale[i][1]
            color = cyan if fraction < SPLIT else magenta
            self._tick(hdc, app, cx, cy, r, fraction, True, color, s)
            if i + 1 < len(self.scale):
                nxt = self.scale[i + 1][1]
                for part in (0.25, 0.5, 0.75):
                    mid = fraction + (nxt - fraction) * part
                    self._tick(hdc, app, cx, cy, r, mid, False,
                               cyan if mid < SPLIT else magenta, s)

        label_r = r + 14 * s
        half_w = int(16 * s)
        half_h = int(9 * s)
        for text, fraction in self.scale:
            lx, ly = self._point(cx, cy, label_r, fraction)
            rc = wintypes.RECT(int(lx) - half_w, int(ly) - half_h,
                               int(lx) + half_w, int(ly) + half_h)
            gdi32.SetBkMode(hdc, TRANSPARENT)
            gdi32.SetTextColor(hdc, COLORREF(*(
                cyan if fraction < SPLIT else magenta)))
            of = gdi32.SelectObject(hdc, app.get_font(10, True))
            user32.DrawTextW(hdc, text, -1, ctypes.byref(rc),
                             DT_CENTER | DT_VCENTER | DT_SINGLELINE)
            gdi32.SelectObject(hdc, of)

        vy = cy - int(r * 0.42)
        rc = wintypes.RECT(int(cx - 60 * s), int(vy - 22 * s),
                           int(cx + 60 * s), int(vy + 22 * s))
        shadow = wintypes.RECT(rc.left + max(1, int(s)),
                               rc.top + max(1, int(s)),
                               rc.right + max(1, int(s)),
                               rc.bottom + max(1, int(s)))
        gdi32.SetBkMode(hdc, TRANSPARENT)
        of = gdi32.SelectObject(hdc, app.get_font(20, True))
        gdi32.SetTextColor(hdc, COLORREF(*st['window']))
        user32.DrawTextW(hdc, self.label, -1, ctypes.byref(shadow),
                         DT_CENTER | DT_VCENTER | DT_SINGLELINE)
        gdi32.SetTextColor(hdc, COLORREF(*st['dark']))
        user32.DrawTextW(hdc, self.label, -1, ctypes.byref(rc),
                         DT_CENTER | DT_VCENTER | DT_SINGLELINE)
        gdi32.SelectObject(hdc, of)

        tip = self._point(cx, cy, r * 0.96, self.value)
        glow = mix((255, 255, 255), st['window'], 0.45)
        pen = app.get_pen(glow, max(3, int(5 * s)))
        old = gdi32.SelectObject(hdc, pen)
        gdi32.MoveToEx(hdc, cx, cy, None)
        gdi32.LineTo(hdc, int(tip[0]), int(tip[1]))
        gdi32.SelectObject(hdc, old)
        pen = app.get_pen((245, 245, 255), max(2, int(2 * s)))
        old = gdi32.SelectObject(hdc, pen)
        gdi32.MoveToEx(hdc, cx, cy, None)
        gdi32.LineTo(hdc, int(tip[0]), int(tip[1]))
        gdi32.SelectObject(hdc, old)

        pr = max(6, int(8 * s))
        fill_round_rect(hdc, app, cx - pr, cy - pr, pr * 2, pr * 2,
                        pr, st['base'])
        stroke_round_rect(hdc, app, cx - pr, cy - pr, pr * 2, pr * 2,
                          pr, st['border'], max(1, int(s)))
        dot = max(2, int(3 * s))
        fill_round_rect(hdc, app, cx - dot, cy - dot, dot * 2, dot * 2,
                        dot, st['mid'])

        rc = wintypes.RECT(int(x + 10 * s), int(y + h - 24 * s),
                           int(x + 40 * s), int(y + h - 6 * s))
        gdi32.SetBkMode(hdc, TRANSPARENT)
        gdi32.SetTextColor(hdc, COLORREF(*st['mid']))
        of = gdi32.SelectObject(hdc, app.get_font(10, True))
        user32.DrawTextW(hdc, self.channel, -1, ctypes.byref(rc),
                         DT_LEFT | DT_VCENTER | DT_SINGLELINE)
        gdi32.SelectObject(hdc, of)
