import vesperui as ui
from tests.helpers import WidgetTestCase


class VUMeterTests(WidgetTestCase):
    def test_measure(self):
        meter = ui.VUMeter(0.5)
        self.assertEqual(meter.measure(self.app), (260, 180))

    def test_initial_value_clamps(self):
        self.assertEqual(ui.VUMeter(2.0).value, 1.0)
        self.assertEqual(ui.VUMeter(-1.0).value, 0.0)

    def test_set_value_clamps_and_notifies(self):
        values = []
        meter = self.add(ui.VUMeter(0.5, on_change=values.append))
        self.assertTrue(meter.set_value(1.5))
        self.assertEqual(meter.value, 1.0)
        self.assertTrue(meter.set_value(-1.0))
        self.assertEqual(meter.value, 0.0)
        self.assertEqual(values, [1.0, 0.0])
        self.assertFalse(meter.set_value(0.0))
        self.assertTrue(meter.set_value(0.25, notify=False))
        self.assertEqual(values, [1.0, 0.0])

    def test_mouse_maps_angle_to_value(self):
        meter = self.add(ui.VUMeter(0.0))
        cx, cy, r = meter._geometry()
        for fraction in (0.0, 0.5, 1.0):
            x, y = meter._point(cx, cy, r, fraction)
            meter.on_mouse_down(x, y)
            self.assertAlmostEqual(meter.value, fraction, delta=0.05)

    def test_mouse_drag_updates_value(self):
        meter = self.add(ui.VUMeter(0.0))
        cx, cy, r = meter._geometry()
        start = meter._point(cx, cy, r, 0.2)
        end = meter._point(cx, cy, r, 0.8)
        meter.on_mouse_down(*start)
        self.assertTrue(meter._dragging)
        meter.on_mouse_move(*end)
        self.assertAlmostEqual(meter.value, 0.8, delta=0.05)
        meter.on_mouse_up(*end)
        self.assertFalse(meter._dragging)

    def test_click_outside_arc_snaps_to_nearest_end(self):
        meter = self.add(ui.VUMeter(0.5))
        cx, cy, r = meter._geometry()
        below_left = meter._point(cx, cy, r, -0.20)
        meter.on_mouse_down(*below_left)
        self.assertEqual(meter.value, 0.0)
        below_right = meter._point(cx, cy, r, 1.20)
        meter.on_mouse_down(*below_right)
        self.assertEqual(meter.value, 1.0)

    def test_keyboard(self):
        meter = self.add(ui.VUMeter(0.5))
        self.app.focus(meter)
        self.app.press_key(ui.VK_RIGHT)
        self.assertGreater(meter.value, 0.5)
        self.app.press_key(ui.VK_UP)
        self.assertAlmostEqual(meter.value, 0.6, delta=1e-6)
        self.app.press_key(ui.VK_LEFT)
        self.app.press_key(ui.VK_DOWN)
        self.assertAlmostEqual(meter.value, 0.5, delta=1e-6)

    def test_wheel_is_not_consumed(self):
        meter = self.add(ui.VUMeter(0.5))
        self.assertFalse(meter.on_wheel(120))
        self.assertEqual(meter.value, 0.5)

    def test_paint_states(self):
        meter = self.add(ui.VUMeter(0.0))
        for value in (0.0, 0.5, 1.0):
            meter.set_value(value, notify=False)
            self.paint(meter)
        meter.focused = True
        self.paint(meter)
        meter._dragging = True
        meter.set_value(0.75, notify=False)
        self.paint(meter)

    def test_custom_scale_and_labels(self):
        meter = self.add(ui.VUMeter(
            0.5, label='OUT', channel='R', on_change=None,
            scale=[('min', 0.0), ('mid', 0.5), ('max', 1.0)]))
        self.assertEqual(meter.label, 'OUT')
        self.assertEqual(meter.channel, 'R')
        self.assertEqual(len(meter.scale), 3)
        self.paint(meter)

    def test_peak_tracks_the_highest_value(self):
        meter = self.add(ui.VUMeter(0.2))
        self.assertEqual(meter.peak, 0.2)
        meter.set_value(0.8)
        self.assertEqual(meter.peak, 0.8)
        meter.set_value(0.3)
        self.assertEqual(meter.value, 0.3)
        self.assertEqual(meter.peak, 0.8)

    def test_peak_holds_then_decays_to_the_value(self):
        meter = self.add(ui.VUMeter(0.2, peak_hold_time=0.5,
                                    peak_decay=0.4))
        meter.set_value(1.0)
        meter.set_value(0.1)
        self.assertFalse(meter.tick(0.3))
        self.assertEqual(meter.peak, 1.0)
        self.assertTrue(meter.tick(0.4))
        self.assertAlmostEqual(meter.peak, 0.84, delta=1e-6)
        for _ in range(50):
            meter.tick(0.05)
        self.assertAlmostEqual(meter.peak, 0.1, delta=1e-6)
        self.assertFalse(meter.tick(0.05))

    def test_reset_peak(self):
        meter = self.add(ui.VUMeter(0.2))
        meter.set_value(0.9)
        meter.set_value(0.2)
        self.assertEqual(meter.peak, 0.9)
        meter.reset_peak()
        self.assertEqual(meter.peak, 0.2)
        self.assertEqual(meter._peak_age, 0.0)

    def test_peak_hold_disabled(self):
        meter = self.add(ui.VUMeter(0.5, peak_hold=False))
        meter.set_value(0.9)
        self.assertEqual(meter.peak, 0.9)
        meter.set_value(0.4)
        self.assertEqual(meter.peak, 0.4)
        self.assertFalse(meter.tick(1.0))

    def test_paint_with_peak_marker(self):
        meter = self.add(ui.VUMeter(0.2))
        meter.set_value(0.9)
        meter.set_value(0.35)
        self.assertGreater(meter.peak, meter.value)
        self.paint(meter)
        meter.set_value(meter.peak, notify=False)
        self.paint(meter)
