import vesperui as ui
from tests.helpers import WidgetTestCase


class SpectrumAnalyzerTests(WidgetTestCase):
    def test_measure_and_defaults(self):
        spec = ui.SpectrumAnalyzer()
        self.assertEqual(spec.measure(self.app), (460, 190))
        self.assertEqual(spec.bins, 96)
        self.assertEqual(len(spec.levels), 96)
        self.assertEqual(len(spec.peaks), 96)

    def test_set_spectrum_clamps_and_smooths(self):
        spec = self.add(ui.SpectrumAnalyzer(bins=4, attack=0.5, release=0.5))
        spec.set_spectrum([2.0, -1.0, 0.5, 0.5])
        self.assertEqual(spec.instant, [1.0, 0.0, 0.5, 0.5])
        self.assertEqual(spec.levels, [0.5, 0.0, 0.25, 0.25])
        spec.set_spectrum([1.0, 0.0, 0.5, 0.5])
        self.assertEqual(spec.levels, [0.75, 0.0, 0.375, 0.375])

    def test_peaks_rise_hold_and_decay(self):
        spec = self.add(ui.SpectrumAnalyzer(
            bins=4, peak_hold_frames=2, peak_decay=0.1))
        spec.set_spectrum([1.0, 0.5, 0.0, 0.0])
        self.assertEqual(spec.peaks[0], 1.0)
        spec.set_spectrum([0.0, 0.0, 0.0, 0.0])
        self.assertEqual(spec.peaks[0], 1.0)
        spec.set_spectrum([0.0, 0.0, 0.0, 0.0])
        self.assertEqual(spec.peaks[0], 1.0)
        spec.set_spectrum([0.0, 0.0, 0.0, 0.0])
        self.assertLess(spec.peaks[0], 1.0)

    def test_db_input_and_mapping(self):
        spec = self.add(ui.SpectrumAnalyzer(bins=4))
        self.assertAlmostEqual(spec.db_to_fraction(-12.0), 1.0)
        self.assertAlmostEqual(spec.db_to_fraction(-60.0), 0.0)
        self.assertAlmostEqual(spec.db_to_fraction(-36.0), 0.5)
        self.assertAlmostEqual(spec.db_to_fraction(-100.0), 0.0)
        spec.set_spectrum_db([-12.0, -60.0, -36.0, -24.0])
        self.assertEqual(spec.instant, [1.0, 0.0, 0.5, 0.75])

    def test_resample_any_length(self):
        spec = ui.SpectrumAnalyzer(bins=4)
        frame = spec.set_spectrum([0.0, 0.5, 1.0])
        self.assertEqual(len(frame), 4)
        self.assertEqual(len(spec.instant), 4)
        self.assertAlmostEqual(spec.instant[0], 0.0)
        self.assertAlmostEqual(spec.instant[-1], 1.0)
        spec.set_spectrum([])
        self.assertEqual(spec.instant, [0.0, 0.0, 0.0, 0.0])

    def test_reset(self):
        spec = self.add(ui.SpectrumAnalyzer(bins=4))
        spec.set_spectrum([1.0] * 4)
        spec.reset()
        self.assertEqual(spec.instant, [0.0] * 4)
        self.assertEqual(spec.levels, [0.0] * 4)
        self.assertEqual(spec.peaks, [0.0] * 4)

    def test_paint_states(self):
        spec = self.add(ui.SpectrumAnalyzer(bins=32))
        self.paint(spec, 480, 210)
        spec.set_spectrum([i / 31.0 for i in range(32)])
        self.paint(spec, 480, 210)
        spec.set_spectrum([1.0] * 32)
        self.paint(spec, 480, 210)
        spec.reset()
        self.paint(spec, 480, 210)

    def test_paint_custom_colors(self):
        spec = self.add(ui.SpectrumAnalyzer(
            bins=16, body_color=(200, 60, 200), cap_color=(60, 120, 255),
            hot_color=(255, 60, 60)))
        spec.set_spectrum([1.0] * 16)
        self.paint(spec, 480, 210)
