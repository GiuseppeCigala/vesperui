"""Render the VesperUI showcases to PNG files for the documentation.

Usage (from the repository root, on Windows):

    python tools/capture_screenshots.py

The script builds each showcase without showing a window, paints it into an
off-screen bitmap, composites the native Win32 controls and writes scaled PNGs
to ``docs/images/``. It is intentionally dependency-light: Pillow is used only
for saving the bitmap as PNG.
"""
import ctypes
import os
import sys
import time
from ctypes import wintypes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import vesperui as ui
import vesperui.app as pkg_app

# Keep screenshots deterministic and small: force 96 DPI before any window is
# created, mirroring the test helpers.
pkg_app.get_window_dpi = lambda hwnd: 96
ui.user32.GetDpiForSystem = lambda: 96

import showcase_audio
import showcase_common

from PIL import Image, ImageChops

WM_PRINT = 0x0317
PRF_NONCLIENT = 0x0002
PRF_CLIENT = 0x0004
PRF_ERASEBKGND = 0x0008
PRF_CHILDREN = 0x0010

BI_RGB = 0
DIB_RGB_COLORS = 0

SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER),
                ("bmiColors", wintypes.DWORD * 3)]


# This module is a development tool, so declare the couple of GDI signatures
# it needs without touching the library's shared bindings.
ui.gdi32.GetDIBits.argtypes = [
    wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT,
    ctypes.c_void_p, ctypes.POINTER(BITMAPINFO), wintypes.UINT,
]
ui.gdi32.GetDIBits.restype = ctypes.c_int
ui.gdi32.SetViewportOrgEx.argtypes = [
    wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_void_p,
]
ui.gdi32.SetViewportOrgEx.restype = wintypes.BOOL


def _ancestor_clip(widget, root_w, root_h):
    """Intersect the widget with its ancestors, honouring ScrollView viewports."""
    left, top = widget.x, widget.y
    right, bottom = widget.x + widget.w, widget.y + widget.h
    parent = widget.parent
    while parent is not None:
        if hasattr(parent, "_viewport_w") and hasattr(parent, "_viewport_h"):
            p_left, p_top = parent.x, parent.y
            p_right = parent.x + parent._viewport_w()
            p_bottom = parent.y + parent._viewport_h()
        else:
            p_left, p_top = parent.x, parent.y
            p_right = parent.x + parent.w
            p_bottom = parent.y + parent.h
        left, top = max(left, p_left), max(top, p_top)
        right, bottom = min(right, p_right), min(bottom, p_bottom)
        parent = parent.parent
    left, top = max(0, left), max(0, top)
    right, bottom = min(root_w, right), min(root_h, bottom)
    return left, top, right, bottom


def _print_combo_text(hdc, app, widget, inset):
    """Draw the selected label of an owner-drawn ComboBox into the print DC."""
    text = widget.current_text()
    if not text:
        return
    style = ui.style_of(app)
    field_w = max(1, widget.w - 2 * inset - int(30 * app.scale))
    field_h = max(1, widget.h - 2 * inset)
    saved = ui.gdi32.SaveDC(hdc)
    try:
        ui.fill_gradient_v(hdc, 0, 0, field_w, field_h,
                           ui.lighten(style["base"], 0.03), style["base"])
        pad = max(4, int(6 * app.scale))
        text_rc = wintypes.RECT(pad, 0, max(pad, field_w - pad), field_h)
        ui.gdi32.SetBkMode(hdc, ui.TRANSPARENT)
        ui.gdi32.SetTextColor(hdc, ui.COLORREF(*style["windowText"]))
        font = ui.gdi32.SelectObject(hdc, app.get_font(widget.font_size))
        ui.user32.DrawTextW(hdc, text, -1, ctypes.byref(text_rc),
                            ui.DT_LEFT | ui.DT_VCENTER | ui.DT_SINGLELINE)
        ui.gdi32.SelectObject(hdc, font)
    finally:
        ui.gdi32.RestoreDC(hdc, saved)


def _print_native_controls(hdc, app, width, height):
    """Composite native child controls into the off-screen bitmap."""
    for widget in app.root.all_widgets():
        hwnd = getattr(widget, "hwnd", None)
        if not hwnd:
            continue
        inset = widget._inset_px()
        left, top, right, bottom = _ancestor_clip(widget, width, height)
        if right <= left or bottom <= top:
            continue
        x, y = widget.x + inset, widget.y + inset
        saved = ui.gdi32.SaveDC(hdc)
        try:
            ui.gdi32.SetViewportOrgEx(hdc, x, y, None)
            ui.gdi32.IntersectClipRect(hdc, left - x, top - y,
                                       right - x, bottom - y)
            ui.user32.SendMessageW(
                hwnd, WM_PRINT, hdc,
                PRF_NONCLIENT | PRF_CLIENT | PRF_ERASEBKGND | PRF_CHILDREN)
            if isinstance(widget, ui.ComboBox):
                _print_combo_text(hdc, app, widget, inset)
        finally:
            ui.gdi32.RestoreDC(hdc, saved)


def _bitmap_image(hdc, bmp, width, height):
    info = BITMAPINFO()
    info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    info.bmiHeader.biWidth = width
    info.bmiHeader.biHeight = -height       # top-down rows
    info.bmiHeader.biPlanes = 1
    info.bmiHeader.biBitCount = 32
    info.bmiHeader.biCompression = BI_RGB
    buf = ctypes.create_string_buffer(width * height * 4)
    copied = ui.gdi32.GetDIBits(hdc, bmp, 0, height, ctypes.byref(buf),
                                ctypes.byref(info), DIB_RGB_COLORS)
    if copied != height:
        raise OSError("GetDIBits failed (copied %d of %d rows)"
                      % (copied, height))
    image = Image.frombuffer("RGB", (width, height), buf, "raw", "BGRX", 0, 1)
    return image.copy()


def _force_client_size(app, width, height):
    """Resize the hidden window so its client area matches the design size."""
    outer = wintypes.RECT()
    client = wintypes.RECT()
    ui.user32.GetWindowRect(app.hwnd, ctypes.byref(outer))
    ui.user32.GetClientRect(app.hwnd, ctypes.byref(client))
    frame_w = (outer.right - outer.left) - client.right
    frame_h = (outer.bottom - outer.top) - client.bottom
    ui.user32.SetWindowPos(app.hwnd, None, 0, 0, width + frame_w,
                           height + frame_h,
                           SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE)
    app.layout()


def _trim_bottom(image, bg, padding=18):
    """Crop empty background rows below the content, keeping the full width."""
    reference = Image.new("RGB", image.size, bg)
    diff = ImageChops.difference(image, reference).convert("L")
    bbox = diff.point(lambda value: 255 if value > 3 else 0).getbbox()
    if not bbox:
        return image
    bottom = min(image.height, bbox[3] + padding)
    return image.crop((0, 0, image.width, bottom))


def capture(app, path, max_width=1400, trim=False):
    app.create(show=False)
    _force_client_size(app, app.width, app.height)
    # Let timers run so animated widgets (spectrum, meters) show real data.
    for _ in range(3):
        time.sleep(0.08)
        app.pump()

    background = app.bg
    width = max(1, app.root.w)
    height = max(1, app.root.h)
    screen = ui.user32.GetDC(None)
    mdc = ui.gdi32.CreateCompatibleDC(screen)
    bmp = ui.gdi32.CreateCompatibleBitmap(screen, width, height)
    old = ui.gdi32.SelectObject(mdc, bmp)
    try:
        rc = wintypes.RECT(0, 0, width, height)
        ui.user32.FillRect(mdc, ctypes.byref(rc), app.get_brush(app.bg))
        app.root.draw(mdc, app)
        _print_native_controls(mdc, app, width, height)
        image = _bitmap_image(mdc, bmp, width, height)
    finally:
        ui.gdi32.SelectObject(mdc, old)
        ui.gdi32.DeleteObject(bmp)
        ui.gdi32.DeleteDC(mdc)
        ui.user32.ReleaseDC(None, screen)
        app.destroy()

    if image.width > max_width:
        ratio = max_width / image.width
        image = image.resize((max_width, round(image.height * ratio)),
                             Image.Resampling.LANCZOS)
    if trim:
        image = _trim_bottom(image, background)
    image.save(path, "PNG", optimize=True)
    print("%s (%dx%d)" % (path, image.width, image.height))


def main():
    out_dir = os.path.join(ROOT, "docs", "images")
    os.makedirs(out_dir, exist_ok=True)
    capture(showcase_common.build_app(),
            os.path.join(out_dir, "showcase-common.png"))
    capture(showcase_audio.build_app(),
            os.path.join(out_dir, "showcase-audio.png"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
