"""Owner-drawn analog VU meter with a needle and a soft gradient scale."""
import math

from .common import *  # noqa: F401,F403
from .style import SCALE_SPLIT, scale_color, style_of

START_ANGLE = 195.0   # degrees, left end of the scale (screen coordinates)
SWEEP = 150.0         # total arc width in degrees
SPLIT = SCALE_SPLIT   # 0 dB reference used to emphasise the label and tick

# Local binding for the polygon-region helper used by the gradient arc.
gdi32.CreatePolygonRgn.argtypes = [ctypes.POINTER(wintypes.POINT),
                                   ctypes.c_int, ctypes.c_int]
gdi32.CreatePolygonRgn.restype = wintypes.HRGN

DEFAULT_SCALE = (
    ('20', 0.00), ('10', 0.10), ('7', 0.20), ('5', 0.30), ('3', 0.40),
    ('2', 0.48), ('1', 0.56), ('0', 0.62), ('1', 0.72), ('2', 0.86),
    ('3', 1.00),
)


class VUMeter(Widget):
    """Analog audio level meter with a soft teal-to-violet scale.

    Drag the needle with the mouse or focus the widget and use the arrow
    keys. The value is always a fraction between 0.0 and 1.0. A peak-hold
    marker remembers the highest level and falls back after a short hold.
    """

    def __init__(self, value=0.0, on_change=None, label='VU', channel='L',
                 scale=None, peak_hold=True, peak_hold_time=1.1,
                 peak_decay=0.30):
        super().__init__()
        self.value = max(0.0, min(1.0, float(value)))
        self.on_change = on_change
        self.label = label
        self.channel = channel
        self.scale = tuple(scale or DEFAULT_SCALE)
        self.peak_hold = peak_hold
        self.peak_hold_time = max(0.0, float(peak_hold_time))
        self.peak_decay = max(0.0, float(peak_decay))
        self.peak = self.value
        self._peak_age = 0.0
        self._timer = False
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
        if not self.peak_hold:
            self.peak = value
        elif value > self.peak:
            self.peak = value
            self._peak_age = 0.0
        if changed and notify and self.on_change:
            self.on_change(value)
        self._invalidate()
        return changed

    def reset_peak(self):
        """Bring the peak marker back onto the current value."""
        self.peak = self.value
        self._peak_age = 0.0
        self._invalidate()

    def tick(self, dt=0.05):
        """Advance the peak-hold timer; call it from an app timer."""
        if not self.peak_hold or self.peak <= self.value:
            self.peak = self.value
            return False
        self._peak_age += max(0.0, float(dt))
        if self._peak_age <= self.peak_hold_time:
            return False
        self.peak = max(self.value,
                        self.peak - self.peak_decay * max(0.0, float(dt)))
        self._invalidate()
        return True

    def _on_peak_timer(self):
        self.tick(0.05)

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
    def _arc_color(self, st, fraction):
        """Return the shared soft Aurora scale color."""
        return scale_color(st, fraction)

    def _arc_region(self, cx, cy, r, width, steps=64):
        """Create a closed region for the arc band."""
        outer = [self._point(cx, cy, r + width * 0.5, i / steps)
                 for i in range(steps + 1)]
        inner = [self._point(cx, cy, r - width * 0.5, i / steps)
                 for i in range(steps + 1)]
        points = outer + inner[::-1]
        array = (wintypes.POINT * len(points))(
            *[wintypes.POINT(int(round(px)), int(round(py)))
              for px, py in points])
        return gdi32.CreatePolygonRgn(array, len(points), 2)  # WINDING

    def _gradient_arc(self, hdc, app, cx, cy, r, width, st):
        """Fill the scale with a smooth horizontal teal-to-violet gradient."""
        s = app.scale
        blend = mix(st['highlight'], st['highlight2'], 0.5)
        low = self._arc_color(st, 0.0)
        mid = self._arc_color(st, SPLIT)
        high = self._arc_color(st, 1.0)

        top = int(cy - r - width * 2)
        height = max(1, int(r + width * 3))
        clip = wintypes.RECT(int(cx - r - width * 2), top,
                             int(cx + r + width * 2), top + height)

        # Two low-contrast halos replace the old bright neon glow.
        for extra, tint in ((8, 0.10), (4, 0.20)):
            band = width + max(2, int(extra * s))
            region = self._arc_region(cx, cy, r, band)
            if not region:
                continue
            saved = gdi32.SaveDC(hdc)
            try:
                gdi32.ExtSelectClipRgn(hdc, region, RGN_AND)
                user32.FillRect(hdc, ctypes.byref(clip),
                                app.get_brush(mix(st['window'], blend, tint)))
            finally:
                gdi32.RestoreDC(hdc, saved)
                gdi32.DeleteObject(region)

        region = self._arc_region(cx, cy, r, width)
        if region:
            x0 = int(self._point(cx, cy, r, 0.0)[0])
            x1 = int(self._point(cx, cy, r, SPLIT)[0])
            x2 = int(self._point(cx, cy, r, 1.0)[0])
            saved = gdi32.SaveDC(hdc)
            try:
                gdi32.ExtSelectClipRgn(hdc, region, RGN_AND)
                fill_gradient_h(hdc, x0, top, max(1, x1 - x0), height,
                                low, mid)
                fill_gradient_h(hdc, x1, top, max(1, x2 - x1), height,
                                mid, high)
            finally:
                gdi32.RestoreDC(hdc, saved)
                gdi32.DeleteObject(region)

        cap = max(1, int(width))
        for fraction in (0.0, 1.0):
            px, py = self._point(cx, cy, r, fraction)
            fill_round_rect(hdc, app, int(px) - cap // 2,
                            int(py) - cap // 2, cap, cap, cap // 2,
                            self._arc_color(st, fraction))

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
        radius = max(6, int(10 * s))

        if self.focused or self._dragging:
            stroke_round_rect(hdc, app, x - 1, y - 1, w + 2, h + 2,
                              radius + 1, st['glow'], max(2, int(2 * s)))
        fill_round_gradient_v(hdc, app, x, y, w, h, radius,
                              st['panel'], st['window'])
        stroke_round_rect(hdc, app, x, y, w, h, radius, st['border'],
                          max(1, int(s)))

        if (self.peak_hold and not self._timer
                and hasattr(app, 'set_timer')):
            self._timer = True
            app.set_timer(50, self._on_peak_timer)

        arc_width = max(5, int(6 * s))
        self._gradient_arc(hdc, app, cx, cy, r, arc_width, st)

        for i in range(len(self.scale)):
            fraction = self.scale[i][1]
            color = self._arc_color(st, fraction)
            major = mix(st['dark'], color, 0.50)
            if abs(fraction - SPLIT) < 1e-6:
                major = mix(st['windowText'], color, 0.35)
            self._tick(hdc, app, cx, cy, r, fraction, True, major, s)
            if i + 1 < len(self.scale):
                nxt = self.scale[i + 1][1]
                for part in (0.25, 0.5, 0.75):
                    mid = fraction + (nxt - fraction) * part
                    self._tick(hdc, app, cx, cy, r, mid, False,
                               mix(st['mid'], self._arc_color(st, mid),
                                   0.45), s)

        label_r = r + 14 * s
        half_w = int(16 * s)
        half_h = int(9 * s)
        for text, fraction in self.scale:
            lx, ly = self._point(cx, cy, label_r, fraction)
            rc = wintypes.RECT(int(lx) - half_w, int(ly) - half_h,
                               int(lx) + half_w, int(ly) + half_h)
            gdi32.SetBkMode(hdc, TRANSPARENT)
            label_color = mix(st['dark'], self._arc_color(st, fraction), 0.48)
            if abs(fraction - SPLIT) < 1e-6:
                label_color = mix(st['windowText'], label_color, 0.25)
            gdi32.SetTextColor(hdc, COLORREF(*label_color))
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
        gdi32.SetTextColor(hdc, COLORREF(*mix(st['dark'], st['mid'], 0.30)))
        user32.DrawTextW(hdc, self.label, -1, ctypes.byref(rc),
                         DT_CENTER | DT_VCENTER | DT_SINGLELINE)
        gdi32.SelectObject(hdc, of)

        tip = self._point(cx, cy, r * 0.96, self.value)
        if self.peak_hold and self.peak > self.value + 0.004:
            p0 = self._point(cx, cy, r - 7 * s, self.peak)
            p1 = self._point(cx, cy, r + 13 * s, self.peak)
            marker = mix(st['windowText'], st['highlight'], 0.30)
            pen = app.get_pen(mix(st['window'], marker, 0.30),
                              max(3, int(3 * s)))
            old = gdi32.SelectObject(hdc, pen)
            gdi32.MoveToEx(hdc, int(p0[0]), int(p0[1]), None)
            gdi32.LineTo(hdc, int(p1[0]), int(p1[1]))
            gdi32.SelectObject(hdc, old)
            pen = app.get_pen(marker, max(1, int(2 * s)))
            old = gdi32.SelectObject(hdc, pen)
            gdi32.MoveToEx(hdc, int(p0[0]), int(p0[1]), None)
            gdi32.LineTo(hdc, int(p1[0]), int(p1[1]))
            gdi32.SelectObject(hdc, old)
            dot = max(1, int(2 * s))
            fill_round_rect(hdc, app, int(p1[0]) - dot, int(p1[1]) - dot,
                            dot * 2, dot * 2, dot, marker)

        needle = mix(st['windowText'], st['dark'], 0.35)
        glow = mix(st['window'], needle, 0.35)
        pen = app.get_pen(glow, max(3, int(4 * s)))
        old = gdi32.SelectObject(hdc, pen)
        gdi32.MoveToEx(hdc, cx, cy, None)
        gdi32.LineTo(hdc, int(tip[0]), int(tip[1]))
        gdi32.SelectObject(hdc, old)
        pen = app.get_pen(needle, max(1, int(2 * s)))
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
                        dot, mix(st['mid'], st['highlight'], 0.18))

        rc = wintypes.RECT(int(x + 10 * s), int(y + h - 24 * s),
                           int(x + 40 * s), int(y + h - 6 * s))
        gdi32.SetBkMode(hdc, TRANSPARENT)
        gdi32.SetTextColor(hdc, COLORREF(*st['mid']))
        of = gdi32.SelectObject(hdc, app.get_font(10, True))
        user32.DrawTextW(hdc, self.channel, -1, ctypes.byref(rc),
                         DT_LEFT | DT_VCENTER | DT_SINGLELINE)
        gdi32.SelectObject(hdc, of)
