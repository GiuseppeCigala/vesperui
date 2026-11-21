"""Owner-drawn tab bar."""
from .common import *  # noqa: F401,F403
from .style import style_of


class TabBar(Widget):
    def __init__(self, items=None, index=0, on_change=None, accent=None):
        super().__init__()
        self.items = list(items or [])
        self.index = int(index)
        self.on_change = on_change
        self.accent = accent
        self.focusable = True
        self._app = None

    def measure(self, app):
        s = app.scale
        pad = int(14 * s)
        gap = max(1, int(2 * s))
        width = sum(app.measure_text(t, 13, True)[0] + 2 * pad
                    for t in self.items)
        width += gap * max(0, len(self.items) - 1)
        height = app.measure_text('Ag', 13, True)[1] + int(12 * s)
        return (max(width, int(60 * s)), height)

    def _tab_rects(self):
        app = self._app
        if app is None:
            return []
        s = app.scale
        pad = int(14 * s)
        gap = max(1, int(2 * s))
        rects = []
        x = self.x
        for text in self.items:
            tw = app.measure_text(text, 13, True)[0] + 2 * pad
            rects.append((x, tw))
            x += tw + gap
        return rects

    def set_index(self, index, notify=True):
        index = max(0, min(int(index), len(self.items) - 1))
        changed = index != self.index
        self.index = index
        if changed and notify and self.on_change:
            self.on_change(index)

    def on_mouse_down(self, x, y):
        for i, (tx, tw) in enumerate(self._tab_rects()):
            if tx <= x < tx + tw:
                self.set_index(i)
                break

    def on_key(self, vk, ch):
        if vk == VK_LEFT:
            self.set_index(self.index - 1)
        elif vk == VK_RIGHT:
            self.set_index(self.index + 1)

    def draw(self, hdc, app):
        self._app = app
        s = app.scale
        st = style_of(app)
        accent = self.accent if self.accent is not None else st['highlight']
        accent2 = st['highlight2']
        radius = self.h // 2
        for i, (tx, tw) in enumerate(self._tab_rects()):
            selected = i == self.index
            if selected:
                if self.focused or self.hovered:
                    stroke_round_rect(hdc, app, tx - 1, self.y - 1, tw + 2,
                                      self.h + 2, radius + 1, st['glow'],
                                      max(2, int(2 * s)))
                fill_round_gradient_h(hdc, app, tx, self.y, tw, self.h, radius,
                                      accent, accent2)
                fg = st['highlightedText']
            else:
                bg = st['buttonHover'] if self.hovered else st['button']
                fill_round_rect(hdc, app, tx, self.y, tw, self.h, radius, bg)
                fg = st['buttonText']
            rc = wintypes.RECT(tx, self.y, tx + tw, self.y + self.h)
            gdi32.SetBkMode(hdc, TRANSPARENT)
            gdi32.SetTextColor(hdc, COLORREF(*fg))
            of = gdi32.SelectObject(hdc, app.get_font(13, True))
            user32.DrawTextW(hdc, self.items[i], -1, ctypes.byref(rc),
                             DT_CENTER | DT_VCENTER | DT_SINGLELINE)
            gdi32.SelectObject(hdc, of)
