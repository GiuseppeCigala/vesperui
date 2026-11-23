"""Native drop-down list combo box."""

from .common import *  # noqa: F401,F403
from .native import _NativeWidget
from .style import scale_color, style_of

WM_PRINT = 0x0317


class COMBOBOXINFO(ctypes.Structure):
    _fields_ = [('cbSize', wintypes.DWORD),
                ('rcItem', wintypes.RECT),
                ('rcButton', wintypes.RECT),
                ('stateButton', wintypes.DWORD),
                ('hwndCombo', wintypes.HWND),
                ('hwndItem', wintypes.HWND),
                ('hwndList', wintypes.HWND)]


user32.GetComboBoxInfo.argtypes = [wintypes.HWND,
                                   ctypes.POINTER(COMBOBOXINFO)]
user32.GetComboBoxInfo.restype = wintypes.BOOL


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
        self._install_subclass(self._subclass_proc)

    def _subclass_proc(self, hwnd, msg, wparam, lparam, uId, ref):
        result = comctl32.DefSubclassProc(hwnd, msg, wparam, lparam)
        if not self._app:
            return result
        if msg == WM_PAINT:
            hdc = user32.GetDC(hwnd)
            try:
                self._paint_arrow(hdc)
            finally:
                user32.ReleaseDC(hwnd, hdc)
        elif msg == WM_PRINT:
            self._paint_arrow(wparam)
        return result

    def _paint_arrow(self, hdc):
        """Draw a small chevron over the native drop-down button."""
        info = COMBOBOXINFO()
        info.cbSize = ctypes.sizeof(COMBOBOXINFO)
        if not user32.GetComboBoxInfo(self.hwnd, ctypes.byref(info)):
            return
        rc = info.rcButton
        width, height = rc.right - rc.left, rc.bottom - rc.top
        if width <= 0 or height <= 0:
            return

        app = self._app
        st = style_of(app)
        s = app.scale
        fill_gradient_v(hdc, rc.left, rc.top, width, height,
                        lighten(st['base'], 0.03), st['base'])

        pen = app.get_pen(mix(st['base'], st['border'], 0.55),
                          max(1, int(s)))
        old = gdi32.SelectObject(hdc, pen)
        gdi32.MoveToEx(hdc, rc.left, rc.top + int(2 * s), None)
        gdi32.LineTo(hdc, rc.left, rc.bottom - int(2 * s))
        gdi32.SelectObject(hdc, old)

        pen = app.get_pen(mix(st['windowText'], st['mid'], 0.30),
                          max(1, int(1.5 * s)))
        old = gdi32.SelectObject(hdc, pen)
        cx = (rc.left + rc.right) // 2
        cy = (rc.top + rc.bottom) // 2
        half_w = max(3, int(5 * s))
        half_h = max(1, int(2 * s))
        gdi32.MoveToEx(hdc, cx - half_w, cy - half_h, None)
        gdi32.LineTo(hdc, cx, cy + half_h)
        gdi32.LineTo(hdc, cx + half_w, cy - half_h)
        gdi32.SelectObject(hdc, old)

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
        rc = dis.rcItem
        fg = st['windowText']
        width = max(1, rc.right - rc.left)
        height = max(1, rc.bottom - rc.top)
        if selected:
            fill_gradient_h(dis.hDC, rc.left, rc.top, width, height,
                            scale_color(st, 0.25), scale_color(st, 0.75))
        else:
            fill_gradient_v(dis.hDC, rc.left, rc.top, width, height,
                            lighten(st['base'], 0.03), st['base'])
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

