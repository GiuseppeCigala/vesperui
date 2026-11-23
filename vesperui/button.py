"""Owner-drawn button widget."""
from .common import *  # noqa: F401,F403
from .style import scale_color, style_of


class Button(Widget):
    def __init__(self, text='', on_click=None, accent=None):
        super().__init__()
        self.text = text
        self.on_click = on_click
        self.focusable = True
        self.accent = accent

    def measure(self, app):
        tw, th = app.measure_text(self.text, 14, True)
        return (tw + int(24 * app.scale), th + int(14 * app.scale))

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
        s = app.scale
        st = style_of(app)
        x, y, w, h = self.x, self.y, self.w, self.h
        r = max(4, int(st.get('radius', 10) * s * 0.75))

        if self.accent is None:
            top = st['buttonPressed'] if self.pressed else st['buttonHover']
            bottom = st['buttonPressed'] if self.pressed else st['button']
            border = st['focus'] if self.focused else (
                scale_color(st, 0.55) if self.hovered else st['border'])
            fg = st['buttonText']
            glow = st['glow']
        else:
            acc = self.accent
            top = mix(acc, st['windowText'], 0.10)
            bottom = mix(acc, st['window'], 0.12)
            border = mix(acc, st['windowText'], 0.25) \
                if (self.hovered or self.focused) else mix(acc, st['window'], 0.15)
            fg = st['windowText']
            glow = mix(st['window'], acc, 0.30)

        if self.hovered or self.focused:
            stroke_round_rect(hdc, app, x - 1, y - 1, w + 2, h + 2, r + 1,
                              glow, max(2, int(2 * s)))

        fill_round_gradient_v(hdc, app, x, y, w, h, r, top, bottom)
        stroke_round_rect(hdc, app, x, y, w, h, r, border, max(1, int(s)))

        rc = wintypes.RECT(x, y, x + w, y + h)
        gdi32.SetBkMode(hdc, TRANSPARENT)
        of = gdi32.SelectObject(hdc, app.get_font(14, True))
        gdi32.SetTextColor(hdc, COLORREF(*fg))
        user32.DrawTextW(hdc, self.text, -1, ctypes.byref(rc),
                         DT_CENTER | DT_VCENTER | DT_SINGLELINE)
        gdi32.SelectObject(hdc, of)

        if self.focused:
            m = int(3 * s)
            stroke_round_rect(hdc, app, x + m, y + m, w - 2 * m, h - 2 * m,
                              max(1, r - 1), st['focus'], max(1, int(s)))
