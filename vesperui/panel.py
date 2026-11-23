"""Panel container with rounded background, shadow and border."""

from .common import *  # noqa: F401,F403

# ============================================================================
# PANEL
# ============================================================================
class Panel(Container):
    def __init__(self, layout=None, padding=0, bg=None, radius=0,
                 shadow=False, gradient=None, border=None):
        super().__init__(); self.layout = layout; self.padding = padding; self.bg = bg
        self.radius = radius          # corner radius in DIPs (0 = square)
        self.shadow = shadow          # draw a soft drop shadow
        self.gradient = gradient      # (top_rgb, bottom_rgb) or None
        self.border = border          # border color or None
    def measure(self, app):
        return self.layout.measure(self, app) if self.layout else (self.w, self.h)
    def arrange(self, app):
        if self.layout: self.layout.arrange(self, app)
        for c in self.children:
            if isinstance(c, Container): c.arrange(app)
    def draw(self, hdc, app):
        s = app.scale
        r = int(self.radius * s)
        if self.shadow and r > 0:
            draw_shadow(hdc, app, self.x, self.y, self.w, self.h, r,
                        spread=int(5 * s), alpha_steps=10)
        if self.gradient is not None:
            if r > 0:
                fill_round_gradient_v(hdc, app, self.x, self.y, self.w,
                                      self.h, r, self.gradient[0],
                                      self.gradient[1])
            else:
                fill_gradient_v(hdc, self.x, self.y, self.w, self.h,
                                self.gradient[0], self.gradient[1])
        elif self.bg is not None:
            top = lighten(self.bg, 0.025)
            bottom = darken(self.bg, 0.015)
            if r > 0:
                fill_round_gradient_v(hdc, app, self.x, self.y, self.w,
                                      self.h, r, top, bottom)
            else:
                fill_gradient_v(hdc, self.x, self.y, self.w, self.h,
                                top, bottom)
        if self.border is not None and r > 0:
            stroke_round_rect(hdc, app, self.x, self.y, self.w, self.h, r,
                              self.border, max(1, int(s)))
        super().draw(hdc, app)

