"""Fusion-style owner-drawn radio button."""
from .common import *  # noqa: F401,F403
from .style import style_of


class RadioButton(Widget):
    def __init__(self, text='', checked=False, on_change=None, group=None):
        super().__init__()
        self.text = text
        self._checked = bool(checked)
        self.on_change = on_change
        self.group = group
        self.focusable = True

    def measure(self, app):
        s = app.scale
        box = int(14 * s)
        tw, th = app.measure_text(self.text, 14)
        return (tw + box + int(10 * s), max(th, box) + int(8 * s))

    def is_checked(self):
        return self._checked

    def set_checked(self, value, notify=True):
        value = bool(value)
        changed = value != self._checked
        self._checked = value
        if changed and notify and self.on_change:
            self.on_change(value)

    def _select(self):
        if self._checked:
            return
        if self.parent is not None:
            for w in self.parent.all_widgets():
                if isinstance(w, RadioButton) and w is not self and w.group == self.group:
                    w.set_checked(False, notify=False)
        self.set_checked(True)

    def on_mouse_down(self, x, y):
        self.pressed = True

    def on_mouse_up(self, x, y):
        was = self.pressed
        self.pressed = False
        if was and self.hit_test(x, y) is self:
            self._select()

    def on_key(self, vk, ch):
        if vk in (VK_SPACE, VK_RETURN):
            self._select()

    def click(self):
        self._select()

    def draw(self, hdc, app):
        s = app.scale
        st = style_of(app)
        box = int(16 * s)
        bx = self.x
        by = self.y + (self.h - box) // 2
        radius = box // 2

        if self._checked or self.hovered or self.focused:
            stroke_round_rect(hdc, app, bx - 1, by - 1, box + 2, box + 2,
                              radius + 1, st['glow'], max(2, int(2 * s)))

        border = st['focus'] if self.focused else (
            st['highlight'] if (self._checked or self.hovered) else st['border'])
        fill_round_rect(hdc, app, bx, by, box, box, radius, st['base'])
        stroke_round_rect(hdc, app, bx, by, box, box, radius, border, max(1, int(s)))

        if self._checked:
            dot = max(3, int(7 * s))
            off = (box - dot) // 2
            fill_round_rect(hdc, app, bx + off, by + off, dot, dot,
                            dot // 2, st['highlight'])

        rc = wintypes.RECT(bx + box + int(7 * s), self.y,
                           self.x + self.w, self.y + self.h)
        gdi32.SetBkMode(hdc, TRANSPARENT)
        gdi32.SetTextColor(hdc, COLORREF(*st['windowText']))
        of = gdi32.SelectObject(hdc, app.get_font(14))
        user32.DrawTextW(hdc, self.text, -1, ctypes.byref(rc),
                         DT_LEFT | DT_VCENTER | DT_SINGLELINE)
        gdi32.SelectObject(hdc, of)
