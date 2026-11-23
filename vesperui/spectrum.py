"""Owner-drawn spectrum analyzer with log frequency and dB axes."""
import math

from .common import *  # noqa: F401,F403
from .style import SCALE_SPLIT, scale_color, style_of

DB_TICKS = (-12, -18, -24, -30, -36, -42, -48, -54, -60)
FREQ_TICKS = (30, 40, 60, 100, 150, 200, 300, 400, 600,
              1000, 2000, 3000, 4000, 6000, 10000)


class SpectrumAnalyzer(Widget):
    """Animated spectrum display driven by :meth:`set_spectrum`.

    Each bin has three levels: a smoothed body with a vertical teal-to-violet
    gradient, a brighter transient tint and a slowly falling peak cap. Bars
    are laid out on a logarithmic frequency axis and the vertical axis is
    labelled in dB. Call ``set_spectrum`` with a list of 0..1 values at each
    frame of the audio data.
    """

    def __init__(self, bins=96, min_db=-60.0, max_db=-12.0,
                 min_hz=20.0, max_hz=20000.0, attack=0.60, release=0.22,
                 peak_hold_frames=10, peak_decay=0.01,
                 body_color=None, cap_color=None, hot_color=None):
        super().__init__()
        self.bins = max(4, int(bins))
        self.min_db = float(min_db)
        self.max_db = float(max_db)
        self.min_hz = max(1.0, float(min_hz))
        self.max_hz = max(self.min_hz + 1.0, float(max_hz))
        self.attack = max(0.0, min(1.0, float(attack)))
        self.release = max(0.0, min(1.0, float(release)))
        self.peak_hold_frames = max(0, int(peak_hold_frames))
        self.peak_decay = max(0.0, float(peak_decay))
        self.body_color = body_color
        self.cap_color = cap_color
        self.hot_color = hot_color
        self.instant = [0.0] * self.bins
        self.levels = [0.0] * self.bins
        self.peaks = [0.0] * self.bins
        self._peak_age = [0] * self.bins
        self._app = None

    # ----------------------------------------------------------- sizing/state
    def measure(self, app):
        return (int(460 * app.scale), int(190 * app.scale))

    def db_to_fraction(self, db):
        span = self.max_db - self.min_db
        if span <= 0:
            return 0.0
        return max(0.0, min(1.0, (float(db) - self.min_db) / span))

    def set_spectrum(self, values, notify=True):
        """Feed a new frame of 0..1 levels, one per bin."""
        frame = self._resample(values)
        for i, target in enumerate(frame):
            target = max(0.0, min(1.0, float(target)))
            previous = self.levels[i]
            factor = self.attack if target > previous else self.release
            self.levels[i] = previous + (target - previous) * factor
            self.instant[i] = target
            if target > self.peaks[i]:
                self.peaks[i] = target
                self._peak_age[i] = 0
            elif self._peak_age[i] < self.peak_hold_frames:
                self._peak_age[i] += 1
            else:
                self.peaks[i] = max(self.levels[i],
                                    self.peaks[i] - self.peak_decay)
        self._invalidate()
        return frame

    def set_spectrum_db(self, db_values, notify=True):
        """Feed a new frame expressed in dB (``min_db``..``max_db``)."""
        return self.set_spectrum([self.db_to_fraction(db) for db in db_values],
                                 notify=notify)

    def reset(self):
        self.instant = [0.0] * self.bins
        self.levels = [0.0] * self.bins
        self.peaks = [0.0] * self.bins
        self._peak_age = [0] * self.bins
        self._invalidate()

    def _resample(self, values):
        frame = [float(v) for v in values]
        count = self.bins
        if len(frame) == count:
            return frame
        if not frame:
            return [0.0] * count
        if len(frame) == 1:
            return [frame[0]] * count
        result = []
        for i in range(count):
            pos = i * (len(frame) - 1) / float(count - 1)
            low = int(pos)
            high = min(len(frame) - 1, low + 1)
            t = pos - low
            result.append(frame[low] * (1.0 - t) + frame[high] * t)
        return result

    def _invalidate(self):
        if self._app:
            self._app.invalidate_rect(self.x, self.y, self.w, self.h)

    # -------------------------------------------------------------- geometry
    def _plot_rect(self, s):
        pad = max(4, int(8 * s))
        label_w = int(28 * s)
        left = self.x + pad + label_w
        right = self.x + self.w - pad - label_w
        top = self.y + pad + int(9 * s)
        bottom = self.y + self.h - pad - int(18 * s)
        return left, top, max(1, right - left), max(1, bottom - top)

    def _freq_x(self, hz, left, width):
        span = math.log(self.max_hz / self.min_hz)
        ratio = math.log(max(self.min_hz, float(hz)) / self.min_hz) / span
        return left + int(round(ratio * width))

    @staticmethod
    def _format_hz(hz):
        if hz >= 1000:
            return '%.1fk' % (hz / 1000.0)
        return '%d' % hz

    # -------------------------------------------------------------- drawing
    @staticmethod
    def _fill(hdc, app, x, y, w, h, color):
        if w <= 0 or h <= 0:
            return
        rc = wintypes.RECT(int(x), int(y), int(x + w), int(y + h))
        user32.FillRect(hdc, ctypes.byref(rc), app.get_brush(color))

    def _draw_grid(self, hdc, app, left, top, width, height, s, st):
        grid = mix(st['window'], st['border'], 0.45)
        pen = app.get_pen(grid, max(1, int(s)))
        old = gdi32.SelectObject(hdc, pen)
        for db in DB_TICKS:
            y = top + height - int(round(self.db_to_fraction(db) * height))
            gdi32.MoveToEx(hdc, left, y, None)
            gdi32.LineTo(hdc, left + width, y)
        for hz in FREQ_TICKS:
            x = self._freq_x(hz, left, width)
            gdi32.MoveToEx(hdc, x, top, None)
            gdi32.LineTo(hdc, x, top + height)
        gdi32.SelectObject(hdc, old)

    def _draw_axes(self, hdc, app, left, top, width, height, s, st):
        gdi32.SetBkMode(hdc, TRANSPARENT)
        gdi32.SetTextColor(hdc, COLORREF(*st['mid']))
        of = gdi32.SelectObject(hdc, app.get_font(8))
        half = int(6 * s)
        for db in DB_TICKS:
            y = top + height - int(round(self.db_to_fraction(db) * height))
            text = '%d' % db
            rc = wintypes.RECT(self.x + int(4 * s), y - half,
                               left - int(4 * s), y + half)
            user32.DrawTextW(hdc, text, -1, ctypes.byref(rc),
                             DT_RIGHT | DT_VCENTER | DT_SINGLELINE)
            rc = wintypes.RECT(left + width + int(4 * s), y - half,
                               self.x + self.w - int(4 * s), y + half)
            user32.DrawTextW(hdc, text, -1, ctypes.byref(rc),
                             DT_LEFT | DT_VCENTER | DT_SINGLELINE)

        label_top = top + height + int(2 * s)
        last_right = None
        for hz in FREQ_TICKS:
            x = self._freq_x(hz, left, width)
            text = self._format_hz(hz)
            tw, _th = app.measure_text(text, 8)
            lx = x - tw / 2.0
            if last_right is not None and lx < last_right + int(4 * s):
                continue
            rc = wintypes.RECT(x - int(tw / 2.0) - int(2 * s), label_top,
                               x + int(tw / 2.0) + int(2 * s),
                               label_top + int(13 * s))
            user32.DrawTextW(hdc, text, -1, ctypes.byref(rc),
                             DT_CENTER | DT_VCENTER | DT_SINGLELINE)
            last_right = x + tw / 2.0
        gdi32.SelectObject(hdc, of)

    def _fill_body(self, hdc, x, bottom, width, plot_height, top_h, st):
        """Fill a bar with the vertical teal-to-violet scale."""
        if top_h <= 0:
            return
        if self.body_color is not None:
            fill_gradient_v(hdc, x, bottom - top_h, width, top_h,
                            self.body_color,
                            mix(self.body_color, st['window'], 0.22))
            return

        split_px = int(round(SCALE_SPLIT * plot_height))
        if top_h <= split_px:
            fill_gradient_v(hdc, x, bottom - top_h, width, top_h,
                            scale_color(st, top_h / float(plot_height)),
                            scale_color(st, 0.0))
            return

        fill_gradient_v(hdc, x, bottom - split_px, width, split_px,
                        scale_color(st, SCALE_SPLIT), scale_color(st, 0.0))
        upper_h = top_h - split_px
        if upper_h > 0:
            fill_gradient_v(hdc, x, bottom - top_h, width, upper_h,
                            scale_color(st, top_h / float(plot_height)),
                            scale_color(st, SCALE_SPLIT))

    def _draw_bars(self, hdc, app, left, top, width, height, s, st):
        gap = max(1, int(1 * s))
        bin_w = width / float(self.bins)
        bar_w = max(1, int(round(bin_w)) - gap)
        bottom = top + height
        for i in range(self.bins):
            x0 = min(left + int(round(i * bin_w)), left + width - bar_w)
            avg_h = int(round(self.levels[i] * height))
            inst_h = int(round(self.instant[i] * height))
            peak_h = int(round(self.peaks[i] * height))
            if avg_h > 0:
                self._fill_body(hdc, x0, bottom, bar_w, height, avg_h, st)
            if inst_h > avg_h:
                if self.hot_color is not None:
                    hot = self.hot_color
                elif self.body_color is not None:
                    hot = lighten(self.body_color, 0.16)
                else:
                    hot = lighten(scale_color(st, inst_h / float(height)),
                                  0.14)
                self._fill(hdc, app, x0, bottom - inst_h, bar_w,
                           inst_h - avg_h, hot)
            above = max(avg_h, inst_h)
            if peak_h > above:
                if self.cap_color is not None:
                    cap = self.cap_color
                elif self.body_color is not None:
                    cap = mix(self.body_color, st['windowText'], 0.40)
                else:
                    cap = mix(scale_color(st, peak_h / float(height)),
                              st['windowText'], 0.40)
                self._fill(hdc, app, x0, bottom - peak_h, bar_w,
                           peak_h - above, cap)

    def draw(self, hdc, app):
        self._app = app
        s = app.scale
        st = style_of(app)
        x, y, w, h = self.x, self.y, self.w, self.h
        radius = max(6, int(10 * s))

        fill_round_gradient_v(hdc, app, x, y, w, h, radius,
                              st['panel'], st['window'])
        stroke_round_rect(hdc, app, x, y, w, h, radius, st['border'],
                          max(1, int(s)))

        left, top, width, height = self._plot_rect(s)
        self._draw_grid(hdc, app, left, top, width, height, s, st)
        self._draw_bars(hdc, app, left, top, width, height, s, st)
        self._draw_axes(hdc, app, left, top, width, height, s, st)
