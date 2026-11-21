import vesperui as ui
from tests.helpers import WidgetTestCase


class SeparatorTests(WidgetTestCase):
    def test_measure_orientation(self):
        horizontal = ui.Separator('h')
        vertical = ui.Separator('v')
        self.assertEqual(horizontal.measure(self.app)[1], 1)
        self.assertEqual(vertical.measure(self.app)[0], 1)

    def test_draw(self):
        for orientation in ('h', 'v'):
            separator = ui.Separator(orientation)
            self.add(separator, width=80, height=80)
            self.paint(separator)
