"""Application object, window procedure and message loop."""

import itertools

from .common import *  # noqa: F401,F403
from .common import _SetWndPtr
from .layouts import VBoxLayout
from .panel import Panel
from .native import _NativeWidget
from .textbox import TextBox
from .checkbox import CheckBox
from .radio import RadioButton
from .combobox import ComboBox
from .listview import ListView
from .scrollview import ScrollView
from .menu import MenuBar
from .style import AURORA, style_of

# ============================================================================
# DOUBLE BUFFER
# ============================================================================
_class_ids = itertools.count(1)


class _DoubleBuffer:
    def __init__(self):
        self.mdc = None; self.bmp = None; self.old = None; self.w = 0; self.h = 0
    def ensure(self, hdc, w, h):
        if not self.mdc: self.mdc = gdi32.CreateCompatibleDC(hdc)
        if (w, h) != (self.w, self.h):
            if self.bmp:
                gdi32.SelectObject(self.mdc, self.old); gdi32.DeleteObject(self.bmp)
            self.bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
            self.old = gdi32.SelectObject(self.mdc, self.bmp)
            self.w, self.h = w, h
        return self.mdc
    def flush(self, hdc, x, y, w, h):
        gdi32.BitBlt(hdc, x, y, w, h, self.mdc, x, y, SRCCOPY)

# ============================================================================
# APP
# ============================================================================
class App:
    def __init__(self, title='App', width=800, height=600, bg=None):
        enable_dpi_awareness()
        self.hinstance = kernel32.GetModuleHandleW(None)
        self.title = title; self.width = width; self.height = height
        self.style = dict(AURORA)
        self.bg = bg if bg is not None else self.style['window']
        self.theme_fg = self.style['windowText']
        if is_dark(self.theme_fg):
            enable_dark_mode()
        self.root = Panel(layout=VBoxLayout(padding=12, spacing=8))
        self.hwnd = None; self.scale = 1.0
        self._next_cmd = 1000; self._next_ctrl = 2000
        self.menu_callbacks = {}; self.menubar = MenuBar(self)
        self.focused = None; self.hovered = None; self._captured = None
        self.scrolling = False
        self._db = _DoubleBuffer()
        self._font_cache = {}; self._brush_cache = {}; self._pen_cache = {}
        self._text_cache = {}
        self._ctl_brush = None
        self._base_brush = None
        self._paint_rgn = None
        self._timers = []; self._pending_timers = []
        self._class_name = f'PyWinUI_{id(self)}_{next(_class_ids)}'
        self._class_registered = False
        self._class_brush = None
        self._wndproc_ref = WNDPROC(self._wndproc)

    def add(self, w): return self.root.add(w)

    def get_font(self, size=14, bold=False, underline=False):
        key = (size, bold, underline)
        if key not in self._font_cache:
            px = max(6, int(size * self.scale))
            # ClearType quality (5) for crisp, modern text rendering
            self._font_cache[key] = gdi32.CreateFontW(
                -px, 0, 0, 0, FW_BOLD if bold else FW_NORMAL, 0,
                1 if underline else 0, 0,
                DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, 0, 'Segoe UI')
        return self._font_cache[key]

    def get_brush(self, rgb):
        if rgb not in self._brush_cache:
            self._brush_cache[rgb] = gdi32.CreateSolidBrush(COLORREF(*rgb))
        return self._brush_cache[rgb]

    def get_pen(self, rgb, width=1):
        key = (rgb, max(1, int(width)))
        if key not in self._pen_cache:
            self._pen_cache[key] = gdi32.CreatePen(0, key[1], COLORREF(*rgb))
        return self._pen_cache[key]

    def measure_text(self, text, size=14, bold=False):
        key = (text, size, bold, self.scale)
        cached = self._text_cache.get(key)
        if cached is not None:
            return cached
        if self.hwnd: hdc = user32.GetDC(self.hwnd)
        else: hdc = gdi32.CreateCompatibleDC(None)
        of = gdi32.SelectObject(hdc, self.get_font(size, bold))
        sz = wintypes.SIZE()
        gdi32.GetTextExtentPoint32W(hdc, text, len(text), ctypes.byref(sz))
        gdi32.SelectObject(hdc, of)
        if self.hwnd: user32.ReleaseDC(self.hwnd, hdc)
        else: gdi32.DeleteDC(hdc)
        self._text_cache[key] = (sz.cx, sz.cy)
        return sz.cx, sz.cy

    def invalidate(self):
        if self.hwnd: user32.InvalidateRect(self.hwnd, None, False)

    def invalidate_rect(self, x, y, w, h):
        """Invalidate only a rectangle, so scrolling repaints just its area."""
        if self.hwnd:
            rc = wintypes.RECT(int(x), int(y), int(x + w), int(y + h))
            user32.InvalidateRect(self.hwnd, ctypes.byref(rc), False)

    def focus(self, widget):
        self._set_focus(widget)

    def click_widget(self, widget):
        return self.click(widget.x + widget.w // 2, widget.y + widget.h // 2)

    def click(self, x, y):
        """Inject a full click at client coordinates (x, y)."""
        hit = self.root.hit_test(x, y)
        if hit is None:
            self._set_focus(None)
            return None
        if isinstance(hit, _NativeWidget):
            if hit.focusable:
                self._set_focus(hit)
            hit.click()
            return hit
        self._captured = hit
        if self.hwnd:
            user32.SetCapture(self.hwnd)
        hit.on_mouse_down(x, y)
        if hit.focusable:
            self._set_focus(hit)
        else:
            self._set_focus(None)
        hit.on_mouse_up(x, y)
        self._captured = None
        if self.hwnd:
            user32.ReleaseCapture()
        self.invalidate()
        return hit

    def move_mouse(self, x, y):
        """Inject a mouse move, updating hover state and drag targets."""
        if self._captured:
            self._captured.on_mouse_move(x, y)
            return
        hit = self.root.hit_test(x, y)
        if hit is not self.hovered:
            if self.hovered:
                self.hovered.hovered = False
            self.hovered = hit
            if hit:
                hit.hovered = True
            self.invalidate()
        if hit:
            hit.on_mouse_move(x, y)

    def wheel(self, delta, x=None, y=None):
        """Inject a wheel event; scrolls the nearest ScrollView ancestor."""
        w = self.focused if (x is None or y is None) else self.root.hit_test(x, y)
        while w is not None and not w.on_wheel(delta):
            w = w.parent
        return w is not None

    def press_key(self, vk):
        """Inject a key press into the focused widget (or cycle focus on Tab)."""
        if vk == VK_TAB:
            self._cycle_focus(reverse=(user32.GetKeyState(VK_SHIFT) & 0x8000) != 0)
            self.invalidate()
            return
        w = self.focused
        if w is None:
            return
        if isinstance(w, _NativeWidget) and w.hwnd:
            user32.SendMessageW(w.hwnd, WM_KEYDOWN, vk, 0)
        else:
            w.on_key(vk, None)
        self.invalidate()

    def type_char(self, ch):
        """Inject a character into the focused widget."""
        w = self.focused
        if w is None:
            return
        code = ord(ch) if isinstance(ch, str) else int(ch)
        if isinstance(w, _NativeWidget) and w.hwnd:
            user32.SendMessageW(w.hwnd, WM_CHAR, code, 0)
        else:
            w.on_key(None, code)
        self.invalidate()

    def set_timer(self, ms, callback):
        tid = len(self._timers) + 1; self._timers.append(callback)
        if self.hwnd: user32.SetTimer(self.hwnd, tid, ms, None)
        else: self._pending_timers.append((tid, ms))
        return tid

    def refresh_theme(self):
        self._ctl_brush = None
        self._base_brush = None
        if is_dark(self.style['windowText']):
            enable_dark_mode()
        self.invalidate()
        # Force native controls to repaint with the new theme color
        for w in self.root.all_widgets():
            if isinstance(w, ListView):
                w._apply_theme(self)
            if isinstance(w, _NativeWidget) and w.hwnd:
                w._apply_window_theme(self)
                user32.InvalidateRect(w.hwnd, None, True)

    def _set_focus(self, widget, _from_native=False):
        if self.focused is widget and not _from_native: return
        if self.focused and self.focused is not widget: self.focused.focused = False
        self.focused = widget
        if widget is None:
            if not _from_native: user32.SetFocus(self.hwnd)
            self.invalidate(); return
        widget.focused = True
        if not _from_native:
            if isinstance(widget, _NativeWidget) and widget.hwnd: user32.SetFocus(widget.hwnd)
            else: user32.SetFocus(self.hwnd)
        self.invalidate()

    def _cycle_focus(self, reverse=False):
        ws = [w for w in self.root.all_widgets() if w.focusable and w.visible]
        if not ws: return
        if self.focused in ws:
            i = ws.index(self.focused)
            i = (i - 1) % len(ws) if reverse else (i + 1) % len(ws)
        else: i = -1 if reverse else 0
        self._set_focus(ws[i])

    def _refresh_fonts(self):
        for w in self.root.all_widgets():
            hwnd = getattr(w, 'hwnd', None)
            if isinstance(w, TextBox) and hwnd:
                text = w.get_text()
                sel = user32.SendMessageW(w.hwnd, EM_GETSEL, 0, 0); start = sel & 0xFFFF
                user32.SendMessageW(w.hwnd, WM_SETFONT, self.get_font(w.font_size), 1)
                user32.SetWindowTextW(w.hwnd, text)
                user32.SendMessageW(w.hwnd, EM_SETSEL, start, start)
            elif isinstance(w, CheckBox) and hwnd:
                user32.SendMessageW(w.hwnd, WM_SETFONT, self.get_font(w.font_size), 1)
            elif isinstance(w, RadioButton) and hwnd:
                user32.SendMessageW(w.hwnd, WM_SETFONT, self.get_font(w.font_size), 1)
            elif isinstance(w, ComboBox) and hwnd:
                user32.SendMessageW(w.hwnd, WM_SETFONT, self.get_font(w.font_size), 1); w._on_bounds()
            elif isinstance(w, ListView) and hwnd:
                user32.SendMessageW(w.hwnd, WM_SETFONT, self.get_font(w.font_size), 1)
                w._rescale_columns(self)

    def _install_subclass(self, w):
        if not w.hwnd or getattr(w, '_subclassed', False): return
        w._sub_wndproc = WNDPROC(lambda hwnd, msg, wp, lp: self._sub_wndproc(w, hwnd, msg, wp, lp))
        w._orig_wndproc = _SetWndPtr(w.hwnd, GWLP_WNDPROC, ctypes.cast(w._sub_wndproc, ctypes.c_void_p))
        w._subclassed = True

    def _sub_wndproc(self, w, hwnd, msg, wp, lp):
        if msg == WM_KEYDOWN and wp == VK_TAB:
            self._cycle_focus(reverse=(user32.GetKeyState(VK_SHIFT) & 0x8000) != 0); return 0
        if msg == WM_SETFOCUS: self._set_focus(w, _from_native=True)
        if msg == WM_NOTIFY and isinstance(w, ListView):
            hdr = ctypes.cast(lp, ctypes.POINTER(NMHDR)).contents
            if (ctypes.c_int(hdr.code).value == NM_CUSTOMDRAW
                    and hdr.hwndFrom == w._header_hwnd):
                return w._draw_header(lp)
        if msg == WM_ERASEBKGND and isinstance(w, ListView):
            rc = wintypes.RECT()
            user32.GetClientRect(hwnd, ctypes.byref(rc))
            user32.FillRect(wp, ctypes.byref(rc),
                            self.get_brush(style_of(self)['base']))
            return 1
        if msg == WM_MOUSEWHEEL:
            # Forward the wheel to the nearest ScrollView ancestor so scrolling
            # works even when the pointer is over a native child control.
            delta = ctypes.c_short((wp >> 16) & 0xFFFF).value
            anc = w.parent
            while anc is not None:
                if isinstance(anc, ScrollView):
                    if anc.on_wheel(delta):
                        return 0
                    break
                anc = anc.parent
        return user32.CallWindowProcW(w._orig_wndproc, hwnd, msg, wp, lp)

    def _register_class(self):
        if self._class_registered:
            return
        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wc.style = CS_HREDRAW | CS_VREDRAW
        wc.lpfnWndProc = self._wndproc_ref
        wc.hInstance = self.hinstance
        wc.hCursor = user32.LoadCursorW(None, IDC_ARROW)
        self._class_brush = gdi32.CreateSolidBrush(COLORREF(*self.bg))
        wc.hbrBackground = self._class_brush
        wc.lpszClassName = self._class_name
        if not user32.RegisterClassExW(ctypes.byref(wc)):
            raise OSError(ctypes.get_last_error(), "RegisterClassExW")
        self._class_registered = True

    def _wndproc(self, hwnd, msg, wp, lp):
        try: return self._handle(hwnd, msg, wp, lp)
        except Exception:
            traceback.print_exc()
            return user32.DefWindowProcW(hwnd, msg, wp, lp)

    def _realize_all(self):
        for w in self.root.all_widgets():
            if hasattr(w, 'realize') and w.parent is not None:
                w.realize(self.hwnd, self.hinstance, self)
                if isinstance(w, _NativeWidget): self._install_subclass(w)
        # After HWNDs exist, (re)apply ScrollView clipping so native children
        # never spill past the viewport borders.
        for w in self.root.all_widgets():
            if isinstance(w, ScrollView):
                w._clip_native_to_viewport()

    def _find_native_by_hwnd(self, hwnd):
        for w in self.root.all_widgets():
            if isinstance(w, _NativeWidget) and w.hwnd == hwnd: return w
        return None

    def _handle(self, hwnd, msg, wp, lp):
        if msg == WM_CREATE:
            self.scale = get_window_dpi(hwnd) / 96.0
            self._font_cache.clear(); self._text_cache.clear(); return 0

        if msg == WM_DPICHANGED:
            self.scale = (wp & 0xFFFF) / 96.0
            self._font_cache.clear()
            self._text_cache.clear()
            r = ctypes.cast(lp, ctypes.POINTER(wintypes.RECT)).contents
            user32.SetWindowPos(hwnd, None, r.left, r.top, r.right - r.left, r.bottom - r.top,
                                SWP_NOZORDER | SWP_NOACTIVATE)
            self._refresh_fonts()
            user32.InvalidateRect(hwnd, None, False); return 0

        if msg == WM_SIZE:
            w = lp & 0xFFFF; h = (lp >> 16) & 0xFFFF
            self.root.set_bounds(0, 0, w, h); self.root.arrange(self); self._realize_all()
            user32.InvalidateRect(hwnd, None, False); return 0

        if msg == WM_ERASEBKGND: return 1

        if msg == WM_PAINT:
            hrgn = gdi32.CreateRectRgn(0, 0, 0, 0)
            update_kind = user32.GetUpdateRgn(hwnd, hrgn, False)
            ps = PAINTSTRUCT(); hdc = user32.BeginPaint(hwnd, ctypes.byref(ps))
            rc = ps.rcPaint
            w, h = rc.right - rc.left, rc.bottom - rc.top
            if w > 0 and h > 0:
                cr = wintypes.RECT(); user32.GetClientRect(hwnd, ctypes.byref(cr))
                mdc = self._db.ensure(hdc, cr.right, cr.bottom)
                saved = gdi32.SaveDC(mdc)
                if update_kind != 0:
                    gdi32.ExtSelectClipRgn(mdc, hrgn, RGN_AND)
                else:
                    gdi32.IntersectClipRect(mdc, rc.left, rc.top, rc.right, rc.bottom)
                user32.FillRect(mdc, ctypes.byref(rc), self.get_brush(self.bg))
                self._paint_rgn = hrgn if update_kind != 0 else None
                try:
                    self.root.draw(mdc, self)
                finally:
                    self._paint_rgn = None
                gdi32.RestoreDC(mdc, saved)
                self._db.flush(hdc, rc.left, rc.top, w, h)
            user32.EndPaint(hwnd, ctypes.byref(ps))
            gdi32.DeleteObject(hrgn)
            return 0

        if msg in (WM_MOUSEMOVE, WM_LBUTTONDOWN, WM_LBUTTONUP):
            x = ctypes.c_short(lp & 0xFFFF).value
            y = ctypes.c_short((lp >> 16) & 0xFFFF).value
            if msg == WM_MOUSEMOVE:
                if self._captured: self._captured.on_mouse_move(x, y); return 0
                hit = self.root.hit_test(x, y)
                if hit is not self.hovered:
                    if self.hovered: self.hovered.hovered = False
                    self.hovered = hit
                    if hit: hit.hovered = True
                    user32.InvalidateRect(hwnd, None, False)
                if hit: hit.on_mouse_move(x, y)
                return 0
            if msg == WM_LBUTTONDOWN:
                hit = self.root.hit_test(x, y)
                if hit:
                    self._captured = hit; user32.SetCapture(hwnd); hit.on_mouse_down(x, y)
                    if hit.focusable: self._set_focus(hit)
                    else: self._set_focus(None)
                else: self._set_focus(None)
                user32.InvalidateRect(hwnd, None, False); return 0
            if msg == WM_LBUTTONUP:
                target = self._captured; self._captured = None; user32.ReleaseCapture()
                if target: target.on_mouse_up(x, y)
                user32.InvalidateRect(hwnd, None, False); return 0

        if msg == WM_MOUSEWHEEL:
            delta = ctypes.c_short((wp >> 16) & 0xFFFF).value
            pt = wintypes.POINT(ctypes.c_short(lp & 0xFFFF).value,
                                ctypes.c_short((lp >> 16) & 0xFFFF).value)
            user32.ScreenToClient(hwnd, ctypes.byref(pt))
            w = self.root.hit_test(pt.x, pt.y)
            while w is not None and not w.on_wheel(delta): w = w.parent
            return 0

        if msg == WM_KEYDOWN:
            if wp == VK_TAB:
                self._cycle_focus(reverse=(user32.GetKeyState(VK_SHIFT) & 0x8000) != 0)
                user32.InvalidateRect(hwnd, None, False); return 0
            if self.focused and not isinstance(self.focused, _NativeWidget):
                self.focused.on_key(wp, None); return 0

        if msg == WM_CHAR:
            if wp in (0x09, 0x0D): return 0
            if self.focused and not isinstance(self.focused, _NativeWidget):
                self.focused.on_key(None, wp); return 0

        if msg == WM_NOTIFY:
            hdr = ctypes.cast(lp, ctypes.POINTER(NMHDR)).contents
            w = self._find_native_by_hwnd(hdr.hwndFrom)
            if isinstance(w, ListView):
                code = ctypes.c_int(hdr.code).value
                if code == NM_CUSTOMDRAW:
                    return w._draw_list(lp)
                w._handle_notify(code, lp)
            return 0

        if msg == WM_COMMAND:
            ctrl = wp & 0xFFFF
            notify = (wp >> 16) & 0xFFFF
            ctl_hwnd = lp
            # Notifications from native controls carry the control HWND in lParam
            if ctl_hwnd:
                w = self._find_native_by_hwnd(ctl_hwnd)
                if isinstance(w, TextBox) and notify == EN_CHANGE and w.on_change:
                    w.on_change(w.get_text())
                elif isinstance(w, CheckBox) and notify == BN_CLICKED and w.on_change:
                    w.on_change(w.is_checked())
                elif isinstance(w, RadioButton) and notify == BN_CLICKED and w.on_change:
                    w.on_change(w.is_checked())
                elif isinstance(w, ComboBox) and notify == CBN_SELCHANGE and w.on_change:
                    w.on_change(w.current_index(), w.current_text())
                return 0
            # Menu commands have lParam == 0
            cb = self.menu_callbacks.get(ctrl)
            if cb: cb()
            return 0

        if msg == WM_MEASUREITEM:
            mis = ctypes.cast(lp, ctypes.POINTER(MEASUREITEMSTRUCT)).contents
            if mis.CtlType == ODT_COMBOBOX:
                mis.itemHeight = max(18, int(24 * self.scale))
                return 1

        if msg == WM_DRAWITEM:
            dis = ctypes.cast(lp, ctypes.POINTER(DRAWITEMSTRUCT)).contents
            if dis.CtlType == ODT_COMBOBOX:
                w = self._find_native_by_hwnd(dis.hwndItem)
                if isinstance(w, ComboBox):
                    w._draw_item(dis)
                    return 1

        if msg == WM_TIMER:
            tid = wp
            if 1 <= tid <= len(self._timers):
                try: self._timers[tid - 1]()
                except Exception:
                    traceback.print_exc()
            return 0

        if msg in (WM_CTLCOLORSTATIC, WM_CTLCOLORBTN, WM_CTLCOLORLISTBOX, WM_CTLCOLOREDIT):
            st = style_of(self)
            gdi32.SetBkMode(wp, TRANSPARENT)
            gdi32.SetTextColor(wp, COLORREF(*st['windowText']))
            if msg in (WM_CTLCOLOREDIT, WM_CTLCOLORLISTBOX):
                gdi32.SetBkColor(wp, COLORREF(*st['base']))
                if not self._base_brush:
                    self._base_brush = gdi32.CreateSolidBrush(COLORREF(*st['base']))
                return self._base_brush
            # The closed part of a combo box also reports as a static control.
            w = self._find_native_by_hwnd(lp) if lp else None
            if isinstance(w, ComboBox):
                gdi32.SetBkColor(wp, COLORREF(*st['base']))
                if not self._base_brush:
                    self._base_brush = gdi32.CreateSolidBrush(COLORREF(*st['base']))
                return self._base_brush
            gdi32.SetBkColor(wp, COLORREF(*st['window']))
            if not self._ctl_brush:
                self._ctl_brush = gdi32.CreateSolidBrush(COLORREF(*st['window']))
            return self._ctl_brush

        if msg == WM_DESTROY:
            user32.PostQuitMessage(0); return 0

        return user32.DefWindowProcW(hwnd, msg, wp, lp)

    def layout(self):
        """Re-run layout and realize native children for the current client."""
        if not self.hwnd:
            return
        cr = wintypes.RECT()
        user32.GetClientRect(self.hwnd, ctypes.byref(cr))
        self.root.set_bounds(0, 0, cr.right, cr.bottom)
        self.root.arrange(self)
        self._realize_all()
        self.invalidate()

    def create(self, show=True):
        """Create the window without entering the message loop.

        ``show=False`` keeps it hidden, which is useful for automated tests.
        """
        if self.hwnd:
            return self.hwnd
        init_common_controls()
        self._register_class()
        # Scale the initial size to the system DPI so the window is
        # self.width x self.height DIPs, then clamp it to the monitor work
        # area so it always fits on screen (important on high-DPI displays).
        try: sys_dpi = user32.GetDpiForSystem() or 96
        except (AttributeError, OSError): sys_dpi = 96
        ww = int(self.width * sys_dpi / 96); wh = int(self.height * sys_dpi / 96)
        work = wintypes.RECT()
        if not user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(work), 0):
            work = wintypes.RECT(0, 0, user32.GetSystemMetrics(0),
                                 user32.GetSystemMetrics(1))
        work_w = max(320, work.right - work.left)
        work_h = max(240, work.bottom - work.top)
        ww = min(ww, work_w); wh = min(wh, work_h)
        wx = work.left + max(0, (work_w - ww) // 2)
        wy = work.top + max(0, (work_h - wh) // 2)
        self.hwnd = user32.CreateWindowExW(
            0, self._class_name, self.title, WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN,
            wx, wy, ww, wh,
            None, None, self.hinstance, None)
        if not self.hwnd: raise OSError(ctypes.get_last_error(), "CreateWindowExW")
        if is_dark(style_of(self)['windowText']):
            allow_dark_window(self.hwnd)
            uxtheme.SetWindowTheme(self.hwnd, 'DarkMode_Explorer', None)
            set_dark_title_bar(self.hwnd, self.style['window'],
                               self.style['windowText'])
        user32.SetMenu(self.hwnd, self.menubar.hmenu)
        if is_dark(style_of(self)['windowText']):
            flush_menu_themes()
        if show:
            user32.ShowWindow(self.hwnd, SW_SHOW)
            user32.UpdateWindow(self.hwnd)
            if is_dark(style_of(self)['windowText']):
                set_dark_title_bar(self.hwnd, self.style['window'],
                                   self.style['windowText'])
        for tid, ms in self._pending_timers: user32.SetTimer(self.hwnd, tid, ms, None)
        self._pending_timers.clear()
        self.layout()
        self.pump()
        return self.hwnd

    def pump(self):
        """Process all pending messages without blocking (useful for tests)."""
        m = MSG()
        while user32.PeekMessageW(ctypes.byref(m), None, 0, 0, PM_REMOVE):
            if m.message == WM_QUIT:
                break
            user32.TranslateMessage(ctypes.byref(m))
            user32.DispatchMessageW(ctypes.byref(m))

    def destroy(self):
        """Close the window and pump until it is gone."""
        if self.hwnd:
            hwnd = self.hwnd
            user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
            for _ in range(100):
                self.pump()
                if not user32.IsWindow(hwnd):
                    break
            self.hwnd = None
        if self._class_registered:
            user32.UnregisterClassW(self._class_name, self.hinstance)
            self._class_registered = False
        if self._class_brush:
            gdi32.DeleteObject(self._class_brush)
            self._class_brush = None

    def run(self):
        self.create()
        m = MSG()
        while True:
            r = user32.GetMessageW(ctypes.byref(m), None, 0, 0)
            if r == 0: break
            if r == -1: raise OSError(ctypes.get_last_error(), "GetMessageW")
            user32.TranslateMessage(ctypes.byref(m))
            user32.DispatchMessageW(ctypes.byref(m))