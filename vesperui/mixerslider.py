"""Owner-drawn mixer fader with a dB taper and a large fader cap."""
from .common import *  # noqa: F401,F403
from .style import style_of

# dB value -> position along the fader (0 = bottom/left, 1 = top/right).
MIXER_STOPS = (
    (-60.0, 0.00), (-40.0, 0.15), (-30.0, 0.22), (-20.0, 0.32),
    (-15.0, 0.39), (-10.0, 0.47), (-5.0, 0.59), (0.0, 0.76),
    (6.0, 1.00),
)

# Printed scale, without minus signs, as on classic mixer faders.
SCALE_LABELS = (
    (6.0, '6'), (0.0, '0'), (-5.0, '5'), (-10.0, '10'),
    (-15.0, '15'), (-20.0, '20'), (-30.0, '30'), (-40.0, '40'),
    (-60.0, '∞'),
)


def fader_db_to_fraction(db):
    """Map a fader level in dB (-60..+6) to a 0..1 position."""
    db = max(MIXER_STOPS[0][0], min(MIXER_STOPS[-1][0], float(db)))
    for i in range(1, len(MIXER_STOPS)):
        db0, f0 = MIXER_STOPS[i - 1]
        db1, f1 = MIXER_STOPS[i]
        if db <= db1:
            span = db1 - db0
            t = (db - db0) / span if span else 0.0
            return f0 + (f1 - f0) * t
    return 1.0


def fader_fraction_to_db(fraction):
    """Map a 0..1 fader position back to a level in dB."""
    fraction = max(0.0, min(1.0, float(fraction)))
    for i in range(1, len(MIXER_STOPS)):
        db0, f0 = MIXER_STOPS[i - 1]
        db1, f1 = MIXER_STOPS[i]
        if fraction <= f1:
            span = f1 - f0
            t = (fraction - f0) / span if span else 0.0
            return db0 + (db1 - db0) * t
    return MIXER_STOPS[-1][0]


class MixerSlider(Widget):
    """Mixer-style fader: thin rail, large cap and a non-linear dB scale.

    ``value`` is expressed in dB between ``min_db`` and ``max_db``. Drag the
    cap anywhere on the rail, or focus the widget and use the arrow keys to
    move it in small steps. The printed scale follows the classic mixer
    layout (6, 0, 5, 10, 15, 20, 30, 40, ∞) without minus signs.
    """

    db_to_fraction = staticmethod(fader_db_to_fraction)
    fraction_to_db = staticmethod(fader_fraction_to_db)

    def __init__(self, value=0.0, on_change=None, orientation='v',
                 min_db=-60.0, max_db=6.0):
        super().__init__()
        self.min_db = float(min_db)
        self.max_db = float(max_db)
        self.orientation = 'h' if orientation in ('h', 'horizontal') else 'v'
        self.value = self._clamp(value)
        self.on_change = on_change
        self.focusable = True
        self._app = None
        self._dragging = False

    # ----------------------------------------------------------- sizing/state
    def measure(self, app):
        if self.orientation == 'v':
            return (int(112 * app.scale), int(340 * app.scale))
        return (int(340 * app.scale), int(84 * app.scale))

    def _clamp(self, value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            value = 0.0
        return max(self.min_db, min(self.max_db, value))

    def set_value(self, value, notify=True):
        value = self._clamp(value)
        changed = value != self.value
        self.value = value
        if changed and notify and self.on_change:
            self.on_change(value)
        self._invalidate()
        return changed

    def value_text(self):
        if self.value <= MIXER_STOPS[0][0] + 1e-9:
            return '-∞ dB'
        return '%.1f dB' % self.value

    def _invalidate(self):
        if self._app:
            self._app.invalidate_rect(self.x, self.y, self.w, self.h)

    # -------------------------------------------------------------- geometry
    def _scale(self):
        return getattr(self._app, 'scale', 1.0)

    def _track_span(self):
        """Return (low, high, center) in pixels along the travel axis."""
        s = self._scale()
        pad = max(4, int(8 * s))
        if self.orientation == 'v':
            inset = int(52 * s) // 2 + max(2, int(4 * s))
            low = self.y + self.h - inset
            high = self.y + inset
            center = self.x + pad + int(34 * s) // 2
        else:
            inset = int(52 * s) // 2 + max(2, int(4 * s))
            low = self.x + inset
            high = self.x + self.w - inset
            center = self.y + pad + int(30 * s) // 2
        return low, high, center

    def _fraction_at(self, x, y):
        low, high, _center = self._track_span()
        span = max(1, abs(high - low))
        if self.orientation == 'v':
            return max(0.0, min(1.0, (low - y) / float(span)))
        return max(0.0, min(1.0, (x - low) / float(span)))

    # ------------------------------------------------------------ interaction
    def on_mouse_down(self, x, y):
        self._dragging = True
        self.set_value(fader_fraction_to_db(self._fraction_at(x, y)))

    def on_mouse_move(self, x, y):
        if self._dragging:
            self.set_value(fader_fraction_to_db(self._fraction_at(x, y)))

    def on_mouse_up(self, x, y):
        self._dragging = False
        self._invalidate()

    def on_key(self, vk, ch):
        fraction = fader_db_to_fraction(self.value)
        if vk in (VK_LEFT, VK_DOWN):
            self.set_value(fader_fraction_to_db(fraction - 0.02))
        elif vk in (VK_RIGHT, VK_UP):
            self.set_value(fader_fraction_to_db(fraction + 0.02))

    def on_wheel(self, delta):
        return False

    # -------------------------------------------------------------- drawing
    def _draw_scale(self, hdc, app, low, high, center, s, st):
        travel = max(1, abs(high - low))
        vertical = self.orientation == 'v'
        tick_x0 = tick_x1 = tick_y0 = tick_y1 = 0
        if vertical:
            tick_x0 = center + int(34 * s) // 2 + max(3, int(6 * s))
            tick_x1 = tick_x0 + max(6, int(12 * s))
        else:
            tick_y0 = center + int(30 * s) // 2 + max(2, int(4 * s))
            tick_y1 = tick_y0 + max(3, int(6 * s))
        for db, text in SCALE_LABELS:
            fraction = fader_db_to_fraction(db)
            color = st['windowText'] if db == 0 else st['dark']
            if vertical:
                py = low - int(round(fraction * travel))
                pen = app.get_pen(st['mid'], max(1, int(s)))
                old = gdi32.SelectObject(hdc, pen)
                gdi32.MoveToEx(hdc, tick_x0, py, None)
                gdi32.LineTo(hdc, tick_x1, py)
                gdi32.SelectObject(hdc, old)
                rc = wintypes.RECT(tick_x1 + int(4 * s), py - int(9 * s),
                                   self.x + self.w - int(4 * s),
                                   py + int(9 * s))
                align = DT_LEFT | DT_VCENTER | DT_SINGLELINE
            else:
                px = low + int(round(fraction * travel))
                pen = app.get_pen(st['mid'], max(1, int(s)))
                old = gdi32.SelectObject(hdc, pen)
                gdi32.MoveToEx(hdc, px, tick_y0, None)
                gdi32.LineTo(hdc, px, tick_y1)
                gdi32.SelectObject(hdc, old)
                left = max(self.x + int(2 * s), px - int(16 * s))
                right = min(self.x + self.w - int(2 * s), px + int(16 * s))
                rc = wintypes.RECT(left, tick_y1 + int(2 * s), right,
                                   tick_y1 + int(16 * s))
                align = DT_CENTER | DT_VCENTER | DT_SINGLELINE
            gdi32.SetBkMode(hdc, TRANSPARENT)
            gdi32.SetTextColor(hdc, COLORREF(*color))
            of = gdi32.SelectObject(
                hdc, app.get_font(11, True) if db == 0 else app.get_font(9))
            user32.DrawTextW(hdc, text, -1, ctypes.byref(rc), align)
            gdi32.SelectObject(hdc, of)

    def _background_color(self, app):
        """Find the background behind the widget, walking up the parents."""
        node = self.parent
        while node is not None:
            bg = getattr(node, 'bg', None)
            if bg is not None:
                return bg
            node = node.parent
        return getattr(app, 'bg', None) or style_of(app)['window']

    def _draw_cap(self, hdc, app, cx, cy, s, st):
        vertical = self.orientation == 'v'
        knob_w = int(34 * s) if vertical else int(52 * s)
        knob_h = int(52 * s) if vertical else int(30 * s)
        kx = cx - knob_w // 2
        ky = cy - knob_h // 2
        radius = max(4, knob_w // 3) if vertical else max(4, knob_h // 3)

        # Soft shadow: many shrinking rounded rectangles fading from the
        # parent background into the dark, so the halo is blurred instead of
        # a solid dark block covering the background.
        base = self._background_color(app)
        steps = max(6, int(10 * s))
        for i in range(steps, 0, -1):
            t = i / (steps + 1.0)
            strength = 0.03 + 0.30 * (1.0 - t)
            col = mix(base, (0, 0, 0), strength)
            fill_round_rect(hdc, app, kx - i + int(2 * s),
                            ky - i + int(3 * s), knob_w + 2 * i,
                            knob_h + 2 * i, radius + i, col)

        if self.focused or self.hovered or self._dragging:
            stroke_round_rect(hdc, app, kx - 2, ky - 2, knob_w + 4,
                              knob_h + 4, radius + 2, st['glow'],
                              max(2, int(2 * s)))

        fill_round_gradient_v(hdc, app, kx, ky, knob_w, knob_h, radius,
                              (241, 249, 249), (203, 220, 222))
        stroke_round_rect(hdc, app, kx, ky, knob_w, knob_h, radius,
                          (58, 68, 72), max(1, int(s)))
        gloss_h = max(2, int(4 * s))
        fill_round_rect(hdc, app, kx + int(5 * s), ky + int(6 * s),
                        knob_w - int(10 * s), gloss_h,
                        max(1, int(2 * s)), (252, 255, 255))

        pen = app.get_pen((40, 48, 52), max(1, int(2 * s)))
        old = gdi32.SelectObject(hdc, pen)
        if vertical:
            gdi32.MoveToEx(hdc, kx + int(5 * s), cy, None)
            gdi32.LineTo(hdc, kx + knob_w - int(5 * s), cy)
        else:
            gdi32.MoveToEx(hdc, cx, ky + int(5 * s), None)
            gdi32.LineTo(hdc, cx, ky + knob_h - int(5 * s))
        gdi32.SelectObject(hdc, old)

    def draw(self, hdc, app):
        self._app = app
        s = app.scale
        st = style_of(app)
        low, high, center = self._track_span()
        fraction = fader_db_to_fraction(self.value)
        travel = max(1, abs(high - low))
        track_w = max(3, int(4 * s))
        track_color = mix(st['window'], (0, 0, 0), 0.45)

        if self.orientation == 'v':
            fill_round_rect(hdc, app, center - track_w // 2, high,
                            track_w, travel, track_w // 2, track_color)
            pos = low - int(round(fraction * travel))
        else:
            fill_round_rect(hdc, app, low, center - track_w // 2,
                            travel, track_w, track_w // 2, track_color)
            pos = low + int(round(fraction * travel))

        self._draw_scale(hdc, app, low, high, center, s, st)
        if self.orientation == 'v':
            self._draw_cap(hdc, app, center, pos, s, st)
        else:
            self._draw_cap(hdc, app, pos, center, s, st)
