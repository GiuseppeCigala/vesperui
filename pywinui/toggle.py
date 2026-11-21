"""Owner-drawn toggle switch."""
from .common import *  # noqa: F401,F403
from .style import style_of


class ToggleSwitch(Widget):
    OFF = (200, 206, 216)

    def __init__(self, checked=False, on_change=None, accent=None):
        super().__init__()
        self.checked = bool(checked)
        self.on_change = on_change
        self.accent = accent
        self.focusable = True

    def measure(self, app):
        return (int(44 * app.scale), int(24 * app.scale))

    def is_checked(self):
        return self.checked

    def set_checked(self, value, notify=True):
        value = bool(value)
        changed = value != self.checked
        self.checked = value
        if changed and notify and self.on_change:
            self.on_change(value)

    def on_mouse_down(self, x, y):
        self.pressed = True

    def on_mouse_up(self, x, y):
        was = self.pressed
        self.pressed = False
        if was and self.hit_test(x, y) is self:
            self.set_checked(not self.checked)

    def on_key(self, vk, ch):
        if vk in (VK_SPACE, VK_RETURN):
            self.set_checked(not self.checked)

    def click(self):
        self.set_checked(not self.checked)

    def draw(self, hdc, app):
        s = app.scale
        st = style_of(app)
        x, y, w, h = self.x, self.y, self.w, self.h
        accent = self.accent if self.accent is not None else st['highlight']
        accent2 = st['highlight2']
        if self.checked:
            if self.hovered:
                stroke_round_rect(hdc, app, x - 1, y - 1, w + 2, h + 2,
                                  h // 2 + 1, st['glow'], max(2, int(2 * s)))
            fill_round_gradient_h(hdc, app, x, y, w, h, h // 2, accent, accent2)
        else:
            fill_round_rect(hdc, app, x, y, w, h, h // 2, st['button'])
        stroke_round_rect(hdc, app, x, y, w, h, h // 2,
                          st['border'] if not self.checked else accent,
                          max(1, int(s)))

        margin = max(2, int(2 * s))
        knob_d = max(4, h - 2 * margin)
        kx = x + w - knob_d - margin if self.checked else x + margin
        fill_round_rect(hdc, app, kx, y + margin, knob_d, knob_d,
                        knob_d // 2, st['base'])
        stroke_round_rect(hdc, app, kx, y + margin, knob_d, knob_d,
                          knob_d // 2, st['border'], max(1, int(s)))
