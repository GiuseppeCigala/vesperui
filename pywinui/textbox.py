"""Native single-line and multi-line text box."""

from .common import *  # noqa: F401,F403
from .native import _NativeWidget

class TextBox(_NativeWidget):
    _win_class = 'EDIT'
    inset = 2
    def __init__(self, text='', multiline=False, on_change=None):
        super().__init__(); self._text = text; self.multiline = multiline; self.on_change = on_change
    def _style(self):
        s = WS_CHILD | WS_VISIBLE | WS_TABSTOP | ES_LEFT | ES_AUTOHSCROLL
        if self.multiline: s |= ES_MULTILINE | WS_VSCROLL | ES_AUTOVSCROLL
        return s
    def _create_title(self): return self._text
    def measure(self, app):
        return (int(240 * app.scale), int((80 if self.multiline else 28) * app.scale))
    def get_text(self):
        if not self.hwnd: return self._text
        n = user32.GetWindowTextLengthW(self.hwnd)
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(self.hwnd, buf, n + 1)
        return buf.value
    def set_text(self, t):
        self._text = t
        if self.hwnd: user32.SetWindowTextW(self.hwnd, t)

