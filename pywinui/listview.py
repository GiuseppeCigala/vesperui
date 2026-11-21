"""Native report-mode list view."""

from .common import *  # noqa: F401,F403
from .native import _NativeWidget
from .style import style_of

class ListView(_NativeWidget):
    _win_class = 'SysListView32'
    inset = 2
    def __init__(self, columns=None, rows=None, on_select=None, height=200):
        super().__init__(); self.columns = list(columns or [('Column', 200)])
        self.rows = [list(r) for r in (rows or [])]; self.on_select = on_select
        self._height = height
        self._header_hwnd = None
    def _style(self):
        return (WS_CHILD | WS_VISIBLE | WS_TABSTOP
                | LVS_REPORT | LVS_SINGLESEL | LVS_SHOWSELALWAYS)
    def _create_title(self): return ''
    def measure(self, app): return (int(400 * app.scale), int(self._height * app.scale))
    def _post_realize(self, app):
        self._header_hwnd = user32.SendMessageW(self.hwnd, LVM_GETHEADER, 0, 0)
        user32.SendMessageW(self.hwnd, LVM_SETEXTENDEDLISTVIEWSTYLE,
                            LVS_EX_FULLROWSELECT, LVS_EX_FULLROWSELECT)
        for i, (name, width) in enumerate(self.columns):
            col = LVCOLUMNW()
            col.mask = LVCF_TEXT | LVCF_WIDTH | LVCF_FMT
            col.fmt = LVCFMT_LEFT; col.cx = int(width * app.scale); col.pszText = name
            SendMessagePtrW(self.hwnd, LVM_INSERTCOLUMNW, i, ctypes.addressof(col))
        self._populate()
        self._rescale_columns(app)
        self._apply_theme(app)

    def _apply_theme(self, app):
        if not self.hwnd:
            return
        st = style_of(app)
        # Keep the dark Explorer theme so native scrollbars match the UI,
        # while the header and client background are custom-drawn below.
        dark = is_dark(st['windowText'])
        name = 'DarkMode_Explorer' if dark else ''
        if dark:
            allow_dark_window(self.hwnd)
        uxtheme.SetWindowTheme(self.hwnd, name, None)
        if self._header_hwnd:
            uxtheme.SetWindowTheme(self._header_hwnd, name, None)
        user32.SendMessageW(self.hwnd, LVM_SETBKCOLOR, 0, COLORREF(*st['base']))
        user32.SendMessageW(self.hwnd, LVM_SETTEXTCOLOR, 0, COLORREF(*st['windowText']))
        user32.SendMessageW(self.hwnd, LVM_SETTEXTBKCOLOR, 0, COLORREF(*st['base']))
        if self._header_hwnd:
            user32.SendMessageW(self._header_hwnd, WM_SETFONT,
                                app.get_font(13, True), 1)

    def _draw_header(self, lp):
        """Custom-draw the column header so it matches the dark theme."""
        if not self._app:
            return CDRF_DODEFAULT
        cd = ctypes.cast(lp, ctypes.POINTER(NMCUSTOMDRAW)).contents
        st = style_of(self._app)
        if cd.dwDrawStage == CDDS_PREPAINT:
            rc = cd.rc
            user32.FillRect(cd.hdc, ctypes.byref(rc),
                            self._app.get_brush(st['card']))
            return CDRF_NOTIFYITEMDRAW
        if cd.dwDrawStage in (CDDS_ITEMPREPAINT,
                              CDDS_ITEMPREPAINT | CDDS_SUBITEM):
            index = int(cd.dwItemSpec)
            title = self.columns[index][0] if index < len(self.columns) else ''
            rc = cd.rc
            user32.FillRect(cd.hdc, ctypes.byref(rc),
                            self._app.get_brush(st['card']))
            gdi32.SetBkMode(cd.hdc, TRANSPARENT)
            gdi32.SetTextColor(cd.hdc, COLORREF(*st['windowText']))
            of = gdi32.SelectObject(cd.hdc, self._app.get_font(13, True))
            user32.DrawTextW(cd.hdc, title, -1, ctypes.byref(rc),
                             DT_LEFT | DT_VCENTER | DT_SINGLELINE)
            gdi32.SelectObject(cd.hdc, of)
            pen = self._app.get_pen(st['border'], 1)
            old = gdi32.SelectObject(cd.hdc, pen)
            gdi32.MoveToEx(cd.hdc, rc.left, rc.bottom - 1, None)
            gdi32.LineTo(cd.hdc, rc.right, rc.bottom - 1)
            gdi32.SelectObject(cd.hdc, old)
            return CDRF_SKIPDEFAULT
        return CDRF_DODEFAULT
    def _populate(self):
        for r, row in enumerate(self.rows):
            item = LVITEMW(); item.mask = LVIF_TEXT; item.iItem = r; item.iSubItem = 0
            item.pszText = row[0] if row else ''
            SendMessagePtrW(self.hwnd, LVM_INSERTITEMW, 0, ctypes.addressof(item))
            for sub in range(1, len(row)):
                it = LVITEMW(); it.iSubItem = sub; it.pszText = row[sub]
                SendMessagePtrW(self.hwnd, LVM_SETITEMTEXTW, r, ctypes.addressof(it))
    def set_rows(self, rows):
        self.rows = [list(r) for r in rows]
        if self.hwnd:
            user32.SendMessageW(self.hwnd, LVM_DELETEALLITEMS, 0, 0); self._populate()
            if self._app:
                self._rescale_columns(self._app)
    def get_selected_index(self):
        if not self.hwnd: return -1
        return user32.SendMessageW(self.hwnd, LVM_GETNEXTITEM, -1, LVNI_SELECTED)
    def get_selected_row(self):
        i = self.get_selected_index()
        return self.rows[i] if 0 <= i < len(self.rows) else None

    def select(self, index):
        """Select a row programmatically (fires on_select)."""
        if not (0 <= index < len(self.rows)):
            return
        if self.hwnd:
            item = LVITEMW()
            item.stateMask = LVIS_SELECTED | LVIS_FOCUSED
            item.state = LVIS_SELECTED | LVIS_FOCUSED
            item.iItem = index
            SendMessagePtrW(self.hwnd, LVM_SETITEMSTATE, index,
                            ctypes.addressof(item))
        elif self.on_select:
            self.on_select(index, self.rows[index])
    def _handle_notify(self, code, lp):
        if code != LVN_ITEMCHANGED: return
        nmlv = ctypes.cast(lp, ctypes.POINTER(NMLISTVIEW)).contents
        newly = ((nmlv.uChanged & LVIF_STATE) and (nmlv.uNewState & LVIS_SELECTED)
                 and not (nmlv.uOldState & LVIS_SELECTED))
        if newly and self.on_select:
            i = nmlv.iItem
            self.on_select(i, self.rows[i] if 0 <= i < len(self.rows) else None)
    def _rescale_columns(self, app):
        if not self.hwnd:
            return
        widths = [int(width * app.scale) for _, width in self.columns]
        if widths:
            # Leave room for the native vertical scrollbar only when it is
            # actually visible, otherwise the last column fills the header.
            vsb = bool(user32.GetWindowLongW(self.hwnd, GWL_STYLE) & WS_VSCROLL)
            available = max(0, self.w - 2 * self._inset_px()
                            - (user32.GetSystemMetrics(2) if vsb else 0))
            extra = max(0, available - sum(widths))
            widths[-1] += extra
        for i, cw in enumerate(widths):
            user32.SendMessageW(self.hwnd, LVM_SETCOLUMNWIDTH, i, cw)

    def _on_bounds(self):
        super()._on_bounds()
        if self.hwnd and self._app:
            self._rescale_columns(self._app)

