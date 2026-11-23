"""Group box container with a title and a border."""
from .common import *  # noqa: F401,F403
from .panel import Panel
from .style import scale_color, style_of


class GroupBox(Container):
    def __init__(self, title='', layout=None, padding=8, bg=None,
                 border=None, radius=None):
        super().__init__()
        self.title = title
        self.bg = bg
        self.border = border
        self.radius = radius
        self.padding = padding
        self.content = Panel(layout=layout, padding=padding, bg=None)
        super().add(self.content)

    def add(self, widget):
        return self.content.add(widget)

    def _title_height(self, app):
        if not self.title:
            return 0
        return app.measure_text(self.title, 13, True)[1] + int(10 * app.scale)

    def measure(self, app):
        cw, ch = self.content.measure(app)
        return (cw, ch + self._title_height(app))

    def arrange(self, app):
        th = self._title_height(app)
        self.content.set_bounds(self.x, self.y + th, self.w,
                                max(0, self.h - th))
        self.content.arrange(app)

    def draw(self, hdc, app):
        s = app.scale
        st = style_of(app)
        r = int((self.radius if self.radius is not None else st.get('radius', 10)) * s)
        if self.bg is not None:
            fill_round_gradient_v(hdc, app, self.x, self.y, self.w, self.h, r,
                                  lighten(self.bg, 0.04),
                                  darken(self.bg, 0.01))
        border = self.border if self.border is not None else st['border']
        stroke_round_rect(hdc, app, self.x, self.y, self.w, self.h, r,
                          border, max(1, int(s)))
        if self.title:
            th = self._title_height(app)
            tw, tth = app.measure_text(self.title, 13, True)
            bar_w = max(2, int(3 * s))
            bar_h = max(4, tth - int(2 * s))
            bx = self.x + int(10 * s)
            by = self.y + int(5 * s)
            fill_round_rect(hdc, app, bx, by, bar_w, bar_h, bar_w // 2,
                            scale_color(st, 0.55))
            rc = wintypes.RECT(bx + bar_w + int(6 * s), self.y + int(2 * s),
                               self.x + self.w - int(10 * s), self.y + th)
            gdi32.SetBkMode(hdc, TRANSPARENT)
            gdi32.SetTextColor(hdc, COLORREF(*st['windowText']))
            of = gdi32.SelectObject(hdc, app.get_font(13, True))
            user32.DrawTextW(hdc, self.title, -1, ctypes.byref(rc),
                             DT_LEFT | DT_VCENTER | DT_SINGLELINE)
            gdi32.SelectObject(hdc, of)
        super().draw(hdc, app)
