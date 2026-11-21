"""Scrollable container with custom scrollbars."""

from .common import *  # noqa: F401,F403
from .native import _NativeWidget
from .style import style_of

# ============================================================================
# SCROLLVIEW
# ============================================================================
class ScrollView(Container):
    def __init__(self, padding=8, spacing=8, bg=(245, 245, 245)):
        super().__init__()
        self.padding = padding; self.spacing = spacing; self.bg = bg
        self.scroll_x = 0.0; self.scroll_y = 0.0
        self._content_w = 0; self._content_h = 0; self._app = None
        self._drag_axis = None; self._drag_start = 0
        self._drag_start_scroll = 0.0; self._sb_hovered = None
        self._native_clip = {}; self._wheel_delta = 0.0

    def _scale(self): return self._app.scale if self._app else 1.0
    def _sb_w(self): return int(12 * self._scale())
    def _has_vsb(self): return self._content_h + 2 * self.padding > self.h
    def _has_hsb(self):
        inner_w = self.w - (self._sb_w() if self._has_vsb() else 0)
        return self._content_w + 2 * self.padding > inner_w
    def _viewport_w(self): return self.w - (self._sb_w() if self._has_vsb() else 0)
    def _viewport_h(self): return self.h - (self._sb_w() if self._has_hsb() else 0)
    def _max_scroll_y(self): return max(0, self._content_h + 2 * self.padding - self._viewport_h())
    def _max_scroll_x(self): return max(0, self._content_w + 2 * self.padding - self._viewport_w())

    def measure(self, app): return (int(240 * app.scale), int(160 * app.scale))

    def arrange(self, app):
        self._app = app
        sizes = [c.measure(app) for c in self.children]
        self._content_w = max((w for w, _ in sizes), default=0)
        self._content_h = (max(0, sum(h + self.spacing for _, h in sizes) - self.spacing)
                           if sizes else 0)
        self.scroll_x = max(0.0, min(self.scroll_x, self._max_scroll_x()))
        self.scroll_y = max(0.0, min(self.scroll_y, self._max_scroll_y()))
        vw, vh = self._viewport_w(), self._viewport_h()
        inner_w = max(0, vw - 2 * self.padding)
        y_local = 0
        for c, (w_, h_) in zip(self.children, sizes):
            # Keep wide children at their natural width so horizontal
            # scrolling can reveal them; narrow ones fill the viewport.
            c.set_bounds(int(self.x + self.padding - self.scroll_x),
                         int(self.y + self.padding + y_local - self.scroll_y),
                         max(int(w_), inner_w), int(h_))
            y_local += h_ + self.spacing
            if hasattr(c, 'arrange'): c.arrange(app)
        self._clip_native_to_viewport()

    def _invalidate(self):
        if self._app:
            self._app.invalidate_rect(self.x, self.y, self.w, self.h)

    def _shift(self, w, dx, dy, moved):
        """Translate a widget subtree without re-running layout or measure."""
        if isinstance(w, _NativeWidget) and w.hwnd:
            old = (w.x, w.y, w.w, w.h)
            w.x += dx; w.y += dy
            moved.append((w.hwnd, old, (w.x, w.y, w.w, w.h)))
        else:
            w.x += dx; w.y += dy
        if isinstance(w, Container):
            for c in w.children:
                self._shift(c, dx, dy, moved)

    def _move_native(self, moved):
        """Move native children in one batch and repaint vacated strips."""
        if not moved:
            return
        flags = SWP_NOZORDER | SWP_NOREDRAW
        hdwp = user32.BeginDeferWindowPos(len(moved))
        if hdwp:
            for hwnd, old, new in moved:
                hdwp = user32.DeferWindowPos(hdwp, hwnd, None, new[0], new[1],
                                             new[2], new[3], flags)
                if not hdwp:
                    break
            if hdwp:
                user32.EndDeferWindowPos(hdwp)
            else:
                for hwnd, old, new in moved:
                    user32.SetWindowPos(hwnd, None, new[0], new[1],
                                        new[2], new[3], flags)
        else:
            for hwnd, old, new in moved:
                user32.SetWindowPos(hwnd, None, new[0], new[1],
                                    new[2], new[3], flags)
        for hwnd, old, new in moved:
            user32.InvalidateRect(hwnd, None, False)
            if self._app:
                ox, oy, ow, oh = old
                nx, ny, nw, nh = new
                dx, dy = nx - ox, ny - oy
                if dx > 0:
                    self._app.invalidate_rect(ox, oy, dx, oh)
                elif dx < 0:
                    self._app.invalidate_rect(ox + ow + dx, oy, -dx, oh)
                if dy > 0:
                    self._app.invalidate_rect(nx, oy, nw, dy)
                elif dy < 0:
                    self._app.invalidate_rect(nx, oy + oh + dy, nw, -dy)

    def _invalidate_scrollbars(self, dx, dy):
        if not self._app:
            return
        sw = self._sb_w()
        if dy and self._has_vsb():
            self._app.invalidate_rect(self.x + self.w - sw, self.y,
                                      sw, self._viewport_h())
        if dx and self._has_hsb():
            self._app.invalidate_rect(self.x, self.y + self.h - sw,
                                      self._viewport_w(), sw)
        if dx and dy and self._has_vsb() and self._has_hsb():
            self._app.invalidate_rect(self.x + self.w - sw,
                                      self.y + self.h - sw, sw, sw)
        radius = int(style_of(self._app).get('radius', 10) * self._app.scale)
        if radius > 0:
            for cx, cy in ((self.x, self.y),
                           (self.x + self.w - radius, self.y),
                           (self.x, self.y + self.h - radius),
                           (self.x + self.w - radius, self.y + self.h - radius)):
                self._app.invalidate_rect(cx, cy, radius, radius)

    def scroll_to(self, x, y):
        """Scroll to (x, y), translating children instead of re-laying out."""
        x = max(0.0, min(float(x), self._max_scroll_x()))
        y = max(0.0, min(float(y), self._max_scroll_y()))
        dx = (int(self.x + self.padding - x)
              - int(self.x + self.padding - self.scroll_x))
        dy = (int(self.y + self.padding - y)
              - int(self.y + self.padding - self.scroll_y))
        self.scroll_x, self.scroll_y = x, y
        if dx == 0 and dy == 0:
            return False
        scrolled = False
        large = (abs(dx) * 2 >= max(1, self._viewport_w())
                 or abs(dy) * 2 >= max(1, self._viewport_h()))
        if self._app and self._app.hwnd and not large:
            vp = wintypes.RECT(self.x, self.y,
                               self.x + self._viewport_w(),
                               self.y + self._viewport_h())
            scrolled = bool(user32.ScrollWindowEx(
                self._app.hwnd, dx, dy, ctypes.byref(vp), ctypes.byref(vp),
                None, None, SW_INVALIDATE))
        moved = []
        for c in self.children:
            self._shift(c, dx, dy, moved)
        self._move_native(moved)
        self._clip_native_to_viewport()
        if scrolled:
            self._invalidate_scrollbars(dx, dy)
        else:
            self._invalidate()
        return True

    def _clip_native_to_viewport(self):
        """Native HWNDs are flat children of the main window and are NOT clipped
        by our GDI viewport rectangle. We must:
          - hide them when fully outside the viewport, and
          - clip them with a window region when they only partially overlap the
            viewport, so they never spill past the ScrollView borders."""
        clip = (self.x, self.y,
                self.x + self._viewport_w(), self.y + self._viewport_h())

        def set_state(hwnd, state):
            if self._native_clip.get(hwnd) == state:
                return
            self._native_clip[hwnd] = state
            if state == 'hidden':
                user32.ShowWindow(hwnd, SW_HIDE)
            elif state == 'full':
                user32.SetWindowRgn(hwnd, None, True)
                user32.ShowWindow(hwnd, SW_SHOWNA)
                user32.InvalidateRect(hwnd, None, True)
            else:
                _, l, t, r, b = state
                rgn = gdi32.CreateRectRgn(l, t, r, b)
                # SetWindowRgn takes ownership of the region on success
                user32.SetWindowRgn(hwnd, rgn, True)
                user32.ShowWindow(hwnd, SW_SHOWNA)
                user32.InvalidateRect(hwnd, None, True)

        def walk(w, clip):
            cx1, cy1, cx2, cy2 = clip
            if isinstance(w, _NativeWidget) and w.hwnd:
                ix1 = max(w.x, cx1); iy1 = max(w.y, cy1)
                ix2 = min(w.x + w.w, cx2); iy2 = min(w.y + w.h, cy2)
                if ix2 <= ix1 or iy2 <= iy1:
                    set_state(w.hwnd, 'hidden')
                elif (w.x >= cx1 and w.y >= cy1
                      and w.x + w.w <= cx2 and w.y + w.h <= cy2):
                    set_state(w.hwnd, 'full')
                else:
                    set_state(w.hwnd, ('clip', ix1 - w.x, iy1 - w.y,
                                       ix2 - w.x, iy2 - w.y))
            if isinstance(w, Container):
                # Also clip descendants to their container (e.g. their row),
                # so a native control can never paint over a neighboring row.
                inner = (max(cx1, w.x), max(cy1, w.y),
                         min(cx2, w.x + w.w), min(cy2, w.y + w.h))
                for child in w.children:
                    walk(child, inner)
        walk(self, clip)

    def hit_test(self, x, y):
        if not self.visible: return None
        if not (self.x <= x < self.x + self.w and self.y <= y < self.y + self.h): return None
        if self._has_vsb() and x >= self.x + self.w - self._sb_w(): return self
        if self._has_hsb() and y >= self.y + self.h - self._sb_w(): return self
        if x >= self.x + self._viewport_w() or y >= self.y + self._viewport_h(): return self
        for c in reversed(self.children):
            r = c.hit_test(x, y)
            if r is not None: return r
        return self

    def on_mouse_down(self, x, y):
        if self._has_vsb() and x >= self.x + self.w - self._sb_w():
            self._drag_axis = 'y'; self._drag_start = y; self._drag_start_scroll = self.scroll_y
            if self._app: self._app.scrolling = True
            self._invalidate()
        elif self._has_hsb() and y >= self.y + self.h - self._sb_w():
            self._drag_axis = 'x'; self._drag_start = x; self._drag_start_scroll = self.scroll_x
            if self._app: self._app.scrolling = True
            self._invalidate()

    def on_mouse_up(self, x, y):
        if self._drag_axis:
            self._drag_axis = None
            if self._app: self._app.scrolling = False
            self._invalidate()

    def on_mouse_move(self, x, y):
        if self._drag_axis == 'y':
            content = self._content_h + 2 * self.padding; vh = self._viewport_h()
            th = max(int(20 * self._scale()), int(vh * vh / content))
            travel = vh - th
            if travel > 0:
                d = (y - self._drag_start) * self._max_scroll_y() / travel
                self.scroll_to(self.scroll_x, self._drag_start_scroll + d)
            return
        if self._drag_axis == 'x':
            content = self._content_w + 2 * self.padding; vw = self._viewport_w()
            tw = max(int(20 * self._scale()), int(vw * vw / content))
            travel = vw - tw
            if travel > 0:
                d = (x - self._drag_start) * self._max_scroll_x() / travel
                self.scroll_to(self._drag_start_scroll + d, self.scroll_y)
            return
        over = None
        if (self._has_vsb() and x >= self.x + self.w - self._sb_w()
                and self.x <= x < self.x + self.w and self.y <= y < self.y + self.h): over = 'y'
        elif (self._has_hsb() and y >= self.y + self.h - self._sb_w()
                and self.x <= x < self.x + self.w and self.y <= y < self.y + self.h): over = 'x'
        if over != self._sb_hovered:
            self._sb_hovered = over
            self._invalidate()

    def on_wheel(self, delta):
        if not (self._has_vsb() or self._has_hsb()): return False
        # Accumulate partial wheel deltas so high-resolution wheels and
        # touchpads scroll smoothly instead of in coarse 120-unit jumps.
        self._wheel_delta += delta
        notches = int(self._wheel_delta / 120)
        if not notches:
            return False
        self._wheel_delta -= notches * 120
        step = notches * int(60 * self._scale())
        shift = (user32.GetKeyState(VK_SHIFT) & 0x8000) != 0
        if shift and self._has_hsb():
            self.scroll_to(self.scroll_x - step, self.scroll_y)
        elif self._has_vsb():
            self.scroll_to(self.scroll_x, self.scroll_y - step)
        else:
            return False
        return True

    def draw(self, hdc, app):
        self._app = app
        st = style_of(app)
        s = app.scale
        radius = max(4, int(st.get('radius', 10) * s))
        saved = gdi32.SaveDC(hdc)
        rgn = gdi32.CreateRoundRectRgn(self.x, self.y, self.x + self.w + 1,
                                       self.y + self.h + 1, radius, radius)
        gdi32.ExtSelectClipRgn(hdc, rgn, RGN_AND)
        gdi32.DeleteObject(rgn)
        if self.bg is not None:
            rc = wintypes.RECT(self.x, self.y, self.x + self.w, self.y + self.h)
            user32.FillRect(hdc, ctypes.byref(rc), app.get_brush(self.bg))
        gdi32.IntersectClipRect(hdc, self.x, self.y,
                                self.x + self._viewport_w(), self.y + self._viewport_h())
        super().draw(hdc, app)
        gdi32.RestoreDC(hdc, saved)
        self._draw_scrollbars(hdc, app)
        stroke_round_rect(hdc, app, self.x, self.y, self.w, self.h, radius,
                          st['border'], max(1, int(s)))

    def _draw_scrollbars(self, hdc, app):
        s = app.scale
        sw = self._sb_w()
        st = style_of(app)
        track = st['panel']
        thumb = st['mid']
        thumb_hot = st['highlight']
        if self._has_vsb():
            sx = self.x + self.w - sw
            rc = wintypes.RECT(sx, self.y, sx + sw, self.y + self._viewport_h())
            user32.FillRect(hdc, ctypes.byref(rc), app.get_brush(track))
            content = self._content_h + 2 * self.padding; vh = self._viewport_h()
            th = max(int(24 * s), int(vh * vh / content))
            ty = self.y + (int((vh - th) * (self.scroll_y / self._max_scroll_y()))
                           if self._max_scroll_y() > 0 else 0)
            c = thumb_hot if (self._drag_axis == 'y' or self._sb_hovered == 'y') else thumb
            pad = max(2, int(3 * s)); rad = max(3, (sw - 2 * pad))
            fill_round_rect(hdc, app, sx + pad, ty + pad, sw - 2 * pad, th - 2 * pad, rad, c)
        if self._has_hsb():
            sy = self.y + self.h - sw; vw = self._viewport_w()
            rc = wintypes.RECT(self.x, sy, self.x + vw, sy + sw)
            user32.FillRect(hdc, ctypes.byref(rc), app.get_brush(track))
            content = self._content_w + 2 * self.padding
            tw = max(int(24 * s), int(vw * vw / content))
            tx = self.x + (int((vw - tw) * (self.scroll_x / self._max_scroll_x()))
                           if self._max_scroll_x() > 0 else 0)
            c = thumb_hot if (self._drag_axis == 'x' or self._sb_hovered == 'x') else thumb
            pad = max(2, int(3 * s)); rad = max(3, (sw - 2 * pad))
            fill_round_rect(hdc, app, tx + pad, sy + pad, tw - 2 * pad, sw - 2 * pad, rad, c)
        if self._has_vsb() and self._has_hsb():
            rc = wintypes.RECT(self.x + self.w - sw, self.y + self.h - sw,
                               self.x + self.w, self.y + self.h)
            user32.FillRect(hdc, ctypes.byref(rc), app.get_brush(track))

