"""Owner-drawn segmented stereo level meter (horizontal or vertical)."""
from .common import *  # noqa: F401,F403
from .style import scale_color, style_of

# dB breakpoints mapped to a 0..1 position along the bar. The scale is
# deliberately non-linear so that the top 20 dB use most of the length.
DB_STOPS = (
    (-60.0, 0.00), (-50.0, 0.05), (-40.0, 0.20), (-30.0, 0.38),
    (-20.0, 0.57), (-10.0, 0.78), (-6.0, 0.87), (-3.0, 0.93),
    (0.0, 1.00),
)

VERTICAL_DB_TICKS = (0.0, -3.0, -6.0, -10.0, -20.0, -30.0, -40.0, -50.0)
HORIZONTAL_DB_TICKS = (0.0, -3.0, -6.0, -10.0, -20.0, -30.0, -40.0, -60.0)


def db_to_fraction(db):
    """Map a level in dB (-60..0) to a position along the bar (0.0..1.0)."""
    db = max(DB_STOPS[0][0], min(0.0, float(db)))
    for i in range(1, len(DB_STOPS)):
        db0, f0 = DB_STOPS[i - 1]
        db1, f1 = DB_STOPS[i]
        if db <= db1:
            span = db1 - db0
            t = (db - db0) / span if span else 0.0
            return f0 + (f1 - f0) * t
    return 1.0


def fraction_to_db(fraction):
    """Map a position along the bar (0.0..1.0) back to a level in dB."""
    fraction = max(0.0, min(1.0, float(fraction)))
    for i in range(1, len(DB_STOPS)):
        db0, f0 = DB_STOPS[i - 1]
        db1, f1 = DB_STOPS[i]
        if fraction <= f1:
            span = f1 - f0
            t = (fraction - f0) / span if span else 0.0
            return db0 + (db1 - db0) * t
    return 0.0


class LevelMeter(Widget):
    """Segmented level meter with one or two channels and a dB scale.

    ``levels`` may be a single number or a sequence (for example ``L`` and
    ``R``). Each level is a fraction between 0.0 and 1.0. Drag a bar to set
    that channel, or focus the widget and use the arrow keys on the active
    channel. Lit segments follow the soft teal-to-violet Aurora scale and a
    muted peak line remembers the maximum before falling back.
    """

    def __init__(self, levels=(0.0, 0.0), orientation='v',
                 labels=('L', 'R'), peak_hold=True, peak_hold_time=1.1,
                 peak_decay=0.30, on_change=None, show_db=True):
        super().__init__()
        if isinstance(levels, (int, float)):
            levels = (levels,)
        levels = tuple(levels) or (0.0,)
        self.levels = [max(0.0, min(1.0, float(v))) for v in levels]
        self.orientation = 'h' if orientation in ('h', 'horizontal') else 'v'
        self.labels = tuple(labels) if labels else ()
        self.peak_hold = peak_hold
        self.peak_hold_time = max(0.0, float(peak_hold_time))
        self.peak_decay = max(0.0, float(peak_decay))
        self.peaks = list(self.levels)
        self._peak_age = [0.0] * len(self.levels)
        self.on_change = on_change
        self.show_db = show_db
        self.focusable = True
        self._timer = False
        self._app = None
        self._dragging = False
        self._active = 0
        self.db_ticks = (VERTICAL_DB_TICKS if self.orientation == 'v'
                         else HORIZONTAL_DB_TICKS)

    # ----------------------------------------------------------- sizing/state
    def measure(self, app):
        if self.orientation == 'v':
            return (int(108 * app.scale), int(320 * app.scale))
        return (int(340 * app.scale), int(90 * app.scale))

    def set_level(self, index, value, notify=True):
        index = max(0, min(len(self.levels) - 1, int(index)))
        value = max(0.0, min(1.0, float(value)))
        changed = value != self.levels[index]
        self.levels[index] = value
        self._update_peak(index)
        if changed and notify and self.on_change:
            self.on_change(index, value)
        self._invalidate()
        return changed

    def set_levels(self, values, notify=True):
        if isinstance(values, (int, float)):
            values = (values,)
        changed = False
        for i, value in enumerate(list(values)[:len(self.levels)]):
            if self.set_level(i, value, notify=notify):
                changed = True
        return changed

    def _update_peak(self, index):
        value = self.levels[index]
        if not self.peak_hold:
            self.peaks[index] = value
        elif value > self.peaks[index]:
            self.peaks[index] = value
            self._peak_age[index] = 0.0

    def reset_peaks(self):
        self.peaks = list(self.levels)
        self._peak_age = [0.0] * len(self.levels)
        self._invalidate()

    def tick(self, dt=0.05):
        """Advance the peak-hold timers; call it from an app timer."""
        if not self.peak_hold:
            return False
        changed = False
        dt = max(0.0, float(dt))
        for i, value in enumerate(self.levels):
            if self.peaks[i] <= value:
                self.peaks[i] = value
                continue
            self._peak_age[i] += dt
            if self._peak_age[i] <= self.peak_hold_time:
                continue
            self.peaks[i] = max(value, self.peaks[i] - self.peak_decay * dt)
            changed = True
        if changed:
            self._invalidate()
        return changed

    def _on_peak_timer(self):
        self.tick(0.05)

    def _invalidate(self):
        if self._app:
            self._app.invalidate_rect(self.x, self.y, self.w, self.h)

    # -------------------------------------------------------------- geometry
    def _scale(self):
        return getattr(self._app, 'scale', 1.0)

    def _bar_rects(self):
        """Return one (x, y, w, h) rectangle per channel bar."""
        s = self._scale()
        pad = max(4, int(10 * s))
        x, y, w, h = self.x, self.y, self.w, self.h
        count = len(self.levels)
        rects = []
        if self.orientation == 'v':
            label_w = int(46 * s)
            chan_h = int(12 * s)
            gap = max(2, int(5 * s))
            bx = x + pad
            by = y + pad
            bw = max(8, w - 2 * pad - label_w)
            bh = max(8, h - 2 * pad - chan_h)
            each = max(4, (bw - gap * (count - 1)) // count)
            for i in range(count):
                rects.append((bx + i * (each + gap), by, each, bh))
        else:
            label_w = int(16 * s)
            row_h = max(6, int(18 * s))
            gap = max(2, int(6 * s))
            bx = x + pad + label_w
            bw = max(8, w - 2 * pad - label_w)
            by = y + pad
            for i in range(count):
                rects.append((bx, by + i * (row_h + gap), bw, row_h))
        return rects

    def _channel_at(self, x, y):
        rects = self._bar_rects()
        best, best_distance = 0, None
        for i, (bx, by, bw, bh) in enumerate(rects):
            if self.orientation == 'v':
                distance = abs(x - (bx + bw / 2.0))
            else:
                distance = abs(y - (by + bh / 2.0))
            if best_distance is None or distance < best_distance:
                best, best_distance = i, distance
        return best

    def _fraction_for(self, index, x, y):
        rects = self._bar_rects()
        index = max(0, min(len(rects) - 1, int(index)))
        bx, by, bw, bh = rects[index]
        if self.orientation == 'v':
            return max(0.0, min(1.0, (by + bh - y) / float(bh)))
        return max(0.0, min(1.0, (x - bx) / float(bw)))

    # ------------------------------------------------------------ interaction
    def on_mouse_down(self, x, y):
        self._dragging = True
        self._active = self._channel_at(x, y)
        self.set_level(self._active, self._fraction_for(self._active, x, y))

    def on_mouse_move(self, x, y):
        if self._dragging:
            self.set_level(self._active,
                           self._fraction_for(self._active, x, y))

    def on_mouse_up(self, x, y):
        self._dragging = False
        self._invalidate()

    def on_key(self, vk, ch):
        index = self._active
        if vk in (VK_LEFT, VK_DOWN):
            self.set_level(index, self.levels[index] - 0.05)
        elif vk in (VK_RIGHT, VK_UP):
            self.set_level(index, self.levels[index] + 0.05)

    def on_wheel(self, delta):
        return False

    # -------------------------------------------------------------- drawing
    @staticmethod
    def _fill(hdc, app, x, y, w, h, color):
        if w <= 0 or h <= 0:
            return
        rc = wintypes.RECT(int(x), int(y), int(x + w), int(y + h))
        user32.FillRect(hdc, ctypes.byref(rc), app.get_brush(color))

    def _color_at(self, fraction, st):
        return scale_color(st, fraction)

    def _db_color(self, db, st):
        if db >= -6.0:
            return mix(st['mid'], scale_color(st, 1.0), 0.42)
        return st['mid']

    @staticmethod
    def _db_text(db):
        return '0 dB' if db == 0 else '%g dB' % db

    def _draw_bar(self, hdc, app, bx, by, bw, bh, level, peak):
        s = app.scale
        st = style_of(app)
        vertical = self.orientation == 'v'
        seg = max(2, int(5 * s))
        gap = max(1, int(2 * s))
        length = bh if vertical else bw
        level_px = level * length
        pos = 0
        while pos + seg <= length:
            a, b = pos, pos + seg
            color = self._color_at((a + b) / 2.0 / length, st)
            dark = mix(st['window'], color, 0.24)
            lit = max(0.0, min(float(b), level_px) - a)
            if vertical:
                self._fill(hdc, app, bx, by + length - b, bw, b - a, dark)
                if lit > 0:
                    hh = int(round(lit))
                    self._fill(hdc, app, bx, by + length - a - hh, bw, hh,
                               lighten(color, 0.05))
            else:
                self._fill(hdc, app, bx + a, by, b - a, bh, dark)
                if lit > 0:
                    self._fill(hdc, app, bx + a, by, int(round(lit)), bh,
                               lighten(color, 0.05))
            pos += seg + gap

        peak_px = int(round(peak * length))
        peak_color = mix(st['windowText'], scale_color(st, 1.0), 0.40)
        glow = mix(st['window'], peak_color, 0.35)
        thick = max(4, int(4 * s))
        core = max(2, int(2 * s))
        if vertical:
            py = by + length - peak_px
            self._fill(hdc, app, bx - int(s), py - thick // 2,
                       bw + int(2 * s), thick, glow)
            self._fill(hdc, app, bx, py - core // 2, bw, core, peak_color)
        else:
            px = bx + peak_px
            self._fill(hdc, app, px - thick // 2, by - int(s),
                       thick, bh + int(2 * s), glow)
            self._fill(hdc, app, px - core // 2, by, core, bh, peak_color)

    def _draw_db_vertical(self, hdc, app, rects):
        s = app.scale
        st = style_of(app)
        right = max(bx + bw for bx, by, bw, bh in rects)
        by = min(by for _, by, _, _ in rects)
        bh = max(bh for _, _, _, bh in rects)
        gdi32.SetBkMode(hdc, TRANSPARENT)
        of = gdi32.SelectObject(hdc, app.get_font(9, True))
        for db in self.db_ticks:
            fraction = db_to_fraction(db)
            py = by + bh - int(round(fraction * bh))
            color = self._db_color(db, st)
            pen = app.get_pen(color, max(1, int(s)))
            old = gdi32.SelectObject(hdc, pen)
            gdi32.MoveToEx(hdc, right + int(2 * s), py, None)
            gdi32.LineTo(hdc, right + int(6 * s), py)
            gdi32.SelectObject(hdc, old)
            rc = wintypes.RECT(right + int(9 * s), py - int(8 * s),
                               self.x + self.w - int(2 * s), py + int(8 * s))
            gdi32.SetTextColor(hdc, COLORREF(*color))
            user32.DrawTextW(hdc, self._db_text(db), -1, ctypes.byref(rc),
                             DT_LEFT | DT_VCENTER | DT_SINGLELINE)
        gdi32.SelectObject(hdc, of)

    def _draw_db_horizontal(self, hdc, app, rects):
        s = app.scale
        st = style_of(app)
        bx = min(bx for bx, by, bw, bh in rects)
        bw = max(bw for _, _, bw, _ in rects)
        bottom = max(by + bh for _, by, _, bh in rects)
        scale_y = bottom + int(8 * s)
        gdi32.SetBkMode(hdc, TRANSPARENT)
        of = gdi32.SelectObject(hdc, app.get_font(9, True))
        for db in self.db_ticks:
            fraction = db_to_fraction(db)
            px = bx + int(round(fraction * bw))
            color = self._db_color(db, st)
            pen = app.get_pen(color, max(1, int(s)))
            old = gdi32.SelectObject(hdc, pen)
            gdi32.MoveToEx(hdc, px, bottom + int(2 * s), None)
            gdi32.LineTo(hdc, px, bottom + int(5 * s))
            gdi32.SelectObject(hdc, old)
            left = max(self.x + int(2 * s), px - int(16 * s))
            right = min(self.x + self.w - int(2 * s), px + int(16 * s))
            rc = wintypes.RECT(left, scale_y, right, scale_y + int(14 * s))
            gdi32.SetTextColor(hdc, COLORREF(*color))
            user32.DrawTextW(hdc, '%g' % db, -1, ctypes.byref(rc),
                             DT_CENTER | DT_VCENTER | DT_SINGLELINE)
        gdi32.SelectObject(hdc, of)

    def _draw_labels(self, hdc, app, rects):
        s = app.scale
        st = style_of(app)
        gdi32.SetBkMode(hdc, TRANSPARENT)
        of = gdi32.SelectObject(hdc, app.get_font(10, True))
        gdi32.SetTextColor(hdc, COLORREF(*st['dark']))
        for i, (bx, by, bw, bh) in enumerate(rects):
            text = self.labels[i] if i < len(self.labels) else str(i + 1)
            if self.orientation == 'v':
                rc = wintypes.RECT(bx, by + bh + int(s), bx + bw,
                                   by + bh + int(13 * s))
                align = DT_CENTER | DT_VCENTER | DT_SINGLELINE
            else:
                rc = wintypes.RECT(self.x + int(10 * s), by, bx - int(4 * s),
                                   by + bh)
                align = DT_RIGHT | DT_VCENTER | DT_SINGLELINE
            user32.DrawTextW(hdc, text, -1, ctypes.byref(rc), align)
        gdi32.SelectObject(hdc, of)

    def draw(self, hdc, app):
        self._app = app
        s = app.scale
        st = style_of(app)
        x, y, w, h = self.x, self.y, self.w, self.h
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

        rects = self._bar_rects()
        for i, (bx, by, bw, bh) in enumerate(rects):
            self._draw_bar(hdc, app, bx, by, bw, bh, self.levels[i],
                           self.peaks[i])
        if self.show_db:
            if self.orientation == 'v':
                self._draw_db_vertical(hdc, app, rects)
            else:
                self._draw_db_horizontal(hdc, app, rects)
        self._draw_labels(hdc, app, rects)


# Friendly alias for the bar-style meter.
BarVUMeter = LevelMeter
