"""Native report-mode list view."""

from .common import *  # noqa: F401,F403
from .common import _SetWndPtr
from .native import _NativeWidget
from .style import scale_color, style_of

class ListView(_NativeWidget):
    _win_class = 'SysListView32'
    inset = 2
    def __init__(self, columns=None, rows=None, on_select=None, height=200,
                 on_edit=None):
        super().__init__(); self.columns = list(columns or [('Column', 200)])
        self.rows = [list(r) for r in (rows or [])]; self.on_select = on_select
        self.on_edit = on_edit
        self._height = height
        self._header_hwnd = None
        self._cd_selected = -1
        self._edit_hwnd = None
        self._edit_item = -1
        self._edit_subitem = -1
        self._edit_old = ''
        self._edit_orig = None
        self._edit_proc = WNDPROC(self._edit_wndproc)
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
            fill_gradient_v(cd.hdc, rc.left, rc.top,
                            max(1, rc.right - rc.left),
                            max(1, rc.bottom - rc.top),
                            lighten(st['card'], 0.03), st['card'])
            return CDRF_NOTIFYITEMDRAW
        if cd.dwDrawStage in (CDDS_ITEMPREPAINT,
                              CDDS_ITEMPREPAINT | CDDS_SUBITEM):
            index = int(cd.dwItemSpec)
            title = self.columns[index][0] if index < len(self.columns) else ''
            rc = cd.rc
            fill_gradient_v(cd.hdc, rc.left, rc.top,
                            max(1, rc.right - rc.left),
                            max(1, rc.bottom - rc.top),
                            lighten(st['card'], 0.03), st['card'])
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

    def _draw_list(self, lp):
        """Custom-draw rows with accent selection and alternating bands."""
        if not self._app:
            return CDRF_DODEFAULT
        cd = ctypes.cast(lp, ctypes.POINTER(NMLVCUSTOMDRAW)).contents
        st = style_of(self._app)
        stage = cd.nmcd.dwDrawStage
        hdc = cd.nmcd.hdc

        if stage == CDDS_PREPAINT:
            self._cd_selected = self.get_selected_index()
            rc = cd.nmcd.rc
            user32.FillRect(hdc, ctypes.byref(rc), self._app.get_brush(st['base']))
            if not self.rows:
                gdi32.SetBkMode(hdc, TRANSPARENT)
                gdi32.SetTextColor(hdc, COLORREF(*st['mid']))
                of = gdi32.SelectObject(hdc, self._app.get_font(13))
                user32.DrawTextW(hdc, 'No rows to display', -1,
                                 ctypes.byref(rc),
                                 DT_CENTER | DT_VCENTER | DT_SINGLELINE)
                gdi32.SelectObject(hdc, of)
                return CDRF_SKIPDEFAULT
            return CDRF_NOTIFYITEMDRAW

        if stage == CDDS_ITEMPREPAINT:
            return CDRF_NOTIFYSUBITEMDRAW

        if stage == (CDDS_ITEMPREPAINT | CDDS_SUBITEM):
            item = int(cd.nmcd.dwItemSpec)
            if not (0 <= item < len(self.rows)):
                return CDRF_DODEFAULT
            row = self.rows[item]
            sub = cd.iSubItem
            text = row[sub] if 0 <= sub < len(row) else ''
            selected = (item == self._cd_selected)
            rc = cd.nmcd.rc
            width = max(1, rc.right - rc.left)
            height = max(1, rc.bottom - rc.top)
            if selected:
                fill_gradient_h(hdc, rc.left, rc.top, width, height,
                                scale_color(st, 0.25), scale_color(st, 0.75))
                fg = st['windowText']
            else:
                bg = st['alternateBase'] if item % 2 else st['base']
                fill_gradient_v(hdc, rc.left, rc.top, width, height,
                                lighten(bg, 0.015), darken(bg, 0.01))
                fg = st['windowText']
            gdi32.SetBkMode(hdc, TRANSPARENT)
            gdi32.SetTextColor(hdc, COLORREF(*fg))
            of = gdi32.SelectObject(hdc, self._app.get_font(self.font_size))
            pad = max(4, int(6 * self._app.scale))
            text_rc = wintypes.RECT(rc.left + pad, rc.top,
                                    rc.right - pad, rc.bottom)
            user32.DrawTextW(hdc, str(text), -1, ctypes.byref(text_rc),
                             DT_LEFT | DT_VCENTER | DT_SINGLELINE)
            gdi32.SelectObject(hdc, of)
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
        if self._edit_hwnd:
            self._end_edit(commit=False)
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

    def begin_edit(self, item, subitem=0):
        """Open an in-place editor over the given cell."""
        if not self.hwnd or not (0 <= item < len(self.rows)):
            return False
        app = self._app
        if app is None:
            return False
        if self._edit_hwnd:
            self._end_edit(commit=True)

        rc = wintypes.RECT()
        rc.left = LVIR_BOUNDS
        rc.top = int(subitem)
        SendMessagePtrW(self.hwnd, LVM_GETSUBITEMRECT, item,
                        ctypes.addressof(rc))
        width = rc.right - rc.left
        height = rc.bottom - rc.top
        if width <= 0 or height <= 0:
            return False

        inset = self._inset_px()
        x = self.x + inset + rc.left
        y = self.y + inset + rc.top
        row = self.rows[item]
        text = row[subitem] if 0 <= subitem < len(row) else ''
        edit_id = app._next_ctrl
        app._next_ctrl += 1
        edit = user32.CreateWindowExW(
            0, 'EDIT', text,
            WS_CHILD | WS_VISIBLE | WS_TABSTOP | ES_LEFT | ES_AUTOHSCROLL,
            x, y, width, height, app.hwnd, ctypes.c_void_p(edit_id),
            app.hinstance, None)
        if not edit:
            return False

        self._edit_hwnd = edit
        self._edit_item = item
        self._edit_subitem = subitem
        self._edit_old = text
        user32.SendMessageW(edit, WM_SETFONT, app.get_font(self.font_size), 1)
        dark = is_dark(style_of(app)['windowText'])
        if dark:
            allow_dark_window(edit)
        uxtheme.SetWindowTheme(edit, 'DarkMode_Explorer' if dark else '', None)
        self._edit_orig = _SetWndPtr(
            edit, GWLP_WNDPROC,
            ctypes.cast(self._edit_proc, ctypes.c_void_p))
        user32.SendMessageW(edit, EM_SETSEL, 0, -1)
        user32.SetFocus(edit)
        return True

    def _end_edit(self, commit=True):
        edit = self._edit_hwnd
        if not edit:
            return
        item = self._edit_item
        subitem = self._edit_subitem
        text = None
        if commit and user32.IsWindow(edit):
            size = user32.GetWindowTextLengthW(edit)
            buffer = ctypes.create_unicode_buffer(size + 1)
            user32.GetWindowTextW(edit, buffer, size + 1)
            text = buffer.value
        self._edit_hwnd = None
        self._edit_item = self._edit_subitem = -1
        self._edit_old = ''
        if user32.IsWindow(edit):
            user32.DestroyWindow(edit)
        self._edit_orig = None
        if self.hwnd and user32.IsWindow(self.hwnd):
            user32.SetFocus(self.hwnd)
        if (commit and text is not None and 0 <= item < len(self.rows)
                and subitem >= 0):
            row = self.rows[item]
            while len(row) <= subitem:
                row.append('')
            if row[subitem] != text:
                row[subitem] = text
                self._set_item_text(item, subitem, text)
                if self.on_edit:
                    self.on_edit(item, subitem, text)
        if self._app:
            self._app.invalidate()

    def _edit_wndproc(self, hwnd, msg, wp, lp):
        if msg == WM_KEYDOWN:
            if wp == VK_RETURN:
                self._end_edit(commit=True)
                return 0
            if wp == VK_ESCAPE:
                self._end_edit(commit=False)
                return 0
            if wp == VK_TAB:
                self._end_edit(commit=True)
                return 0
        if msg == WM_CHAR and wp in (13, 27):
            self._end_edit(commit=(wp == 13))
            return 0
        if msg == WM_KILLFOCUS:
            self._end_edit(commit=True)
            return 0
        if self._edit_orig:
            return user32.CallWindowProcW(self._edit_orig, hwnd, msg, wp, lp)
        return user32.DefWindowProcW(hwnd, msg, wp, lp)

    def _set_item_text(self, item, subitem, text):
        if not self.hwnd:
            return
        entry = LVITEMW()
        entry.iSubItem = subitem
        entry.pszText = text
        SendMessagePtrW(self.hwnd, LVM_SETITEMTEXTW, item,
                        ctypes.addressof(entry))

    def _handle_notify(self, code, lp):
        if code == NM_DBLCLK:
            nm = ctypes.cast(lp, ctypes.POINTER(NMITEMACTIVATE)).contents
            hit = LVHITTESTINFO()
            hit.pt.x = nm.ptAction.x
            hit.pt.y = nm.ptAction.y
            item = SendMessagePtrW(self.hwnd, LVM_SUBITEMHITTEST, 0,
                                   ctypes.addressof(hit))
            if item >= 0:
                self.begin_edit(item, hit.iSubItem if hit.iSubItem >= 0 else 0)
            return
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
        if self._edit_hwnd:
            self._end_edit(commit=True)
        super()._on_bounds()
        if self.hwnd and self._app:
            self._rescale_columns(self._app)

