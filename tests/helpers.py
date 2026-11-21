"""Shared test fixtures for the pywinui widget test suite."""
import unittest
from contextlib import contextmanager

import pywinui as ui
import pywinui.app as pkg_app

# Keep automated tests deterministic: no high-DPI scaling.
pkg_app.get_window_dpi = lambda hwnd: 96
ui.user32.GetDpiForSystem = lambda: 96


@contextmanager
def memory_dc(width=400, height=300):
    """Yield a memory DC so drawing code can be exercised off-screen."""
    screen = ui.user32.GetDC(None)
    mdc = ui.gdi32.CreateCompatibleDC(screen)
    bmp = ui.gdi32.CreateCompatibleBitmap(screen, width, height)
    old = ui.gdi32.SelectObject(mdc, bmp)
    try:
        yield mdc
    finally:
        ui.gdi32.SelectObject(mdc, old)
        ui.gdi32.DeleteObject(bmp)
        ui.gdi32.DeleteDC(mdc)
        ui.user32.ReleaseDC(None, screen)


class WidgetTestCase(unittest.TestCase):
    """Headless tests for owner-drawn widgets."""

    def setUp(self):
        self.app = ui.App('pywinui unittest', 640, 480)
        self.app.root.set_bounds(0, 0, 640, 480)
        self.app.scale = 1.0
        self.app.style = dict(ui.AURORA)

    def tearDown(self):
        self.app.destroy()

    def add(self, widget, x=10, y=10, width=None, height=None):
        self.app.root.add(widget)
        mw, mh = widget.measure(self.app)
        widget.set_bounds(x, y,
                          width if width is not None else mw,
                          height if height is not None else mh)
        return widget

    def paint(self, widget, width=320, height=200):
        """Draw the widget into a memory DC to catch GDI/argument errors."""
        screen = ui.user32.GetDC(None)
        mdc = ui.gdi32.CreateCompatibleDC(screen)
        bmp = ui.gdi32.CreateCompatibleBitmap(screen, width, height)
        old = ui.gdi32.SelectObject(mdc, bmp)
        try:
            widget.draw(mdc, self.app)
        finally:
            ui.gdi32.SelectObject(mdc, old)
            ui.gdi32.DeleteObject(bmp)
            ui.gdi32.DeleteDC(mdc)
            ui.user32.ReleaseDC(None, screen)


class WindowTestCase(unittest.TestCase):
    """Tests that need a real hidden window (native Win32 controls)."""

    def setUp(self):
        self.app = ui.App('pywinui window unittest', 480, 360)

    def tearDown(self):
        self.app.destroy()

    def create(self):
        self.app.create(show=False)
        self.app.pump()
        return self.app

    def add(self, widget):
        """Add a widget to the live window and run the layout pass."""
        self.app.add(widget)
        self.app.layout()
        return widget
