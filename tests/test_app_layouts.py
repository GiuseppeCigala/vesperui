import vesperui as ui
from tests.helpers import WidgetTestCase, WindowTestCase


class VBoxLayoutTests(WidgetTestCase):
    def _panel(self, padding=10, spacing=5):
        return ui.Panel(layout=ui.VBoxLayout(padding=padding, spacing=spacing))

    def test_measure(self):
        panel = self._panel()
        first = panel.add(ui.Label('alpha'))
        second = panel.add(ui.Label('beta'))
        fw, fh = first.measure(self.app)
        sw, sh = second.measure(self.app)
        self.assertEqual(panel.measure(self.app),
                         (max(fw, sw) + 20, fh + sh + 5 + 20))

    def test_arrange_fixed_children(self):
        panel = self._panel()
        first = panel.add(ui.Label('fixed'))
        second = panel.add(ui.Label('other'))
        panel.set_bounds(0, 0, 300, 200)
        panel.arrange(self.app)

        fw, fh = first.measure(self.app)
        sw, sh = second.measure(self.app)
        self.assertEqual((first.x, first.y, first.w, first.h), (10, 10, 280, fh))
        self.assertEqual((second.x, second.y, second.w, second.h),
                         (10, 10 + fh + 5, 280, sh))

    def test_stretch_distributes_remaining_space(self):
        panel = self._panel()
        fixed = panel.add(ui.Label('fixed'))
        grow = panel.add(ui.Label('grow'))
        grow.stretch = 1
        panel.set_bounds(0, 0, 300, 200)
        panel.arrange(self.app)

        _, fh = fixed.measure(self.app)
        self.assertEqual(fixed.h, fh)
        self.assertEqual(grow.y, 10 + fh + 5)
        self.assertEqual(grow.h, 180 - fh - 5)
        self.assertEqual(grow.w, 280)

    def test_clamps_when_container_is_too_small(self):
        panel = self._panel()
        first = panel.add(ui.Label('one'))
        second = panel.add(ui.Label('two'))
        third = panel.add(ui.Label('three'))
        panel.set_bounds(0, 0, 40, 30)
        panel.arrange(self.app)

        self.assertEqual((first.w, first.h), (20, 10))
        self.assertEqual(second.h, 0)
        self.assertEqual(third.h, 0)


class HBoxLayoutTests(WidgetTestCase):
    def test_measure_and_arrange(self):
        panel = ui.Panel(layout=ui.HBoxLayout(padding=4, spacing=6))
        first = panel.add(ui.Label('one'))
        second = panel.add(ui.Label('two'))
        fw, fh = first.measure(self.app)
        sw, sh = second.measure(self.app)

        self.assertEqual(panel.measure(self.app),
                         (fw + sw + 6 + 8, max(fh, sh) + 8))

        panel.set_bounds(0, 0, 200, 50)
        panel.arrange(self.app)
        self.assertEqual((first.x, first.y, first.w), (4, 4, fw))
        self.assertEqual((second.x, second.y, second.w), (4 + fw + 6, 4, sw))
        self.assertEqual(first.h, 42)
        self.assertEqual(second.h, 42)

    def test_stretch_distributes_remaining_space(self):
        panel = ui.Panel(layout=ui.HBoxLayout(padding=0, spacing=0))
        fixed = panel.add(ui.Label('x'))
        grow = panel.add(ui.Label('y'))
        grow.stretch = 1
        panel.set_bounds(0, 0, 300, 40)
        panel.arrange(self.app)

        fw, _ = fixed.measure(self.app)
        self.assertEqual(fixed.w, fw)
        self.assertEqual(grow.x, fw)
        self.assertEqual(grow.w, 300 - fw)


class AppInteractionTests(WidgetTestCase):
    def test_tab_cycles_focus(self):
        first = self.add(ui.Button('first'))
        second = self.add(ui.Button('second'))
        self.assertIsNone(self.app.focused)

        self.app.press_key(ui.VK_TAB)
        self.assertIs(self.app.focused, first)
        self.app.press_key(ui.VK_TAB)
        self.assertIs(self.app.focused, second)
        self.app.press_key(ui.VK_TAB)
        self.assertIs(self.app.focused, first)

    def test_keyboard_activation_of_focused_button(self):
        calls = []
        button = self.add(ui.Button('go', on_click=lambda: calls.append(1)))
        self.app.focus(button)
        self.app.press_key(ui.VK_RETURN)
        self.assertEqual(calls, [1])

    def test_hover_tracking(self):
        label = self.add(ui.Label('hover'))
        label.focusable = True
        self.app.move_mouse(label.x + 1, label.y + 1)
        self.assertIs(self.app.hovered, label)
        self.assertTrue(label.hovered)
        self.app.move_mouse(600, 470)
        self.assertFalse(label.hovered)
        self.assertIsNot(self.app.hovered, label)


class AppLifecycleTests(WindowTestCase):
    def test_create_layout_and_destroy(self):
        app = self.create()
        self.assertIsNotNone(app.hwnd)
        self.assertTrue(ui.user32.IsWindow(app.hwnd))

        hwnd = app.hwnd
        app.layout()
        app.pump()
        app.destroy()
        self.assertIsNone(app.hwnd)
        self.assertFalse(ui.user32.IsWindow(hwnd))

    def test_layout_realizes_native_widgets(self):
        app = self.create()
        box = self.add(ui.TextBox('hi'))
        self.assertIsNotNone(box.hwnd)
        self.assertTrue(ui.user32.IsWindow(box.hwnd))
        self.assertEqual(box.get_text(), 'hi')

    def test_click_owner_drawn_widget(self):
        app = self.create()
        calls = []
        button = self.add(ui.Button('Press', on_click=lambda: calls.append(1)))
        self.assertGreater(button.w, 0)
        app.click_widget(button)
        self.assertEqual(calls, [1])

    def test_recreate_after_destroy(self):
        app = self.create()
        app.destroy()
        app.create(show=False)
        app.pump()
        self.assertIsNotNone(app.hwnd)
        self.assertTrue(ui.user32.IsWindow(app.hwnd))

    def test_class_names_are_unique(self):
        other = ui.App('other window', 100, 100)
        self.assertNotEqual(other._class_name, self.app._class_name)
        other.destroy()
