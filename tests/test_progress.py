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

    def test_vertical_measure(self):
        progress = ui.ProgressBar(0.5, orientation='v', show_text=True)
        self.assertEqual(progress.measure(self.app), (36, 220))

    def test_vertical_value_and_draw(self):
        progress = self.add(ui.ProgressBar(0.6, orientation='v',
                                           show_text=True))
        self.paint(progress, 100, 260)
        progress.set_value(2)
        self.assertEqual(progress.value, 1.0)
        self.paint(progress, 100, 260)
        progress.set_value(0)
        self.paint(progress, 100, 260)

    def test_vertical_indeterminate_tick(self):
        progress = self.add(ui.ProgressBar(indeterminate=True,
                                           orientation='v'))
        progress.tick(0.5)
        self.assertGreater(progress.phase, 0.0)
        self.paint(progress, 100, 260)
