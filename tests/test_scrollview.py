import vesperui as ui
from tests.helpers import WidgetTestCase, WindowTestCase


class FixedRow(ui.Panel):
    """Deterministic ScrollView child whose size does not depend on text."""

    def __init__(self, width=200, height=30):
        super().__init__()
        self._size = (width, height)

    def measure(self, app):
        return self._size


class ScrollViewLayoutTests(WidgetTestCase):
    def _make(self, rows=10, width=300, height=150):
        view = ui.ScrollView(padding=8, spacing=8)
        for _ in range(rows):
            view.add(FixedRow())
        view.set_bounds(10, 10, width, height)
        view.arrange(self.app)
        return view

    def test_content_size_and_vertical_scrollbar(self):
        view = self._make()
        self.assertEqual(view._content_h, 10 * 30 + 9 * 8)
        self.assertEqual(view._content_w, 200)
        self.assertTrue(view._has_vsb())
        self.assertFalse(view._has_hsb())

    def test_fitting_content_has_no_scrollbars(self):
        view = ui.ScrollView(padding=8, spacing=8)
        view.add(FixedRow(height=30))
        view.set_bounds(10, 10, 300, 200)
        view.arrange(self.app)
        self.assertFalse(view._has_vsb())
        self.assertFalse(view._has_hsb())

    def test_scroll_to_clamps_to_bounds(self):
        view = self._make()
        max_y = view._max_scroll_y()
        self.assertGreater(max_y, 0)

        view.scroll_to(0, 10 ** 6)
        self.assertEqual(view.scroll_y, max_y)

        view.scroll_to(-100, -100)
        self.assertEqual((view.scroll_x, view.scroll_y), (0.0, 0.0))
        self.assertEqual(view.children[0].y, 10 + 8)

    def test_scroll_translates_children(self):
        view = self._make()
        before = view.children[1].y
        view.scroll_to(0, 50)
        self.assertEqual(view.children[1].y, before - 50)
        self.assertEqual(view.children[0].y, 10 + 8 - 50)

    def test_wheel_scrolls_and_buffers_partial_deltas(self):
        view = self._make()
        self.assertTrue(view.on_wheel(-120))
        self.assertEqual(view.scroll_y, 60)
        self.assertTrue(view.on_wheel(120))
        self.assertEqual(view.scroll_y, 0)

        self.assertFalse(view.on_wheel(-60))
        self.assertEqual(view.scroll_y, 0)
        self.assertTrue(view.on_wheel(-60))
        self.assertEqual(view.scroll_y, 60)

    def test_wide_content_enables_horizontal_scrollbar(self):
        view = ui.ScrollView(padding=8, spacing=8)
        view.add(FixedRow(width=480, height=40))
        view.set_bounds(10, 10, 300, 200)
        view.arrange(self.app)

        self.assertTrue(view._has_hsb())
        max_x = view._max_scroll_x()
        self.assertGreater(max_x, 0)

        view.scroll_to(10 ** 6, 0)
        self.assertEqual(view.scroll_x, max_x)
        self.assertLess(view.children[0].x, 10)


class ScrollViewNativeTests(WindowTestCase):
    def _make(self, rows=12):
        app = self.create()
        app.root.layout = None
        view = ui.ScrollView(padding=8, spacing=8)
        app.root.add(view)
        view.set_bounds(10, 10, 300, 200)
        boxes = [ui.TextBox('row %d' % i) for i in range(rows)]
        for box in boxes:
            view.add(box)
        app.layout()
        return view, boxes

    def _visible(self, hwnd):
        return bool(ui.user32.GetWindowLongW(hwnd, ui.GWL_STYLE) & ui.WS_VISIBLE)

    def test_native_children_are_realized(self):
        view, boxes = self._make()
        self.assertTrue(view._has_vsb())
        self.assertEqual(view._content_h, 12 * 28 + 11 * 8)
        self.assertTrue(all(box.hwnd for box in boxes))

    def test_offscreen_native_children_are_clipped(self):
        view, boxes = self._make()
        self.assertTrue(self._visible(boxes[0].hwnd))
        self.assertFalse(self._visible(boxes[-1].hwnd))

        view.scroll_to(0, view._max_scroll_y())
        self.assertFalse(self._visible(boxes[0].hwnd))
        self.assertTrue(self._visible(boxes[-1].hwnd))

        view.scroll_to(0, 0)
        self.assertTrue(self._visible(boxes[0].hwnd))

    def test_wheel_over_native_child_scrolls_view(self):
        view, _ = self._make()
        before = view.scroll_y
        self.app.wheel(-120, view.x + 20, view.y + 20)
        self.assertGreater(view.scroll_y, before)
        self.assertLessEqual(view.scroll_y, view._max_scroll_y())
