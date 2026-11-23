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
        st = style_of(app)
        color = self.color if self.color is not None \
            else mix(st['border'], st['mid'], 0.45)
        faded = mix(st['window'], color, 0.25)
        if self.orientation == 'h':
            y = self.y + self.h // 2
            mid = self.x + self.w // 2
            fill_gradient_h(hdc, self.x, y, max(1, mid - self.x), s,
                            faded, color)
            fill_gradient_h(hdc, mid, y,
                            max(1, self.x + self.w - mid), s,
                            color, faded)
        else:
            x = self.x + self.w // 2
            mid = self.y + self.h // 2
            fill_gradient_v(hdc, x, self.y, s, max(1, mid - self.y),
                            faded, color)
            fill_gradient_v(hdc, x, mid, s,
                            max(1, self.y + self.h - mid),
                            color, faded)
