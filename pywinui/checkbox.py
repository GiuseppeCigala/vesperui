"""Fusion-style owner-drawn check box."""
from .common import *  # noqa: F401,F403
from .style import style_of


class CheckBox(Widget):
    def __init__(self, text='', checked=False, on_change=None):
        super().__init__()
        self.text = text
        self._checked = bool(checked)
        self.on_change = on_change
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

    def _toggle(self):
        self.set_checked(not self._checked)

    def on_mouse_down(self, x, y):
        self.pressed = True

    def on_mouse_up(self, x, y):
        was = self.pressed
        self.pressed = False
        if was and self.hit_test(x, y) is self:
            self._toggle()

    def on_key(self, vk, ch):
        if vk in (VK_SPACE, VK_RETURN):
            self._toggle()

    def draw(self, hdc, app):
        s = app.scale
        st = style_of(app)
        box = int(15 * s)
        radius = max(3, int(4 * s))
        bx = self.x
        by = self.y + (self.h - box) // 2

        if self.hovered or self.focused:
            stroke_round_rect(hdc, app, bx - 1, by - 1, box + 2, box + 2,
                              radius + 1, st['glow'], max(2, int(2 * s)))

        border = st['focus'] if self.focused else (
            st['highlight'] if self.hovered else st['border'])
        if self._checked:
            fill_round_gradient_v(hdc, app, bx, by, box, box, radius,
                                  st['highlight'], st['highlight2'])
        else:
            fill_round_rect(hdc, app, bx, by, box, box, radius, st['base'])
        stroke_round_rect(hdc, app, bx, by, box, box, radius, border, max(1, int(s)))

        if self._checked:
            pen = app.get_pen(st['highlightedText'], max(2, int(2 * s)))
            old = gdi32.SelectObject(hdc, pen)
            gdi32.MoveToEx(hdc, bx + int(4 * s), by + int(7.5 * s), None)
            gdi32.LineTo(hdc, bx + int(6.5 * s), by + int(10.5 * s))
            gdi32.LineTo(hdc, bx + int(11.5 * s), by + int(4.5 * s))
            gdi32.SelectObject(hdc, old)

        rc = wintypes.RECT(bx + box + int(7 * s), self.y,
                           self.x + self.w, self.y + self.h)
        gdi32.SetBkMode(hdc, TRANSPARENT)
        gdi32.SetTextColor(hdc, COLORREF(*st['windowText']))
        of = gdi32.SelectObject(hdc, app.get_font(14))
        user32.DrawTextW(hdc, self.text, -1, ctypes.byref(rc),
                         DT_LEFT | DT_VCENTER | DT_SINGLELINE)
        gdi32.SelectObject(hdc, of)
