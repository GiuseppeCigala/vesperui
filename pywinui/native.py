"""Base class for native Win32 child controls."""
from .common import *  # noqa: F401,F403
from .style import style_of


class _NativeWidget(Widget):
    _win_class = ''
    inset = 0

    def __init__(self):
        super().__init__()
        self.hwnd = None
        self.ctrl_id = 0
        self.font_size = 14
        self.focusable = True
        self._app = None

    def _inset_px(self):
        scale = self._app.scale if self._app else 1.0
        return int(self.inset * scale)

    def _style(self):
        return WS_CHILD | WS_VISIBLE | WS_TABSTOP

    def _create_title(self):
        return ''

    def realize(self, parent_hwnd, hinstance, app):
        if self.hwnd:
            return
        self._app = app
        # Always assign a unique ctrl_id, no matter how the widget was added
        if not self.ctrl_id:
            self.ctrl_id = app._next_ctrl
            app._next_ctrl += 1
        ins = self._inset_px()
        self.hwnd = user32.CreateWindowExW(
            0, self._win_class, self._create_title(), self._style(),
            self.x + ins, self.y + ins,
            max(1, self.w - 2 * ins), max(1, self.h - 2 * ins),
            parent_hwnd, ctypes.c_void_p(self.ctrl_id), hinstance, None)
        # Use flat classic rendering so the surrounding modern border shows.
        self._apply_window_theme(app)
        user32.SendMessageW(self.hwnd, WM_SETFONT, app.get_font(self.font_size), 1)
        self._post_realize(app)

    def _apply_window_theme(self, app):
        if not self.hwnd:
            return
        name = 'DarkMode_Explorer' if is_dark(style_of(app)['windowText']) else ''
        uxtheme.SetWindowTheme(self.hwnd, name, '')

    def _post_realize(self, app):
        pass

    def click(self):
        """Focus the control; concrete native widgets may override."""
        if self.hwnd:
            user32.SetFocus(self.hwnd)

    def _on_bounds(self):
        if self.hwnd:
            ins = self._inset_px()
            user32.SetWindowPos(self.hwnd, None, self.x + ins, self.y + ins,
                                max(1, self.w - 2 * ins),
                                max(1, self.h - 2 * ins), SWP_NOZORDER)

    def draw(self, hdc, app):
        if not self.inset:
            return
        s = app.scale
        st = style_of(app)
        radius = max(4, int(st.get('inputRadius', 6) * s))
        if self.focused:
            stroke_round_rect(hdc, app, self.x - 1, self.y - 1,
                              self.w + 2, self.h + 2, radius + 1,
                              st['glow'], max(2, int(2 * s)))
        fill_round_gradient_v(hdc, app, self.x, self.y, self.w, self.h, radius,
                              lighten(st['base'], 0.04), st['base'])
        border = st['focus'] if self.focused else st['border']
        stroke_round_rect(hdc, app, self.x, self.y, self.w, self.h, radius,
                          border, max(1, int(s)))
