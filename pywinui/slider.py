"""Owner-drawn horizontal slider."""
from .common import *  # noqa: F401,F403
from .style import style_of


class Slider(Widget):
    TRACK = (220, 225, 232)

    def __init__(self, value=0.0, on_change=None, accent=None):
        super().__init__()
        self.value = max(0.0, min(1.0, float(value)))
        self.on_change = on_change
        self.accent = accent
        self.focusable = True
        self._dragging = False

    def measure(self, app):
        return (int(220 * app.scale), int(28 * app.scale))

    def set_value(self, value, notify=True):
        value = max(0.0, min(1.0, float(value)))
        changed = value != self.value
        self.value = value
        if changed and notify and self.on_change:
            self.on_change(value)

    def _pad(self):
        return max(6, self.h // 2)

    def _set_from_x(self, x):
        pad = self._pad()
        span = max(1, self.w - 2 * pad)
        self.set_value((x - self.x - pad) / span)

    def on_mouse_down(self, x, y):
        self._dragging = True
        self._set_from_x(x)

    def on_mouse_move(self, x, y):
        if self._dragging:
            self._set_from_x(x)

    def on_mouse_up(self, x, y):
        self._dragging = False

    def on_key(self, vk, ch):
        if vk in (VK_LEFT, VK_DOWN):
            self.set_value(self.value - 0.05)
        elif vk in (VK_RIGHT, VK_UP):
            self.set_value(self.value + 0.05)

    def draw(self, hdc, app):
        s = app.scale
        st = style_of(app)
        accent = self.accent if self.accent is not None else st['highlight']
        accent2 = st['highlight2']
        x, y, w, h = self.x, self.y, self.w, self.h
        pad = self._pad()
        cy = y + h // 2
        track_h = max(4, int(6 * s))
        left, span = x + pad, max(1, w - 2 * pad)

        fill_round_rect(hdc, app, left, cy - track_h // 2, span, track_h,
                        track_h // 2, st['button'])
        filled = int(span * self.value)
        if filled > 0:
            fill_round_gradient_h(hdc, app, left, cy - track_h // 2, filled,
                                  track_h, track_h // 2, accent, accent2)

        knob_r = max(5, int(8 * s))
        kx = left + filled
        if self.hovered or self._dragging or self.focused:
            stroke_round_rect(hdc, app, kx - knob_r - 1, cy - knob_r - 1,
                              knob_r * 2 + 2, knob_r * 2 + 2, knob_r + 1,
                              st['glow'], max(2, int(2 * s)))
        fill_round_rect(hdc, app, kx - knob_r, cy - knob_r,
                        knob_r * 2, knob_r * 2, knob_r, st['base'])
        stroke_round_rect(hdc, app, kx - knob_r, cy - knob_r,
                          knob_r * 2, knob_r * 2, knob_r, accent, max(1, int(s)))
        dot = max(2, int(3 * s))
        fill_round_rect(hdc, app, kx - dot, cy - dot, dot * 2, dot * 2,
                        dot, accent)
