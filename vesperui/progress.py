"""Owner-drawn progress bar."""
from .common import *  # noqa: F401,F403
from .style import style_of


class ProgressBar(Widget):
    TRACK = (222, 226, 232)

    def __init__(self, value=0.0, indeterminate=False, show_text=False,
                 accent=None, orientation='h'):
        super().__init__()
        self.value = max(0.0, min(1.0, float(value)))
        self.indeterminate = indeterminate
        self.show_text = show_text
        self.accent = accent
        self.orientation = 'v' if orientation in ('v', 'vertical') else 'h'
        self.phase = 0.0

    def measure(self, app):
        if self.orientation == 'v':
            return (int(18 * app.scale), int(220 * app.scale))
        return (int(220 * app.scale), int(18 * app.scale))

    def set_value(self, value):
        self.value = max(0.0, min(1.0, float(value)))

    def tick(self, dt=0.03):
        """Advance the marquee phase (call from a timer when indeterminate)."""
        if self.indeterminate:
            self.phase = (self.phase + dt * 0.8) % 1.0

    def draw(self, hdc, app):
        s = app.scale
        st = style_of(app)
        accent = self.accent if self.accent is not None else st['highlight']
        accent2 = st['highlight2']
        x, y, w, h = self.x, self.y, self.w, self.h

        if self.orientation == 'v':
            radius = w // 2
            fill_round_rect(hdc, app, x, y, w, h, radius, st['button'])
            if self.indeterminate:
                seg = max(int(h * 0.28), int(8 * s))
                ty = y + int(self.phase * max(1, h - seg))
                fill_round_gradient_v(hdc, app, x, ty, w, seg, radius,
                                      accent2, accent)
            else:
                filled = int(h * self.value)
                if filled > 0:
                    seg = min(h, max(filled, radius * 2))
                    fill_round_gradient_v(hdc, app, x, y + h - seg, w, seg,
                                          radius, accent2, accent)
        else:
            radius = h // 2
            fill_round_rect(hdc, app, x, y, w, h, radius, st['button'])
            if self.indeterminate:
                seg = max(int(w * 0.28), int(8 * s))
                tx = x + int(self.phase * max(1, w - seg))
                fill_round_gradient_h(hdc, app, tx, y, seg, h, radius,
                                      accent, accent2)
            else:
                filled = int(w * self.value)
                if filled > 0:
                    fill_round_gradient_h(hdc, app, x, y,
                                          max(filled, radius * 2), h,
                                          radius, accent, accent2)

        stroke_round_rect(hdc, app, x, y, w, h, radius,
                          st['border'], max(1, int(s)))
        if self.show_text:
            rc = wintypes.RECT(x, y, x + w, y + h)
            gdi32.SetBkMode(hdc, TRANSPARENT)
            gdi32.SetTextColor(hdc, COLORREF(*st['windowText']))
            angle = 90 if self.orientation == 'v' else 0
            of = gdi32.SelectObject(hdc, app.get_font(10, True, angle=angle))
            user32.DrawTextW(hdc, f'{int(self.value * 100)}%', -1,
                             ctypes.byref(rc),
                             DT_CENTER | DT_VCENTER | DT_SINGLELINE)
            gdi32.SelectObject(hdc, of)
