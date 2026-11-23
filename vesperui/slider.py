"""Owner-drawn horizontal or vertical slider."""
from .common import *  # noqa: F401,F403
from .style import scale_color, style_of


class Slider(Widget):
    TRACK = (220, 225, 232)

    def __init__(self, value=0.0, on_change=None, accent=None,
                 orientation='h'):
        super().__init__()
        self.value = max(0.0, min(1.0, float(value)))
        self.on_change = on_change
        self.accent = accent
        self.orientation = 'v' if orientation in ('v', 'vertical') else 'h'
        self.focusable = True
        self._dragging = False

    def measure(self, app):
        if self.orientation == 'v':
            return (int(28 * app.scale), int(220 * app.scale))
        return (int(220 * app.scale), int(28 * app.scale))

    def set_value(self, value, notify=True):
        value = max(0.0, min(1.0, float(value)))
        changed = value != self.value
        self.value = value
        if changed and notify and self.on_change:
            self.on_change(value)

    def _pad(self):
        if self.orientation == 'v':
            return max(6, self.w // 2)
        return max(6, self.h // 2)

    def _set_from_pos(self, x, y):
        pad = self._pad()
        if self.orientation == 'v':
            span = max(1, self.h - 2 * pad)
            self.set_value((self.h - pad - (y - self.y)) / span)
        else:
            span = max(1, self.w - 2 * pad)
            self.set_value((x - self.x - pad) / span)

    def on_mouse_down(self, x, y):
        self._dragging = True
        self._set_from_pos(x, y)

    def on_mouse_move(self, x, y):
        if self._dragging:
            self._set_from_pos(x, y)

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
        x, y, w, h = self.x, self.y, self.w, self.h
        pad = self._pad()
        knob_r = max(5, int(8 * s))

        if self.accent is not None:
            low = mix(self.accent, st['window'], 0.30)
            high = self.accent
        else:
            low = scale_color(st, 0.0)
            high = scale_color(st, max(0.08, self.value))
        knob_color = self.accent if self.accent is not None \
            else scale_color(st, 0.65)

        if self.orientation == 'v':
            cx = x + w // 2
            track_w = max(4, int(6 * s))
            top = y + pad
            span = max(1, h - 2 * pad)
            bottom = top + span
            fill_round_gradient_h(hdc, app, cx - track_w // 2, top,
                                  track_w, span, track_w // 2,
                                  mix(st['window'], st['button'], 0.45),
                                  st['buttonHover'])
            filled = int(span * self.value)
            if filled > 0:
                fill_round_gradient_v(hdc, app, cx - track_w // 2,
                                      bottom - filled, track_w, filled,
                                      track_w // 2, high, low)
            ky = bottom - filled
            if self.hovered or self._dragging or self.focused:
                stroke_round_rect(hdc, app, cx - knob_r - 1, ky - knob_r - 1,
                                  knob_r * 2 + 2, knob_r * 2 + 2,
                                  knob_r + 1, st['glow'], max(2, int(2 * s)))
            fill_round_gradient_v(hdc, app, cx - knob_r, ky - knob_r,
                                  knob_r * 2, knob_r * 2, knob_r,
                                  lighten(st['base'], 0.04), st['base'])
            stroke_round_rect(hdc, app, cx - knob_r, ky - knob_r,
                              knob_r * 2, knob_r * 2, knob_r, knob_color,
                              max(1, int(s)))
            dot = max(2, int(3 * s))
            fill_round_rect(hdc, app, cx - dot, ky - dot, dot * 2, dot * 2,
                            dot, knob_color)
            return

        cy = y + h // 2
        track_h = max(4, int(6 * s))
        left, span = x + pad, max(1, w - 2 * pad)

        fill_round_gradient_v(hdc, app, left, cy - track_h // 2, span,
                              track_h, track_h // 2, st['buttonHover'],
                              mix(st['window'], st['button'], 0.55))
        filled = int(span * self.value)
        if filled > 0:
            fill_round_gradient_h(hdc, app, left, cy - track_h // 2, filled,
                                  track_h, track_h // 2, low, high)

        kx = left + filled
        if self.hovered or self._dragging or self.focused:
            stroke_round_rect(hdc, app, kx - knob_r - 1, cy - knob_r - 1,
                              knob_r * 2 + 2, knob_r * 2 + 2, knob_r + 1,
                              st['glow'], max(2, int(2 * s)))
        fill_round_gradient_v(hdc, app, kx - knob_r, cy - knob_r,
                              knob_r * 2, knob_r * 2, knob_r,
                              lighten(st['base'], 0.04), st['base'])
        stroke_round_rect(hdc, app, kx - knob_r, cy - knob_r,
                          knob_r * 2, knob_r * 2, knob_r, knob_color,
                          max(1, int(s)))
        dot = max(2, int(3 * s))
        fill_round_rect(hdc, app, kx - dot, cy - dot, dot * 2, dot * 2,
                        dot, knob_color)
