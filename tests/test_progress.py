import vesperui as ui
from tests.helpers import WidgetTestCase


class ProgressBarTests(WidgetTestCase):
    def test_value_clamps(self):
        progress = ui.ProgressBar(0.3)
        self.add(progress)
        progress.set_value(2)
        self.assertEqual(progress.value, 1.0)
        progress.set_value(-1)
        self.assertEqual(progress.value, 0.0)

    def test_indeterminate_tick_and_draw(self):
        progress = self.add(ui.ProgressBar(indeterminate=True))
        progress.tick(0.5)
        self.assertGreater(progress.phase, 0.0)
        labelled = ui.ProgressBar(0.5, show_text=True)
        self.add(labelled, y=40)
        self.paint(labelled)
