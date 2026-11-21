import pywinui as ui
from tests.helpers import WidgetTestCase


class RadioButtonTests(WidgetTestCase):
    def _group(self):
        parent = ui.Panel(layout=ui.VBoxLayout(padding=0, spacing=4))
        self.app.root.add(parent)
        parent.set_bounds(10, 10, 220, 140)
        return parent

    def test_group_selection_is_exclusive(self):
        parent = self._group()
        first = ui.RadioButton('A', checked=True, group='demo')
        second = ui.RadioButton('B', group='demo')
        parent.add(first)
        parent.add(second)
        parent.arrange(self.app)
        self.assertTrue(first.is_checked())
        self.app.click_widget(second)
        self.assertTrue(second.is_checked())
        self.assertFalse(first.is_checked())

    def test_separate_groups_are_independent(self):
        parent = self._group()
        first = ui.RadioButton('A', checked=True, group='one')
        second = ui.RadioButton('B', group='two')
        parent.add(first)
        parent.add(second)
        parent.arrange(self.app)
        self.app.click_widget(second)
        self.assertTrue(first.is_checked())
        self.assertTrue(second.is_checked())

    def test_draw(self):
        radio = ui.RadioButton('A', checked=True)
        self.add(radio)
        self.paint(radio)
