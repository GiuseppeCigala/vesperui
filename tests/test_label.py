import pywinui as ui
from tests.helpers import WidgetTestCase


class LabelTests(WidgetTestCase):
    def test_measure_positive(self):
        label = self.add(ui.Label('Hello', size=16, bold=True))
        width, height = label.measure(self.app)
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)

    def test_default_color_comes_from_style(self):
        label = self.add(ui.Label('Hello'))
        self.assertIsNone(label.color)

    def test_all_alignments_draw(self):
        for align in ('left', 'center', 'right'):
            label = ui.Label('Sample', align=align)
            self.add(label)
            self.paint(label)
