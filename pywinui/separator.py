"""Horizontal or vertical separator line."""
from .common import *  # noqa: F401,F403
from .style import style_of


class Separator(Widget):
    def __init__(self, orientation='h', color=None):
        super().__init__()
        self.orientation = orientation
        self.color = color

    def measure(self, app):
        s = max(1, int(app.scale))
        if self.orientation == 'h':
            return (int(100 * app.scale), s)
        return (s, int(100 * app.scale))

    def draw(self, hdc, app):
        s = max(1, int(app.scale))
        color = self.color if self.color is not None else style_of(app)['mid']
        pen = app.get_pen(color, s)
        old = gdi32.SelectObject(hdc, pen)
        if self.orientation == 'h':
            y = self.y + self.h // 2
            gdi32.MoveToEx(hdc, self.x, y, None)
            gdi32.LineTo(hdc, self.x + self.w, y)
        else:
            x = self.x + self.w // 2
            gdi32.MoveToEx(hdc, x, self.y, None)
            gdi32.LineTo(hdc, x, self.y + self.h)
        gdi32.SelectObject(hdc, old)
