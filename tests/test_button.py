import vesperui as ui
from tests.helpers import WidgetTestCase


class ButtonTests(WidgetTestCase):
    def test_click_callback_and_focus(self):
        calls = []
        button = self.add(ui.Button('Go', on_click=lambda: calls.append(1)))
        self.app.click_widget(button)
        self.assertEqual(calls, [1])
        self.assertIs(self.app.focused, button)

    def test_keyboard_activation(self):
        calls = []
        button = self.add(ui.Button('Go', on_click=lambda: calls.append(1)))
        self.app.focus(button)
        self.app.press_key(ui.VK_RETURN)
        self.app.press_key(ui.VK_SPACE)
        self.assertEqual(calls, [1, 1])

    def test_draw_default_and_accent(self):
        for accent in (None, (20, 200, 120)):
            button = ui.Button('Go', accent=accent)
            self.add(button)
            self.paint(button)
