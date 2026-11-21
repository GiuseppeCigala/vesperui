import pywinui as ui
from tests.helpers import WidgetTestCase


class TabBarTests(WidgetTestCase):
    def test_select_and_notify(self):
        events = []
        tabs = self.add(ui.TabBar(['A', 'B', 'C'], on_change=events.append))
        tabs.select(2)
        self.assertEqual(tabs.index, 2)
        self.assertEqual(events, [2])
        tabs.select(2)
        self.assertEqual(events, [2])
        tabs.select(-5)
        self.assertEqual(tabs.index, 0)

    def test_click_and_keyboard(self):
        tabs = ui.TabBar(['A', 'B'])
        self.add(tabs)
        self.paint(tabs)  # caches the app for hit testing
        second_x = tabs._tab_rects()[1][0] + 2
        self.app.click(second_x, tabs.y + 2)
        self.assertEqual(tabs.index, 1)
        self.app.focus(tabs)
        self.app.press_key(ui.VK_LEFT)
        self.assertEqual(tabs.index, 0)

    def test_draw(self):
        tabs = ui.TabBar(['A', 'B', 'C'])
        self.add(tabs)
        self.paint(tabs)
