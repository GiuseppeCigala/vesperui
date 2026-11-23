"""Clickable hyperlink label."""
from .common import *  # noqa: F401,F403
from .style import scale_color, style_of


class Hyperlink(Widget):
    def __init__(self, text='', on_click=None, size=13, color=None):
        super().__init__()
        self.text = text
        self.on_click = on_click
        self.size = size
        self.color = color
        self.focusable = True

    def measure(self, app):
        tw, th = app.measure_text(self.text, self.size, False)
        return (tw + int(8 * app.scale), th + int(8 * app.scale))

    def on_mouse_down(self, x, y):
        self.pressed = True

    def on_mouse_up(self, x, y):
        was = self.pressed
        self.pressed = False
        if was and self.hit_test(x, y) is self and self.on_click:
            self.on_click()

    def on_key(self, vk, ch):
        if vk in (VK_RETURN, VK_SPACE) and self.on_click:
            self.on_click()

    def click(self):
        if self.on_click:
            self.on_click()

    def draw(self, hdc, app):
        rc = wintypes.RECT(self.x, self.y, self.x + self.w, self.y + self.h)
        st = style_of(app)
        color = self.color if self.color is not None \
            else scale_color(st, 0.55)
        if self.hovered:
            color = lighten(color, 0.14)
        gdi32.SetBkMode(hdc, TRANSPARENT)
        gdi32.SetTextColor(hdc, COLORREF(*color))
        of = gdi32.SelectObject(hdc, app.get_font(self.size, False, True))
        user32.DrawTextW(hdc, self.text, -1, ctypes.byref(rc),
                         DT_LEFT | DT_VCENTER | DT_SINGLELINE)
        gdi32.SelectObject(hdc, of)
