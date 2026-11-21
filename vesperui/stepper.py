"""Owner-drawn numeric stepper with decrement and increment buttons."""
from .common import *  # noqa: F401,F403
from .style import style_of


class Stepper(Widget):
    def __init__(self, value=0, min=0, max=100, step=1,
                 on_change=None, prefix='', suffix=''):
        super().__init__()
        lo, hi = float(min), float(max)
        if hi < lo:
            lo, hi = hi, lo
        self.min, self.max = lo, hi
        self.step = abs(float(step)) or 1.0
        value = float(value)
        self.value = lo if value < lo else hi if value > hi else value
        self.on_change = on_change
        self.prefix = prefix
        self.suffix = suffix
        self.focusable = True
        self._app = None
        self._hover_part = None
        self._pressed_part = None

    def measure(self, app):
        return (int(120 * app.scale), int(28 * app.scale))

    def set_value(self, value, notify=True):
        value = max(self.min, min(self.max, float(value)))
        changed = value != self.value
        self.value = value
        if changed and notify and self.on_change:
            self.on_change(value)
        return changed

    def increment(self):
        return self.set_value(self.value + self.step)

    def decrement(self):
        return self.set_value(self.value - self.step)

    def _button_w(self):
        return max(1, min(self.h, self.w // 2))

    def _part_at(self, x):
        bw = self._button_w()
        if x < self.x + bw:
            return 'dec'
        if x >= self.x + self.w - bw:
            return 'inc'
        return None

    def _disabled(self, part):
        if part == 'dec':
            return self.value <= self.min
        if part == 'inc':
            return self.value >= self.max
        return False

    def on_mouse_down(self, x, y):
        part = self._part_at(x)
        self._pressed_part = part if part and not self._disabled(part) else None

    def on_mouse_up(self, x, y):
        part = self._pressed_part
        self._pressed_part = None
        if part and self._part_at(x) == part and not self._disabled(part):
            if part == 'inc':
                self.increment()
            else:
                self.decrement()

    def on_mouse_move(self, x, y):
        part = self._part_at(x)
        if part != self._hover_part:
            self._hover_part = part
            if self._app:
                self._app.invalidate_rect(self.x, self.y, self.w, self.h)

    def on_key(self, vk, ch):
        if vk in (VK_LEFT, VK_DOWN):
            self.decrement()
        elif vk in (VK_RIGHT, VK_UP):
            self.increment()

    def on_wheel(self, delta):
        if delta > 0:
            return self.increment()
        if delta < 0:
            return self.decrement()
        return False

    def _value_text(self):
        value = self.value
        if float(value).is_integer():
            text = str(int(value))
        else:
            text = ('%.2f' % value).rstrip('0').rstrip('.')
        return '%s%s%s' % (self.prefix, text, self.suffix)

    def draw(self, hdc, app):
        self._app = app
        s = app.scale
        st = style_of(app)
        x, y, w, h = self.x, self.y, self.w, self.h
        radius = max(4, int(st.get('inputRadius', 6) * s))
        bw = self._button_w()

        if self.focused:
            stroke_round_rect(hdc, app, x - 1, y - 1, w + 2, h + 2,
                              radius + 1, st['glow'], max(2, int(2 * s)))
        fill_round_gradient_v(hdc, app, x, y, w, h, radius,
                              lighten(st['base'], 0.04), st['base'])
        stroke_round_rect(hdc, app, x, y, w, h, radius,
                          st['focus'] if self.focused else st['border'],
                          max(1, int(s)))

        for part in ('dec', 'inc'):
            bx = x if part == 'dec' else x + w - bw
            pressed = self._pressed_part == part
            hovered = self.hovered and self._hover_part == part
            disabled = self._disabled(part)
            if pressed:
                fill_round_gradient_v(hdc, app, bx + 2, y + 2,
                                      max(1, bw - 4), max(1, h - 4),
                                      max(2, radius - 2),
                                      st['highlight'], st['highlight2'])
                glyph = st['highlightedText']
            elif hovered and not disabled:
                fill_round_rect(hdc, app, bx + 2, y + 2,
                                max(1, bw - 4), max(1, h - 4),
                                max(2, radius - 2), st['buttonHover'])
                glyph = st['windowText']
            else:
                glyph = st['disabled'] if disabled else st['windowText']
            self._draw_glyph(hdc, app, part, bx, bw, h, glyph)

        pen = app.get_pen(st['border'], max(1, int(s)))
        old = gdi32.SelectObject(hdc, pen)
        for sx in (x + bw, x + w - bw):
            gdi32.MoveToEx(hdc, sx, y + max(3, int(4 * s)), None)
            gdi32.LineTo(hdc, sx, y + h - max(3, int(4 * s)))
        gdi32.SelectObject(hdc, old)

        rc = wintypes.RECT(x + bw, y, x + w - bw, y + h)
        gdi32.SetBkMode(hdc, TRANSPARENT)
        gdi32.SetTextColor(hdc, COLORREF(*st['windowText']))
        of = gdi32.SelectObject(hdc, app.get_font(14, True))
        user32.DrawTextW(hdc, self._value_text(), -1, ctypes.byref(rc),
                         DT_CENTER | DT_VCENTER | DT_SINGLELINE)
        gdi32.SelectObject(hdc, of)

    def _draw_glyph(self, hdc, app, part, bx, bw, h, color):
        s = app.scale
        cx = bx + bw // 2
        cy = self.y + h // 2
        gh = max(6, int(8 * s))
        pen = app.get_pen(color, max(1, int(2 * s)))
        old = gdi32.SelectObject(hdc, pen)
        gdi32.MoveToEx(hdc, cx - gh // 2, cy, None)
        gdi32.LineTo(hdc, cx + gh // 2 + 1, cy)
        if part == 'inc':
            gdi32.MoveToEx(hdc, cx, cy - gh // 2, None)
            gdi32.LineTo(hdc, cx, cy + gh // 2 + 1)
        gdi32.SelectObject(hdc, old)


StepperButton = Stepper
