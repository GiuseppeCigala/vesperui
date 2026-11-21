"""Owner-drawn text label widget."""
from .common import *  # noqa: F401,F403
from .style import style_of


class Label(Widget):
    def __init__(self, text='', size=14, bold=False, color=None, align='left'):
        super().__init__()
        self.text = text
        self.size = size
        self.bold = bold
        self.color = color
        self.align = align   # 'left' | 'center' | 'right'

    def measure(self, app):
        tw, th = app.measure_text(self.text, self.size, self.bold)
        return (tw + int(4 * app.scale), th + int(4 * app.scale))

    def draw(self, hdc, app):
        color = self.color if self.color is not None else style_of(app)['windowText']
        rc = wintypes.RECT(self.x, self.y, self.x + self.w, self.y + self.h)
        gdi32.SetBkMode(hdc, TRANSPARENT)
        gdi32.SetTextColor(hdc, COLORREF(*color))
        of = gdi32.SelectObject(hdc, app.get_font(self.size, self.bold))
        flags = DT_VCENTER | DT_SINGLELINE
        if self.align == 'center': flags |= DT_CENTER
        elif self.align == 'right': flags |= 0x0002  # DT_RIGHT
        else: flags |= DT_LEFT
        user32.DrawTextW(hdc, self.text, -1, ctypes.byref(rc), flags)
        gdi32.SelectObject(hdc, of)
