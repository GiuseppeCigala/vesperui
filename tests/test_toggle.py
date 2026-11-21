import vesperui as ui
from tests.helpers import WidgetTestCase


class ToggleSwitchTests(WidgetTestCase):
    def test_size_and_click(self):
        events = []
        toggle = self.add(ui.ToggleSwitch(on_change=events.append))
        self.assertEqual((toggle.w, toggle.h), (44, 24))
        self.app.click_widget(toggle)
        self.assertTrue(toggle.is_checked())
        self.assertEqual(events, [True])
        self.app.click_widget(toggle)
        self.assertFalse(toggle.is_checked())
        self.assertEqual(events, [True, False])

    def test_keyboard_and_draw(self):
        toggle = self.add(ui.ToggleSwitch())
        self.app.focus(toggle)
        self.app.press_key(ui.VK_SPACE)
        self.assertTrue(toggle.is_checked())
        self.paint(toggle)
