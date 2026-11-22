import vesperui as ui
from tests.helpers import WidgetTestCase


class LevelMeterTests(WidgetTestCase):
    def test_defaults_and_scalar_levels(self):
        meter = ui.LevelMeter(0.5)
        self.assertEqual(meter.levels, [0.5])
        self.assertEqual(meter.peaks, [0.5])
        self.assertEqual(ui.LevelMeter((0.2, 0.8)).levels, [0.2, 0.8])

    def test_measure_orientations(self):
        self.assertEqual(ui.LevelMeter(orientation='v').measure(self.app),
                         (108, 320))
        self.assertEqual(ui.LevelMeter(orientation='h').measure(self.app),
                         (340, 90))

    def test_set_level_clamps_and_notifies(self):
        events = []
        meter = self.add(ui.LevelMeter(
            (0.5, 0.5), on_change=lambda i, v: events.append((i, v))))
        self.assertTrue(meter.set_level(0, 2.0))
        self.assertEqual(meter.levels[0], 1.0)
        self.assertFalse(meter.set_level(0, 1.0))
        self.assertTrue(meter.set_level(1, -1.0))
        self.assertEqual(meter.levels[1], 0.0)
        self.assertEqual(events, [(0, 1.0), (1, 0.0)])
        self.assertTrue(meter.set_level(0, 0.25, notify=False))
        self.assertEqual(events, [(0, 1.0), (1, 0.0)])

    def test_set_levels(self):
        events = []
        meter = self.add(ui.LevelMeter(
            (0.2, 0.2), on_change=lambda i, v: events.append((i, v))))
        self.assertTrue(meter.set_levels((0.3, 0.9)))
        self.assertEqual(meter.levels, [0.3, 0.9])
        self.assertEqual(events, [(0, 0.3), (1, 0.9)])
        self.assertFalse(meter.set_levels((0.3, 0.9)))
        self.assertFalse(meter.set_levels(0.3))

    def test_db_mapping(self):
        self.assertEqual(ui.db_to_fraction(0.0), 1.0)
        self.assertEqual(ui.db_to_fraction(-60.0), 0.0)
        self.assertAlmostEqual(ui.db_to_fraction(-6.0), 0.87)
        self.assertAlmostEqual(ui.fraction_to_db(0.87), -6.0)
        self.assertAlmostEqual(ui.fraction_to_db(1.0), 0.0)
        previous = -1.0
        for db in (-60.0, -50.0, -40.0, -30.0, -20.0, -10.0, -6.0, -3.0, 0.0):
            fraction = ui.db_to_fraction(db)
            self.assertGreater(fraction, previous)
            previous = fraction

    def test_peak_holds_then_decays(self):
        meter = self.add(ui.LevelMeter((0.2, 0.4), peak_hold_time=0.5,
                                       peak_decay=0.4))
        meter.set_level(0, 1.0)
        meter.set_level(0, 0.1)
        self.assertEqual(meter.peaks[0], 1.0)
        self.assertFalse(meter.tick(0.3))
        self.assertEqual(meter.peaks[0], 1.0)
        self.assertTrue(meter.tick(0.4))
        self.assertAlmostEqual(meter.peaks[0], 0.84, delta=1e-6)
        for _ in range(50):
            meter.tick(0.05)
        self.assertAlmostEqual(meter.peaks[0], 0.1, delta=1e-6)
        self.assertEqual(meter.peaks[1], 0.4)

    def test_reset_peaks(self):
        meter = self.add(ui.LevelMeter((0.2, 0.4)))
        meter.set_levels((0.9, 0.8))
        meter.set_levels((0.2, 0.4))
        meter.reset_peaks()
        self.assertEqual(meter.peaks, [0.2, 0.4])
        self.assertEqual(meter._peak_age, [0.0, 0.0])

    def test_peak_hold_disabled(self):
        meter = self.add(ui.LevelMeter((0.5, 0.5), peak_hold=False))
        meter.set_level(0, 0.9)
        self.assertEqual(meter.peaks[0], 0.9)
        meter.set_level(0, 0.4)
        self.assertEqual(meter.peaks[0], 0.4)
        self.assertFalse(meter.tick(1.0))

    def test_vertical_mouse_mapping(self):
        meter = self.add(ui.LevelMeter((0.5, 0.5), orientation='v'))
        rects = meter._bar_rects()
        bx, by, bw, bh = rects[0]
        cx = bx + bw // 2
        meter.on_mouse_down(cx, by + bh)
        self.assertEqual(meter.levels[0], 0.0)
        meter.on_mouse_move(cx, by)
        self.assertEqual(meter.levels[0], 1.0)
        bx1, by1, bw1, bh1 = rects[1]
        meter.on_mouse_move(bx1 + bw1 // 2, by1 + bh1 // 2)
        self.assertAlmostEqual(meter.levels[0], 0.5, delta=0.01)
        self.assertEqual(meter.levels[1], 0.5)
        meter.on_mouse_up(cx, by)
        meter.on_mouse_down(bx1 + bw1 // 2, by1)
        self.assertEqual(meter.levels[1], 1.0)
        meter.on_mouse_up(bx1 + bw1 // 2, by1)
        self.assertFalse(meter._dragging)

    def test_horizontal_mouse_mapping(self):
        meter = self.add(ui.LevelMeter((0.5, 0.5), orientation='h'))
        rects = meter._bar_rects()
        bx, by, bw, bh = rects[0]
        meter.on_mouse_down(bx, by + bh // 2)
        self.assertEqual(meter.levels[0], 0.0)
        meter.on_mouse_move(bx + bw, by + bh // 2)
        self.assertEqual(meter.levels[0], 1.0)
        meter.on_mouse_up(bx + bw, by + bh // 2)
        bx1, by1, bw1, bh1 = rects[1]
        meter.on_mouse_down(bx1 + bw1 // 2, by1 + bh1 // 2)
        self.assertAlmostEqual(meter.levels[1], 0.5, delta=0.01)
        meter.on_mouse_up(bx1 + bw1 // 2, by1 + bh1 // 2)

    def test_keyboard_adjusts_the_active_channel(self):
        meter = self.add(ui.LevelMeter((0.5, 0.5), orientation='h'))
        self.app.focus(meter)
        self.app.press_key(ui.VK_RIGHT)
        self.assertAlmostEqual(meter.levels[0], 0.55, delta=1e-6)
        self.assertEqual(meter.levels[1], 0.5)
        self.app.press_key(ui.VK_DOWN)
        self.assertAlmostEqual(meter.levels[0], 0.5, delta=1e-6)

    def test_wheel_is_not_consumed(self):
        meter = self.add(ui.LevelMeter((0.5, 0.5)))
        self.assertFalse(meter.on_wheel(120))

    def test_paint_orientations_and_states(self):
        meter_v = self.add(ui.LevelMeter((0.0, 1.0), orientation='v'))
        self.paint(meter_v, 130, 340)
        meter_v.focused = True
        meter_v._dragging = True
        self.paint(meter_v, 130, 340)
        meter_h = self.add(ui.LevelMeter((0.3, 0.9), orientation='h'))
        self.paint(meter_h, 360, 110)
        meter_h.set_levels((0.6, 0.0), notify=False)
        self.paint(meter_h, 360, 110)
        single = self.add(ui.LevelMeter(0.45, orientation='v',
                                        show_db=False, peak_hold=False))
        self.paint(single, 130, 340)

    def test_paint_with_peak_markers(self):
        meter_h = self.add(ui.LevelMeter((0.2, 0.2), orientation='h'))
        meter_h.set_levels((0.9, 0.8))
        meter_h.set_levels((0.2, 0.25), notify=False)
        self.paint(meter_h, 360, 110)
        meter_v = self.add(ui.LevelMeter((0.2, 0.2), orientation='v'))
        meter_v.set_levels((0.9, 0.8))
        meter_v.set_levels((0.2, 0.25), notify=False)
        self.paint(meter_v, 130, 340)

    def test_alias(self):
        self.assertIs(ui.BarVUMeter, ui.LevelMeter)
