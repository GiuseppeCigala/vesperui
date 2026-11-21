"""Native drop-down list combo box."""

from .common import *  # noqa: F401,F403
from .native import _NativeWidget

class ComboBox(_NativeWidget):
    _win_class = 'COMBOBOX'
    inset = 2
    def __init__(self, items=None, on_change=None, index=0):
        super().__init__(); self.items = list(items or []); self.on_change = on_change
        self._initial_index = index
    def _style(self):
        return WS_CHILD | WS_VISIBLE | WS_VSCROLL | WS_TABSTOP | CBS_DROPDOWNLIST
    def _create_title(self): return ''
    def measure(self, app): return (int(180 * app.scale), int(28 * app.scale))
    def _post_realize(self, app):
        for it in self.items: SendMessageStrW(self.hwnd, CB_ADDSTRING, 0, it)
        if self.items: user32.SendMessageW(self.hwnd, CB_SETCURSEL, self._initial_index, 0)
    def current_index(self):
        if self.hwnd: return user32.SendMessageW(self.hwnd, CB_GETCURSEL, 0, 0)
        return self._initial_index
    def current_text(self):
        i = self.current_index()
        return self.items[i] if 0 <= i < len(self.items) else ''
    def set_index(self, i):
        self._initial_index = i
        if self.hwnd: user32.SendMessageW(self.hwnd, CB_SETCURSEL, i, 0)

