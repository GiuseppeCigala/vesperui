import pywinui as ui
from tests.helpers import WidgetTestCase


class HyperlinkTests(WidgetTestCase):
    def test_click_and_keyboard(self):
        calls = []
        link = self.add(ui.Hyperlink('Docs', on_click=lambda: calls.append(1)))
        self.app.click_widget(link)
        self.assertEqual(calls, [1])
        self.app.focus(link)
        self.app.press_key(ui.VK_RETURN)
        self.assertEqual(calls, [1, 1])

    def test_draw(self):
        link = ui.Hyperlink('Docs')
        self.add(link)
        self.paint(link)
