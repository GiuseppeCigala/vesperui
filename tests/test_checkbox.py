import vesperui as ui
from tests.helpers import WidgetTestCase


class CheckBoxTests(WidgetTestCase):
    def test_click_toggles_and_notifies(self):
        events = []
        check = self.add(ui.CheckBox('Agree', on_change=events.append))
        self.assertFalse(check.is_checked())
        self.app.click_widget(check)
        self.assertTrue(check.is_checked())
        self.assertEqual(events, [True])
        self.app.click_widget(check)
        self.assertFalse(check.is_checked())
        self.assertEqual(events, [True, False])

    def test_set_checked_without_notify(self):
        events = []
        check = self.add(ui.CheckBox('Agree', on_change=events.append))
        check.set_checked(True, notify=False)
        self.assertTrue(check.is_checked())
        self.assertEqual(events, [])

    def test_keyboard_and_draw(self):
        check = self.add(ui.CheckBox('Agree'))
        self.app.focus(check)
        self.app.press_key(ui.VK_SPACE)
        self.assertTrue(check.is_checked())
        self.paint(check)
