"""Owner-drawn media transport buttons and their container bar."""
from .common import *  # noqa: F401,F403
from .layouts import HBoxLayout
from .panel import Panel
from .style import style_of


class MediaButton(Widget):
    """Square transport button with a vector icon.

    Supported icons: ``play``, ``pause``, ``stop``, ``ff`` and ``rew``.
    The play/pause buttons can be highlighted with ``active`` so the current
    playback state is visible.
    """

    ICONS = ('play', 'pause', 'stop', 'ff', 'rew')

    def __init__(self, icon='play', on_click=None, size=40, accent=None,
                 active=False):
        super().__init__()
        self.icon = icon if icon in self.ICONS else 'play'
        self.on_click = on_click
        self.size = size
        self.accent = accent
        self.active = active
        self.focusable = True
        self._app = None

    def measure(self, app):
        side = int(self.size * app.scale)
        return (side, side)

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

    # -------------------------------------------------------------- drawing
    @staticmethod
    def _fill_polygon(hdc, app, points, color):
        pts = (wintypes.POINT * len(points))(
            *[wintypes.POINT(int(round(px)), int(round(py)))
              for px, py in points])
        brush = app.get_brush(color)
        old_brush = gdi32.SelectObject(hdc, brush)
        old_pen = gdi32.SelectObject(hdc, gdi32.GetStockObject(NULL_PEN))
        gdi32.Polygon(hdc, pts, len(points))
        gdi32.SelectObject(hdc, old_brush)
        gdi32.SelectObject(hdc, old_pen)

    def _triangle(self, hdc, app, left, cy, width, height, direction, color):
        if direction > 0:
            points = [(left, cy - height / 2.0), (left, cy + height / 2.0),
                      (left + width, cy)]
        else:
            points = [(left + width, cy - height / 2.0),
                      (left + width, cy + height / 2.0), (left, cy)]
        self._fill_polygon(hdc, app, points, color)

    def _draw_icon(self, hdc, app, color):
        cx = self.x + self.w / 2.0
        cy = self.y + self.h / 2.0
        i = min(self.w, self.h) * 0.40

        if self.icon == 'play':
            self._fill_polygon(hdc, app, [
                (cx - i * 0.52, cy - i * 0.72),
                (cx - i * 0.52, cy + i * 0.72),
                (cx + i * 0.72, cy)], color)
        elif self.icon == 'pause':
            bar_w = max(2, int(i * 0.30))
            bar_h = max(4, int(i * 1.35))
            gap = max(2, int(i * 0.28))
            radius = max(1, bar_w // 3)
            fill_round_rect(hdc, app, int(cx - gap / 2.0 - bar_w),
                            int(cy - bar_h / 2.0), bar_w, bar_h, radius, color)
            fill_round_rect(hdc, app, int(cx + gap / 2.0),
                            int(cy - bar_h / 2.0), bar_w, bar_h, radius, color)
        elif self.icon == 'stop':
            side = max(4, int(i * 1.20))
            radius = max(2, int(side * 0.22))
            fill_round_rect(hdc, app, int(cx - side / 2.0),
                            int(cy - side / 2.0), side, side, radius, color)
        else:
            direction = 1 if self.icon == 'ff' else -1
            tri_w = max(3, int(i * 0.55))
            tri_h = max(4, int(i * 1.30))
            gap = max(1, int(i * 0.14))
            total = tri_w * 2 + gap
            left = cx - total / 2.0
            for k in range(2):
                self._triangle(hdc, app, int(left + k * (tri_w + gap)),
                               cy, tri_w, tri_h, direction, color)

    def draw(self, hdc, app):
        self._app = app
        s = app.scale
        st = style_of(app)
        x, y, w, h = self.x, self.y, self.w, self.h
        radius = max(4, int(10 * s))
        accent = self.accent if self.accent is not None else st['highlight']

        if self.active:
            top = lighten(accent, 0.10)
            bottom = darken(accent, 0.10)
            border = lighten(accent, 0.35) if (self.hovered or self.focused) \
                else accent
            icon = st['highlightedText']
            glow = mix(st['window'], accent, 0.45)
        else:
            top = st['buttonPressed'] if self.pressed else st['buttonHover']
            bottom = st['buttonPressed'] if self.pressed else st['button']
            border = st['focus'] if self.focused else (
                st['highlight'] if self.hovered else st['border'])
            icon = st['highlight'] if (self.hovered or self.focused) \
                else st['buttonText']
            glow = st['glow']

        if self.hovered or self.focused:
            stroke_round_rect(hdc, app, x - 1, y - 1, w + 2, h + 2,
                              radius + 1, glow, max(2, int(2 * s)))
        fill_round_gradient_v(hdc, app, x, y, w, h, radius, top, bottom)
        stroke_round_rect(hdc, app, x, y, w, h, radius, border,
                          max(1, int(s)))

        self._draw_icon(hdc, app, icon)

        if self.focused:
            m = int(3 * s)
            stroke_round_rect(hdc, app, x + m, y + m, w - 2 * m, h - 2 * m,
                              max(1, radius - 1), st['focus'],
                              max(1, int(s)))


class TransportBar(Panel):
    """Row of media buttons: rewind, play, pause, stop, fast-forward."""

    ORDER = ('rew', 'play', 'pause', 'stop', 'ff')

    def __init__(self, on_command=None, on_play=None, on_pause=None,
                 on_stop=None, on_ff=None, on_rew=None, spacing=8,
                 button_size=40):
        super().__init__(layout=HBoxLayout(padding=0, spacing=spacing))
        self.on_command = on_command
        self.callbacks = {
            'rew': on_rew, 'play': on_play, 'pause': on_pause,
            'stop': on_stop, 'ff': on_ff,
        }
        self.buttons = {}
        self._app = None
        for name in self.ORDER:
            button = MediaButton(name, size=button_size,
                                 on_click=lambda n=name: self._emit(n))
            self.add(button)
            self.buttons[name] = button

    def _emit(self, name):
        callback = self.callbacks.get(name)
        if callback:
            callback()
        if self.on_command:
            self.on_command(name)

    def set_active(self, name):
        """Highlight one command (``None`` clears the highlight)."""
        changed = False
        for key, button in self.buttons.items():
            active = key == name
            if button.active != active:
                button.active = active
                changed = True
        if changed and self._app:
            self._app.invalidate_rect(self.x, self.y, self.w, self.h)

    def draw(self, hdc, app):
        self._app = app
        super().draw(hdc, app)
