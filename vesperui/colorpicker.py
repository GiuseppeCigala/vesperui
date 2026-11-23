"""Owner-drawn HSV color picker with a hue strip and preview swatch."""
from .common import *  # noqa: F401,F403
from .style import style_of


def _clamp01(value):
    return max(0.0, min(1.0, float(value)))


def _clamp_rgb(rgb):
    return tuple(max(0, min(255, int(round(c)))) for c in rgb)


def rgb_to_hsv(r, g, b):
    """Convert an RGB triple to (hue, saturation, value) floats in 0..1."""
    r, g, b = [max(0, min(255, int(c))) / 255.0 for c in (r, g, b)]
    high = max(r, g, b)
    low = min(r, g, b)
    delta = high - low
    value = high
    sat = 0.0 if high == 0 else delta / high
    if delta == 0:
        hue = 0.0
    elif high == r:
        hue = ((g - b) / delta) % 6.0
    elif high == g:
        hue = (b - r) / delta + 2.0
    else:
        hue = (r - g) / delta + 4.0
    return (hue / 6.0) % 1.0, sat, value


def hsv_to_rgb(hue, sat, val):
    """Convert (hue, saturation, value) floats in 0..1 to an RGB triple."""
    hue = float(hue) % 1.0
    sat = _clamp01(sat)
    val = _clamp01(val)
    sector = int(hue * 6.0)
    frac = hue * 6.0 - sector
    p = val * (1.0 - sat)
    q = val * (1.0 - frac * sat)
    t = val * (1.0 - (1.0 - frac) * sat)
    r, g, b = ((val, t, p), (q, val, p), (p, val, t),
               (p, q, val), (t, p, val), (val, p, q))[sector % 6]
    return (int(r * 255 + 0.5), int(g * 255 + 0.5), int(b * 255 + 0.5))


def rgb_to_hex(rgb):
    return '#%02X%02X%02X' % _clamp_rgb(rgb)


class ColorPicker(Widget):
    def __init__(self, color=(0, 214, 255), on_change=None):
        super().__init__()
        self.on_change = on_change
        self.focusable = True
        self._app = None
        self._drag = None
        self._rgb = (0, 0, 0)
        self.hue = self.sat = self.val = 0.0
        self.set_color(color, notify=False)

    def measure(self, app):
        return (int(240 * app.scale), int(170 * app.scale))

    def _scale(self):
        return self._app.scale if self._app else 1.0

    def _metrics(self):
        s = self._scale()
        return (max(4, int(8 * s)), max(6, int(14 * s)),
                max(4, int(8 * s)), max(12, int(22 * s)))

    def _sv_rect(self):
        pad, hue_w, gap, preview_h = self._metrics()
        w = max(0, self.w - 2 * pad - hue_w - gap)
        h = max(0, self.h - 2 * pad - preview_h - gap)
        return (self.x + pad, self.y + pad, w, h)

    def _hue_rect(self):
        _pad, hue_w, gap, _preview_h = self._metrics()
        sx, sy, sw, sh = self._sv_rect()
        return (sx + sw + gap, sy, hue_w, sh)

    def _preview_rect(self):
        pad, _hue_w, _gap, preview_h = self._metrics()
        return (self.x + pad, self.y + self.h - pad - preview_h,
                self.w - 2 * pad, preview_h)

    def _invalidate(self):
        if self._app:
            self._app.invalidate_rect(self.x, self.y, self.w, self.h)

    def get_color(self):
        return self._rgb

    def set_color(self, rgb, notify=True):
        rgb = _clamp_rgb(rgb)
        changed = rgb != self._rgb
        self.hue, self.sat, self.val = rgb_to_hsv(*rgb)
        self._rgb = rgb
        if changed and notify and self.on_change:
            self.on_change(rgb)
        self._invalidate()
        return changed

    def set_hsv(self, hue, sat, val, notify=True):
        hue = float(hue) % 1.0
        sat = _clamp01(sat)
        val = _clamp01(val)
        rgb = hsv_to_rgb(hue, sat, val)
        changed = rgb != self._rgb
        self.hue, self.sat, self.val = hue, sat, val
        self._rgb = rgb
        if changed and notify and self.on_change:
            self.on_change(rgb)
        self._invalidate()
        return changed

    @staticmethod
    def _inside(x, y, rect):
        rx, ry, rw, rh = rect
        return rx <= x < rx + rw and ry <= y < ry + rh

    def _set_from_sv(self, x, y):
        sx, sy, sw, sh = self._sv_rect()
        sat = (x - sx) / max(1, sw - 1)
        val = 1.0 - (y - sy) / max(1, sh - 1)
        self.set_hsv(self.hue, sat, val)

    def _set_from_hue(self, x, y):
        _hx, hy, _hw, hh = self._hue_rect()
        hue = (y - hy) / max(1, hh - 1)
        self.set_hsv(max(0.0, min(0.999999, hue)), self.sat, self.val)

    def on_mouse_down(self, x, y):
        if self._inside(x, y, self._sv_rect()):
            self._drag = 'sv'
            self._set_from_sv(x, y)
        elif self._inside(x, y, self._hue_rect()):
            self._drag = 'hue'
            self._set_from_hue(x, y)
        else:
            self._drag = None

    def on_mouse_move(self, x, y):
        if self._drag == 'sv':
            self._set_from_sv(x, y)
        elif self._drag == 'hue':
            self._set_from_hue(x, y)

    def on_mouse_up(self, x, y):
        self._drag = None
        self._invalidate()

    def on_key(self, vk, ch):
        if vk == VK_LEFT:
            self.set_hsv(self.hue - 1.0 / 60.0, self.sat, self.val)
        elif vk == VK_RIGHT:
            self.set_hsv(self.hue + 1.0 / 60.0, self.sat, self.val)
        elif vk == VK_UP:
            self.set_hsv(self.hue, self.sat, self.val + 0.05)
        elif vk == VK_DOWN:
            self.set_hsv(self.hue, self.sat, self.val - 0.05)

    def on_wheel(self, delta):
        return False

    def draw(self, hdc, app):
        self._app = app
        s = app.scale
        st = style_of(app)
        x, y, w, h = self.x, self.y, self.w, self.h
        radius = max(6, int(10 * s))

        if self.focused or self._drag:
            stroke_round_rect(hdc, app, x - 1, y - 1, w + 2, h + 2,
                              radius + 1, st['glow'], max(2, int(2 * s)))
        fill_round_gradient_v(hdc, app, x, y, w, h, radius,
                              st['panel'], st['window'])
        stroke_round_rect(hdc, app, x, y, w, h, radius, st['border'],
                          max(1, int(s)))

        sx, sy, sw, sh = self._sv_rect()
        hx, hy, hw, hh = self._hue_rect()
        px, py, pw, ph = self._preview_rect()

        if sw > 0 and sh > 0:
            saved = gdi32.SaveDC(hdc)
            corner = max(2, int(5 * s))
            rgn = gdi32.CreateRoundRectRgn(sx, sy, sx + sw + 1, sy + sh + 1,
                                           corner * 2, corner * 2)
            gdi32.ExtSelectClipRgn(hdc, rgn, RGN_AND)
            gdi32.DeleteObject(rgn)
            pure = hsv_to_rgb(self.hue, 1.0, 1.0)
            for row in range(sh):
                value = 1.0 - row / max(1, sh - 1)
                gray = int(255 * value + 0.5)
                right = (int(pure[0] * value + 0.5),
                         int(pure[1] * value + 0.5),
                         int(pure[2] * value + 0.5))
                fill_gradient_h(hdc, sx, sy + row, sw, 1,
                                (gray, gray, gray), right)
            gdi32.RestoreDC(hdc, saved)
            stroke_round_rect(hdc, app, sx, sy, sw, sh, corner,
                              st['border'], max(1, int(s)))

        if hw > 0 and hh > 0:
            saved = gdi32.SaveDC(hdc)
            rgn = gdi32.CreateRoundRectRgn(hx, hy, hx + hw + 1, hy + hh + 1,
                                           hw, hw)
            gdi32.ExtSelectClipRgn(hdc, rgn, RGN_AND)
            gdi32.DeleteObject(rgn)
            colors = [(255, 0, 0), (255, 255, 0), (0, 255, 0),
                      (0, 255, 255), (0, 0, 255), (255, 0, 255),
                      (255, 0, 0)]
            seg = hh / 6.0
            for i in range(6):
                top = hy + int(i * seg)
                bottom = hy + int((i + 1) * seg)
                fill_gradient_v(hdc, hx, top, hw, max(1, bottom - top),
                                colors[i], colors[i + 1])
            gdi32.RestoreDC(hdc, saved)
            stroke_round_rect(hdc, app, hx, hy, hw, hh, hw // 2,
                              st['border'], max(1, int(s)))

            my = hy + int(self.hue * max(1, hh - 1))
            for color, width in ((st['window'], max(2, int(3 * s))),
                                 (st['windowText'], max(1, int(s)))):
                pen = app.get_pen(color, width)
                old = gdi32.SelectObject(hdc, pen)
                gdi32.MoveToEx(hdc, hx - max(1, int(2 * s)), my, None)
                gdi32.LineTo(hdc, hx + hw + max(1, int(2 * s)), my)
                gdi32.SelectObject(hdc, old)

        if sw > 0 and sh > 0:
            cx = sx + int(self.sat * max(1, sw - 1))
            cy = sy + int((1.0 - self.val) * max(1, sh - 1))
            fill_round_rect(hdc, app, cx - 5, cy - 5, 10, 10, 5, st['window'])
            fill_round_rect(hdc, app, cx - 3, cy - 3, 6, 6, 3,
                            st['windowText'])

        if pw > 0 and ph > 0:
            fill_round_rect(hdc, app, px, py, pw, ph, max(3, int(5 * s)),
                            self._rgb)
            stroke_round_rect(hdc, app, px, py, pw, ph, max(3, int(5 * s)),
                              st['border'], max(1, int(s)))
            fg = (10, 10, 10) if sum(self._rgb) > 380 else (250, 250, 250)
            rc = wintypes.RECT(px, py, px + pw, py + ph)
            gdi32.SetBkMode(hdc, TRANSPARENT)
            gdi32.SetTextColor(hdc, COLORREF(*fg))
            of = gdi32.SelectObject(hdc, app.get_font(12, True))
            user32.DrawTextW(hdc, rgb_to_hex(self._rgb), -1,
                             ctypes.byref(rc),
                             DT_CENTER | DT_VCENTER | DT_SINGLELINE)
            gdi32.SelectObject(hdc, of)
