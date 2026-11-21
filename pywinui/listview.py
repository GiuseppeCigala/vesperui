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
    def _style(self):
        return (WS_CHILD | WS_VISIBLE | WS_TABSTOP
                | LVS_REPORT | LVS_SINGLESEL | LVS_SHOWSELALWAYS)
    def _create_title(self): return ''
    def measure(self, app): return (int(400 * app.scale), int(self._height * app.scale))
    def _post_realize(self, app):
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
        user32.SendMessageW(self.hwnd, LVM_SETBKCOLOR, 0, COLORREF(*st['base']))
        user32.SendMessageW(self.hwnd, LVM_SETTEXTCOLOR, 0, COLORREF(*st['windowText']))
        user32.SendMessageW(self.hwnd, LVM_SETTEXTBKCOLOR, 0, COLORREF(*st['base']))
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
    def get_selected_index(self):
        if not self.hwnd: return -1
        return user32.SendMessageW(self.hwnd, LVM_GETNEXTITEM, -1, LVNI_SELECTED)
    def get_selected_row(self):
        i = self.get_selected_index()
        return self.rows[i] if 0 <= i < len(self.rows) else None
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
            # Leave room for the native vertical scrollbar so the last column
            # does not force a horizontal scrollbar.
            available = max(0, self.w - 2 * self._inset_px()
                            - user32.GetSystemMetrics(2))
            extra = max(0, available - sum(widths))
            widths[-1] += extra
        for i, cw in enumerate(widths):
            user32.SendMessageW(self.hwnd, LVM_SETCOLUMNWIDTH, i, cw)

    def _on_bounds(self):
        super()._on_bounds()
        if self.hwnd and self._app:
            self._rescale_columns(self._app)

