"""Native single-line and multi-line text box."""

from .common import *  # noqa: F401,F403
from .native import _NativeWidget
from .style import style_of

WM_PRINT = 0x0317
SM_CXVSCROLL = 2

user32.GetWindowDC.argtypes = [wintypes.HWND]
user32.GetWindowDC.restype = wintypes.HDC


class TextBox(_NativeWidget):
    _win_class = 'EDIT'
    inset = 2

    def __init__(self, text='', multiline=False, on_change=None):
        super().__init__()
        self._text = text
        self.multiline = multiline
        self.on_change = on_change

    def _style(self):
        s = WS_CHILD | WS_VISIBLE | WS_TABSTOP | ES_LEFT | ES_AUTOHSCROLL
        if self.multiline:
            s |= ES_MULTILINE | WS_VSCROLL | ES_AUTOVSCROLL
        return s

    def _create_title(self):
        return self._text

    def measure(self, app):
        return (int(240 * app.scale),
                int((80 if self.multiline else 28) * app.scale))

    def _post_realize(self, app):
        if self.multiline:
            self._install_subclass(self._subclass_proc)

    def _subclass_proc(self, hwnd, msg, wparam, lparam, uId, ref):
        result = comctl32.DefSubclassProc(hwnd, msg, wparam, lparam)
        if not self._app:
            return result
        if msg == WM_PAINT:
            hdc = user32.GetWindowDC(hwnd)
            try:
                self._paint_scroll_arrows(hdc)
            finally:
                user32.ReleaseDC(hwnd, hdc)
        elif msg == WM_PRINT:
            self._paint_scroll_arrows(wparam)
        return result

    def _paint_scroll_arrows(self, hdc):
        """Draw compact chevrons over the native scrollbar arrow buttons."""
        window = wintypes.RECT()
        if not user32.GetWindowRect(self.hwnd, ctypes.byref(window)):
            return
        width = window.right - window.left
        height = window.bottom - window.top
        sb_w = user32.GetSystemMetrics(SM_CXVSCROLL)
        if width <= 0 or height <= 0 or sb_w <= 0 or sb_w >= width:
            return

        app = self._app
        st = style_of(app)
        s = app.scale
        left = width - sb_w
        arrow = min(sb_w, height // 2)
        track = mix(st['window'], st['base'], 0.45)
        for box_top in (0, height - arrow):
            rc = wintypes.RECT(left, box_top, width, box_top + arrow)
            user32.FillRect(hdc, ctypes.byref(rc), app.get_brush(track))

        pen = app.get_pen(mix(st['windowText'], st['mid'], 0.30),
                          max(1, int(1.5 * s)))
        old = gdi32.SelectObject(hdc, pen)
        cx = left + sb_w // 2
        half_w = max(2, int(5 * s))
        half_h = max(1, int(2 * s))
        cy = arrow // 2
        gdi32.MoveToEx(hdc, cx - half_w, cy + half_h, None)
        gdi32.LineTo(hdc, cx, cy - half_h)
        gdi32.LineTo(hdc, cx + half_w, cy + half_h)
        cy = height - arrow // 2
        gdi32.MoveToEx(hdc, cx - half_w, cy - half_h, None)
        gdi32.LineTo(hdc, cx, cy + half_h)
        gdi32.LineTo(hdc, cx + half_w, cy - half_h)
        gdi32.SelectObject(hdc, old)

    def get_text(self):
        if not self.hwnd:
            return self._text
        n = user32.GetWindowTextLengthW(self.hwnd)
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(self.hwnd, buf, n + 1)
        return buf.value

    def set_text(self, t, notify=True):
        self._text = t
        if self.hwnd:
            user32.SetWindowTextW(self.hwnd, t)
        elif notify and self.on_change:
            self.on_change(t)

    def type_text(self, text):
        """Simulate typing text into the control."""
        if self.hwnd:
            for ch in text:
                user32.SendMessageW(self.hwnd, WM_CHAR, ord(ch), 0)
        else:
            self.set_text(self._text + text, notify=True)
