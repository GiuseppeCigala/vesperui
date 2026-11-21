"""Native drop-down list combo box."""

from .common import *  # noqa: F401,F403
from .native import _NativeWidget
from .style import style_of

class ComboBox(_NativeWidget):
    _win_class = 'COMBOBOX'
    inset = 2
    def __init__(self, items=None, on_change=None, index=0):
        super().__init__(); self.items = list(items or []); self.on_change = on_change
        self._initial_index = index
    def _style(self):
        return (WS_CHILD | WS_VISIBLE | WS_VSCROLL | WS_TABSTOP
                | CBS_DROPDOWNLIST | CBS_OWNERDRAWFIXED | CBS_HASSTRINGS)
    def _create_title(self): return ''
    def measure(self, app): return (int(180 * app.scale), int(28 * app.scale))
    def _apply_window_theme(self, app):
        if not self.hwnd:
            return
        dark = is_dark(style_of(app)['windowText'])
        if dark:
            allow_dark_window(self.hwnd)
        uxtheme.SetWindowTheme(self.hwnd, 'DarkMode_CFD' if dark else '', None)
    def _post_realize(self, app):
        for it in self.items: SendMessageStrW(self.hwnd, CB_ADDSTRING, 0, it)
        if self.items: user32.SendMessageW(self.hwnd, CB_SETCURSEL, self._initial_index, 0)

    def _draw_item(self, dis):
        """Owner-draw the closed field and the drop-down rows."""
        if not self._app:
            return
        st = style_of(self._app)
        item = ctypes.c_int(dis.itemID).value
        if item == -1:
            text = self.current_text()
            selected = False
        else:
            text = self.items[item] if 0 <= item < len(self.items) else ''
            selected = bool(dis.itemState & ODS_SELECTED)
        if selected:
            bg, fg = st['highlight'], st['highlightedText']
        else:
            bg, fg = st['base'], st['windowText']
        rc = dis.rcItem
        user32.FillRect(dis.hDC, ctypes.byref(rc), self._app.get_brush(bg))
        gdi32.SetBkMode(dis.hDC, TRANSPARENT)
        gdi32.SetTextColor(dis.hDC, COLORREF(*fg))
        of = gdi32.SelectObject(dis.hDC, self._app.get_font(self.font_size))
        pad = max(4, int(6 * self._app.scale))
        text_rc = wintypes.RECT(rc.left + pad, rc.top, rc.right - pad, rc.bottom)
        user32.DrawTextW(dis.hDC, text, -1, ctypes.byref(text_rc),
                         DT_LEFT | DT_VCENTER | DT_SINGLELINE)
        gdi32.SelectObject(dis.hDC, of)
    def current_index(self):
        if self.hwnd: return user32.SendMessageW(self.hwnd, CB_GETCURSEL, 0, 0)
        return self._initial_index
    def current_text(self):
        i = self.current_index()
        return self.items[i] if 0 <= i < len(self.items) else ''
    def set_index(self, i):
        self._initial_index = i
        if self.hwnd: user32.SendMessageW(self.hwnd, CB_SETCURSEL, i, 0)

    def select(self, index):
        """Select an item programmatically and fire on_change."""
        self.set_index(index)
        if self.on_change:
            self.on_change(index, self.current_text())

